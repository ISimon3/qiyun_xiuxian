# 游戏常量 (境界名称, 物品ID, 事件类型等)

# 修炼境界常量
CULTIVATION_REALMS = [
    "凡人",
    "练气初期", "练气中期", "练气后期", "练气大圆满",
    "筑基初期", "筑基中期", "筑基后期", "筑基大圆满",
    "金丹初期", "金丹中期", "金丹后期", "金丹大圆满",
    "元婴初期", "元婴中期", "元婴后期", "元婴大圆满",
    "化神初期", "化神中期", "化神后期", "化神大圆满",
    "炼虚初期", "炼虚中期", "炼虚后期", "炼虚大圆满",
    "合体初期", "合体中期", "合体后期", "合体大圆满",
    "大乘初期", "大乘中期", "大乘后期", "大乘大圆满",
    "渡劫初期", "渡劫中期", "渡劫后期", "渡劫大圆满",
    "仙人"
]

# 境界对应的修为需求 (累计修为) - 完整平滑成长曲线
CULTIVATION_EXP_REQUIREMENTS = {
    # 凡人阶段
    0: 0,        # 凡人

    # 练气期 (1-4)
    1: 100,      # 练气初期
    2: 250,      # 练气中期
    3: 450,      # 练气后期
    4: 700,      # 练气大圆满

    # 筑基期 (5-8)
    5: 1000,     # 筑基初期
    6: 1400,     # 筑基中期
    7: 1900,     # 筑基后期
    8: 2500,     # 筑基大圆满

    # 金丹期 (9-12)
    9: 3200,     # 金丹初期
    10: 4000,    # 金丹中期
    11: 4900,    # 金丹后期
    12: 5900,    # 金丹大圆满

    # 元婴期 (13-16)
    13: 7000,    # 元婴初期
    14: 8200,    # 元婴中期
    15: 9500,    # 元婴后期
    16: 10900,   # 元婴大圆满

    # 化神期 (17-20)
    17: 12400,   # 化神初期
    18: 14000,   # 化神中期
    19: 15700,   # 化神后期
    20: 17500,   # 化神大圆满

    # 炼虚期 (21-24)
    21: 19400,   # 炼虚初期
    22: 21400,   # 炼虚中期
    23: 23500,   # 炼虚后期
    24: 25700,   # 炼虚大圆满

    # 合体期 (25-28)
    25: 28000,   # 合体初期
    26: 30400,   # 合体中期
    27: 32900,   # 合体后期
    28: 35500,   # 合体大圆满

    # 大乘期 (29-32)
    29: 38200,   # 大乘初期
    30: 41000,   # 大乘中期
    31: 43900,   # 大乘后期
    32: 46900,   # 大乘大圆满

    # 仙人 (33)
    33: 50000,   # 仙人
}

# 灵根类型
SPIRITUAL_ROOTS = {
    "废灵根": {"name": "废灵根", "multiplier": 0.5, "rarity": "common"},
    "单灵根": {"name": "单灵根", "multiplier": 1.5, "rarity": "uncommon"},
    "双灵根": {"name": "双灵根", "multiplier": 1.2, "rarity": "common"},
    "三灵根": {"name": "三灵根", "multiplier": 1.0, "rarity": "common"},
    "四灵根": {"name": "四灵根", "multiplier": 0.8, "rarity": "common"},
    "五灵根": {"name": "五灵根", "multiplier": 0.6, "rarity": "common"},
    "天灵根": {"name": "天灵根", "multiplier": 3.0, "rarity": "legendary"},
    "变异灵根": {"name": "变异灵根", "multiplier": 2.0, "rarity": "epic"}
}

# 气运等级
LUCK_LEVELS = {
    "大凶": {"min": 0, "max": 10, "color": "#8B0000"},
    "凶": {"min": 11, "max": 25, "color": "#DC143C"},
    "小凶": {"min": 26, "max": 40, "color": "#FF6347"},
    "平": {"min": 41, "max": 60, "color": "#808080"},
    "小吉": {"min": 61, "max": 75, "color": "#32CD32"},
    "吉": {"min": 76, "max": 90, "color": "#00CED1"},
    "大吉": {"min": 91, "max": 100, "color": "#FFD700"}
}

