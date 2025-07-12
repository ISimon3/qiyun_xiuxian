# 数据库初始化数据脚本

import sys
import os
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.database.database import get_db_session
from server.database.models import Item
from shared.constants import ITEM_QUALITY, EQUIPMENT_SLOTS, ITEM_TYPES
from shared.utils import generate_equipment_attributes


class DataInitializer:
    """数据初始化器"""
    
    def __init__(self):
        self.basic_items = []
        self.equipment_items = []
        
    async def initialize_all_data(self):
        """初始化所有基础数据"""
        print("🚀 开始初始化游戏基础数据...")
        
        async with get_db_session() as db:
            # 检查是否已经初始化过
            result = await db.execute(select(Item).limit(1))
            existing_item = result.scalar_one_or_none()
            
            if existing_item:
                print("⚠️  数据已存在，跳过初始化")
                return
            
            # 初始化基础物品
            await self._init_basic_items(db)
            
            # 初始化装备
            await self._init_equipment_items(db)
            
            print("✅ 游戏基础数据初始化完成！")
    
    async def _init_basic_items(self, db: AsyncSession):
        """初始化基础物品（消耗品、材料等）"""
        print("📦 初始化基础物品...")
        
        basic_items_data = [
            # 基础丹药
            {
                "name": "回血丹",
                "description": "恢复少量生命值的基础丹药",
                "item_type": "PILL",
                "quality": "COMMON",
                "stack_size": 99,
                "sell_price": 10,
                "base_attributes": {"hp_restore": 100}
            },
            {
                "name": "回灵丹", 
                "description": "恢复法力的基础丹药",
                "item_type": "PILL",
                "quality": "COMMON",
                "stack_size": 99,
                "sell_price": 15,
                "base_attributes": {"mp_restore": 50}
            },
            {
                "name": "转运丹",
                "description": "临时提升气运值的珍贵丹药",
                "item_type": "PILL",
                "quality": "UNCOMMON",
                "stack_size": 10,
                "sell_price": 100,
                "base_attributes": {"luck_boost": 10, "duration": 3600}
            },
            
            # 基础材料
            {
                "name": "灵草",
                "description": "常见的炼丹材料",
                "item_type": "MATERIAL",
                "quality": "COMMON",
                "stack_size": 999,
                "sell_price": 2
            },
            {
                "name": "灵石碎片",
                "description": "蕴含灵力的石头碎片",
                "item_type": "MATERIAL", 
                "quality": "COMMON",
                "stack_size": 999,
                "sell_price": 5
            },
            {
                "name": "妖兽内丹",
                "description": "妖兽体内的珍贵内丹",
                "item_type": "MATERIAL",
                "quality": "RARE",
                "stack_size": 99,
                "sell_price": 50
            },
            
            # 种子
            {
                "name": "灵草种子",
                "description": "可以种植灵草的种子",
                "item_type": "SEED",
                "quality": "COMMON",
                "stack_size": 99,
                "sell_price": 1
            },
            {
                "name": "灵芝种子",
                "description": "珍贵的灵芝种子",
                "item_type": "SEED",
                "quality": "UNCOMMON",
                "stack_size": 50,
                "sell_price": 10
            }
        ]
        
        for item_data in basic_items_data:
            item = Item(**item_data)
            db.add(item)
        
        await db.commit()
        print(f"✅ 已添加 {len(basic_items_data)} 个基础物品")
    
    async def _init_equipment_items(self, db: AsyncSession):
        """初始化装备物品"""
        print("⚔️ 初始化装备物品...")
        
        equipment_data = []
        
        # 为每个装备部位创建不同品质的装备
        for slot_key, slot_name in EQUIPMENT_SLOTS.items():
            for quality_key, quality_info in ITEM_QUALITY.items():
                # 为每个境界阶段创建装备（每5个境界一个阶段）
                for realm_tier in range(0, 8):  # 0-35境界，分为8个阶段
                    required_realm = realm_tier * 4  # 0, 4, 8, 12, 16, 20, 24, 28
                    
                    # 生成装备属性
                    base_attrs, _ = generate_equipment_attributes(slot_key, quality_key, required_realm)
                    
                    equipment_name = f"{quality_info['name']}{slot_name}"
                    if realm_tier > 0:
                        tier_names = ["", "精良", "优秀", "精品", "极品", "传承", "仙品", "神器"]
                        equipment_name = f"{tier_names[realm_tier]}{equipment_name}"
                    
                    equipment_item = {
                        "name": equipment_name,
                        "description": f"适合{required_realm}境界修士使用的{quality_info['name']}品质{slot_name}",
                        "item_type": "EQUIPMENT",
                        "quality": quality_key,
                        "stack_size": 1,
                        "sell_price": (required_realm + 1) * 50 * (list(ITEM_QUALITY.keys()).index(quality_key) + 1),
                        "equipment_slot": slot_key,
                        "required_realm": required_realm,
                        "base_attributes": base_attrs.model_dump()
                    }
                    
                    equipment_data.append(equipment_item)
        
        # 批量添加装备
        for eq_data in equipment_data:
            item = Item(**eq_data)
            db.add(item)
        
        await db.commit()
        print(f"✅ 已添加 {len(equipment_data)} 个装备物品")


async def main():
    """主函数"""
    initializer = DataInitializer()
    await initializer.initialize_all_data()


if __name__ == "__main__":
    asyncio.run(main())
