# 共享工具函数

import random
from typing import Dict, Any
from .constants import (
    CULTIVATION_REALMS,
    REALM_BASE_ATTRIBUTES,
    EQUIPMENT_QUALITY_MULTIPLIERS,
    EQUIPMENT_ATTRIBUTE_VARIATION,
    LUCK_LEVELS,
    LUCK_SPECIAL_EVENTS
)
from .schemas import CharacterAttributes, EquipmentAttributes, CharacterTrainingAttributes


def get_realm_name(realm_level: int) -> str:
    """获取境界名称"""
    if 0 <= realm_level < len(CULTIVATION_REALMS):
        return CULTIVATION_REALMS[realm_level]
    return "未知境界"


def get_luck_level_name(luck_value: int) -> str:
    """根据气运值获取气运等级名称"""
    for level_name, level_info in LUCK_LEVELS.items():
        if level_info["min"] <= luck_value <= level_info["max"]:
            return level_name
    return "平"


def get_luck_color(luck_value: int) -> str:
    """根据气运值获取显示颜色"""
    for level_name, level_info in LUCK_LEVELS.items():
        if level_info["min"] <= luck_value <= level_info["max"]:
            return level_info["color"]
    return "#808080"


def calculate_base_attributes(realm_level: int) -> CharacterAttributes:
    """计算角色基础属性（不含装备加成）- 移除等级系统"""
    # 获取境界基础属性
    base_attrs = REALM_BASE_ATTRIBUTES.get(realm_level, REALM_BASE_ATTRIBUTES[0])

    # 基础属性只依赖境界，暴击率和暴击倍数只通过装备获得
    return CharacterAttributes(
        hp=base_attrs["HP"],
        physical_attack=base_attrs["PHYSICAL_ATTACK"],
        magic_attack=base_attrs["MAGIC_ATTACK"],
        physical_defense=base_attrs["PHYSICAL_DEFENSE"],
        magic_defense=base_attrs["MAGIC_DEFENSE"],
        critical_rate=5.0,      # 基础暴击率5%
        critical_damage=150.0,  # 基础暴击倍数150%
        cultivation_speed=1.0,
        luck_bonus=0
    )


def generate_equipment_attributes(
    equipment_slot: str,
    quality: str,
    base_realm: int = 0
) -> tuple[EquipmentAttributes, float]:
    """
    生成装备属性
    返回: (装备属性, 属性波动系数)
    """
    quality_info = EQUIPMENT_QUALITY_MULTIPLIERS.get(quality, EQUIPMENT_QUALITY_MULTIPLIERS["COMMON"])
    slot_info = EQUIPMENT_ATTRIBUTE_VARIATION.get(equipment_slot, {})

    # 生成属性波动系数
    variation = random.uniform(quality_info["min_variation"], quality_info["max_variation"])

    # 基础属性值 (根据装备境界需求)
    base_value = (base_realm + 1) * 15
    
    # 初始化装备属性
    attrs = EquipmentAttributes()
    
    # 根据装备部位设置主要属性
    primary_attrs = slot_info.get("primary_attributes", [])
    secondary_attrs = slot_info.get("secondary_attributes", [])
    
    # 设置主要属性 (较高数值)
    for attr_name in primary_attrs:
        value = int(base_value * quality_info["base_multiplier"] * variation)
        setattr(attrs, attr_name.lower(), value)

    # 设置次要属性 (较低数值)
    for attr_name in secondary_attrs:
        value = int(base_value * quality_info["base_multiplier"] * variation * 0.6)
        if attr_name == "CULTIVATION_SPEED":
            # 修炼速度是倍率属性
            setattr(attrs, attr_name.lower(), float(value * 0.01))
        elif attr_name in ["CRITICAL_RATE", "CRITICAL_DAMAGE"]:
            # 暴击属性是百分比
            if attr_name == "CRITICAL_RATE":
                setattr(attrs, attr_name.lower(), float(value * 0.1))  # 暴击率
            else:
                setattr(attrs, attr_name.lower(), float(value * 0.5))  # 暴击倍数
        else:
            setattr(attrs, attr_name.lower(), value)
    
    return attrs, variation


def calculate_final_attributes(
    base_attrs: CharacterAttributes,
    training_attrs: CharacterTrainingAttributes,
    equipment_list: list[EquipmentAttributes]
) -> CharacterAttributes:
    """计算最终属性（基础属性 + 修习属性 + 装备加成）"""
    final_attrs = CharacterAttributes(**base_attrs.model_dump())

    # 加上修习获得的属性
    final_attrs.hp += training_attrs.hp_training
    final_attrs.physical_attack += training_attrs.physical_attack_training
    final_attrs.magic_attack += training_attrs.magic_attack_training
    final_attrs.physical_defense += training_attrs.physical_defense_training
    final_attrs.magic_defense += training_attrs.magic_defense_training

    # 累加所有装备属性
    for equipment_attrs in equipment_list:
        final_attrs.hp += equipment_attrs.hp
        final_attrs.physical_attack += equipment_attrs.physical_attack
        final_attrs.magic_attack += equipment_attrs.magic_attack
        final_attrs.physical_defense += equipment_attrs.physical_defense
        final_attrs.magic_defense += equipment_attrs.magic_defense
        final_attrs.critical_rate += equipment_attrs.critical_rate
        final_attrs.critical_damage += equipment_attrs.critical_damage
        final_attrs.cultivation_speed += equipment_attrs.cultivation_speed
        final_attrs.luck_bonus += equipment_attrs.luck_bonus

    # 确保属性在合理范围内
    final_attrs.cultivation_speed = max(final_attrs.cultivation_speed, 1.0)
    final_attrs.critical_rate = max(final_attrs.critical_rate, 5.0)  # 最低5%暴击率
    final_attrs.critical_damage = max(final_attrs.critical_damage, 150.0)  # 最低150%暴击倍数

    return final_attrs