# 物品类型
ITEM_TYPES = {
    "CONSUMABLE": "消耗品",
    "EQUIPMENT": "装备",
    "MATERIAL": "材料",
    "PILL": "丹药",
    "SEED": "种子",
    "MISC": "杂物"
}

# 装备部位
EQUIPMENT_SLOTS = {
    "WEAPON": "武器",
    "ARMOR": "护甲",
    "HELMET": "头盔",
    "BOOTS": "靴子",
    "BRACELET": "手镯",
    "MAGIC_WEAPON": "法宝"
}

# 角色属性类型
ATTRIBUTE_TYPES = {
    # 战斗属性 (主要属性)
    "HP": "生命值",
    "PHYSICAL_ATTACK": "物理攻击",
    "MAGIC_ATTACK": "法术攻击",
    "PHYSICAL_DEFENSE": "物理防御",
    "MAGIC_DEFENSE": "法术防御",
    "CRITICAL_RATE": "暴击率",
    "CRITICAL_DAMAGE": "暴击倍数",

    # 特殊属性
    "CULTIVATION_SPEED": "修炼速度",
    "LUCK_BONUS": "气运加成"
}

# 可修习的基础属性方向
CULTIVATION_FOCUS_TYPES = {
    "HP": {
        "name": "体修",
        "description": "专注修炼生命力，增强体魄",
        "attribute": "HP",
        "icon": "🛡️"
    },
    "PHYSICAL_ATTACK": {
        "name": "力修",
        "description": "专注修炼肉身力量，增强物理攻击",
        "attribute": "PHYSICAL_ATTACK",
        "icon": "⚔️"
    },
    "MAGIC_ATTACK": {
        "name": "法修",
        "description": "专注修炼法力，增强法术攻击",
        "attribute": "MAGIC_ATTACK",
        "icon": "🔮"
    },
    "PHYSICAL_DEFENSE": {
        "name": "护体",
        "description": "专注修炼防御，增强物理抗性",
        "attribute": "PHYSICAL_DEFENSE",
        "icon": "🛡️"
    },
    "MAGIC_DEFENSE": {
        "name": "抗法",
        "description": "专注修炼法抗，增强法术抗性",
        "attribute": "MAGIC_DEFENSE",
        "icon": "✨"
    }
}

# 挂机修炼配置
CULTIVATION_CONFIG = {
    "BASE_EXP_GAIN": 10,           # 基础修为获得/分钟
    "BASE_ATTRIBUTE_GAIN": 1,      # 基础属性获得/分钟
    "LUCK_MULTIPLIER_MIN": 0.5,    # 气运影响最小倍率
    "LUCK_MULTIPLIER_MAX": 2.0,    # 气运影响最大倍率
    "SPECIAL_EVENT_CHANCE": 0.05,  # 特殊事件概率 (5%)
}

