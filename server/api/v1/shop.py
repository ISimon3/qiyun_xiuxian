# 商城API接口

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.crud import CharacterCRUD
from server.database.models import User
from server.core.dependencies import get_current_active_user
from server.core.systems.shop_system import ShopSystem
from shared.schemas import (
    BaseResponse, ShopListResponse, PurchaseItem, 
    CreateTradeRequest, BuyTradeRequest, CancelTradeRequest, TradeResult
)

router = APIRouter()


@router.get("/shop-info", response_model=BaseResponse, summary="获取商城信息")
async def get_shop_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取商城信息，包括系统商城和玩家交易所
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取商城信息
        result = await ShopSystem.get_shop_info(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取商城信息成功" if result["success"] else result.get("message", "获取商城信息失败"),
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商城信息失败: {str(e)}"
        )


@router.post("/purchase-system-item", response_model=BaseResponse, summary="购买系统商城物品")
async def purchase_system_item(
    request: PurchaseItem,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    购买系统商城物品
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 购买物品
        result = await ShopSystem.purchase_system_item(
            db, character, request.shop_item_id, request.quantity
        )

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"购买物品失败: {str(e)}"
        )


@router.post("/create-trade", response_model=BaseResponse, summary="创建玩家交易")
async def create_trade(
    request: CreateTradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建玩家交易
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 创建交易
        result = await ShopSystem.create_player_trade(
            db, character, request.item_id, request.quantity, 
            request.price, request.currency_type
        )

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建交易失败: {str(e)}"
        )


@router.post("/buy-trade", response_model=BaseResponse, summary="购买玩家交易物品")
async def buy_trade(
    request: BuyTradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    购买玩家交易物品
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 购买交易物品
        result = await ShopSystem.buy_player_trade(db, character, request.trade_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"购买交易物品失败: {str(e)}"
        )


@router.post("/cancel-trade", response_model=BaseResponse, summary="取消玩家交易")
async def cancel_trade(
    request: CancelTradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消玩家交易
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 取消交易
        result = await ShopSystem.cancel_player_trade(db, character, request.trade_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消交易失败: {str(e)}"
        )


@router.get("/my-trades", response_model=BaseResponse, summary="获取我的交易")
async def get_my_trades(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的交易列表
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取交易列表
        result = await ShopSystem.get_my_trades(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取交易列表成功" if result["success"] else result.get("message", "获取交易列表失败"),
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易列表失败: {str(e)}"
        )
