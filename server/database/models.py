# SQLAlchemy数据模型 (User, Character, Item等)

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, JSON, BigInteger, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from server.database.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    plain_password: Mapped[str] = mapped_column(String(50), nullable=False)  # 存储明文密码

    # 用户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    characters: Mapped[List["Character"]] = relationship("Character", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Character(Base):
    """角色表"""
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 修炼相关
    cultivation_exp: Mapped[int] = mapped_column(BigInteger, default=0)
    cultivation_realm: Mapped[int] = mapped_column(Integer, default=0)  # 境界等级
    spiritual_root: Mapped[str] = mapped_column(String(20), nullable=False)

    # 资源
    luck_value: Mapped[int] = mapped_column(Integer, default=50)  # 初始气运值，首次签到时会重新生成
    gold: Mapped[int] = mapped_column(BigInteger, default=0)
    spirit_stone: Mapped[int] = mapped_column(BigInteger, default=0)

    # 战斗相关
    current_hp: Mapped[int] = mapped_column(Integer, default=100)  # 当前生命值
    max_stamina: Mapped[int] = mapped_column(Integer, default=100)  # 最大体力值
    current_stamina: Mapped[int] = mapped_column(Integer, default=100)  # 当前体力值

    # 副本相关
    current_dungeon_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 当前所在副本ID
    dungeon_progress: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 副本进度

    # 挂机修炼设置
    cultivation_focus: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # HP, PHYSICAL_ATTACK等

    # 修习获得的额外属性
    hp_training: Mapped[int] = mapped_column(Integer, default=0)
    physical_attack_training: Mapped[int] = mapped_column(Integer, default=0)
    magic_attack_training: Mapped[int] = mapped_column(Integer, default=0)
    physical_defense_training: Mapped[int] = mapped_column(Integer, default=0)
    magic_defense_training: Mapped[int] = mapped_column(Integer, default=0)

    # 洞府相关
    cave_level: Mapped[int] = mapped_column(Integer, default=0)  # 洞府等级，默认0级
    spirit_gathering_array_level: Mapped[int] = mapped_column(Integer, default=0)  # 聚灵阵等级

    # 炼丹相关
    alchemy_level: Mapped[int] = mapped_column(Integer, default=1)  # 炼丹等级
    alchemy_exp: Mapped[int] = mapped_column(Integer, default=0)  # 炼丹经验

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sign_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # 最后签到日期

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="characters")
    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="character", cascade="all, delete-orphan")
    equipped_items: Mapped[List["EquippedItem"]] = relationship("EquippedItem", back_populates="character", cascade="all, delete-orphan")
    game_logs: Mapped[List["GameLog"]] = relationship("GameLog", back_populates="character", cascade="all, delete-orphan")
    farm_plots: Mapped[List["FarmPlot"]] = relationship("FarmPlot", back_populates="character", cascade="all, delete-orphan")
    alchemy_sessions: Mapped[List["AlchemySession"]] = relationship("AlchemySession", cascade="all, delete-orphan")
    dungeon_instances: Mapped[List["DungeonInstance"]] = relationship("DungeonInstance", cascade="all, delete-orphan")
    combat_logs: Mapped[List["CombatLog"]] = relationship("CombatLog", cascade="all, delete-orphan")

    # 索引 - 每个用户只能有一个角色
    __table_args__ = (
        Index('ix_character_user_unique', 'user_id', unique=True),
    )

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}', realm={self.cultivation_realm})>"


class Item(Base):
    """物品表"""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # CONSUMABLE, EQUIPMENT等
    quality: Mapped[str] = mapped_column(String(20), nullable=False)  # COMMON, UNCOMMON等

    # 基础属性
    stack_size: Mapped[int] = mapped_column(Integer, default=1)
    sell_price: Mapped[int] = mapped_column(Integer, default=0)

    # 装备专用属性 (JSON格式存储)
    equipment_slot: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # WEAPON, ARMOR等
    required_realm: Mapped[int] = mapped_column(Integer, default=0)
    base_attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 基础属性
    special_effects: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 特殊效果

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="item")
    equipped_items: Mapped[List["EquippedItem"]] = relationship("EquippedItem", back_populates="item")

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', type='{self.item_type}')>"


