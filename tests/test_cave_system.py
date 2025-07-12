# 洞府系统测试脚本

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server.database.database import AsyncSessionLocal
from server.database.crud import UserCRUD, CharacterCRUD
from server.core.systems.cave_system import CaveSystem
from shared.constants import CAVE_SYSTEM_CONFIG
from shared.schemas import UserRegister


async def test_cave_system():
    """测试洞府系统功能"""
    print("🏠 开始测试洞府系统...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 创建测试用户和角色
            print("\n1. 创建测试角色...")
            user_data = UserRegister(
                username="cave_test_user",
                email="cave_test@example.com",
                password="password123"
            )
            test_user = await UserCRUD.create_user(db, user_data)
            character = await CharacterCRUD.get_or_create_character(
                db, test_user.id, test_user.username
            )
            
            # 给角色一些灵石用于测试
            character.spirit_stone = 100000
            await db.commit()
            
            print(f"✅ 测试角色创建成功: {character.name}")
            print(f"   初始洞府等级: {character.cave_level}")
            print(f"   初始聚灵阵等级: {character.spirit_gathering_array_level}")
            print(f"   灵石数量: {character.spirit_stone}")
            
            # 测试获取洞府信息
            print("\n2. 测试获取洞府信息...")
            cave_info = await CaveSystem.get_cave_info(db, character)
            if cave_info["success"]:
                print("✅ 获取洞府信息成功")
                print(f"   洞府等级: {cave_info['cave_level']}")
                print(f"   聚灵阵等级: {cave_info['spirit_gathering_array_level']}")
                print(f"   修炼速度加成: {cave_info['cultivation_speed_bonus']:.1f}x")
                print(f"   可用功能: {', '.join(cave_info['available_features'])}")
            else:
                print(f"❌ 获取洞府信息失败: {cave_info['message']}")
                return
            
            # 测试升级洞府
            print("\n3. 测试升级洞府...")
            upgrade_result = await CaveSystem.upgrade_cave(db, character, "cave")
            if upgrade_result["success"]:
                print("✅ 洞府升级成功")
                print(f"   {upgrade_result['message']}")
                print(f"   消耗灵石: {upgrade_result['cost_spirit_stone']}")
                print(f"   剩余灵石: {character.spirit_stone}")
            else:
                print(f"❌ 洞府升级失败: {upgrade_result['message']}")
            
            # 测试升级聚灵阵
            print("\n4. 测试升级聚灵阵...")
            spirit_upgrade_result = await CaveSystem.upgrade_cave(db, character, "spirit_array")
            if spirit_upgrade_result["success"]:
                print("✅ 聚灵阵升级成功")
                print(f"   {spirit_upgrade_result['message']}")
                print(f"   消耗灵石: {spirit_upgrade_result['cost_spirit_stone']}")
                print(f"   剩余灵石: {character.spirit_stone}")
            else:
                print(f"❌ 聚灵阵升级失败: {spirit_upgrade_result['message']}")
            
            # 测试修炼速度加成
            print("\n5. 测试修炼速度加成...")
            speed_bonus = CaveSystem.get_cultivation_speed_bonus(character.spirit_gathering_array_level)
            print(f"✅ 当前修炼速度加成: {speed_bonus:.1f}x")
            
            # 再次获取洞府信息查看变化
            print("\n6. 查看升级后的洞府信息...")
            updated_cave_info = await CaveSystem.get_cave_info(db, character)
            if updated_cave_info["success"]:
                print("✅ 获取更新后洞府信息成功")
                print(f"   洞府等级: {updated_cave_info['cave_level']}")
                print(f"   聚灵阵等级: {updated_cave_info['spirit_gathering_array_level']}")
                print(f"   修炼速度加成: {updated_cave_info['cultivation_speed_bonus']:.1f}x")
                print(f"   可用功能: {', '.join(updated_cave_info['available_features'])}")
            
            # 测试多次升级
            print("\n7. 测试连续升级...")
            for i in range(3):
                print(f"\n   第{i+1}次升级尝试:")
                
                # 尝试升级洞府
                cave_result = await CaveSystem.upgrade_cave(db, character, "cave")
                if cave_result["success"]:
                    print(f"   ✅ 洞府升级到{cave_result['new_level']}级")
                else:
                    print(f"   ❌ 洞府升级失败: {cave_result['message']}")
                
                # 尝试升级聚灵阵
                spirit_result = await CaveSystem.upgrade_cave(db, character, "spirit_array")
                if spirit_result["success"]:
                    print(f"   ✅ 聚灵阵升级到{spirit_result['new_level']}级")
                else:
                    print(f"   ❌ 聚灵阵升级失败: {spirit_result['message']}")
                
                print(f"   剩余灵石: {character.spirit_stone}")
            
            # 测试边界条件
            print("\n8. 测试边界条件...")
            
            # 消耗所有灵石
            character.spirit_stone = 0
            await db.commit()
            
            no_money_result = await CaveSystem.upgrade_cave(db, character, "cave")
            if not no_money_result["success"]:
                print("✅ 灵石不足时正确拒绝升级")
                print(f"   错误信息: {no_money_result['message']}")
            else:
                print("❌ 灵石不足时应该拒绝升级")
            
            # 测试无效升级类型
            invalid_type_result = await CaveSystem.upgrade_cave(db, character, "invalid_type")
            if not invalid_type_result["success"]:
                print("✅ 无效升级类型时正确拒绝")
                print(f"   错误信息: {invalid_type_result['message']}")
            else:
                print("❌ 无效升级类型时应该拒绝")
            
            print("\n🎉 洞府系统测试完成！")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理测试数据
            try:
                if 'test_user' in locals():
                    await UserCRUD.delete_user(db, test_user.id)
                    print("\n🧹 测试数据已清理")
            except:
                pass


async def test_cave_constants():
    """测试洞府系统常量配置"""
    print("\n📋 测试洞府系统常量配置...")
    
    config = CAVE_SYSTEM_CONFIG
    
    print(f"✅ 最大洞府等级: {config['MAX_CAVE_LEVEL']}")
    print(f"✅ 最大聚灵阵等级: {config['MAX_SPIRIT_ARRAY_LEVEL']}")
    
    print("\n洞府升级费用:")
    for level, cost in config['CAVE_UPGRADE_COSTS'].items():
        print(f"   {level}级: {cost['spirit_stone']} 灵石")
    
    print("\n聚灵阵升级费用:")
    for level, cost in config['SPIRIT_ARRAY_UPGRADE_COSTS'].items():
        print(f"   {level}级: {cost['spirit_stone']} 灵石")
    
    print("\n聚灵阵速度加成:")
    for level, bonus in config['SPIRIT_ARRAY_SPEED_BONUS'].items():
        print(f"   {level}级: {bonus:.1f}x ({(bonus-1)*100:.0f}%)")
    
    print("\n洞府等级功能:")
    for level, features in config['CAVE_LEVEL_FEATURES'].items():
        print(f"   {level}级: {', '.join(features)}")


if __name__ == "__main__":
    print("🧪 洞府系统测试开始...")
    
    # 测试常量配置
    asyncio.run(test_cave_constants())
    
    # 测试系统功能
    asyncio.run(test_cave_system())
    
    print("\n✅ 所有测试完成！")
