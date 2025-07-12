# 数据库迁移脚本：添加灵田相关表

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from sqlalchemy import text
from server.database.database import engine


async def add_farm_tables():
    """添加灵田相关表"""
    
    try:
        async with engine.begin() as conn:
            # 检查farm_plots表是否已存在
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='farm_plots'
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            if 'farm_plots' not in existing_tables:
                # 创建farm_plots表
                await conn.execute(text("""
                    CREATE TABLE farm_plots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER NOT NULL,
                        plot_index INTEGER NOT NULL,
                        plot_type VARCHAR(20) DEFAULT 'normal',
                        is_unlocked BOOLEAN DEFAULT 0,
                        seed_item_id INTEGER,
                        planted_at DATETIME,
                        harvest_at DATETIME,
                        growth_stage INTEGER DEFAULT 0,
                        is_ready BOOLEAN DEFAULT 0,
                        is_withered BOOLEAN DEFAULT 0,
                        has_pest BOOLEAN DEFAULT 0,
                        has_weed BOOLEAN DEFAULT 0,
                        mutation_chance REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (character_id) REFERENCES characters(id),
                        FOREIGN KEY (seed_item_id) REFERENCES items(id),
                        UNIQUE(character_id, plot_index)
                    )
                """))
                
                # 创建索引
                await conn.execute(text("""
                    CREATE INDEX ix_farm_plot_character_index 
                    ON farm_plots(character_id, plot_index)
                """))
                
                print("✅ 已创建 farm_plots 表")
            else:
                print("ℹ️ farm_plots 表已存在")
            
            # 添加一些基础种子物品（如果不存在）
            seed_items = [
                ("灵草种子", "seed", "可种植的灵草种子，2小时成熟", 50),
                ("灵芝种子", "seed", "可种植的灵芝种子，6小时成熟", 100),
                ("聚气草种子", "seed", "可种植的聚气草种子，4小时成熟", 75),
                ("灵草", "material", "从灵田收获的灵草", 20),
                ("灵芝", "material", "从灵田收获的灵芝", 50),
                ("聚气草", "material", "从灵田收获的聚气草", 30),
                ("高品质灵草", "material", "变异的高品质灵草", 100),
                ("灵草精华", "material", "灵草的精华", 200),
                ("千年灵芝", "material", "变异的千年灵芝", 500),
                ("灵芝王", "material", "变异的灵芝王", 800),
                ("聚气草精华", "material", "聚气草的精华", 150),
                ("灵气结晶", "material", "聚气草变异产生的灵气结晶", 300),
            ]
            
            for name, item_type, description, value in seed_items:
                # 检查物品是否已存在
                result = await conn.execute(text("""
                    SELECT id FROM items WHERE name = :name
                """), {"name": name})
                
                if not result.fetchone():
                    await conn.execute(text("""
                        INSERT INTO items (name, item_type, description, sell_price, quality, stack_size, required_realm)
                        VALUES (:name, :item_type, :description, :sell_price, :quality, :stack_size, :required_realm)
                    """), {
                        "name": name,
                        "item_type": item_type,
                        "description": description,
                        "sell_price": value,
                        "quality": "common",
                        "stack_size": 999,
                        "required_realm": 0
                    })
                    print(f"✅ 已添加物品: {name}")
            
            print("✅ 数据库迁移完成")
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        raise
    finally:
        await engine.dispose()


async def initialize_character_farm_plots():
    """为现有角色初始化灵田地块"""
    try:
        async with engine.begin() as conn:
            # 获取所有角色
            result = await conn.execute(text("SELECT id FROM characters"))
            characters = result.fetchall()
            
            for character in characters:
                character_id = character[0]
                
                # 检查是否已有地块
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM farm_plots WHERE character_id = :character_id
                """), {"character_id": character_id})
                
                plot_count = result.scalar()
                
                if plot_count == 0:
                    # 为角色创建12个地块，前4个解锁
                    for i in range(12):
                        await conn.execute(text("""
                            INSERT INTO farm_plots (
                                character_id, plot_index, plot_type, is_unlocked,
                                growth_stage, is_ready, is_withered, has_pest, has_weed, mutation_chance
                            ) VALUES (:character_id, :plot_index, 'normal', :is_unlocked, 0, 0, 0, 0, 0, 0.0)
                        """), {
                            "character_id": character_id,
                            "plot_index": i,
                            "is_unlocked": i < 4  # 前4个地块默认解锁
                        })
                    
                    print(f"✅ 为角色 {character_id} 初始化了灵田地块")
            
            print("✅ 角色灵田初始化完成")
            
    except Exception as e:
        print(f"❌ 角色灵田初始化失败: {str(e)}")
        raise


async def give_starter_seeds():
    """给现有角色一些初始种子"""
    try:
        # 导入必要的模块
        from server.database.database import AsyncSessionLocal
        from server.database.crud import InventoryCRUD

        async with AsyncSessionLocal() as db:
            # 获取所有角色
            result = await db.execute(text("SELECT id FROM characters"))
            characters = result.fetchall()

            # 获取种子物品ID
            seed_result = await db.execute(text("""
                SELECT id, name FROM items WHERE item_type = 'seed'
            """))
            seeds = seed_result.fetchall()

            for character in characters:
                character_id = character[0]

                # 给每个角色一些初始种子
                for seed in seeds:
                    seed_id, seed_name = seed

                    # 检查是否已有该种子
                    result = await db.execute(text("""
                        SELECT id FROM inventory_items
                        WHERE character_id = :character_id AND item_id = :item_id
                    """), {"character_id": character_id, "item_id": seed_id})

                    if not result.fetchone():
                        # 使用CRUD添加种子到背包
                        quantity = 10 if "灵草" in seed_name else 5  # 灵草种子给10个，其他给5个
                        await InventoryCRUD.add_item_to_inventory(db, character_id, seed_id, quantity)

                        print(f"✅ 给角色 {character_id} 添加了 {quantity} 个 {seed_name}")

            await db.commit()
            print("✅ 初始种子分发完成")

    except Exception as e:
        print(f"❌ 初始种子分发失败: {str(e)}")
        raise


if __name__ == "__main__":
    print("开始数据库迁移：添加灵田系统...")
    
    # 创建表和物品
    asyncio.run(add_farm_tables())
    
    # 初始化角色地块
    asyncio.run(initialize_character_farm_plots())
    
    # 分发初始种子
    asyncio.run(give_starter_seeds())
    
    print("数据库迁移完成！")
