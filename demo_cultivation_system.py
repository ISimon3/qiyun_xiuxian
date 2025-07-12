#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修炼系统功能演示脚本
展示修炼系统的主要功能
"""

import asyncio
import sys
import os
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.network.api_client import GameAPIClient


async def demo_cultivation_system():
    """演示修炼系统功能"""
    print("🎮 气运修仙游戏 - 修炼系统演示")
    print("=" * 50)
    
    # 创建API客户端
    client = GameAPIClient()
    
    # 测试用户
    demo_user = {
        "username": "demo_cult_user",
        "email": "demo_cult@example.com", 
        "password": "demo123456"
    }
    
    try:
        # 1. 用户注册/登录
        print("\n👤 用户认证...")
        try:
            result = client.auth.register(demo_user["username"], demo_user["email"], demo_user["password"])
            print("✅ 用户注册成功")
        except:
            print("⚠️  用户可能已存在，尝试登录...")
        
        result = client.auth.login(demo_user["username"], demo_user["password"])
        if result["success"]:
            print("✅ 登录成功")
        else:
            print("❌ 登录失败")
            return
        
        # 2. 获取角色信息
        print("\n📊 获取角色信息...")
        character_result = client.user.get_character()
        if character_result["success"]:
            character = character_result["data"]
            print(f"✅ 角色: {character['name']}")
            print(f"   境界: {character['cultivation_realm']}")
            print(f"   修为: {character['cultivation_exp']}")
            print(f"   气运: {character['luck_value']}")
        
        # 3. 获取修炼状态
        print("\n🧘 获取修炼状态...")
        cultivation_status = client.game.get_cultivation_status()
        if cultivation_status["success"]:
            status = cultivation_status["data"]
            print(f"✅ 修炼状态:")
            print(f"   当前境界: {status['current_realm_name']}")
            print(f"   当前修为: {status['current_exp']}")
            print(f"   下一境界: {status['next_realm_name']}")
            print(f"   所需修为: {status['required_exp']}")
            print(f"   修炼进度: {status['exp_progress']:.1%}")
            print(f"   修炼方向: {status['focus_name']}")
            print(f"   是否在修炼: {status['is_cultivating']}")
            print(f"   可否突破: {status['can_breakthrough']}")
            if status['can_breakthrough']:
                print(f"   突破成功率: {status['breakthrough_rate']:.1%}")
        
        # 4. 开始修炼
        print("\n🌟 开始修炼...")
        cultivation_focuses = [
            ("HP", "体修"),
            ("PHYSICAL_ATTACK", "力修"),
            ("MAGIC_ATTACK", "法修"),
            ("PHYSICAL_DEFENSE", "防修"),
            ("MAGIC_DEFENSE", "抗修")
        ]
        
        for focus, name in cultivation_focuses:
            result = client.game.start_cultivation(focus)
            if result["success"]:
                print(f"✅ 开始{name}修炼")
            else:
                print(f"❌ 开始{name}修炼失败: {result['message']}")
            await asyncio.sleep(0.5)
        
        # 5. 演示修炼周期
        print("\n⏰ 演示修炼周期...")
        print("正在执行修炼周期，观察修为和属性变化...")
        
        for i in range(5):
            result = client.game.force_cultivation_cycle()
            if result["success"]:
                data = result["data"]
                print(f"\n🔄 修炼周期 {i+1}:")
                print(f"   修为获得: +{data.get('exp_gained', 0)}")
                print(f"   属性获得: {data.get('focus_name', '')} +{data.get('attribute_gained', 0)}")
                print(f"   气运倍率: {data.get('luck_multiplier', 1.0):.2f}x")
                
                if data.get('luck_effect'):
                    print(f"   气运影响: {data['luck_effect']}")
                
                if data.get('special_event'):
                    print(f"   🎉 特殊事件: {data['special_event']}")
                    if data.get('special_event_result'):
                        print(f"      事件结果: {data['special_event_result']['message']}")
                
                print(f"   当前修为: {data.get('current_exp', 0)}")
            else:
                print(f"❌ 修炼周期 {i+1} 失败: {result['message']}")
            
            await asyncio.sleep(1)
        
        # 6. 手动突破演示
        print("\n⚡ 手动突破演示...")
        
        # 先获取当前状态
        cultivation_status = client.game.get_cultivation_status()
        if cultivation_status["success"]:
            status = cultivation_status["data"]
            if status['can_breakthrough']:
                print(f"✅ 满足突破条件，尝试突破到 {status['next_realm_name']}")
                print(f"   突破成功率: {status['breakthrough_rate']:.1%}")
                
                breakthrough_result = client.game.manual_breakthrough()
                if breakthrough_result["success"]:
                    data = breakthrough_result["data"]
                    print("🎉 突破成功！")
                    print(f"   境界变化: {data.get('old_realm', 0)} → {data.get('new_realm', 0)}")
                    print(f"   消耗修为: {data.get('exp_consumed', 0)}")
                else:
                    print("💥 突破失败")
                    print(f"   失败原因: {breakthrough_result['message']}")
                    data = breakthrough_result["data"]
                    if data.get('exp_loss'):
                        print(f"   修为损失: {data['exp_loss']}")
            else:
                print("⚠️  当前不满足突破条件")
                print(f"   当前修为: {status['current_exp']}")
                print(f"   所需修为: {status['required_exp']}")
        
        # 7. 最终状态
        print("\n📈 最终修炼状态...")
        cultivation_status = client.game.get_cultivation_status()
        if cultivation_status["success"]:
            status = cultivation_status["data"]
            print(f"✅ 修炼结果:")
            print(f"   最终境界: {status['current_realm_name']}")
            print(f"   最终修为: {status['current_exp']}")
            print(f"   修炼方向: {status['focus_name']}")
            print(f"   修炼进度: {status['exp_progress']:.1%}")
        
        print("\n🌟 修炼系统演示完成！")
        print("\n💡 修炼系统特点:")
        print("   • 每5分钟自动进行一次修炼周期")
        print("   • 可选择不同的修炼方向（体修、力修、法修、防修、抗修）")
        print("   • 气运影响修炼效率和特殊事件触发")
        print("   • 只支持手动突破，需要玩家主动操作")
        print("   • 特殊事件包括顿悟、灵气共鸣、走火入魔等")
        print("   • 游戏主循环自动处理所有在线角色的修炼")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    await demo_cultivation_system()


if __name__ == "__main__":
    asyncio.run(main())
