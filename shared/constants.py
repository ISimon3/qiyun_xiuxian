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

# 境界对应的修为需求 - 突破后修为清空的平滑成长曲线
CULTIVATION_EXP_REQUIREMENTS = {
    # 凡人阶段
    0: 0,        # 凡人

    # 练气期 (1-4) - 基础阶段，需求较低
    1: 100,      # 练气初期
    2: 150,      # 练气中期
    3: 200,      # 练气后期
    4: 300,      # 练气大圆满

    # 筑基期 (5-8) - 进阶阶段，需求适中
    5: 400,      # 筑基初期
    6: 500,      # 筑基中期
    7: 600,      # 筑基后期
    8: 800,      # 筑基大圆满

    # 金丹期 (9-12) - 中级阶段，需求增加
    9: 1000,     # 金丹初期
    10: 1200,    # 金丹中期
    11: 1500,    # 金丹后期
    12: 1800,    # 金丹大圆满

    # 元婴期 (13-16) - 高级阶段，需求较高
    13: 2200,    # 元婴初期
    14: 2600,    # 元婴中期
    15: 3000,    # 元婴后期
    16: 3500,    # 元婴大圆满

    # 化神期 (17-20) - 顶级阶段，需求很高
    17: 4000,    # 化神初期
    18: 4500,    # 化神中期
    19: 5000,    # 化神后期
    20: 5500,    # 化神大圆满

    # 炼虚期 (21-24) - 超级阶段，需求极高
    21: 6000,    # 炼虚初期
    22: 6500,    # 炼虚中期
    23: 7000,    # 炼虚后期
    24: 7500,    # 炼虚大圆满

    # 合体期 (25-28) - 准仙级阶段
    25: 8000,    # 合体初期
    26: 8500,    # 合体中期
    27: 9000,    # 合体后期
    28: 9500,    # 合体大圆满

    # 大乘期 (29-32) - 仙级前期
    29: 10000,   # 大乘初期
    30: 11000,   # 大乘中期
    31: 12000,   # 大乘后期
    32: 13000,   # 大乘大圆满

    # 仙人 (33) - 最终境界
    33: 15000,   # 仙人
}

# 灵根类型
SPIRITUAL_ROOTS = {
    "天灵根": {
        "name": "天灵根",
        "multiplier": 2.0,  # 2.0倍修炼速度
        "breakthrough_bonus": 0.15,  # +15%突破成功率
        "rarity": "legendary",
        "weight": 1  # 权重1（最稀有）
    },
    "变异灵根": {
        "name": "变异灵根",
        "multiplier": 1.5,  # 1.5倍修炼速度
        "breakthrough_bonus": 0.10,  # +10%突破成功率
        "rarity": "epic",
        "weight": 3  # 权重3
    },
    "单灵根": {
        "name": "单灵根",
        "multiplier": 1.2,  # 1.2倍修炼速度
        "breakthrough_bonus": 0.05,  # +5%突破成功率
        "rarity": "excellent",
        "weight": 20  # 权重20
    },
    "双灵根": {
        "name": "双灵根",
        "multiplier": 1.1,  # 1.1倍修炼速度
        "breakthrough_bonus": 0.0,  # 无突破加成
        "rarity": "common",
        "weight": 40  # 权重40
    },
    "三灵根": {
        "name": "三灵根",
        "multiplier": 1.0,  # 1.0倍修炼速度（基准）
        "breakthrough_bonus": 0.0,  # 无突破加成
        "rarity": "common",
        "weight": 40  # 权重40
    },
    "四灵根": {
        "name": "四灵根",
        "multiplier": 0.9,  # 0.9倍修炼速度
        "breakthrough_bonus": 0.0,  # 无突破加成
        "rarity": "common",
        "weight": 40  # 权重40
    },
    "五灵根": {
        "name": "五灵根",
        "multiplier": 0.8,  # 0.8倍修炼速度
        "breakthrough_bonus": 0.0,  # 无突破加成
        "rarity": "common",
        "weight": 40  # 权重40
    },
    "废灵根": {
        "name": "废灵根",
        "multiplier": 0.7,  # 0.7倍修炼速度
        "breakthrough_bonus": 0.0,  # 无突破加成
        "rarity": "common",
        "weight": 40  # 权重40
    }
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
    "BASE_EXP_GAIN": 10,            # 基础修为获得/周期
    "BASE_ATTRIBUTE_GAIN": 3,      # 基础属性获得/周期
    "LUCK_MULTIPLIER_MIN": 0.5,    # 气运影响最小倍率
    "LUCK_MULTIPLIER_MAX": 2.0,    # 气运影响最大倍率
    "BASE_SPECIAL_EVENT_CHANCE": 0.05,  # 基础特殊事件概率 (5%)
}

