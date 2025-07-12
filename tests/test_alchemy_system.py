# 炼丹系统测试脚本

import sys
import os
import asyncio
import pytest
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.database.database import get_db_session
from server.database.models import Character, User, AlchemyRecipe, AlchemySession, Item, InventoryItem
from server.core.systems.alchemy_system import AlchemySystem
from server.database.crud import CharacterCRUD, InventoryCRUD
from shared.constants import ALCHEMY_RECIPES
from sqlalchemy import select, delete


class TestAlchemySystem:
    """炼丹系统测试类"""

    async def setup_test_data(self):
        """设置测试数据"""
        async with get_db_session() as db:
            # 清理测试数据
            await db.execute(delete(AlchemySession))
            await db.execute(delete(InventoryItem))
            await db.execute(delete(Character))
            await db.execute(delete(User))
            await db.commit()
            
            # 创建测试用户
            user = User(
                username="test_alchemist",
                email="test@example.com",
                hashed_password="test_password"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # 创建测试角色
            character = Character(
                user_id=user.id,
                name="测试炼丹师",
                cultivation_realm=5,  # 筑基初期
                alchemy_level=2,
                alchemy_exp=50,
                luck_value=70,
                cave_level=3  # 有丹房
            )
            db.add(character)
            await db.commit()
            await db.refresh(character)
            
            # 添加测试材料
            materials = [
                ("灵草", 100),
                ("聚气草", 50),
                ("清水", 200),
                ("灵石粉", 30),
                ("灵芝", 20),
                ("虎骨草", 10),
                ("智慧花", 10),
                ("龟甲草", 10)
            ]
            
            for material_name, quantity in materials:
                # 查找材料物品
                result = await db.execute(
                    select(Item).where(Item.name == material_name)
                )
                item = result.scalar_one_or_none()
                
                if item:
                    # 添加到背包
                    inventory_item = InventoryItem(
                        character_id=character.id,
                        item_id=item.id,
                        quantity=quantity,
                        attribute_variation=1.0
                    )
                    db.add(inventory_item)
            
            await db.commit()
            
            return user, character
    
    async def test_get_alchemy_info(self, setup_test_data):
        """测试获取炼丹信息"""
        user, character = setup_test_data
        
        async with get_db_session() as db:
            result = await AlchemySystem.get_alchemy_info(db, character)
            
            assert result["success"] == True
            assert result["alchemy_level"] == 2
            assert result["alchemy_exp"] == 50
            assert len(result["available_recipes"]) > 0
            assert len(result["materials_inventory"]) > 0
            
            print("✅ 获取炼丹信息测试通过")
    
    async def test_start_alchemy_success(self, setup_test_data):
        """测试成功开始炼丹"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 尝试炼制回血丹
            result = await AlchemySystem.start_alchemy(db, character, "healing_pill")
            
            assert result["success"] == True
            assert "session_info" in result
            assert result["session_info"]["recipe_id"] == "healing_pill"
            assert result["session_info"]["status"] == "IN_PROGRESS"
            
            print("✅ 开始炼丹测试通过")
    
    async def test_start_alchemy_insufficient_materials(self, setup_test_data):
        """测试材料不足时开始炼丹"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 清空材料
            await db.execute(
                delete(InventoryItem).where(InventoryItem.character_id == character.id)
            )
            await db.commit()
            
            # 尝试炼制回血丹
            result = await AlchemySystem.start_alchemy(db, character, "healing_pill")
            
            assert result["success"] == False
            assert "材料不足" in result["message"]
            
            print("✅ 材料不足测试通过")
    
    async def test_start_alchemy_realm_requirement(self, setup_test_data):
        """测试境界要求"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 降低角色境界
            character.cultivation_realm = 0
            await db.commit()
            
            # 尝试炼制需要更高境界的丹药
            result = await AlchemySystem.start_alchemy(db, character, "strength_pill")
            
            assert result["success"] == False
            assert "境界不足" in result["message"]
            
            print("✅ 境界要求测试通过")
    
    async def test_collect_alchemy_result_not_ready(self, setup_test_data):
        """测试收取未完成的炼丹结果"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 开始炼丹
            start_result = await AlchemySystem.start_alchemy(db, character, "healing_pill")
            assert start_result["success"] == True
            
            session_id = start_result["session_info"]["id"]
            
            # 立即尝试收取
            collect_result = await AlchemySystem.collect_alchemy_result(db, character, session_id)
            
            assert collect_result["success"] == False
            assert "尚未完成" in collect_result["message"]
            
            print("✅ 收取未完成结果测试通过")
    
    async def test_collect_alchemy_result_completed(self, setup_test_data):
        """测试收取已完成的炼丹结果"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 创建一个已完成的炼丹会话
            session = AlchemySession(
                character_id=character.id,
                recipe_id="healing_pill",
                quality="COMMON",
                started_at=datetime.now() - timedelta(hours=1),
                finish_at=datetime.now() - timedelta(minutes=1),  # 已完成
                success_rate=0.9,
                result_item_name="回血丹"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # 收取结果
            collect_result = await AlchemySystem.collect_alchemy_result(db, character, session.id)
            
            # 由于是随机结果，只检查基本结构
            assert collect_result["success"] == True
            assert "message" in collect_result
            
            print("✅ 收取已完成结果测试通过")
    
    async def test_max_concurrent_sessions(self, setup_test_data):
        """测试最大并发会话限制"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 创建最大数量的活跃会话
            from shared.constants import ALCHEMY_SYSTEM_CONFIG
            max_sessions = ALCHEMY_SYSTEM_CONFIG["MAX_CONCURRENT_SESSIONS"]
            
            for i in range(max_sessions):
                session = AlchemySession(
                    character_id=character.id,
                    recipe_id="healing_pill",
                    quality="COMMON",
                    started_at=datetime.now(),
                    finish_at=datetime.now() + timedelta(hours=1),
                    success_rate=0.7,
                    result_item_name="回血丹"
                )
                db.add(session)
            
            await db.commit()
            
            # 尝试开始新的炼丹
            result = await AlchemySystem.start_alchemy(db, character, "healing_pill")
            
            assert result["success"] == False
            assert "上限" in result["message"]
            
            print("✅ 最大并发会话限制测试通过")
    
    async def test_calculate_success_rate(self, setup_test_data):
        """测试成功率计算"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 获取丹方
            result = await db.execute(
                select(AlchemyRecipe).where(AlchemyRecipe.recipe_id == "healing_pill")
            )
            recipe = result.scalar_one_or_none()
            
            if recipe:
                # 计算成功率
                success_rate = AlchemySystem._calculate_success_rate(character, recipe)
                
                # 成功率应该在合理范围内
                assert 0.1 <= success_rate <= 0.95
                
                print(f"✅ 成功率计算测试通过，成功率: {success_rate:.2%}")
    
    async def test_calculate_alchemy_time(self, setup_test_data):
        """测试炼制时间计算"""
        user, character = await setup_test_data
        
        async with get_db_session() as db:
            # 获取丹方
            result = await db.execute(
                select(AlchemyRecipe).where(AlchemyRecipe.recipe_id == "healing_pill")
            )
            recipe = result.scalar_one_or_none()
            
            if recipe:
                # 计算炼制时间
                alchemy_time = AlchemySystem._calculate_alchemy_time(character, recipe)
                
                # 时间应该小于等于基础时间（因为有洞府和等级加成）
                assert alchemy_time <= recipe.base_time_minutes
                assert alchemy_time >= 5  # 最少5分钟
                
                print(f"✅ 炼制时间计算测试通过，时间: {alchemy_time}分钟")


async def run_simple_tests():
    """运行简单的炼丹系统测试"""
    print("🧪 开始炼丹系统测试...")

    try:
        async with get_db_session() as db:
            # 测试1: 检查丹方是否正确初始化
            print("📋 测试丹方初始化...")
            result = await db.execute(select(AlchemyRecipe))
            recipes = result.scalars().all()
            assert len(recipes) >= 7, f"丹方数量不足，期望>=7，实际{len(recipes)}"
            print(f"✅ 丹方初始化测试通过，共{len(recipes)}个丹方")

            # 测试2: 检查炼丹系统基本功能
            print("⚗️ 测试炼丹系统基本功能...")

            # 获取一个测试角色
            result = await db.execute(select(Character).limit(1))
            character = result.scalar_one_or_none()

            if character:
                # 测试获取炼丹信息
                alchemy_info = await AlchemySystem.get_alchemy_info(db, character)
                assert alchemy_info["success"] == True, "获取炼丹信息失败"
                assert "alchemy_level" in alchemy_info, "缺少炼丹等级信息"
                assert "available_recipes" in alchemy_info, "缺少可用丹方信息"
                print("✅ 获取炼丹信息测试通过")

                # 测试成功率计算
                recipe = recipes[0] if recipes else None
                if recipe:
                    success_rate = AlchemySystem._calculate_success_rate(character, recipe)
                    assert 0.1 <= success_rate <= 0.95, f"成功率超出范围: {success_rate}"
                    print(f"✅ 成功率计算测试通过，成功率: {success_rate:.2%}")

                    # 测试时间计算
                    alchemy_time = AlchemySystem._calculate_alchemy_time(character, recipe)
                    assert alchemy_time >= 5, f"炼制时间过短: {alchemy_time}"
                    print(f"✅ 炼制时间计算测试通过，时间: {alchemy_time}分钟")

            else:
                print("⚠️ 没有找到测试角色，跳过角色相关测试")

            # 测试3: 检查材料是否正确添加
            print("📦 测试材料初始化...")
            result = await db.execute(
                select(Item).where(Item.item_type == "MATERIAL")
            )
            materials = result.scalars().all()
            assert len(materials) >= 10, f"材料数量不足，期望>=10，实际{len(materials)}"
            print(f"✅ 材料初始化测试通过，共{len(materials)}种材料")

            print("✅ 所有炼丹系统测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_simple_tests())