# 境界对应的基础战斗属性 - 完整属性表
REALM_BASE_ATTRIBUTES = {
    # 凡人阶段
    0: {  # 凡人
        "HP": 100,
        "PHYSICAL_ATTACK": 20,
        "MAGIC_ATTACK": 20,
        "PHYSICAL_DEFENSE": 15,
        "MAGIC_DEFENSE": 15
    },

    # 练气期 (1-4)
    1: {  # 练气初期
        "HP": 200,
        "PHYSICAL_ATTACK": 40,
        "MAGIC_ATTACK": 40,
        "PHYSICAL_DEFENSE": 30,
        "MAGIC_DEFENSE": 30
    },
    2: {  # 练气中期
        "HP": 350,
        "PHYSICAL_ATTACK": 70,
        "MAGIC_ATTACK": 70,
        "PHYSICAL_DEFENSE": 50,
        "MAGIC_DEFENSE": 50
    },
    3: {  # 练气后期
        "HP": 550,
        "PHYSICAL_ATTACK": 110,
        "MAGIC_ATTACK": 110,
        "PHYSICAL_DEFENSE": 80,
        "MAGIC_DEFENSE": 80
    },
    4: {  # 练气大圆满
        "HP": 800,
        "PHYSICAL_ATTACK": 160,
        "MAGIC_ATTACK": 160,
        "PHYSICAL_DEFENSE": 120,
        "MAGIC_DEFENSE": 120
    },

    # 筑基期 (5-8)
    5: {  # 筑基初期
        "HP": 1200,
        "PHYSICAL_ATTACK": 240,
        "MAGIC_ATTACK": 240,
        "PHYSICAL_DEFENSE": 180,
        "MAGIC_DEFENSE": 180
    },
    6: {  # 筑基中期
        "HP": 1800,
        "PHYSICAL_ATTACK": 360,
        "MAGIC_ATTACK": 360,
        "PHYSICAL_DEFENSE": 270,
        "MAGIC_DEFENSE": 270
    },
    7: {  # 筑基后期
        "HP": 2600,
        "PHYSICAL_ATTACK": 520,
        "MAGIC_ATTACK": 520,
        "PHYSICAL_DEFENSE": 390,
        "MAGIC_DEFENSE": 390
    },
    8: {  # 筑基大圆满
        "HP": 3600,
        "PHYSICAL_ATTACK": 720,
        "MAGIC_ATTACK": 720,
        "PHYSICAL_DEFENSE": 540,
        "MAGIC_DEFENSE": 540
    },

    # 金丹期 (9-12)
    9: {  # 金丹初期
        "HP": 5000,
        "PHYSICAL_ATTACK": 1000,
        "MAGIC_ATTACK": 1000,
        "PHYSICAL_DEFENSE": 750,
        "MAGIC_DEFENSE": 750
    },
    10: {  # 金丹中期
        "HP": 7000,
        "PHYSICAL_ATTACK": 1400,
        "MAGIC_ATTACK": 1400,
        "PHYSICAL_DEFENSE": 1050,
        "MAGIC_DEFENSE": 1050
    },
    11: {  # 金丹后期
        "HP": 9500,
        "PHYSICAL_ATTACK": 1900,
        "MAGIC_ATTACK": 1900,
        "PHYSICAL_DEFENSE": 1425,
        "MAGIC_DEFENSE": 1425
    },
    12: {  # 金丹大圆满
        "HP": 12500,
        "PHYSICAL_ATTACK": 2500,
        "MAGIC_ATTACK": 2500,
        "PHYSICAL_DEFENSE": 1875,
        "MAGIC_DEFENSE": 1875
    },

    # 元婴期 (13-16)
    13: {  # 元婴初期
        "HP": 16000,
        "PHYSICAL_ATTACK": 3200,
        "MAGIC_ATTACK": 3200,
        "PHYSICAL_DEFENSE": 2400,
        "MAGIC_DEFENSE": 2400
    },
    14: {  # 元婴中期
        "HP": 20000,
        "PHYSICAL_ATTACK": 4000,
        "MAGIC_ATTACK": 4000,
        "PHYSICAL_DEFENSE": 3000,
        "MAGIC_DEFENSE": 3000
    },
    15: {  # 元婴后期
        "HP": 24500,
        "PHYSICAL_ATTACK": 4900,
        "MAGIC_ATTACK": 4900,
        "PHYSICAL_DEFENSE": 3675,
        "MAGIC_DEFENSE": 3675
    },
    16: {  # 元婴大圆满
        "HP": 29500,
        "PHYSICAL_ATTACK": 5900,
        "MAGIC_ATTACK": 5900,
        "PHYSICAL_DEFENSE": 4425,
        "MAGIC_DEFENSE": 4425
    },

    # 化神期 (17-20)
    17: {  # 化神初期
        "HP": 35000,
        "PHYSICAL_ATTACK": 7000,
        "MAGIC_ATTACK": 7000,
        "PHYSICAL_DEFENSE": 5250,
        "MAGIC_DEFENSE": 5250
    },
    18: {  # 化神中期
        "HP": 41000,
        "PHYSICAL_ATTACK": 8200,
        "MAGIC_ATTACK": 8200,
        "PHYSICAL_DEFENSE": 6150,
        "MAGIC_DEFENSE": 6150
    },
    19: {  # 化神后期
        "HP": 47500,
        "PHYSICAL_ATTACK": 9500,
        "MAGIC_ATTACK": 9500,
        "PHYSICAL_DEFENSE": 7125,
        "MAGIC_DEFENSE": 7125
    },
    20: {  # 化神大圆满
        "HP": 54500,
        "PHYSICAL_ATTACK": 10900,
        "MAGIC_ATTACK": 10900,
        "PHYSICAL_DEFENSE": 8175,
        "MAGIC_DEFENSE": 8175
    },

    # 炼虚期 (21-24)
    21: {  # 炼虚初期
        "HP": 62000,
        "PHYSICAL_ATTACK": 12400,
        "MAGIC_ATTACK": 12400,
        "PHYSICAL_DEFENSE": 9300,
        "MAGIC_DEFENSE": 9300
    },
    22: {  # 炼虚中期
        "HP": 70000,
        "PHYSICAL_ATTACK": 14000,
        "MAGIC_ATTACK": 14000,
        "PHYSICAL_DEFENSE": 10500,
        "MAGIC_DEFENSE": 10500
    },
    23: {  # 炼虚后期
        "HP": 78500,
        "PHYSICAL_ATTACK": 15700,
        "MAGIC_ATTACK": 15700,
        "PHYSICAL_DEFENSE": 11775,
        "MAGIC_DEFENSE": 11775
    },
    24: {  # 炼虚大圆满
        "HP": 87500,
        "PHYSICAL_ATTACK": 17500,
        "MAGIC_ATTACK": 17500,
        "PHYSICAL_DEFENSE": 13125,
        "MAGIC_DEFENSE": 13125
    },

    # 合体期 (25-28)
    25: {  # 合体初期
        "HP": 97000,
        "PHYSICAL_ATTACK": 19400,
        "MAGIC_ATTACK": 19400,
        "PHYSICAL_DEFENSE": 14550,
        "MAGIC_DEFENSE": 14550
    },
    26: {  # 合体中期
        "HP": 107000,
        "PHYSICAL_ATTACK": 21400,
        "MAGIC_ATTACK": 21400,
        "PHYSICAL_DEFENSE": 16050,
        "MAGIC_DEFENSE": 16050
    },
    27: {  # 合体后期
        "HP": 117500,
        "PHYSICAL_ATTACK": 23500,
        "MAGIC_ATTACK": 23500,
        "PHYSICAL_DEFENSE": 17625,
        "MAGIC_DEFENSE": 17625
    },
    28: {  # 合体大圆满
        "HP": 128500,
        "PHYSICAL_ATTACK": 25700,
        "MAGIC_ATTACK": 25700,
        "PHYSICAL_DEFENSE": 19275,
        "MAGIC_DEFENSE": 19275
    },

    # 大乘期 (29-32)
    29: {  # 大乘初期
        "HP": 140000,
        "PHYSICAL_ATTACK": 28000,
        "MAGIC_ATTACK": 28000,
        "PHYSICAL_DEFENSE": 21000,
        "MAGIC_DEFENSE": 21000
    },
    30: {  # 大乘中期
        "HP": 152000,
        "PHYSICAL_ATTACK": 30400,
        "MAGIC_ATTACK": 30400,
        "PHYSICAL_DEFENSE": 22800,
        "MAGIC_DEFENSE": 22800
    },
    31: {  # 大乘后期
        "HP": 164500,
        "PHYSICAL_ATTACK": 32900,
        "MAGIC_ATTACK": 32900,
        "PHYSICAL_DEFENSE": 24675,
        "MAGIC_DEFENSE": 24675
    },
    32: {  # 大乘大圆满
        "HP": 177500,
        "PHYSICAL_ATTACK": 35500,
        "MAGIC_ATTACK": 35500,
        "PHYSICAL_DEFENSE": 26625,
        "MAGIC_DEFENSE": 26625
    },

    # 仙人 (33)
    33: {  # 仙人
        "HP": 200000,
        "PHYSICAL_ATTACK": 40000,
        "MAGIC_ATTACK": 40000,
        "PHYSICAL_DEFENSE": 30000,
        "MAGIC_DEFENSE": 30000
    }
}


