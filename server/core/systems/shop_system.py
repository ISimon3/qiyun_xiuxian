# 商城系统核心逻辑

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from server.database.models import Character, Item, ShopItem, PlayerTrade, InventoryItem
from server.database.crud import InventoryCRUD, GameLogCRUD
from shared.constants import ITEM_QUALITY


class ShopSystem:
    """商城系统"""

    @staticmethod
    async def get_shop_info(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """获取商城信息"""
        try:
            # 获取系统商城物品
            system_items = await ShopSystem._get_system_shop_items(db)
            
            # 获取玩家交易所物品
            player_trades = await ShopSystem._get_player_trades(db, character)
            
            return {
                "success": True,
                "system_items": system_items,
                "player_trades": player_trades
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取商城信息失败: {str(e)}"
            }

    @staticmethod
    async def _get_system_shop_items(db: AsyncSession) -> List[Dict[str, Any]]:
        """获取系统商城物品"""
        result = await db.execute(
            select(ShopItem)
            .options(selectinload(ShopItem.item))
            .where(and_(
                ShopItem.shop_type == "system",
                ShopItem.is_active == True
            ))
            .order_by(ShopItem.item_id)
        )
        shop_items = result.scalars().all()
        
        items_data = []
        for shop_item in shop_items:
            item_data = {
                "id": shop_item.id,
                "item_id": shop_item.item_id,
                "item_info": {
                    "id": shop_item.item.id,
                    "name": shop_item.item.name,
                    "description": shop_item.item.description,
                    "item_type": shop_item.item.item_type,
                    "quality": shop_item.item.quality,
                    "stack_size": shop_item.item.stack_size,
                    "sell_price": shop_item.item.sell_price,
                    "equipment_slot": shop_item.item.equipment_slot,
                    "required_realm": shop_item.item.required_realm,
                    "base_attributes": shop_item.item.base_attributes,
                    "special_effects": shop_item.item.special_effects
                },
                "price": shop_item.price,
                "currency_type": shop_item.currency_type,
                "stock": shop_item.stock
            }
            items_data.append(item_data)
        
        return items_data

    @staticmethod
    async def _get_player_trades(db: AsyncSession, character: Character) -> List[Dict[str, Any]]:
        """获取玩家交易所物品"""
        result = await db.execute(
            select(PlayerTrade)
            .options(
                selectinload(PlayerTrade.item),
                selectinload(PlayerTrade.seller)
            )
            .where(and_(
                PlayerTrade.status == "ACTIVE",
                PlayerTrade.expires_at > datetime.now(),
                PlayerTrade.seller_id != character.id  # 不显示自己的交易
            ))
            .order_by(PlayerTrade.created_at.desc())
        )
        trades = result.scalars().all()
        
        trades_data = []
        for trade in trades:
            trade_data = {
                "id": trade.id,
                "seller_name": trade.seller.name,
                "item_info": {
                    "id": trade.item.id,
                    "name": trade.item.name,
                    "description": trade.item.description,
                    "item_type": trade.item.item_type,
                    "quality": trade.item.quality,
                    "stack_size": trade.item.stack_size,
                    "sell_price": trade.item.sell_price,
                    "equipment_slot": trade.item.equipment_slot,
                    "required_realm": trade.item.required_realm,
                    "base_attributes": trade.item.base_attributes,
                    "special_effects": trade.item.special_effects
                },
                "quantity": trade.quantity,
                "price": trade.price,
                "currency_type": trade.currency_type,
                "created_at": trade.created_at.isoformat(),
                "expires_at": trade.expires_at.isoformat()
            }
            trades_data.append(trade_data)
        
        return trades_data

    @staticmethod
    async def purchase_system_item(db: AsyncSession, character: Character, shop_item_id: int, quantity: int = 1) -> Dict[str, Any]:
        """购买系统商城物品"""
        try:
            # 获取商城物品
            result = await db.execute(
                select(ShopItem)
                .options(selectinload(ShopItem.item))
                .where(and_(
                    ShopItem.id == shop_item_id,
                    ShopItem.shop_type == "system",
                    ShopItem.is_active == True
                ))
            )
            shop_item = result.scalar_one_or_none()
            
            if not shop_item:
                return {"success": False, "message": "商品不存在或已下架"}
            
            # 检查库存
            if shop_item.stock != -1 and shop_item.stock < quantity:
                return {"success": False, "message": "库存不足"}
            
            # 计算总价
            total_price = shop_item.price * quantity
            
            # 检查货币
            if shop_item.currency_type == "gold":
                if character.gold < total_price:
                    return {"success": False, "message": "金币不足"}
                character.gold -= total_price
            elif shop_item.currency_type == "spirit_stone":
                if character.spirit_stone < total_price:
                    return {"success": False, "message": "灵石不足"}
                character.spirit_stone -= total_price
            else:
                return {"success": False, "message": "不支持的货币类型"}
            
            # 添加物品到背包
            await InventoryCRUD.add_item_to_inventory(db, character.id, shop_item.item_id, quantity)
            
            # 更新库存
            if shop_item.stock != -1:
                shop_item.stock -= quantity
                shop_item.sold_count += quantity
            
            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "SHOP_PURCHASE",
                f"购买了{quantity}个{shop_item.item.name}",
                {
                    "shop_item_id": shop_item_id,
                    "item_name": shop_item.item.name,
                    "quantity": quantity,
                    "total_price": total_price,
                    "currency_type": shop_item.currency_type
                }
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功购买{quantity}个{shop_item.item.name}"
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"购买失败: {str(e)}"
            }

    @staticmethod
    async def create_player_trade(db: AsyncSession, character: Character, item_id: int, quantity: int, price: int, currency_type: str = "gold") -> Dict[str, Any]:
        """创建玩家交易"""
        try:
            # 检查物品是否存在于背包中（获取所有相同物品的记录）
            result = await db.execute(
                select(InventoryItem)
                .options(selectinload(InventoryItem.item))
                .where(and_(
                    InventoryItem.character_id == character.id,
                    InventoryItem.item_id == item_id
                ))
                .order_by(InventoryItem.quantity.desc())  # 按数量降序排列
            )
            inventory_items = result.scalars().all()

            if not inventory_items:
                return {"success": False, "message": "背包中没有该物品"}

            # 计算总数量
            total_quantity = sum(item.quantity for item in inventory_items)
            if total_quantity < quantity:
                return {"success": False, "message": "背包中没有足够的物品"}

            # 从背包中移除物品（从数量最多的记录开始移除）
            remaining_to_remove = quantity
            for inventory_item in inventory_items:
                if remaining_to_remove <= 0:
                    break

                if inventory_item.quantity <= remaining_to_remove:
                    # 删除整个记录
                    remaining_to_remove -= inventory_item.quantity
                    await db.delete(inventory_item)
                else:
                    # 减少数量
                    inventory_item.quantity -= remaining_to_remove
                    remaining_to_remove = 0
            
            # 创建交易
            trade = PlayerTrade(
                seller_id=character.id,
                item_id=item_id,
                quantity=quantity,
                price=price,
                currency_type=currency_type,
                expires_at=datetime.now() + timedelta(days=7)  # 7天后过期
            )
            
            db.add(trade)
            await db.flush()  # 获取ID
            
            # 获取物品信息用于日志
            first_item = inventory_items[0]  # 使用第一个物品记录获取物品信息

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "TRADE_CREATE",
                f"上架了{quantity}个{first_item.item.name}",
                {
                    "trade_id": trade.id,
                    "item_name": first_item.item.name,
                    "quantity": quantity,
                    "price": price,
                    "currency_type": currency_type
                }
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功上架{quantity}个{first_item.item.name}",
                "trade_id": trade.id
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"创建交易失败: {str(e)}"
            }

    @staticmethod
    async def buy_player_trade(db: AsyncSession, character: Character, trade_id: int) -> Dict[str, Any]:
        """购买玩家交易物品"""
        try:
            # 获取交易信息
            result = await db.execute(
                select(PlayerTrade)
                .options(
                    selectinload(PlayerTrade.item),
                    selectinload(PlayerTrade.seller)
                )
                .where(and_(
                    PlayerTrade.id == trade_id,
                    PlayerTrade.status == "ACTIVE",
                    PlayerTrade.expires_at > datetime.now()
                ))
            )
            trade = result.scalar_one_or_none()
            
            if not trade:
                return {"success": False, "message": "交易不存在或已过期"}
            
            if trade.seller_id == character.id:
                return {"success": False, "message": "不能购买自己的物品"}
            
            # 检查货币
            if trade.currency_type == "gold":
                if character.gold < trade.price:
                    return {"success": False, "message": "金币不足"}
                character.gold -= trade.price
                trade.seller.gold += trade.price
            elif trade.currency_type == "spirit_stone":
                if character.spirit_stone < trade.price:
                    return {"success": False, "message": "灵石不足"}
                character.spirit_stone -= trade.price
                trade.seller.spirit_stone += trade.price
            else:
                return {"success": False, "message": "不支持的货币类型"}
            
            # 添加物品到买家背包
            await InventoryCRUD.add_item_to_inventory(db, character.id, trade.item_id, trade.quantity)
            
            # 更新交易状态
            trade.status = "SOLD"
            trade.buyer_id = character.id
            trade.sold_at = datetime.now()
            
            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "TRADE_BUY",
                f"购买了{trade.quantity}个{trade.item.name}",
                {
                    "trade_id": trade_id,
                    "item_name": trade.item.name,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "currency_type": trade.currency_type,
                    "seller_name": trade.seller.name
                }
            )
            
            await GameLogCRUD.create_log(
                db,
                trade.seller_id,
                "TRADE_SELL",
                f"出售了{trade.quantity}个{trade.item.name}",
                {
                    "trade_id": trade_id,
                    "item_name": trade.item.name,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "currency_type": trade.currency_type,
                    "buyer_name": character.name
                }
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功购买{trade.quantity}个{trade.item.name}"
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"购买失败: {str(e)}"
            }

    @staticmethod
    async def cancel_player_trade(db: AsyncSession, character: Character, trade_id: int) -> Dict[str, Any]:
        """取消玩家交易"""
        try:
            # 获取交易信息
            result = await db.execute(
                select(PlayerTrade)
                .options(selectinload(PlayerTrade.item))
                .where(and_(
                    PlayerTrade.id == trade_id,
                    PlayerTrade.seller_id == character.id,
                    PlayerTrade.status == "ACTIVE"
                ))
            )
            trade = result.scalar_one_or_none()
            
            if not trade:
                return {"success": False, "message": "交易不存在或无权取消"}
            
            # 返还物品到背包
            await InventoryCRUD.add_item_to_inventory(db, character.id, trade.item_id, trade.quantity)
            
            # 更新交易状态
            trade.status = "CANCELLED"
            
            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "TRADE_CANCEL",
                f"取消了{trade.quantity}个{trade.item.name}的交易",
                {
                    "trade_id": trade_id,
                    "item_name": trade.item.name,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "currency_type": trade.currency_type
                }
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功取消{trade.quantity}个{trade.item.name}的交易"
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"取消交易失败: {str(e)}"
            }

    @staticmethod
    async def get_my_trades(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """获取我的交易"""
        try:
            result = await db.execute(
                select(PlayerTrade)
                .options(selectinload(PlayerTrade.item))
                .where(PlayerTrade.seller_id == character.id)
                .order_by(PlayerTrade.created_at.desc())
            )
            trades = result.scalars().all()
            
            trades_data = []
            for trade in trades:
                trade_data = {
                    "id": trade.id,
                    "item_info": {
                        "id": trade.item.id,
                        "name": trade.item.name,
                        "description": trade.item.description,
                        "item_type": trade.item.item_type,
                        "quality": trade.item.quality
                    },
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "currency_type": trade.currency_type,
                    "status": trade.status,
                    "created_at": trade.created_at.isoformat(),
                    "expires_at": trade.expires_at.isoformat(),
                    "sold_at": trade.sold_at.isoformat() if trade.sold_at else None
                }
                trades_data.append(trade_data)
            
            return {
                "success": True,
                "trades": trades_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取交易列表失败: {str(e)}"
            }
