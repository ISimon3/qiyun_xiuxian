# 灵田系统测试脚本

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server.database.database import AsyncSessionLocal
from server.database.crud import UserCRUD, CharacterCRUD
from server.core.systems.farm_system import FarmSystem
from shared.constants import FARM_SYSTEM_CONFIG
from shared.schemas import UserRegister


async def test_farm_system():
    """测试灵田系统功能"""
    print("🌱 开始测试灵田系统...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 创建测试用户和角色
            print("\n1. 创建测试角色...")
            user_data = UserRegister(
                username="farm_test_user",
                email="farm_test@example.com", 
                password="password123"
            )
            test_user = await UserCRUD.create_user(db, user_data)
            character = await CharacterCRUD.get_or_create_character(
                db, test_user.id, test_user.username
            )
            
            # 给角色一些金币用于测试
            character.gold = 50000
            character.cave_level = 5  # 设置洞府等级以便解锁更多地块
            await db.commit()
            
            print(f"✅ 测试角色创建成功: {character.name}")
            print(f"   洞府等级: {character.cave_level}")
            print(f"   金币数量: {character.gold}")
            
            # 测试获取灵田信息
            print("\n2. 测试获取灵田信息...")
            farm_info = await FarmSystem.get_farm_info(db, character)
            if farm_info["success"]:
                print("✅ 获取灵田信息成功")
                print(f"   总地块数: {farm_info['total_plots']}")
                print(f"   已解锁地块: {farm_info['unlocked_plots']}")
                print(f"   可用种子数: {len(farm_info['available_seeds'])}")
                
                # 显示可用种子
                for seed in farm_info['available_seeds']:
                    print(f"     - {seed['name']}: {seed['quantity']}个")
            else:
                print(f"❌ 获取灵田信息失败: {farm_info['message']}")
                return
            
            # 测试解锁地块
            print("\n3. 测试解锁地块...")
            unlock_result = await FarmSystem.unlock_plot(db, character, 4)  # 解锁第5个地块
            if unlock_result["success"]:
                print("✅ 地块解锁成功")
                print(f"   {unlock_result['message']}")
                print(f"   消耗金币: {unlock_result['cost']}")
                print(f"   剩余金币: {character.gold}")
            else:
                print(f"❌ 地块解锁失败: {unlock_result['message']}")
            
            # 测试种植种子
            print("\n4. 测试种植种子...")
            # 获取第一个可用种子
            farm_info = await FarmSystem.get_farm_info(db, character)
            if farm_info["success"] and farm_info['available_seeds']:
                seed = farm_info['available_seeds'][0]
                plant_result = await FarmSystem.plant_seed(db, character, 0, seed['item_id'])
                if plant_result["success"]:
                    print("✅ 种植成功")
                    print(f"   {plant_result['message']}")
                    plot_info = plant_result['plot_info']
                    print(f"   地块状态: {plot_info['growth_stage_name']}")
                    print(f"   预计收获时间: {plot_info['harvest_at']}")
                else:
                    print(f"❌ 种植失败: {plant_result['message']}")
            else:
                print("❌ 没有可用种子进行种植测试")
            
            # 测试强制成熟（修改收获时间）
            print("\n5. 测试强制成熟作物...")
            from datetime import datetime
            from sqlalchemy import text, update
            from server.database.models import FarmPlot
            
            # 将第一个地块的作物设为成熟
            await db.execute(
                update(FarmPlot)
                .where(FarmPlot.character_id == character.id)
                .where(FarmPlot.plot_index == 0)
                .values(
                    harvest_at=datetime.now(),
                    is_ready=True,
                    growth_stage=4
                )
            )
            await db.commit()
            print("✅ 作物已强制成熟")
            
            # 测试收获
            print("\n6. 测试收获作物...")
            harvest_result = await FarmSystem.harvest_plot(db, character, 0)
            if harvest_result["success"]:
                print("✅ 收获成功")
                print(f"   {harvest_result['message']}")
                if harvest_result.get('is_mutation', False):
                    print("   🎉 发生了变异！")
                
                harvested_items = harvest_result.get('harvested_items', [])
                for item in harvested_items:
                    print(f"   收获: {item['quantity']}个 {item['name']}")
            else:
                print(f"❌ 收获失败: {harvest_result['message']}")
            
            # 测试多个地块种植
            print("\n7. 测试多地块种植...")
            farm_info = await FarmSystem.get_farm_info(db, character)
            if farm_info["success"] and farm_info['available_seeds']:
                planted_count = 0
                for i in range(1, min(4, len(farm_info['plots']))):  # 在地块1-3种植
                    plot = farm_info['plots'][i]
                    if plot['is_unlocked'] and not plot['seed_item_id']:
                        seed = farm_info['available_seeds'][0]
                        plant_result = await FarmSystem.plant_seed(db, character, i, seed['item_id'])
                        if plant_result["success"]:
                            planted_count += 1
                            print(f"   ✅ 地块{i+1}种植成功")
                        else:
                            print(f"   ❌ 地块{i+1}种植失败: {plant_result['message']}")
                
                print(f"✅ 成功种植了{planted_count}个地块")
            
            # 测试边界条件
            print("\n8. 测试边界条件...")
            
            # 测试在已种植的地块再次种植
            if farm_info["success"] and farm_info['available_seeds']:
                seed = farm_info['available_seeds'][0]
                duplicate_plant = await FarmSystem.plant_seed(db, character, 1, seed['item_id'])
                if not duplicate_plant["success"]:
                    print("✅ 正确拒绝在已种植地块重复种植")
                    print(f"   错误信息: {duplicate_plant['message']}")
                else:
                    print("❌ 应该拒绝在已种植地块重复种植")
            
            # 测试在未解锁地块种植
            if farm_info["success"] and farm_info['available_seeds']:
                seed = farm_info['available_seeds'][0]
                locked_plant = await FarmSystem.plant_seed(db, character, 11, seed['item_id'])  # 最后一个地块通常未解锁
                if not locked_plant["success"]:
                    print("✅ 正确拒绝在未解锁地块种植")
                    print(f"   错误信息: {locked_plant['message']}")
                else:
                    print("❌ 应该拒绝在未解锁地块种植")
            
            # 测试收获未成熟作物
            early_harvest = await FarmSystem.harvest_plot(db, character, 1)
            if not early_harvest["success"]:
                print("✅ 正确拒绝收获未成熟作物")
                print(f"   错误信息: {early_harvest['message']}")
            else:
                print("❌ 应该拒绝收获未成熟作物")
            
            # 测试最终状态
            print("\n9. 查看最终灵田状态...")
            final_farm_info = await FarmSystem.get_farm_info(db, character)
            if final_farm_info["success"]:
                print("✅ 获取最终灵田状态成功")
                planted_plots = [p for p in final_farm_info['plots'] if p.get('seed_item_id')]
                ready_plots = [p for p in final_farm_info['plots'] if p.get('is_ready', False)]
                
                print(f"   已解锁地块: {final_farm_info['unlocked_plots']}")
                print(f"   已种植地块: {len(planted_plots)}")
                print(f"   可收获地块: {len(ready_plots)}")
                print(f"   剩余金币: {character.gold}")
            
            print("\n🎉 灵田系统测试完成！")
            
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


async def test_farm_constants():
    """测试灵田系统常量配置"""
    print("\n📋 测试灵田系统常量配置...")
    
    config = FARM_SYSTEM_CONFIG
    
    print(f"✅ 总地块数: {config['TOTAL_PLOTS']}")
    print(f"✅ 初始解锁地块: {config['INITIAL_UNLOCKED_PLOTS']}")
    
    print("\n地块类型配置:")
    for plot_type, settings in config['PLOT_TYPES'].items():
        print(f"   {plot_type}: {settings['name']}")
        print(f"     成长速度: {settings['growth_speed_multiplier']}x")
        print(f"     产量倍率: {settings['yield_multiplier']}x")
        print(f"     变异率: {settings['mutation_base_chance']*100:.1f}%")
    
    print("\n种子配置:")
    for seed_name, settings in config['SEED_CONFIG'].items():
        print(f"   {seed_name}:")
        print(f"     成长时间: {settings['growth_time_hours']}小时")
        print(f"     产量: {settings['yield_min']}-{settings['yield_max']}")
        print(f"     产出: {settings['result_item']}")
    
    print("\n地块解锁需求:")
    for plot_index, req in config['PLOT_UNLOCK_REQUIREMENTS'].items():
        print(f"   地块{plot_index+1}: 需要{req['cave_level']}级洞府, {req['cost']}金币")


if __name__ == "__main__":
    print("🧪 灵田系统测试开始...")
    
    # 测试常量配置
    asyncio.run(test_farm_constants())
    
    # 测试系统功能
    asyncio.run(test_farm_system())
    
    print("\n✅ 所有测试完成！")