# 属性计算公式 - 简化版本
ATTRIBUTE_FORMULAS = {
    # 基础属性 = 境界基础值 + 等级加成 + 装备加成
    "HP": {
        "level_multiplier": 20,  # 每级增加20点生命
        "equipment_bonus": True
    },
    "PHYSICAL_ATTACK": {
        "level_multiplier": 5,   # 每级增加5点物攻
        "equipment_bonus": True
    },
    "MAGIC_ATTACK": {
        "level_multiplier": 5,   # 每级增加5点法攻
        "equipment_bonus": True
    },
    "PHYSICAL_DEFENSE": {
        "level_multiplier": 3,   # 每级增加3点物防
        "equipment_bonus": True
    },
    "MAGIC_DEFENSE": {
        "level_multiplier": 3,   # 每级增加3点法防
        "equipment_bonus": True
    }
}

# 物品品质
ITEM_QUALITY = {
    "COMMON": {"name": "普通", "color": "#FFFFFF"},
    "UNCOMMON": {"name": "优秀", "color": "#00FF00"},
    "RARE": {"name": "稀有", "color": "#0080FF"},
    "EPIC": {"name": "史诗", "color": "#8000FF"},
    "LEGENDARY": {"name": "传说", "color": "#FF8000"},
    "MYTHIC": {"name": "神话", "color": "#FF0080"}
}