def calculate_luck_multiplier(luck_value: int) -> float:
    """根据气运值计算修炼倍率"""
    from .constants import CULTIVATION_CONFIG

    # 气运值转换为倍率 (0-100 -> 0.5-2.0)
    luck_ratio = luck_value / 100.0
    multiplier = (CULTIVATION_CONFIG["LUCK_MULTIPLIER_MIN"] +
                 luck_ratio * (CULTIVATION_CONFIG["LUCK_MULTIPLIER_MAX"] -
                              CULTIVATION_CONFIG["LUCK_MULTIPLIER_MIN"]))
    return round(multiplier, 2)


def simulate_cultivation_session(
    luck_value: int,
    cultivation_focus: str,
    cultivation_speed: float = 1.0
) -> dict:
    """
    模拟一次挂机修炼（30秒周期）
    返回修炼结果
    """
    from .constants import CULTIVATION_CONFIG, CULTIVATION_FOCUS_TYPES

    # 计算气运倍率
    luck_multiplier = calculate_luck_multiplier(luck_value)

    # 基础收益
    base_exp = CULTIVATION_CONFIG["BASE_EXP_GAIN"]
    base_attr = CULTIVATION_CONFIG["BASE_ATTRIBUTE_GAIN"]

    # 应用修炼速度和气运倍率
    final_exp = int(base_exp * cultivation_speed * luck_multiplier)
    final_attr = int(base_attr * cultivation_speed * luck_multiplier)

    # 随机波动 (±20%)
    exp_variation = random.uniform(0.8, 1.2)
    attr_variation = random.uniform(0.8, 1.2)

    final_exp = max(1, int(final_exp * exp_variation))
    final_attr = max(1, int(final_attr * attr_variation))

    # 检查特殊事件 - 使用新的气运影响系统
    special_event = None
    luck_level = get_luck_level_name(luck_value)

    # 获取基础特殊事件概率
    base_chance = CULTIVATION_CONFIG["BASE_SPECIAL_EVENT_CHANCE"]
    luck_multipliers = LUCK_SPECIAL_EVENTS["LUCK_LEVEL_MULTIPLIERS"].get(luck_level, {"positive": 1.0, "negative": 1.0})

    # 计算正面和负面事件概率
    positive_chance = base_chance * luck_multipliers["positive"]
    negative_chance = base_chance * luck_multipliers["negative"]

    # 检查是否触发特殊事件
    event_roll = random.random()
    if event_roll < positive_chance:
        # 触发正面事件
        positive_events = LUCK_SPECIAL_EVENTS["POSITIVE_EVENTS"]
        # 根据权重选择事件
        events = []
        weights = []
        for event_name, event_config in positive_events.items():
            events.append(event_name)
            weights.append(event_config.get("probability_weight", 1))

        chosen_event = random.choices(events, weights=weights)[0]
        special_event = {"event_type": chosen_event, "is_positive": True}

    elif event_roll < positive_chance + negative_chance:
        # 触发负面事件
        negative_events = LUCK_SPECIAL_EVENTS["NEGATIVE_EVENTS"]
        # 根据权重选择事件
        events = []
        weights = []
        for event_name, event_config in negative_events.items():
            events.append(event_name)
            weights.append(event_config.get("probability_weight", 1))

        chosen_event = random.choices(events, weights=weights)[0]
        special_event = {"event_type": chosen_event, "is_positive": False}

    # 获取修习方向信息
    focus_info = CULTIVATION_FOCUS_TYPES.get(cultivation_focus, CULTIVATION_FOCUS_TYPES["HP"])

    # 生成气运效果描述
    if luck_multiplier >= 1.5:
        luck_effect = "气运极佳"
    elif luck_multiplier >= 1.2:
        luck_effect = "气运不错"
    elif luck_multiplier >= 0.8:
        luck_effect = "气运平平"
    else:
        luck_effect = "气运不佳"

    return {
        "exp_gained": final_exp,
        "attribute_gained": final_attr,
        "attribute_type": cultivation_focus,
        "luck_multiplier": luck_multiplier,
        "luck_effect": luck_effect,
        "special_event": special_event,
        "focus_name": focus_info["name"]
    }


def generate_daily_luck() -> int:
    """生成每日随机气运值"""
    from .constants import DEFAULT_CONFIG
    return random.randint(
        DEFAULT_CONFIG["DAILY_LUCK_MIN"],
        DEFAULT_CONFIG["DAILY_LUCK_MAX"]
    )


def format_attribute_display(attr_name: str, value: Any) -> str:
    """格式化属性显示"""
    if attr_name == "cultivation_speed":
        return f"{value:.2f}x"
    elif attr_name in ["critical_rate", "critical_damage"]:
        return f"{value:.1f}%"
    else:
        return str(int(value))
