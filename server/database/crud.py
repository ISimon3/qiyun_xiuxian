# 数据库增删改查操作封装

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext

from server.database.models import User, Character, Item, InventoryItem, EquippedItem, GameLog, UserSession
from shared.schemas import UserRegister, CharacterUpdate

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCRUD:
    """用户相关CRUD操作"""

    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserRegister) -> User:
        """创建用户"""
        hashed_password = UserCRUD.hash_password(user_data.password)

        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user_login_time(db: AsyncSession, user_id: int) -> None:
        """更新用户最后登录时间"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await db.commit()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = await UserCRUD.get_user_by_username(db, username)
        if not user:
            return None
        if not UserCRUD.verify_password(password, user.hashed_password):
            return None
        return user


class CharacterCRUD:
    """角色相关CRUD操作"""

    @staticmethod
    async def get_or_create_character(db: AsyncSession, user_id: int, username: str) -> Character:
        """获取或创建用户角色（每个用户只有一个角色）"""
        try:
            # 先尝试获取现有角色
            result = await db.execute(
                select(Character).where(Character.user_id == user_id).limit(1)
            )
            existing_character = result.scalar_one_or_none()

            if existing_character:
                return existing_character

            # 如果不存在，创建新角色
            # 使用简单的默认灵根，避免复杂的随机选择
            selected_root = "单灵根"

            # 生成8位随机角色ID
            import random
            while True:
                random_id = random.randint(10000000, 99999999)  # 8位随机数
                # 检查ID是否已存在
                existing_check = await db.execute(
                    select(Character).where(Character.id == random_id)
                )
                if not existing_check.scalar_one_or_none():
                    break

            # 创建角色，使用用户名作为角色名
            db_character = Character(
                id=random_id,
                user_id=user_id,
                name=username,
                spiritual_root=selected_root
            )

            db.add(db_character)
            await db.commit()
            await db.refresh(db_character)

            return db_character

        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    def _get_random_spiritual_root() -> str:
        """随机选择灵根类型（根据稀有度权重）"""
        from shared.constants import SPIRITUAL_ROOTS
        import random

        # 随机分配灵根（根据稀有度权重）
        spiritual_roots = list(SPIRITUAL_ROOTS.keys())
        weights = []
        for root_name in spiritual_roots:
            root_info = SPIRITUAL_ROOTS[root_name]
            rarity_weights = {
                "common": 40,
                "uncommon": 20,
                "rare": 10,
                "epic": 3,
                "legendary": 1
            }
            weights.append(rarity_weights.get(root_info["rarity"], 10))

        return random.choices(spiritual_roots, weights=weights)[0]

    @staticmethod
    async def get_character_by_id(db: AsyncSession, character_id: int) -> Optional[Character]:
        """根据ID获取角色"""
        result = await db.execute(
            select(Character)
            .options(selectinload(Character.equipped_items).selectinload(EquippedItem.item))
            .where(Character.id == character_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_character(db: AsyncSession, user_id: int) -> Optional[Character]:
        """获取用户角色（每个用户只有一个角色）"""
        result = await db.execute(
            select(Character)
            .options(selectinload(Character.equipped_items).selectinload(EquippedItem.item))
            .where(Character.user_id == user_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_character(db: AsyncSession, character_id: int, update_data: CharacterUpdate) -> Optional[Character]:
        """更新角色信息"""
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await CharacterCRUD.get_character_by_id(db, character_id)

        await db.execute(
            update(Character)
            .where(Character.id == character_id)
            .values(**update_dict, updated_at=datetime.utcnow())
        )
        await db.commit()
        return await CharacterCRUD.get_character_by_id(db, character_id)

    @staticmethod
    async def update_character_activity(db: AsyncSession, character_id: int) -> None:
        """更新角色活跃时间"""
        await db.execute(
            update(Character)
            .where(Character.id == character_id)
            .values(last_active=datetime.utcnow())
        )
        await db.commit()


class ItemCRUD:
    """物品相关CRUD操作"""

    @staticmethod
    async def get_item_by_id(db: AsyncSession, item_id: int) -> Optional[Item]:
        """根据ID获取物品"""
        result = await db.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_items_by_type(db: AsyncSession, item_type: str) -> List[Item]:
        """根据类型获取物品列表"""
        result = await db.execute(
            select(Item)
            .where(Item.item_type == item_type)
            .order_by(Item.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_item_by_name(db: AsyncSession, name: str) -> Optional[Item]:
        """根据名称获取物品"""
        result = await db.execute(select(Item).where(Item.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def search_items(db: AsyncSession, keyword: str, limit: int = 50) -> List[Item]:
        """搜索物品"""
        result = await db.execute(
            select(Item)
            .where(or_(
                Item.name.ilike(f"%{keyword}%"),
                Item.description.ilike(f"%{keyword}%")
            ))
            .limit(limit)
        )
        return result.scalars().all()


class InventoryCRUD:
    """背包相关CRUD操作"""

    @staticmethod
    async def get_character_inventory(db: AsyncSession, character_id: int) -> List[InventoryItem]:
        """获取角色背包"""
        result = await db.execute(
            select(InventoryItem)
            .options(selectinload(InventoryItem.item))
            .where(InventoryItem.character_id == character_id)
            .order_by(InventoryItem.slot_position.asc().nullslast(), InventoryItem.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def add_item_to_inventory(
        db: AsyncSession,
        character_id: int,
        item_id: int,
        quantity: int = 1,
        attribute_variation: float = 1.0,
        actual_attributes: Optional[Dict[str, Any]] = None
    ) -> InventoryItem:
        """添加物品到背包"""
        inventory_item = InventoryItem(
            character_id=character_id,
            item_id=item_id,
            quantity=quantity,
            attribute_variation=attribute_variation,
            actual_attributes=actual_attributes
        )

        db.add(inventory_item)
        await db.commit()
        await db.refresh(inventory_item)
        return inventory_item

    @staticmethod
    async def remove_item_from_inventory(db: AsyncSession, inventory_item_id: int, quantity: int = None) -> bool:
        """从背包移除物品"""
        result = await db.execute(select(InventoryItem).where(InventoryItem.id == inventory_item_id))
        inventory_item = result.scalar_one_or_none()

        if not inventory_item:
            return False

        if quantity is None or quantity >= inventory_item.quantity:
            # 删除整个物品
            await db.delete(inventory_item)
        else:
            # 减少数量
            inventory_item.quantity -= quantity

        await db.commit()
        return True


class EquipmentCRUD:
    """装备相关CRUD操作"""

    @staticmethod
    async def get_character_equipment(db: AsyncSession, character_id: int) -> List[EquippedItem]:
        """获取角色装备"""
        result = await db.execute(
            select(EquippedItem)
            .options(selectinload(EquippedItem.item))
            .where(EquippedItem.character_id == character_id)
        )
        return result.scalars().all()

    @staticmethod
    async def equip_item(
        db: AsyncSession,
        character_id: int,
        item_id: int,
        slot: str,
        attribute_variation: float = 1.0,
        actual_attributes: Optional[Dict[str, Any]] = None
    ) -> EquippedItem:
        """装备物品"""
        # 先卸下该部位的装备
        await EquipmentCRUD.unequip_item(db, character_id, slot)

        equipped_item = EquippedItem(
            character_id=character_id,
            item_id=item_id,
            slot=slot,
            attribute_variation=attribute_variation,
            actual_attributes=actual_attributes
        )

        db.add(equipped_item)
        await db.commit()
        await db.refresh(equipped_item)
        return equipped_item

    @staticmethod
    async def unequip_item(db: AsyncSession, character_id: int, slot: str) -> bool:
        """卸下装备"""
        result = await db.execute(
            select(EquippedItem)
            .where(and_(EquippedItem.character_id == character_id, EquippedItem.slot == slot))
        )
        equipped_item = result.scalar_one_or_none()

        if equipped_item:
            await db.delete(equipped_item)
            await db.commit()
            return True
        return False


class GameLogCRUD:
    """游戏日志相关CRUD操作"""

    @staticmethod
    async def create_log(
        db: AsyncSession,
        character_id: int,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> GameLog:
        """创建游戏日志"""
        game_log = GameLog(
            character_id=character_id,
            event_type=event_type,
            message=message,
            details=details
        )

        db.add(game_log)
        await db.commit()
        await db.refresh(game_log)
        return game_log

    @staticmethod
    async def get_character_logs(
        db: AsyncSession,
        character_id: int,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[GameLog]:
        """获取角色日志"""
        query = select(GameLog).where(GameLog.character_id == character_id)

        if event_type:
            query = query.where(GameLog.event_type == event_type)

        query = query.order_by(desc(GameLog.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete_old_logs(db: AsyncSession, days_to_keep: int = 30) -> int:
        """删除旧日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        result = await db.execute(
            delete(GameLog).where(GameLog.created_at < cutoff_date)
        )
        await db.commit()
        return result.rowcount


class SessionCRUD:
    """用户会话相关CRUD操作"""

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        token_jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """创建用户会话"""
        session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session_by_jti(db: AsyncSession, token_jti: str) -> Optional[UserSession]:
        """根据JWT ID获取会话"""
        result = await db.execute(
            select(UserSession)
            .where(and_(UserSession.token_jti == token_jti, UserSession.is_active == True))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session_activity(db: AsyncSession, token_jti: str) -> None:
        """更新会话活跃时间"""
        await db.execute(
            update(UserSession)
            .where(UserSession.token_jti == token_jti)
            .values(last_used=datetime.utcnow())
        )
        await db.commit()

    @staticmethod
    async def deactivate_session(db: AsyncSession, token_jti: str) -> bool:
        """停用会话"""
        result = await db.execute(
            update(UserSession)
            .where(UserSession.token_jti == token_jti)
            .values(is_active=False)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """清理过期会话"""
        current_time = datetime.utcnow()

        result = await db.execute(
            update(UserSession)
            .where(UserSession.expires_at < current_time)
            .values(is_active=False)
        )
        await db.commit()
        return result.rowcount