# 游戏事件类型
EVENT_TYPES = {
    "CULTIVATION": "修炼",
    "BREAKTHROUGH": "突破",
    "ALCHEMY": "炼丹",
    "FARMING": "农场",
    "COMBAT": "战斗",
    "TRADE": "交易",
    "SYSTEM": "系统"
}

# 装备品质对应的属性倍率和波动范围
EQUIPMENT_QUALITY_MULTIPLIERS = {
    "COMMON": {
        "base_multiplier": 1.0,
        "min_variation": 0.8,    # 最低80%属性
        "max_variation": 1.0,    # 最高100%属性
        "color": "#FFFFFF"
    },
    "UNCOMMON": {
        "base_multiplier": 1.3,
        "min_variation": 0.9,    # 最低90%属性
        "max_variation": 1.1,    # 最高110%属性
        "color": "#00FF00"
    },
    "RARE": {
        "base_multiplier": 1.6,
        "min_variation": 0.9,
        "max_variation": 1.15,   # 最高115%属性
        "color": "#0080FF"
    },
    "EPIC": {
        "base_multiplier": 2.0,
        "min_variation": 0.95,
        "max_variation": 1.2,    # 最高120%属性
        "color": "#8000FF"
    },
    "LEGENDARY": {
        "base_multiplier": 2.5,
        "min_variation": 1.0,    # 传说装备不会低于基础值
        "max_variation": 1.3,    # 最高130%属性
        "color": "#FF8000"
    },
    "MYTHIC": {
        "base_multiplier": 3.0,
        "min_variation": 1.1,    # 神话装备必定超过基础值
        "max_variation": 1.5,    # 最高150%属性
        "color": "#FF0080"
    }
}

# 装备属性分配 - 更新版本
EQUIPMENT_ATTRIBUTE_VARIATION = {
    "WEAPON": {
        "primary_attributes": ["PHYSICAL_ATTACK", "MAGIC_ATTACK"],  # 武器主要属性
        "secondary_attributes": ["CRITICAL_RATE"]                   # 武器次要属性
    },
    "ARMOR": {
        "primary_attributes": ["PHYSICAL_DEFENSE", "HP"],
        "secondary_attributes": ["MAGIC_DEFENSE"]
    },
    "HELMET": {
        "primary_attributes": ["MAGIC_DEFENSE", "HP"],
        "secondary_attributes": ["PHYSICAL_DEFENSE"]
    },
    "BOOTS": {
        "primary_attributes": ["PHYSICAL_DEFENSE", "MAGIC_DEFENSE"],
        "secondary_attributes": ["HP"]
    },
    "BRACELET": {
        "primary_attributes": ["CRITICAL_RATE", "CRITICAL_DAMAGE"],
        "secondary_attributes": ["CULTIVATION_SPEED"]
    },
    "MAGIC_WEAPON": {
        "primary_attributes": ["HP", "CULTIVATION_SPEED"],
        "secondary_attributes": ["LUCK_BONUS"]
    }
}

# 默认配置
DEFAULT_CONFIG = {
    "CULTIVATION_BASE_EXP": 10,       # 基础修炼经验/分钟
    "MAX_LUCK_VALUE": 100,            # 最大气运值
    "MIN_LUCK_VALUE": 0,              # 最小气运值
    "BREAKTHROUGH_BASE_CHANCE": 0.5,  # 基础突破成功率
    "DAILY_LUCK_MIN": 30,             # 每日随机气运最小值
    "DAILY_LUCK_MAX": 80,             # 每日随机气运最大值
}