class InventoryItem(Base):
    """背包物品表"""
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    slot_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 背包位置

    # 装备专用属性 (每个装备实例的属性可能不同)
    attribute_variation: Mapped[float] = mapped_column(Float, default=1.0)  # 属性波动系数
    actual_attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 实际属性

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    character: Mapped["Character"] = relationship("Character", back_populates="inventory_items")
    item: Mapped["Item"] = relationship("Item", back_populates="inventory_items")

    # 索引
    __table_args__ = (
        Index('ix_inventory_character_item', 'character_id', 'item_id'),
    )

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, character_id={self.character_id}, item_id={self.item_id}, quantity={self.quantity})>"


class EquippedItem(Base):
    """已装备物品表"""
    __tablename__ = "equipped_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    slot: Mapped[str] = mapped_column(String(20), nullable=False)  # WEAPON, ARMOR等

    # 装备属性 (继承自背包物品)
    attribute_variation: Mapped[float] = mapped_column(Float, default=1.0)
    actual_attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间戳
    equipped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    character: Mapped["Character"] = relationship("Character", back_populates="equipped_items")
    item: Mapped["Item"] = relationship("Item", back_populates="equipped_items")

    # 索引
    __table_args__ = (
        Index('ix_equipped_character_slot', 'character_id', 'slot', unique=True),
    )

    def __repr__(self):
        return f"<EquippedItem(id={self.id}, character_id={self.character_id}, slot='{self.slot}')>"


class GameLog(Base):
    """游戏日志表"""
    __tablename__ = "game_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # CULTIVATION, BREAKTHROUGH等
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 详细信息

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 关系
    character: Mapped["Character"] = relationship("Character", back_populates="game_logs")

    # 索引
    __table_args__ = (
        Index('ix_game_log_character_type_time', 'character_id', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return f"<GameLog(id={self.id}, character_id={self.character_id}, event_type='{self.event_type}')>"


class UserSession(Base):
    """用户会话表 (用于JWT token管理)"""
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)  # JWT ID

    # 会话信息
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6支持
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class FarmPlot(Base):
    """灵田地块表"""
    __tablename__ = "farm_plots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    plot_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 地块编号 (0-11，3x4网格)

    # 地块属性
    plot_type: Mapped[str] = mapped_column(String(20), default="normal")  # normal, fertile, spiritual
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已解锁

    # 种植信息
    seed_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("items.id"), nullable=True)
    planted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    harvest_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 作物状态
    growth_stage: Mapped[int] = mapped_column(Integer, default=0)  # 0-4 成长阶段
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否可收获
    is_withered: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否枯萎

    # 特殊状态
    has_pest: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否有虫害
    has_weed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否有杂草
    mutation_chance: Mapped[float] = mapped_column(Float, default=0.0)  # 变异概率

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    character: Mapped["Character"] = relationship("Character", back_populates="farm_plots")
    seed_item: Mapped[Optional["Item"]] = relationship("Item", foreign_keys=[seed_item_id])

    # 索引
    __table_args__ = (
        Index('ix_farm_plot_character_index', 'character_id', 'plot_index', unique=True),
    )

    def __repr__(self):
        return f"<FarmPlot(id={self.id}, character_id={self.character_id}, plot_index={self.plot_index})>"


class AlchemyRecipe(Base):
    """炼丹丹方表"""
    __tablename__ = "alchemy_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # 丹方ID
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 丹方属性
    quality: Mapped[str] = mapped_column(String(20), nullable=False)  # 丹药品质
    required_realm: Mapped[int] = mapped_column(Integer, default=0)  # 需要境界
    required_alchemy_level: Mapped[int] = mapped_column(Integer, default=1)  # 需要炼丹等级

    # 炼制配置
    materials: Mapped[dict] = mapped_column(JSON, nullable=False)  # 所需材料 {"材料名": 数量}
    result_item_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 产出物品名
    base_time_minutes: Mapped[int] = mapped_column(Integer, default=30)  # 基础炼制时间(分钟)
    base_success_rate: Mapped[float] = mapped_column(Float, default=0.7)  # 基础成功率

    # 丹药效果
    effects: Mapped[dict] = mapped_column(JSON, nullable=True)  # 丹药效果配置

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AlchemyRecipe(id={self.id}, recipe_id='{self.recipe_id}', name='{self.name}')>"


