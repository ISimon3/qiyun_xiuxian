# 灵根系统 API 文档

## 📋 概述

本文档描述了灵根系统的API接口、数据结构和使用方法，供开发者参考。

## 🔧 核心API

### 1. 灵根随机分配

#### `CharacterCRUD._get_random_spiritual_root()`

**功能**：根据权重随机选择灵根类型

**返回值**：
- `str` - 灵根名称

**示例**：
```python
from server.database.crud import CharacterCRUD

spiritual_root = CharacterCRUD._get_random_spiritual_root()
print(spiritual_root)  # 输出：天灵根、变异灵根等
```

**权重配置**：
```python
权重分布：
天灵根: 1 (0.45%)
变异灵根: 3 (1.34%)
单灵根: 20 (8.93%)
其他灵根: 40×5 (89.28%)
```

### 2. 修炼速度计算

#### `simulate_cultivation_session(luck_value, cultivation_focus, cultivation_speed)`

**功能**：模拟一次修炼周期，应用灵根修炼速度加成

**参数**：
- `luck_value: int` - 气运值 (0-100)
- `cultivation_focus: str` - 修炼方向 ("HP", "PHYSICAL_ATTACK"等)
- `cultivation_speed: float` - 修炼速度倍率（灵根提供）

**返回值**：
```python
{
    "exp_gained": int,           # 获得的修为
    "attribute_gained": int,     # 获得的属性点
    "attribute_type": str,       # 属性类型
    "luck_effect": str,          # 气运影响描述
    "luck_multiplier": float,    # 气运倍率
    "special_event": str|None,   # 特殊事件
    "message": str               # 结果描述
}
```

**示例**：
```python
from shared.utils import simulate_cultivation_session
from shared.constants import SPIRITUAL_ROOTS

# 获取天灵根的修炼速度
tianling_speed = SPIRITUAL_ROOTS["天灵根"]["multiplier"]  # 2.0

# 模拟修炼
result = simulate_cultivation_session(
    luck_value=50,
    cultivation_focus="HP", 
    cultivation_speed=tianling_speed
)

print(f"获得修为：{result['exp_gained']}")
print(f"获得属性：{result['attribute_gained']}")
```

### 3. 突破成功率计算

#### `CharacterService.calculate_breakthrough_success_rate(character, target_realm, use_items)`

**功能**：计算突破成功率，包含灵根加成

**参数**：
- `character: Character` - 角色对象
- `target_realm: int` - 目标境界
- `use_items: List[int]|None` - 使用的辅助物品

**返回值**：
- `float` - 突破成功率 (0.0-1.0)

**示例**：
```python
from server.core.character_service import CharacterService

# 假设有一个角色对象
success_rate = CharacterService.calculate_breakthrough_success_rate(
    character=character,
    target_realm=character.cultivation_realm + 1,
    use_items=None
)

print(f"突破成功率：{success_rate * 100:.1f}%")
```

**突破加成配置**：
```python
天灵根: +15% (0.15)
变异灵根: +10% (0.10)  
单灵根: +5% (0.05)
其他灵根: 无加成 (0.0)
```

## 📊 数据结构

### 1. 灵根配置结构

```python
SPIRITUAL_ROOTS = {
    "灵根名称": {
        "name": str,                    # 显示名称
        "multiplier": float,            # 修炼速度倍率
        "breakthrough_bonus": float,    # 突破成功率加成 (0.0-1.0)
        "rarity": str,                 # 稀有度标识
        "weight": int                  # 随机分配权重
    }
}
```

### 2. 角色灵根字段

```python
class Character:
    spiritual_root: str  # 灵根名称，如"天灵根"
```

### 3. 灵根信息响应

```python
{
    "spiritual_root": "天灵根",
    "multiplier": 2.0,
    "breakthrough_bonus": 0.15,
    "rarity": "legendary",
    "description": "修炼速度2.0倍，突破成功率+15%"
}
```

## 🔍 查询接口

### 1. 获取灵根信息

```python
from shared.constants import SPIRITUAL_ROOTS

def get_spiritual_root_info(root_name: str) -> dict:
    """获取指定灵根的详细信息"""
    if root_name not in SPIRITUAL_ROOTS:
        return None
    
    root_info = SPIRITUAL_ROOTS[root_name]
    return {
        "name": root_info["name"],
        "multiplier": root_info["multiplier"],
        "breakthrough_bonus": root_info.get("breakthrough_bonus", 0.0),
        "rarity": root_info["rarity"],
        "weight": root_info["weight"]
    }

# 使用示例
info = get_spiritual_root_info("天灵根")
print(info)
```

### 2. 获取所有灵根列表

```python
def get_all_spiritual_roots() -> list:
    """获取所有灵根信息列表"""
    roots = []
    for root_name, root_info in SPIRITUAL_ROOTS.items():
        roots.append({
            "name": root_name,
            "multiplier": root_info["multiplier"],
            "breakthrough_bonus": root_info.get("breakthrough_bonus", 0.0),
            "rarity": root_info["rarity"],
            "weight": root_info["weight"]
        })
    
    # 按修炼速度排序
    roots.sort(key=lambda x: x["multiplier"], reverse=True)
    return roots
```

