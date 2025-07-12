# 游戏行为接口 (炼丹、突破等)

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.crud import CharacterCRUD
from server.database.models import User
from server.core.dependencies import get_current_active_user
from server.core.systems.luck_system import LuckSystem
from shared.schemas import (
    BaseResponse, DailySignInResult, UseLuckItemRequest, UseLuckItemResult,
    LuckSystemInfo, LuckEffectInfo, CaveInfo, UpgradeCaveRequest, UpgradeCaveResult,
    FarmInfo, PlantSeedRequest, HarvestPlotRequest, UnlockPlotRequest,
    PlantSeedResult, HarvestResult, UnlockPlotResult,
    AlchemyInfo, StartAlchemyRequest, StartAlchemyResult,
    CollectAlchemyRequest, CollectAlchemyResult
)
from shared.utils import get_luck_level_name
from shared.constants import LUCK_LEVELS, DEFAULT_CONFIG

router = APIRouter()


@router.post("/daily-sign", response_model=BaseResponse, summary="每日签到")
async def daily_sign_in(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    每日签到，随机获得气运值
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 执行签到
        result = await LuckSystem.daily_sign_in(db, character)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=DailySignInResult(**result).model_dump()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"每日签到失败: {str(e)}"
        )


@router.post("/use-luck-item", response_model=BaseResponse, summary="使用气运道具")
async def use_luck_item(
    request: UseLuckItemRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    使用气运道具（如转运丹）
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 使用道具
        result = await LuckSystem.use_luck_item(db, character, request.item_id, request.quantity)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=UseLuckItemResult(**result).model_dump() if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"使用气运道具失败: {str(e)}"
        )


@router.get("/luck-info", response_model=BaseResponse, summary="获取气运系统信息")
async def get_luck_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前角色的气运系统详细信息
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 计算气运影响
        luck_level = get_luck_level_name(character.luck_value)
        luck_color = LUCK_LEVELS[luck_level]["color"]

        # 检查今日是否可以签到
        from datetime import datetime
        today = datetime.now().date()
        last_sign_date = character.last_active.date() if character.last_active else None
        can_sign_today = last_sign_date != today

        # 获取修炼影响
        cultivation_effect = LuckSystem.calculate_luck_effect_on_cultivation(character.luck_value)

        # 获取突破加成
        breakthrough_bonus = (character.luck_value - 50) * 0.01

        # 获取掉落影响
        drop_effects = LuckSystem.calculate_luck_effect_on_drops(character.luck_value)

        luck_info = LuckSystemInfo(
            current_luck=character.luck_value,
            luck_level=luck_level,
            luck_color=luck_color,
            can_sign_today=can_sign_today,
            last_sign_date=last_sign_date.isoformat() if last_sign_date else None,
            cultivation_effect=LuckEffectInfo(**cultivation_effect),
            breakthrough_bonus=breakthrough_bonus,
            drop_effects=drop_effects
        )

        return BaseResponse(
            success=True,
            message="获取气运信息成功",
            data=luck_info.model_dump()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取气运信息失败: {str(e)}"
        )