# 气运特殊事件配置
LUCK_SPECIAL_EVENTS = {
    # 正面事件 (小吉、吉、大吉)
    "POSITIVE_EVENTS": {
        "顿悟": {
            "description": "修炼时突然顿悟，修为大增",
            "exp_bonus_min": 100,
            "exp_bonus_max": 200,
            "probability_weight": 18
        },
        "灵气共鸣": {
            "description": "与天地灵气产生共鸣，获得灵石",
            "spirit_stone_bonus_min": 10,
            "spirit_stone_bonus_max": 50,
            "probability_weight": 27
        },
        "天材地宝": {
            "description": "偶遇天材地宝，属性永久提升",
            "attribute_bonus": 20,
            "probability_weight": 37
        },
        "福运降临": {
            "description": "天降福运，气运值提升",
            "luck_bonus_min": 1,
            "luck_bonus_max": 3,
            "probability_weight": 18
        }
    },

    # 负面事件 (小凶、凶、大凶)
    "NEGATIVE_EVENTS": {

        "走火入魔": {
            "description": "修炼时走火入魔，损失修为",
            "exp_penalty_min": 50,
            "exp_penalty_max": 100,
            "probability_weight": 29
        },
        "灵气紊乱": {
            "description": "周围灵气紊乱，消耗额外灵石",
            "spirit_stone_penalty_min": 5,
            "spirit_stone_penalty_max": 20,
            "probability_weight": 29
        },
        "财物散失": {
            "description": "修炼时心神不宁，财物散失",
            "gold_penalty_min": 100,
            "gold_penalty_max": 500,
            "probability_weight": 24
        },
        "气运受损": {
            "description": "修炼时触犯禁忌，气运受损",
            "luck_penalty_min": 1,
            "luck_penalty_max": 3,
            "probability_weight": 18
        }
    },

    # 气运等级对应的事件概率倍率
    "LUCK_LEVEL_MULTIPLIERS": {
        "大凶": {"positive": 0.1, "negative": 4.0},  # 负面事件概率x4，正面事件概率x0.1
        "凶": {"positive": 0.3, "negative": 2.5},    # 负面事件概率x2.5，正面事件概率x0.3
        "小凶": {"positive": 0.6, "negative": 1.5},  # 负面事件概率x1.5，正面事件概率x0.6
        "平": {"positive": 1.0, "negative": 1.0},    # 正常概率
        "小吉": {"positive": 1.5, "negative": 0.6},  # 正面事件概率x1.5，负面事件概率x0.6
        "吉": {"positive": 2.5, "negative": 0.3},    # 正面事件概率x2.5，负面事件概率x0.3
        "大吉": {"positive": 4.0, "negative": 0.1}   # 正面事件概率x4，负面事件概率x0.1
    }
}

