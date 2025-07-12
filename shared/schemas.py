# Pydantic数据模型 (DTOs), 规范通信数据结构

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# 基础响应模型
class BaseResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Any] = None


# 用户认证相关
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


# 角色相关
class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=20, description="角色名")
    spiritual_root: str = Field(..., description="灵根类型")


class CharacterAttributes(BaseModel):
    # 战斗属性 (主要属性) - 境界基础值
    hp: int = 100
    physical_attack: int = 20
    magic_attack: int = 20
    physical_defense: int = 15
    magic_defense: int = 15
    critical_rate: float = 5.0      # 暴击率 (%)
    critical_damage: float = 150.0  # 暴击倍数 (%)

    # 特殊属性
    cultivation_speed: float = 1.0
    luck_bonus: int = 0


class CharacterTrainingAttributes(BaseModel):
    """角色修习获得的额外属性"""
    hp_training: int = 0
    physical_attack_training: int = 0
    magic_attack_training: int = 0
    physical_defense_training: int = 0
    magic_defense_training: int = 0


# 装备相关类定义 (需要在CharacterInfo之前定义)
class EquipmentAttributes(BaseModel):
    """装备属性加成"""
    # 战斗属性
    hp: int = 0
    physical_attack: int = 0
    magic_attack: int = 0
    physical_defense: int = 0
    magic_defense: int = 0
    critical_rate: float = 0.0
    critical_damage: float = 0.0

    # 特殊属性
    cultivation_speed: float = 0.0
    luck_bonus: int = 0


class EquipmentInfo(BaseModel):
    id: int
    name: str
    description: str
    equipment_slot: str  # WEAPON, ARMOR, HELMET, BOOTS, BRACELET, MAGIC_WEAPON
    quality: str
    required_realm: int = 0

    # 装备属性 (已经包含品质波动)
    attributes: EquipmentAttributes

    # 属性波动系数 (0.8-1.5之间，表示该装备的属性品质)
    attribute_variation: float = 1.0

    # 特殊效果 (可选)
    special_effects: Optional[List[str]] = None

    class Config:
        from_attributes = True


class EquippedItem(BaseModel):
    """已装备的物品"""
    slot: str
    equipment_id: int
    equipment_info: EquipmentInfo

    class Config:
        from_attributes = True


class EquipmentSet(BaseModel):
    """角色装备套装"""
    weapon: Optional[EquippedItem] = None
    armor: Optional[EquippedItem] = None
    helmet: Optional[EquippedItem] = None
    boots: Optional[EquippedItem] = None
    bracelet: Optional[EquippedItem] = None
    magic_weapon: Optional[EquippedItem] = None


class CharacterInfo(BaseModel):
    id: int
    name: str
    cultivation_exp: int = 0
    cultivation_realm: int = 0
    spiritual_root: str
    luck_value: int = 50
    gold: int = 0
    spirit_stone: int = 0
    created_at: datetime
    last_active: datetime

    # 当前挂机修习方向
    cultivation_focus: Optional[str] = None  # HP, PHYSICAL_ATTACK, MAGIC_ATTACK, PHYSICAL_DEFENSE, MAGIC_DEFENSE

    # 角色属性 (包含装备加成后的最终属性)
    attributes: CharacterAttributes

    # 修习获得的额外属性
    training_attributes: CharacterTrainingAttributes

    # 装备信息 (可选，详细信息时包含)
    equipment: Optional[EquipmentSet] = None

    class Config:
        from_attributes = True


class CharacterUpdate(BaseModel):
    cultivation_exp: Optional[int] = None
    luck_value: Optional[int] = None
    gold: Optional[int] = None
    spirit_stone: Optional[int] = None


# 物品相关
class ItemInfo(BaseModel):
    id: int
    name: str
    description: str
    item_type: str
    quality: str
    stack_size: int = 1
    sell_price: int = 0

    class Config:
        from_attributes = True








class EquipItem(BaseModel):
    """装备物品请求"""
    item_id: int
    slot: str


class UnequipItem(BaseModel):
    """卸下装备请求"""
    slot: str





class AttributeCalculation(BaseModel):
    """属性计算结果"""
    base_attributes: CharacterAttributes  # 基础属性（不含装备）
    equipment_bonus: CharacterAttributes  # 装备加成
    final_attributes: CharacterAttributes  # 最终属性（基础+装备）


class InventoryItem(BaseModel):
    item_id: int
    item_info: ItemInfo
    quantity: int
    slot_position: Optional[int] = None

    class Config:
        from_attributes = True


# 游戏行为相关
class SetCultivationFocus(BaseModel):
    """设置挂机修习方向"""
    focus_type: str  # HP, PHYSICAL_ATTACK, MAGIC_ATTACK, PHYSICAL_DEFENSE, MAGIC_DEFENSE


class CultivationResult(BaseModel):
    """挂机修炼结果"""
    exp_gained: int
    attribute_gained: int
    attribute_type: str
    luck_effect: str
    luck_multiplier: float
    special_event: Optional[str] = None
    new_realm: Optional[int] = None
    total_cultivation_exp: int
    message: str


class BreakthroughAttempt(BaseModel):
    target_realm: int
    use_items: Optional[List[int]] = None  # 使用的辅助物品ID列表


class BreakthroughResult(BaseModel):
    success: bool
    new_realm: Optional[int] = None
    exp_cost: int
    luck_effect: str
    message: str


# WebSocket消息
class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class WSCultivationUpdate(BaseModel):
    character_id: int
    cultivation_exp: int
    cultivation_realm: int
    luck_value: int


class WSSystemNotification(BaseModel):
    message: str
    event_type: str
    importance: str = "normal"  # normal, important, critical


# 农场相关
class PlantSeed(BaseModel):
    seed_item_id: int
    plot_id: int


class HarvestPlot(BaseModel):
    plot_id: int


class FarmPlot(BaseModel):
    id: int
    plot_type: str = "normal"  # normal, fertile, spiritual
    seed_id: Optional[int] = None
    plant_time: Optional[datetime] = None
    harvest_time: Optional[datetime] = None
    is_ready: bool = False

    class Config:
        from_attributes = True


# 炼丹相关
class AlchemyRecipe(BaseModel):
    id: int
    name: str
    description: str
    required_materials: Dict[int, int]  # {material_id: quantity}
    success_rate: float
    result_item_id: int
    result_quantity: int = 1

    class Config:
        from_attributes = True


class StartAlchemy(BaseModel):
    recipe_id: int
    auto_mode: bool = True


class AlchemyResult(BaseModel):
    success: bool
    result_items: List[Dict[str, Any]]  # [{"item_id": int, "quantity": int, "quality": str}]
    exp_gained: int
    message: str


# 副本相关
class DungeonInfo(BaseModel):
    id: int
    name: str
    description: str
    required_level: int
    energy_cost: int
    rewards: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class EnterDungeon(BaseModel):
    dungeon_id: int


class DungeonResult(BaseModel):
    success: bool
    rewards: List[Dict[str, Any]]
    exp_gained: int
    message: str


# 商城相关
class ShopItem(BaseModel):
    id: int
    item_id: int
    item_info: ItemInfo
    price: int
    currency_type: str = "gold"  # gold, spirit_stone
    stock: int = -1  # -1 表示无限库存

    class Config:
        from_attributes = True


class PurchaseItem(BaseModel):
    shop_item_id: int
    quantity: int = 1


# 日志相关
class GameLog(BaseModel):
    id: int
    character_id: int
    event_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LogQuery(BaseModel):
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