@router.post("/start-cultivation", response_model=BaseResponse, summary="开始修炼")
async def start_cultivation(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    开始挂机修炼

    Args:
        request: 包含cultivation_focus的请求数据
    """
    try:
        # 获取修炼方向
        cultivation_focus = request.get("cultivation_focus", "HP")

        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 开始修炼
        from server.core.systems.cultivation_system import CultivationSystem
        result = await CultivationSystem.start_cultivation(db, character, cultivation_focus)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始修炼失败: {str(e)}"
        )


@router.post("/change-cultivation-focus", response_model=BaseResponse, summary="变更修炼方向")
async def change_cultivation_focus(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    变更修炼方向

    Args:
        request: 包含cultivation_focus的请求数据
    """
    try:
        # 获取修炼方向
        cultivation_focus = request.get("cultivation_focus", "HP")

        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 变更修炼方向
        from server.core.systems.cultivation_system import CultivationSystem
        result = await CultivationSystem.change_cultivation_focus(db, character, cultivation_focus)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        logger.error(f"变更修炼方向失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"变更修炼方向失败: {str(e)}"
        )


@router.post("/manual-breakthrough", response_model=BaseResponse, summary="手动突破")
async def manual_breakthrough(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    手动突破境界
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 尝试突破
        from server.core.systems.cultivation_system import CultivationSystem
        result = await CultivationSystem.manual_breakthrough(db, character)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动突破失败: {str(e)}"
        )


@router.get("/cultivation-status", response_model=BaseResponse, summary="获取修炼状态")
async def get_cultivation_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前角色的修炼状态信息
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取修炼状态
        from server.core.systems.cultivation_system import CultivationSystem
        result = await CultivationSystem.get_cultivation_status(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取修炼状态成功",
            data=result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取修炼状态失败: {str(e)}"
        )


@router.get("/cave-info", response_model=BaseResponse, summary="获取洞府信息")
async def get_cave_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取洞府信息
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取洞府信息
        from server.core.systems.cave_system import CaveSystem
        result = await CaveSystem.get_cave_info(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取洞府信息成功" if result["success"] else result.get("message", "获取洞府信息失败"),
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取洞府信息失败: {str(e)}"
        )


@router.post("/upgrade-cave", response_model=BaseResponse, summary="升级洞府")
async def upgrade_cave(
    request: UpgradeCaveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    升级洞府或聚灵阵
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 执行升级
        from server.core.systems.cave_system import CaveSystem
        result = await CaveSystem.upgrade_cave(db, character, request.upgrade_type)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"升级洞府失败: {str(e)}"
        )


@router.get("/farm-info", response_model=BaseResponse, summary="获取灵田信息")
async def get_farm_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取灵田信息
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取灵田信息
        from server.core.systems.farm_system import FarmSystem
        result = await FarmSystem.get_farm_info(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取灵田信息成功" if result["success"] else result.get("message", "获取灵田信息失败"),
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取灵田信息失败: {str(e)}"
        )


@router.post("/plant-seed", response_model=BaseResponse, summary="种植种子")
async def plant_seed(
    request: PlantSeedRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    种植种子
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 种植种子
        from server.core.systems.farm_system import FarmSystem
        result = await FarmSystem.plant_seed(db, character, request.plot_index, request.seed_item_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"种植种子失败: {str(e)}"
        )


@router.post("/harvest-plot", response_model=BaseResponse, summary="收获地块")
async def harvest_plot(
    request: HarvestPlotRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    收获地块
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 收获地块
        from server.core.systems.farm_system import FarmSystem
        result = await FarmSystem.harvest_plot(db, character, request.plot_index)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收获地块失败: {str(e)}"
        )


@router.post("/unlock-plot", response_model=BaseResponse, summary="解锁地块")
async def unlock_plot(
    request: UnlockPlotRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    解锁地块
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 解锁地块
        from server.core.systems.farm_system import FarmSystem
        result = await FarmSystem.unlock_plot(db, character, request.plot_index)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解锁地块失败: {str(e)}"
        )


@router.post("/force-cultivation-cycle", response_model=BaseResponse, summary="强制修炼周期")
async def force_cultivation_cycle(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    强制执行一次修炼周期（用于测试）
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 强制执行修炼周期
        from server.core.game_loop import game_loop
        result = await game_loop.force_cultivation_cycle(character.id)

        return BaseResponse(
            success=result["success"],
            message=result.get("message", "修炼周期执行完成"),
            data=result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"强制修炼周期失败: {str(e)}"
        )


@router.get("/alchemy-info", response_model=BaseResponse, summary="获取炼丹信息")
async def get_alchemy_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取炼丹系统信息
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取炼丹信息
        from server.core.systems.alchemy_system import AlchemySystem
        result = await AlchemySystem.get_alchemy_info(db, character)

        return BaseResponse(
            success=result["success"],
            message="获取炼丹信息成功" if result["success"] else result.get("message", "获取炼丹信息失败"),
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取炼丹信息失败: {str(e)}"
        )


@router.post("/start-alchemy", response_model=BaseResponse, summary="开始炼丹")
async def start_alchemy(
    request: StartAlchemyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    开始炼丹
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 开始炼丹
        from server.core.systems.alchemy_system import AlchemySystem
        result = await AlchemySystem.start_alchemy(db, character, request.recipe_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始炼丹失败: {str(e)}"
        )


@router.post("/collect-alchemy", response_model=BaseResponse, summary="收取炼丹结果")
async def collect_alchemy_result(
    request: CollectAlchemyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    收取炼丹结果
    """
    try:
        # 获取角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 收取炼丹结果
        from server.core.systems.alchemy_system import AlchemySystem
        result = await AlchemySystem.collect_alchemy_result(db, character, request.session_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result if result["success"] else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收取炼丹结果失败: {str(e)}"
        )