# 境界对应的基础战斗属性 - 平滑成长曲线
REALM_BASE_ATTRIBUTES = {
    # 凡人阶段
    0: {  # 凡人
        "HP": 100,
        "PHYSICAL_ATTACK": 20,
        "MAGIC_ATTACK": 20,
        "PHYSICAL_DEFENSE": 15,
        "MAGIC_DEFENSE": 15
    },

    # 练气期 (1-4) - 基础修士阶段
    1: {  # 练气初期
        "HP": 180,
        "PHYSICAL_ATTACK": 35,
        "MAGIC_ATTACK": 35,
        "PHYSICAL_DEFENSE": 25,
        "MAGIC_DEFENSE": 25
    },
    2: {  # 练气中期
        "HP": 280,
        "PHYSICAL_ATTACK": 55,
        "MAGIC_ATTACK": 55,
        "PHYSICAL_DEFENSE": 40,
        "MAGIC_DEFENSE": 40
    },
    3: {  # 练气后期
        "HP": 400,
        "PHYSICAL_ATTACK": 80,
        "MAGIC_ATTACK": 80,
        "PHYSICAL_DEFENSE": 60,
        "MAGIC_DEFENSE": 60
    },
    4: {  # 练气大圆满
        "HP": 550,
        "PHYSICAL_ATTACK": 110,
        "MAGIC_ATTACK": 110,
        "PHYSICAL_DEFENSE": 85,
        "MAGIC_DEFENSE": 85
    },

    # 筑基期 (5-8) - 进阶修士阶段
    5: {  # 筑基初期
        "HP": 750,
        "PHYSICAL_ATTACK": 150,
        "MAGIC_ATTACK": 150,
        "PHYSICAL_DEFENSE": 115,
        "MAGIC_DEFENSE": 115
    },
    6: {  # 筑基中期
        "HP": 1000,
        "PHYSICAL_ATTACK": 200,
        "MAGIC_ATTACK": 200,
        "PHYSICAL_DEFENSE": 150,
        "MAGIC_DEFENSE": 150
    },
    7: {  # 筑基后期
        "HP": 1300,
        "PHYSICAL_ATTACK": 260,
        "MAGIC_ATTACK": 260,
        "PHYSICAL_DEFENSE": 195,
        "MAGIC_DEFENSE": 195
    },
    8: {  # 筑基大圆满
        "HP": 1650,
        "PHYSICAL_ATTACK": 330,
        "MAGIC_ATTACK": 330,
        "PHYSICAL_DEFENSE": 250,
        "MAGIC_DEFENSE": 250
    },

    # 金丹期 (9-12) - 中级修士阶段
    9: {  # 金丹初期
        "HP": 2050,
        "PHYSICAL_ATTACK": 410,
        "MAGIC_ATTACK": 410,
        "PHYSICAL_DEFENSE": 310,
        "MAGIC_DEFENSE": 310
    },
    10: {  # 金丹中期
        "HP": 2500,
        "PHYSICAL_ATTACK": 500,
        "MAGIC_ATTACK": 500,
        "PHYSICAL_DEFENSE": 380,
        "MAGIC_DEFENSE": 380
    },
    11: {  # 金丹后期
        "HP": 3000,
        "PHYSICAL_ATTACK": 600,
        "MAGIC_ATTACK": 600,
        "PHYSICAL_DEFENSE": 450,
        "MAGIC_DEFENSE": 450
    },
    12: {  # 金丹大圆满
        "HP": 3600,
        "PHYSICAL_ATTACK": 720,
        "MAGIC_ATTACK": 720,
        "PHYSICAL_DEFENSE": 540,
        "MAGIC_DEFENSE": 540
    },

    # 元婴期 (13-16) - 高级修士阶段
    13: {  # 元婴初期
        "HP": 4300,
        "PHYSICAL_ATTACK": 860,
        "MAGIC_ATTACK": 860,
        "PHYSICAL_DEFENSE": 645,
        "MAGIC_DEFENSE": 645
    },
    14: {  # 元婴中期
        "HP": 5100,
        "PHYSICAL_ATTACK": 1020,
        "MAGIC_ATTACK": 1020,
        "PHYSICAL_DEFENSE": 765,
        "MAGIC_DEFENSE": 765
    },
    15: {  # 元婴后期
        "HP": 6000,
        "PHYSICAL_ATTACK": 1200,
        "MAGIC_ATTACK": 1200,
        "PHYSICAL_DEFENSE": 900,
        "MAGIC_DEFENSE": 900
    },
    16: {  # 元婴大圆满
        "HP": 7000,
        "PHYSICAL_ATTACK": 1400,
        "MAGIC_ATTACK": 1400,
        "PHYSICAL_DEFENSE": 1050,
        "MAGIC_DEFENSE": 1050
    },

    # 化神期 (17-20) - 顶级修士阶段
    17: {  # 化神初期
        "HP": 8200,
        "PHYSICAL_ATTACK": 1640,
        "MAGIC_ATTACK": 1640,
        "PHYSICAL_DEFENSE": 1230,
        "MAGIC_DEFENSE": 1230
    },
    18: {  # 化神中期
        "HP": 9600,
        "PHYSICAL_ATTACK": 1920,
        "MAGIC_ATTACK": 1920,
        "PHYSICAL_DEFENSE": 1440,
        "MAGIC_DEFENSE": 1440
    },
    19: {  # 化神后期
        "HP": 11200,
        "PHYSICAL_ATTACK": 2240,
        "MAGIC_ATTACK": 2240,
        "PHYSICAL_DEFENSE": 1680,
        "MAGIC_DEFENSE": 1680
    },
    20: {  # 化神大圆满
        "HP": 13000,
        "PHYSICAL_ATTACK": 2600,
        "MAGIC_ATTACK": 2600,
        "PHYSICAL_DEFENSE": 1950,
        "MAGIC_DEFENSE": 1950
    },

    # 炼虚期 (21-24) - 超级修士阶段
    21: {  # 炼虚初期
        "HP": 15000,
        "PHYSICAL_ATTACK": 3000,
        "MAGIC_ATTACK": 3000,
        "PHYSICAL_DEFENSE": 2250,
        "MAGIC_DEFENSE": 2250
    },
    22: {  # 炼虚中期
        "HP": 17200,
        "PHYSICAL_ATTACK": 3440,
        "MAGIC_ATTACK": 3440,
        "PHYSICAL_DEFENSE": 2580,
        "MAGIC_DEFENSE": 2580
    },
    23: {  # 炼虚后期
        "HP": 19600,
        "PHYSICAL_ATTACK": 3920,
        "MAGIC_ATTACK": 3920,
        "PHYSICAL_DEFENSE": 2940,
        "MAGIC_DEFENSE": 2940
    },
    24: {  # 炼虚大圆满
        "HP": 22200,
        "PHYSICAL_ATTACK": 4440,
        "MAGIC_ATTACK": 4440,
        "PHYSICAL_DEFENSE": 3330,
        "MAGIC_DEFENSE": 3330
    },

    # 合体期 (25-28) - 准仙级阶段
    25: {  # 合体初期
        "HP": 25000,
        "PHYSICAL_ATTACK": 5000,
        "MAGIC_ATTACK": 5000,
        "PHYSICAL_DEFENSE": 3750,
        "MAGIC_DEFENSE": 3750
    },
    26: {  # 合体中期
        "HP": 28000,
        "PHYSICAL_ATTACK": 5600,
        "MAGIC_ATTACK": 5600,
        "PHYSICAL_DEFENSE": 4200,
        "MAGIC_DEFENSE": 4200
    },
    27: {  # 合体后期
        "HP": 31200,
        "PHYSICAL_ATTACK": 6240,
        "MAGIC_ATTACK": 6240,
        "PHYSICAL_DEFENSE": 4680,
        "MAGIC_DEFENSE": 4680
    },
    28: {  # 合体大圆满
        "HP": 34600,
        "PHYSICAL_ATTACK": 6920,
        "MAGIC_ATTACK": 6920,
        "PHYSICAL_DEFENSE": 5190,
        "MAGIC_DEFENSE": 5190
    },

    # 大乘期 (29-32) - 仙级前期
    29: {  # 大乘初期
        "HP": 38200,
        "PHYSICAL_ATTACK": 7640,
        "MAGIC_ATTACK": 7640,
        "PHYSICAL_DEFENSE": 5730,
        "MAGIC_DEFENSE": 5730
    },
    30: {  # 大乘中期
        "HP": 42000,
        "PHYSICAL_ATTACK": 8400,
        "MAGIC_ATTACK": 8400,
        "PHYSICAL_DEFENSE": 6300,
        "MAGIC_DEFENSE": 6300
    },
    31: {  # 大乘后期
        "HP": 46000,
        "PHYSICAL_ATTACK": 9200,
        "MAGIC_ATTACK": 9200,
        "PHYSICAL_DEFENSE": 6900,
        "MAGIC_DEFENSE": 6900
    },
    32: {  # 大乘大圆满
        "HP": 50200,
        "PHYSICAL_ATTACK": 10040,
        "MAGIC_ATTACK": 10040,
        "PHYSICAL_DEFENSE": 7530,
        "MAGIC_DEFENSE": 7530
    },

    # 仙人 (33) - 最终境界
    33: {  # 仙人
        "HP": 55000,
        "PHYSICAL_ATTACK": 11000,
        "MAGIC_ATTACK": 11000,
        "PHYSICAL_DEFENSE": 8250,
        "MAGIC_DEFENSE": 8250
    }
}