### 3. 计算获得概率

```python
def calculate_spiritual_root_probabilities() -> dict:
    """计算各灵根的获得概率"""
    total_weight = sum(root_info["weight"] for root_info in SPIRITUAL_ROOTS.values())
    
    probabilities = {}
    for root_name, root_info in SPIRITUAL_ROOTS.items():
        probability = root_info["weight"] / total_weight
        probabilities[root_name] = {
            "probability": probability,
            "percentage": probability * 100,
            "weight": root_info["weight"]
        }
    
    return probabilities

# 使用示例
probs = calculate_spiritual_root_probabilities()
for root, data in probs.items():
    print(f"{root}: {data['percentage']:.2f}%")
```

## 🧪 测试工具

### 1. 灵根分配测试

```python
def test_spiritual_root_distribution(sample_size: int = 1000) -> dict:
    """测试灵根分配概率"""
    from collections import Counter
    
    results = []
    for _ in range(sample_size):
        root = CharacterCRUD._get_random_spiritual_root()
        results.append(root)
    
    counter = Counter(results)
    distribution = {}
    
    for root_name in SPIRITUAL_ROOTS.keys():
        count = counter.get(root_name, 0)
        distribution[root_name] = {
            "count": count,
            "percentage": count / sample_size * 100
        }
    
    return distribution
```

### 2. 修炼效果测试

```python
def test_cultivation_effects(cycles: int = 100) -> dict:
    """测试不同灵根的修炼效果"""
    results = {}
    
    for root_name, root_info in SPIRITUAL_ROOTS.items():
        total_exp = 0
        total_attr = 0
        
        for _ in range(cycles):
            result = simulate_cultivation_session(
                luck_value=50,
                cultivation_focus="HP",
                cultivation_speed=root_info["multiplier"]
            )
            total_exp += result["exp_gained"]
            total_attr += result["attribute_gained"]
        
        results[root_name] = {
            "avg_exp": total_exp / cycles,
            "avg_attr": total_attr / cycles,
            "multiplier": root_info["multiplier"]
        }
    
    return results
```

## ⚙️ 配置管理

### 1. 修改灵根配置

```python
# 在 shared/constants.py 中修改
SPIRITUAL_ROOTS = {
    "天灵根": {
        "name": "天灵根",
        "multiplier": 2.0,              # 修改修炼速度
        "breakthrough_bonus": 0.15,     # 修改突破加成
        "rarity": "legendary",
        "weight": 1                     # 修改获得概率
    },
    # ... 其他配置
}
```

### 2. 添加新灵根

```python
# 在 SPIRITUAL_ROOTS 中添加新条目
"新灵根": {
    "name": "新灵根",
    "multiplier": 1.8,
    "breakthrough_bonus": 0.08,
    "rarity": "epic",
    "weight": 2
}
```

### 3. 验证配置

```python
def validate_spiritual_root_config() -> bool:
    """验证灵根配置的正确性"""
    required_fields = ["name", "multiplier", "rarity", "weight"]
    
    for root_name, root_info in SPIRITUAL_ROOTS.items():
        # 检查必需字段
        for field in required_fields:
            if field not in root_info:
                print(f"错误：{root_name} 缺少字段 {field}")
                return False
        
        # 检查数值范围
        if root_info["multiplier"] <= 0:
            print(f"错误：{root_name} 修炼倍率必须大于0")
            return False
        
        if root_info["weight"] <= 0:
            print(f"错误：{root_name} 权重必须大于0")
            return False
        
        breakthrough_bonus = root_info.get("breakthrough_bonus", 0.0)
        if breakthrough_bonus < 0 or breakthrough_bonus > 1:
            print(f"错误：{root_name} 突破加成必须在0-1之间")
            return False
    
    print("✅ 灵根配置验证通过")
    return True
```

## 🚨 错误处理

### 1. 常见错误

```python
# 灵根不存在
if character.spiritual_root not in SPIRITUAL_ROOTS:
    # 设置默认灵根
    character.spiritual_root = "三灵根"

# 配置缺失字段
root_info = SPIRITUAL_ROOTS.get(character.spiritual_root, {})
multiplier = root_info.get("multiplier", 1.0)  # 默认1.0倍
breakthrough_bonus = root_info.get("breakthrough_bonus", 0.0)  # 默认无加成
```

### 2. 异常处理

```python
def safe_get_spiritual_root_multiplier(spiritual_root: str) -> float:
    """安全获取灵根修炼倍率"""
    try:
        return SPIRITUAL_ROOTS[spiritual_root]["multiplier"]
    except KeyError:
        print(f"警告：未知灵根 {spiritual_root}，使用默认倍率")
        return 1.0
```

## 📝 使用建议

1. **总是验证配置**：修改后运行验证函数
2. **使用安全接口**：处理可能的配置缺失
3. **记录日志**：重要操作要记录日志
4. **定期测试**：使用测试工具验证功能
5. **备份配置**：修改前备份原始配置

---

**API文档版本**：v1.0  
**对应系统版本**：灵根系统 v1.0  
**最后更新**：2025-07-17