class AlchemySession(Base):
    """炼丹会话表"""
    __tablename__ = "alchemy_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    recipe_id: Mapped[str] = mapped_column(String(50), nullable=False)  # 丹方ID

    # 炼制状态
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    quality: Mapped[str] = mapped_column(String(20), nullable=False)  # 炼制品质

    # 时间信息
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 炼制结果
    success_rate: Mapped[float] = mapped_column(Float, default=0.7)  # 实际成功率
    result_item_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 产出物品
    result_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 产出品质
    exp_gained: Mapped[int] = mapped_column(Integer, default=0)  # 获得的炼丹经验

    # 关系
    character: Mapped["Character"] = relationship("Character", overlaps="alchemy_sessions")

    # 索引
    __table_args__ = (
        Index('ix_alchemy_session_character_status', 'character_id', 'status'),
    )

    def __repr__(self):
        return f"<AlchemySession(id={self.id}, character_id={self.character_id}, recipe_id='{self.recipe_id}', status='{self.status}')>"


class Dungeon(Base):
    """副本表"""
    __tablename__ = "dungeons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dungeon_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # 副本ID
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 副本属性
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # EASY, NORMAL, HARD, HELL
    required_realm: Mapped[int] = mapped_column(Integer, default=0)  # 需要境界
    stamina_cost: Mapped[int] = mapped_column(Integer, default=10)  # 体力消耗
    max_floors: Mapped[int] = mapped_column(Integer, default=1)  # 最大层数

    # 奖励配置
    base_exp_reward: Mapped[int] = mapped_column(Integer, default=100)  # 基础经验奖励
    base_gold_reward: Mapped[int] = mapped_column(Integer, default=50)  # 基础金币奖励
    drop_table: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 掉落表配置

    # 怪物配置
    monster_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # 怪物配置

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Dungeon(id={self.id}, dungeon_id='{self.dungeon_id}', name='{self.name}')>"


class DungeonInstance(Base):
    """副本实例表"""
    __tablename__ = "dungeon_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    dungeon_id: Mapped[str] = mapped_column(String(50), nullable=False)  # 副本ID

    # 实例状态
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    current_floor: Mapped[int] = mapped_column(Integer, default=1)  # 当前层数
    current_monster_index: Mapped[int] = mapped_column(Integer, default=0)  # 当前怪物索引

    # 战斗状态
    player_hp: Mapped[int] = mapped_column(Integer, nullable=False)  # 玩家当前血量
    monster_hp: Mapped[int] = mapped_column(Integer, default=0)  # 当前怪物血量
    monster_max_hp: Mapped[int] = mapped_column(Integer, default=0)  # 当前怪物最大血量
    monster_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 当前怪物数据

    # 进度数据
    progress_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 进度数据
    rewards_collected: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已收取奖励

    # 时间戳
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    character: Mapped["Character"] = relationship("Character", overlaps="dungeon_instances")

    # 索引
    __table_args__ = (
        Index('ix_dungeon_instance_character_status', 'character_id', 'status'),
    )

    def __repr__(self):
        return f"<DungeonInstance(id={self.id}, character_id={self.character_id}, dungeon_id='{self.dungeon_id}', status='{self.status}')>"


class Monster(Base):
    """怪物表"""
    __tablename__ = "monsters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    monster_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # 怪物ID
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 怪物属性
    monster_type: Mapped[str] = mapped_column(String(20), nullable=False)  # NORMAL, ELITE, BOSS
    level: Mapped[int] = mapped_column(Integer, default=1)  # 怪物等级

    # 基础属性
    base_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    base_physical_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    base_magic_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    base_physical_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    base_magic_defense: Mapped[int] = mapped_column(Integer, nullable=False)

    # 特殊属性
    critical_rate: Mapped[float] = mapped_column(Float, default=0.05)  # 暴击率
    critical_damage: Mapped[float] = mapped_column(Float, default=1.5)  # 暴击倍数

    # 技能和AI
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 技能配置
    ai_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # AI行为模式

    # 掉落配置
    drop_table: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 掉落表
    exp_reward: Mapped[int] = mapped_column(Integer, default=50)  # 经验奖励
    gold_reward: Mapped[int] = mapped_column(Integer, default=20)  # 金币奖励

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Monster(id={self.id}, monster_id='{self.monster_id}', name='{self.name}')>"