# 属性计算说明
# 基础属性 = 境界基础值 + 修炼（挂机获得的基础属性等）+ 装备加成
# 不再使用等级系统，所有属性提升通过境界突破和挂机修炼获得

# 物品品质
ITEM_QUALITY = {
    "COMMON": {"name": "普通", "color": "#333333"},
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

# 突破系统配置
BREAKTHROUGH_CONFIG = {
    "DEFAULT_FAILURE_LOSS_RATE": 0.2,  # 默认突破失败损失20%当前修为
    "BASE_SUCCESS_RATE": 0.5,          # 基础突破成功率50%
    "REALM_DIFFICULTY_REDUCTION": 0.01, # 每升一个境界等级减少1%成功率
}

# 灵田系统配置
FARM_SYSTEM_CONFIG = {
    # 基础配置
    "TOTAL_PLOTS": 12,  # 总地块数量 (3x4网格)
    "INITIAL_UNLOCKED_PLOTS": 4,  # 初始解锁地块数量

    # 地块类型配置
    "PLOT_TYPES": {
        "normal": {
            "name": "普通土地",
            "growth_speed_multiplier": 1.0,
            "yield_multiplier": 1.0,
            "unlock_cost": 0
        },
        "fertile": {
            "name": "肥沃土地",
            "growth_speed_multiplier": 1.3,
            "yield_multiplier": 1.2,
            "unlock_cost": 1000  # 金币
        },
        "spiritual": {
            "name": "灵田",
            "growth_speed_multiplier": 1.5,
            "yield_multiplier": 1.5,
            "unlock_cost": 5000  # 金币
        }
    },

    # 种子配置
    "SEED_CONFIG": {
        "灵草种子": {
            "growth_time_hours": 2,  # 2小时成熟
            "yield_min": 1,
            "yield_max": 3,
            "result_item": "灵草"
        },
        "灵芝种子": {
            "growth_time_hours": 6,  # 6小时成熟
            "yield_min": 1,
            "yield_max": 2,
            "result_item": "灵芝"
        },
        "聚气草种子": {
            "growth_time_hours": 4,  # 4小时成熟
            "yield_min": 2,
            "yield_max": 4,
            "result_item": "聚气草"
        }
    },

    # 成长阶段
    "GROWTH_STAGES": {
        0: "种子",
        1: "发芽",
        2: "幼苗",
        3: "成长",
        4: "成熟"
    },

    # 特殊事件概率
    "EVENT_CHANCES": {
        "wither_chance": 0.05, # 5%枯萎概率（成熟后每小时计算一次）
    },

    # 地块解锁需求
    "PLOT_UNLOCK_REQUIREMENTS": {
        4: {"cave_level": 4, "cost": 500},    # 第5个地块需要4级洞府
        5: {"cave_level": 4, "cost": 500},    # 第6个地块
        6: {"cave_level": 5, "cost": 1000},   # 第7个地块需要5级洞府
        7: {"cave_level": 5, "cost": 1000},   # 第8个地块
        8: {"cave_level": 6, "cost": 2000},   # 第9个地块需要6级洞府
        9: {"cave_level": 6, "cost": 2000},   # 第10个地块
        10: {"cave_level": 7, "cost": 5000},  # 第11个地块需要7级洞府
        11: {"cave_level": 7, "cost": 5000},  # 第12个地块
    }
}

# 炼丹系统配置
ALCHEMY_SYSTEM_CONFIG = {
    # 基础配置
    "MAX_CONCURRENT_SESSIONS": 3,  # 最大同时炼制数量
    "BASE_SUCCESS_RATE": 0.7,      # 基础成功率
    "QUALITY_BONUS_RATE": 0.1,     # 品质加成概率

    # 炼制时间配置 (分钟)
    "ALCHEMY_TIME": {
        "COMMON": 30,      # 普通丹药30分钟
        "UNCOMMON": 60,    # 优秀丹药1小时
        "RARE": 120,       # 稀有丹药2小时
        "EPIC": 240,       # 史诗丹药4小时
        "LEGENDARY": 480,  # 传说丹药8小时
    },

    # 成功率修正
    "SUCCESS_RATE_MODIFIERS": {
        "realm_bonus": 0.02,      # 每个境界+2%成功率
        "luck_bonus": 0.001,      # 每点气运+0.1%成功率
        "cave_bonus": 0.05,       # 丹房等级每级+5%成功率
    },

    # 品质提升概率
    "QUALITY_UPGRADE_CHANCE": {
        "COMMON_TO_UNCOMMON": 0.15,
        "UNCOMMON_TO_RARE": 0.10,
        "RARE_TO_EPIC": 0.05,
        "EPIC_TO_LEGENDARY": 0.02,
    }
}

# 丹方配置
ALCHEMY_RECIPES = {
    # 基础恢复类丹药
    "healing_pill": {
        "id": "healing_pill",
        "name": "回血丹",
        "description": "恢复生命值的基础丹药",
        "quality": "COMMON",
        "required_realm": 1,  # 练气初期
        "materials": {
            "灵草": 2,
            "清水": 1
        },
        "result_item": "回血丹",
        "base_time_minutes": 30,
        "effects": {
            "HP_RESTORE": 500
        }
    },
    "qi_pill": {
        "id": "qi_pill",
        "name": "聚气丹",
        "description": "增加修炼经验的丹药",
        "quality": "COMMON",
        "required_realm": 1,
        "materials": {
            "聚气草": 3,
            "灵石粉": 1
        },
        "result_item": "聚气丹",
        "base_time_minutes": 45,
        "effects": {
            "CULTIVATION_EXP": 100
        }
    },
    "strength_pill": {
        "id": "strength_pill",
        "name": "力量丹",
        "description": "永久提升物理攻击的丹药",
        "quality": "UNCOMMON",
        "required_realm": 5,  # 筑基初期
        "materials": {
            "虎骨草": 2,
            "铁精": 1,
            "灵芝": 1
        },
        "result_item": "力量丹",
        "base_time_minutes": 60,
        "effects": {
            "PHYSICAL_ATTACK_PERMANENT": 10
        }
    },
    "wisdom_pill": {
        "id": "wisdom_pill",
        "name": "智慧丹",
        "description": "永久提升法术攻击的丹药",
        "quality": "UNCOMMON",
        "required_realm": 5,
        "materials": {
            "智慧花": 2,
            "月华露": 1,
            "灵芝": 1
        },
        "result_item": "智慧丹",
        "base_time_minutes": 60,
        "effects": {
            "MAGIC_ATTACK_PERMANENT": 10
        }
    },
    "defense_pill": {
        "id": "defense_pill",
        "name": "护体丹",
        "description": "永久提升防御力的丹药",
        "quality": "UNCOMMON",
        "required_realm": 5,
        "materials": {
            "龟甲草": 2,
            "玄铁粉": 1,
            "灵芝": 1
        },
        "result_item": "护体丹",
        "base_time_minutes": 60,
        "effects": {
            "PHYSICAL_DEFENSE_PERMANENT": 8,
            "MAGIC_DEFENSE_PERMANENT": 8
        }
    },
    "breakthrough_pill": {
        "id": "breakthrough_pill",
        "name": "破境丹",
        "description": "提升突破成功率的丹药",
        "quality": "RARE",
        "required_realm": 9,  # 金丹初期
        "materials": {
            "千年灵芝": 1,
            "破境草": 3,
            "天雷石": 1,
            "龙血": 1
        },
        "result_item": "破境丹",
        "base_time_minutes": 120,
        "effects": {
            "BREAKTHROUGH_RATE_BONUS": 0.3  # +30%突破成功率
        }
    },
    "luck_pill": {
        "id": "luck_pill",
        "name": "转运丹",
        "description": "提升气运值的丹药",
        "quality": "RARE",
        "required_realm": 9,
        "materials": {
            "四叶草": 5,
            "幸运石": 2,
            "凤凰羽": 1
        },
        "result_item": "转运丹",
        "base_time_minutes": 90,
        "effects": {
            "LUCK_VALUE": 20
        }
    }
}

# 炼丹材料配置
ALCHEMY_MATERIALS = {
    # 基础草药
    "灵草": {"type": "herb", "rarity": "common", "description": "最基础的炼丹材料"},
    "聚气草": {"type": "herb", "rarity": "common", "description": "蕴含灵气的草药"},
    "灵芝": {"type": "herb", "rarity": "uncommon", "description": "珍贵的药材"},
    "千年灵芝": {"type": "herb", "rarity": "rare", "description": "极其珍贵的千年药材"},

    # 特殊草药
    "虎骨草": {"type": "herb", "rarity": "uncommon", "description": "增强力量的草药"},
    "智慧花": {"type": "herb", "rarity": "uncommon", "description": "提升智慧的花朵"},
    "龟甲草": {"type": "herb", "rarity": "uncommon", "description": "增强防御的草药"},
    "破境草": {"type": "herb", "rarity": "rare", "description": "助力突破的神奇草药"},
    "四叶草": {"type": "herb", "rarity": "rare", "description": "带来好运的稀有草药"},

    # 矿物材料
    "灵石粉": {"type": "mineral", "rarity": "common", "description": "研磨的灵石粉末"},
    "铁精": {"type": "mineral", "rarity": "uncommon", "description": "精炼的铁质材料"},
    "玄铁粉": {"type": "mineral", "rarity": "uncommon", "description": "珍贵的玄铁粉末"},
    "天雷石": {"type": "mineral", "rarity": "rare", "description": "蕴含雷电之力的石头"},
    "幸运石": {"type": "mineral", "rarity": "rare", "description": "带来好运的神秘石头"},

    # 特殊材料
    "清水": {"type": "liquid", "rarity": "common", "description": "纯净的清水"},
    "月华露": {"type": "liquid", "rarity": "uncommon", "description": "月光凝聚的露水"},
    "龙血": {"type": "liquid", "rarity": "epic", "description": "传说中的龙族血液"},
    "凤凰羽": {"type": "material", "rarity": "epic", "description": "凤凰的珍贵羽毛"}
}

# 洞府系统配置
CAVE_SYSTEM_CONFIG = {
    # 基础配置
    "MAX_CAVE_LEVEL": 10,  # 最大洞府等级
    "MAX_SPIRIT_ARRAY_LEVEL": 10,  # 最大聚灵阵等级

    # 洞府等级解锁功能（只保留已实现的功能）
    "CAVE_LEVEL_FEATURES": {
        0: ["突破"],  # 0级洞府可以突破
        1: [],
        2: [],
        3: ["聚灵阵"]  # 3级洞府解锁聚灵阵
    },

    # 洞府升级成本（返回字典格式）
    "CAVE_UPGRADE_COSTS": {
        1: {"spirit_stone": 500},   # 0级升1级
        2: {"spirit_stone": 1000},  # 1级升2级
        3: {"spirit_stone": 2000},
        4: {"spirit_stone": 3000},
        5: {"spirit_stone": 4000},
        6: {"spirit_stone": 5000},
        7: {"spirit_stone": 6000},
        8: {"spirit_stone": 7000},
        9: {"spirit_stone": 8000},
        10: {"spirit_stone": 9000}
    },

    # 聚灵阵升级成本（返回字典格式）
    "SPIRIT_ARRAY_UPGRADE_COSTS": {
        1: {"spirit_stone": 500},
        2: {"spirit_stone": 1000},
        3: {"spirit_stone": 1500},
        4: {"spirit_stone": 2000},
        5: {"spirit_stone": 2500},
        6: {"spirit_stone": 3000},
        7: {"spirit_stone": 3500},
        8: {"spirit_stone": 4000},
        9: {"spirit_stone": 4500},
        10: {"spirit_stone": 5000}
    },

    # 洞府升级配置
    "CAVE_UPGRADE": {
        "MAX_LEVEL": 10,  # 最大等级
        "LEVEL_BENEFITS": {
            # 0级洞府无减免，每级减少1%修为损失，每周期获得金币
            0: {"cultivation_loss_reduction": 0.00, "gold_per_cycle": (0, 0)},
            1: {"cultivation_loss_reduction": 0.01, "gold_per_cycle": (2, 6)},
            2: {"cultivation_loss_reduction": 0.02, "gold_per_cycle": (4, 12)},
            3: {"cultivation_loss_reduction": 0.03, "gold_per_cycle": (6, 18)},
            4: {"cultivation_loss_reduction": 0.04, "gold_per_cycle": (8, 24)},
            5: {"cultivation_loss_reduction": 0.05, "gold_per_cycle": (10, 30)},
            6: {"cultivation_loss_reduction": 0.06, "gold_per_cycle": (12, 36)},
            7: {"cultivation_loss_reduction": 0.07, "gold_per_cycle": (14, 42)},
            8: {"cultivation_loss_reduction": 0.08, "gold_per_cycle": (16, 48)},
            9: {"cultivation_loss_reduction": 0.09, "gold_per_cycle": (18, 54)},
            10: {"cultivation_loss_reduction": 0.10, "gold_per_cycle": (20, 60)},
        },
        "UPGRADE_COSTS": {
            # 升级到对应等级所需的灵石
            1: 500, 2: 1000, 3: 2000, 4: 3000, 5: 4000,
            6: 5000, 7: 6000, 8: 7000, 9: 8000, 10: 9000
        }
    },

    # 聚灵阵配置
    "SPIRIT_GATHERING_ARRAY": {
        "MAX_LEVEL": 10,  # 最大等级
        "UNLOCK_CAVE_LEVEL": 3,  # 需要3级洞府解锁
        "LEVEL_BENEFITS": {
            # 每级减少5%修炼间隔，每周期获得灵石
            1: {"cultivation_interval_reduction": 0.05, "spirit_stone_per_cycle": (1, 3)},
            2: {"cultivation_interval_reduction": 0.10, "spirit_stone_per_cycle": (2, 6)},
            3: {"cultivation_interval_reduction": 0.15, "spirit_stone_per_cycle": (3, 9)},
            4: {"cultivation_interval_reduction": 0.20, "spirit_stone_per_cycle": (4, 12)},
            5: {"cultivation_interval_reduction": 0.25, "spirit_stone_per_cycle": (5, 15)},
            6: {"cultivation_interval_reduction": 0.30, "spirit_stone_per_cycle": (6, 18)},
            7: {"cultivation_interval_reduction": 0.35, "spirit_stone_per_cycle": (7, 21)},
            8: {"cultivation_interval_reduction": 0.40, "spirit_stone_per_cycle": (8, 24)},
            9: {"cultivation_interval_reduction": 0.45, "spirit_stone_per_cycle": (9, 27)},
            10: {"cultivation_interval_reduction": 0.50, "spirit_stone_per_cycle": (10, 30)},
        },
        "UPGRADE_COSTS": {
            # 升级到对应等级所需的灵石
            1: 500, 2: 1000, 3: 1500, 4: 2000, 5: 2500,
            6: 3000, 7: 3500, 8: 4000, 9: 4500, 10: 5000
        }
    }
}

# 默认配置
DEFAULT_CONFIG = {
    "MAX_LUCK_VALUE": 100,            # 最大气运值
    "MIN_LUCK_VALUE": 0,              # 最小气运值
    "BREAKTHROUGH_BASE_CHANCE": 0.5,  # 基础突破成功率
    "DAILY_LUCK_MIN": 0,              # 每日随机气运最小值
    "DAILY_LUCK_MAX": 100,            # 每日随机气运最大值
}

# 副本系统配置
DUNGEON_SYSTEM_CONFIG = {
    # 基础配置
    "MAX_CONCURRENT_DUNGEONS": 1,  # 最大同时进行的副本数量
    "STAMINA_REGEN_RATE": 1,  # 体力恢复速度（每分钟）
    "MAX_STAMINA": 100,  # 最大体力值

    # 副本难度配置
    "DIFFICULTY_MULTIPLIERS": {
        "EASY": {
            "monster_hp_multiplier": 0.8,
            "monster_attack_multiplier": 0.8,
            "exp_multiplier": 1.0,
            "gold_multiplier": 1.0,
            "drop_rate_multiplier": 1.0
        },
        "NORMAL": {
            "monster_hp_multiplier": 1.0,
            "monster_attack_multiplier": 1.0,
            "exp_multiplier": 1.2,
            "gold_multiplier": 1.2,
            "drop_rate_multiplier": 1.1
        },
        "HARD": {
            "monster_hp_multiplier": 1.5,
            "monster_attack_multiplier": 1.3,
            "exp_multiplier": 1.5,
            "gold_multiplier": 1.5,
            "drop_rate_multiplier": 1.3
        },
        "HELL": {
            "monster_hp_multiplier": 2.0,
            "monster_attack_multiplier": 1.8,
            "exp_multiplier": 2.0,
            "gold_multiplier": 2.0,
            "drop_rate_multiplier": 1.5
        }
    },

    # 怪物类型配置
    "MONSTER_TYPE_MULTIPLIERS": {
        "NORMAL": {
            "hp_multiplier": 1.0,
            "attack_multiplier": 1.0,
            "defense_multiplier": 1.0,
            "exp_multiplier": 1.0,
            "gold_multiplier": 1.0
        },
        "ELITE": {
            "hp_multiplier": 2.0,
            "attack_multiplier": 1.5,
            "defense_multiplier": 1.3,
            "exp_multiplier": 2.0,
            "gold_multiplier": 2.0
        },
        "BOSS": {
            "hp_multiplier": 5.0,
            "attack_multiplier": 2.0,
            "defense_multiplier": 1.8,
            "exp_multiplier": 5.0,
            "gold_multiplier": 5.0
        }
    }
}

# 战斗系统配置
COMBAT_SYSTEM_CONFIG = {
    # 基础战斗配置
    "BASE_CRITICAL_RATE": 0.05,  # 基础暴击率 5%
    "BASE_CRITICAL_DAMAGE": 1.5,  # 基础暴击倍数 150%
    "DODGE_RATE": 0.05,  # 基础闪避率 5%

    # 伤害计算配置
    "DAMAGE_VARIANCE": 0.1,  # 伤害浮动范围 ±10%
    "DEFENSE_REDUCTION_FACTOR": 0.5,  # 防御减伤系数
    "MIN_DAMAGE": 1,  # 最小伤害

    # 技能配置
    "SKILL_COOLDOWNS": {
        "NORMAL_ATTACK": 0,  # 普通攻击无冷却
        "HEAVY_ATTACK": 3,  # 重击3回合冷却
        "MAGIC_ATTACK": 2,  # 法术攻击2回合冷却
        "HEAL": 5,  # 治疗5回合冷却
        "DEFEND": 1  # 防御1回合冷却
    },

    # 技能效果配置
    "SKILL_EFFECTS": {
        "NORMAL_ATTACK": {
            "damage_multiplier": 1.0,
            "type": "PHYSICAL"
        },
        "HEAVY_ATTACK": {
            "damage_multiplier": 1.8,
            "type": "PHYSICAL",
            "critical_rate_bonus": 0.2
        },
        "MAGIC_ATTACK": {
            "damage_multiplier": 1.5,
            "type": "MAGIC"
        },
        "HEAL": {
            "heal_multiplier": 0.3,  # 恢复30%最大生命值
            "type": "HEAL"
        },
        "DEFEND": {
            "damage_reduction": 0.5,  # 减少50%伤害
            "type": "DEFEND"
        }
    }
}

# 副本配置数据
DUNGEON_CONFIGS = {
    "beginner_cave": {
        "name": "初心者洞穴",
        "description": "适合新手修士探索的洞穴，里面有一些低级妖兽",
        "difficulty": "EASY",
        "required_realm": 0,  # 凡人即可进入
        "stamina_cost": 10,
        "max_floors": 3,
        "base_exp_reward": 100,
        "base_gold_reward": 50,
        "monster_config": {
            "floor_1": [
                {"monster_id": "cave_rat", "count": 2},
                {"monster_id": "cave_spider", "count": 1}
            ],
            "floor_2": [
                {"monster_id": "cave_spider", "count": 2},
                {"monster_id": "cave_bat", "count": 1}
            ],
            "floor_3": [
                {"monster_id": "cave_guardian", "count": 1, "type": "BOSS"}
            ]
        },
        "drop_table": {
            "common_drops": [
                {"item": "灵草", "rate": 0.3, "quantity": [1, 2]},
                {"item": "铜币", "rate": 0.5, "quantity": [10, 30]}
            ],
            "rare_drops": [
                {"item": "初级丹药", "rate": 0.1, "quantity": [1, 1]},
                {"item": "普通装备", "rate": 0.05, "quantity": [1, 1]}
            ]
        }
    },
    "forest_ruins": {
        "name": "森林遗迹",
        "description": "古老的修士遗迹，隐藏着珍贵的宝物",
        "difficulty": "NORMAL",
        "required_realm": 3,  # 练气后期
        "stamina_cost": 20,
        "max_floors": 5,
        "base_exp_reward": 300,
        "base_gold_reward": 150,
        "monster_config": {
            "floor_1": [
                {"monster_id": "forest_wolf", "count": 2}
            ],
            "floor_2": [
                {"monster_id": "forest_wolf", "count": 1},
                {"monster_id": "tree_spirit", "count": 1}
            ],
            "floor_3": [
                {"monster_id": "tree_spirit", "count": 2}
            ],
            "floor_4": [
                {"monster_id": "forest_guardian", "count": 1, "type": "ELITE"}
            ],
            "floor_5": [
                {"monster_id": "ancient_treant", "count": 1, "type": "BOSS"}
            ]
        },
        "drop_table": {
            "common_drops": [
                {"item": "灵芝", "rate": 0.4, "quantity": [1, 3]},
                {"item": "木灵石", "rate": 0.3, "quantity": [1, 2]}
            ],
            "rare_drops": [
                {"item": "中级丹药", "rate": 0.2, "quantity": [1, 2]},
                {"item": "精良装备", "rate": 0.1, "quantity": [1, 1]}
            ],
            "epic_drops": [
                {"item": "森林之心", "rate": 0.02, "quantity": [1, 1]}
            ]
        }
    }
}

# 怪物配置数据
MONSTER_CONFIGS = {
    # 初心者洞穴怪物
    "cave_rat": {
        "name": "洞穴鼠",
        "description": "生活在洞穴中的普通老鼠",
        "monster_type": "NORMAL",
        "level": 1,
        "base_hp": 50,
        "base_physical_attack": 15,
        "base_magic_attack": 5,
        "base_physical_defense": 8,
        "base_magic_defense": 5,
        "critical_rate": 0.02,
        "critical_damage": 1.3,
        "skills": ["NORMAL_ATTACK"],
        "ai_pattern": {"aggressive": 0.7, "defensive": 0.3},
        "exp_reward": 20,
        "gold_reward": 5
    },
    "cave_spider": {
        "name": "洞穴蜘蛛",
        "description": "有毒的洞穴蜘蛛",
        "monster_type": "NORMAL",
        "level": 2,
        "base_hp": 80,
        "base_physical_attack": 25,
        "base_magic_attack": 10,
        "base_physical_defense": 12,
        "base_magic_defense": 8,
        "critical_rate": 0.05,
        "critical_damage": 1.4,
        "skills": ["NORMAL_ATTACK", "POISON_BITE"],
        "ai_pattern": {"aggressive": 0.8, "defensive": 0.2},
        "exp_reward": 35,
        "gold_reward": 8
    },
    "cave_bat": {
        "name": "洞穴蝙蝠",
        "description": "敏捷的洞穴蝙蝠",
        "monster_type": "NORMAL",
        "level": 3,
        "base_hp": 60,
        "base_physical_attack": 30,
        "base_magic_attack": 15,
        "base_physical_defense": 10,
        "base_magic_defense": 12,
        "critical_rate": 0.08,
        "critical_damage": 1.5,
        "skills": ["NORMAL_ATTACK", "SWIFT_STRIKE"],
        "ai_pattern": {"aggressive": 0.9, "defensive": 0.1},
        "exp_reward": 40,
        "gold_reward": 10
    },
    "cave_guardian": {
        "name": "洞穴守护者",
        "description": "守护洞穴的强大石像",
        "monster_type": "BOSS",
        "level": 5,
        "base_hp": 300,
        "base_physical_attack": 50,
        "base_magic_attack": 30,
        "base_physical_defense": 25,
        "base_magic_defense": 20,
        "critical_rate": 0.1,
        "critical_damage": 1.8,
        "skills": ["NORMAL_ATTACK", "HEAVY_ATTACK", "STONE_SHIELD"],
        "ai_pattern": {"aggressive": 0.6, "defensive": 0.4},
        "exp_reward": 150,
        "gold_reward": 50
    },

    # 森林遗迹怪物
    "forest_wolf": {
        "name": "森林狼",
        "description": "凶猛的森林狼",
        "monster_type": "NORMAL",
        "level": 8,
        "base_hp": 150,
        "base_physical_attack": 45,
        "base_magic_attack": 20,
        "base_physical_defense": 20,
        "base_magic_defense": 15,
        "critical_rate": 0.1,
        "critical_damage": 1.6,
        "skills": ["NORMAL_ATTACK", "BITE", "HOWL"],
        "ai_pattern": {"aggressive": 0.8, "defensive": 0.2},
        "exp_reward": 80,
        "gold_reward": 20
    },
    "tree_spirit": {
        "name": "树灵",
        "description": "古老的树木精灵",
        "monster_type": "NORMAL",
        "level": 10,
        "base_hp": 200,
        "base_physical_attack": 35,
        "base_magic_attack": 60,
        "base_physical_defense": 25,
        "base_magic_defense": 30,
        "critical_rate": 0.05,
        "critical_damage": 1.4,
        "skills": ["NORMAL_ATTACK", "MAGIC_ATTACK", "HEAL"],
        "ai_pattern": {"aggressive": 0.5, "defensive": 0.5},
        "exp_reward": 120,
        "gold_reward": 30
    },
    "forest_guardian": {
        "name": "森林守护者",
        "description": "保护森林的强大精灵",
        "monster_type": "ELITE",
        "level": 12,
        "base_hp": 400,
        "base_physical_attack": 60,
        "base_magic_attack": 80,
        "base_physical_defense": 35,
        "base_magic_defense": 40,
        "critical_rate": 0.12,
        "critical_damage": 1.7,
        "skills": ["NORMAL_ATTACK", "MAGIC_ATTACK", "NATURE_BLESSING", "ENTANGLE"],
        "ai_pattern": {"aggressive": 0.7, "defensive": 0.3},
        "exp_reward": 250,
        "gold_reward": 80
    },
    "ancient_treant": {
        "name": "远古树人",
        "description": "森林中最古老最强大的存在",
        "monster_type": "BOSS",
        "level": 15,
        "base_hp": 800,
        "base_physical_attack": 80,
        "base_magic_attack": 100,
        "base_physical_defense": 50,
        "base_magic_defense": 60,
        "critical_rate": 0.15,
        "critical_damage": 2.0,
        "skills": ["NORMAL_ATTACK", "HEAVY_ATTACK", "MAGIC_ATTACK", "HEAL", "FOREST_RAGE"],
        "ai_pattern": {"aggressive": 0.6, "defensive": 0.4},
        "exp_reward": 500,
        "gold_reward": 200
    }
}
