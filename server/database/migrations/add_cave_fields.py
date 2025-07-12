# 数据库迁移脚本：添加洞府相关字段

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from sqlalchemy import text
from server.database.database import engine


async def add_cave_fields():
    """添加洞府相关字段到characters表"""
    
    try:
        async with engine.begin() as conn:
            # SQLite检查字段是否已存在
            result = await conn.execute(text("PRAGMA table_info(characters)"))
            existing_columns = [row[1] for row in result.fetchall()]  # row[1] 是列名

            # 添加cave_level字段
            if 'cave_level' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE characters
                    ADD COLUMN cave_level INTEGER DEFAULT 1
                """))
                print("✅ 已添加 cave_level 字段")
            else:
                print("ℹ️ cave_level 字段已存在")

            # 添加spirit_gathering_array_level字段
            if 'spirit_gathering_array_level' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE characters
                    ADD COLUMN spirit_gathering_array_level INTEGER DEFAULT 0
                """))
                print("✅ 已添加 spirit_gathering_array_level 字段")
            else:
                print("ℹ️ spirit_gathering_array_level 字段已存在")
            
            # 更新现有角色的默认值
            await conn.execute(text("""
                UPDATE characters 
                SET cave_level = 1 
                WHERE cave_level IS NULL
            """))
            
            await conn.execute(text("""
                UPDATE characters 
                SET spirit_gathering_array_level = 0 
                WHERE spirit_gathering_array_level IS NULL
            """))
            
            print("✅ 数据库迁移完成")
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("开始数据库迁移：添加洞府相关字段...")
    asyncio.run(add_cave_fields())
    print("数据库迁移完成！")