class CombatLog(Base):
    """战斗日志表"""
    __tablename__ = "combat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dungeon_instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("dungeon_instances.id"), nullable=False)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)

    # 战斗信息
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ATTACK, SKILL, DEFEND等
    actor: Mapped[str] = mapped_column(String(20), nullable=False)  # PLAYER, MONSTER
    target: Mapped[str] = mapped_column(String(20), nullable=False)  # PLAYER, MONSTER

    # 伤害信息
    damage: Mapped[int] = mapped_column(Integer, default=0)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    damage_type: Mapped[str] = mapped_column(String(20), nullable=True)  # PHYSICAL, MAGIC

    # 状态信息
    player_hp_before: Mapped[int] = mapped_column(Integer, nullable=False)
    player_hp_after: Mapped[int] = mapped_column(Integer, nullable=False)
    monster_hp_before: Mapped[int] = mapped_column(Integer, nullable=False)
    monster_hp_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # 描述信息
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    dungeon_instance: Mapped["DungeonInstance"] = relationship("DungeonInstance")
    character: Mapped["Character"] = relationship("Character", overlaps="combat_logs")

    # 索引
    __table_args__ = (
        Index('ix_combat_log_instance_time', 'dungeon_instance_id', 'created_at'),
    )

    def __repr__(self):
        return f"<CombatLog(id={self.id}, dungeon_instance_id={self.dungeon_instance_id}, action_type='{self.action_type}')>"


class ShopItem(Base):
    """商城物品表"""
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)

    # 价格信息
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_type: Mapped[str] = mapped_column(String(20), default="gold")  # gold, spirit_stone

    # 库存信息
    stock: Mapped[int] = mapped_column(Integer, default=-1)  # -1表示无限库存
    sold_count: Mapped[int] = mapped_column(Integer, default=0)  # 已售数量

    # 商城类型
    shop_type: Mapped[str] = mapped_column(String(20), default="system")  # system, player

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    item: Mapped["Item"] = relationship("Item")

    def __repr__(self):
        return f"<ShopItem(id={self.id}, item_id={self.item_id}, price={self.price})>"


class PlayerTrade(Base):
    """玩家交易表"""
    __tablename__ = "player_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    buyer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("characters.id"), nullable=True)

    # 交易物品
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # 价格信息
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_type: Mapped[str] = mapped_column(String(20), default="gold")  # gold, spirit_stone

    # 交易状态
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, SOLD, CANCELLED

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # 关系
    seller: Mapped["Character"] = relationship("Character", foreign_keys=[seller_id])
    buyer: Mapped[Optional["Character"]] = relationship("Character", foreign_keys=[buyer_id])
    item: Mapped["Item"] = relationship("Item")

    # 索引
    __table_args__ = (
        Index('ix_player_trade_seller_status', 'seller_id', 'status'),
        Index('ix_player_trade_item_status', 'item_id', 'status'),
    )

    def __repr__(self):
        return f"<PlayerTrade(id={self.id}, seller_id={self.seller_id}, item_id={self.item_id}, status='{self.status}')>"


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)

    # 消息内容
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # WORLD, SYSTEM, PRIVATE等
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="NORMAL")  # NORMAL, SYSTEM, ANNOUNCEMENT

    # 私聊相关 (可选)
    target_character_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("characters.id"), nullable=True)

    # 消息状态
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 关系
    character: Mapped["Character"] = relationship("Character", foreign_keys=[character_id])
    target_character: Mapped[Optional["Character"]] = relationship("Character", foreign_keys=[target_character_id])

    # 索引
    __table_args__ = (
        Index('ix_chat_message_channel_time', 'channel', 'created_at'),
        Index('ix_chat_message_character_time', 'character_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, channel='{self.channel}', character_id={self.character_id})>"
