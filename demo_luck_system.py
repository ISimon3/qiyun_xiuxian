#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
气运系统功能演示脚本
展示气运系统的主要功能
"""

import asyncio
import sys
import os
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.network.api_client import GameAPIClient


async def demo_luck_system():
    """演示气运系统功能"""
    print("🎮 气运修仙游戏 - 气运系统演示")
    print("=" * 50)
    
    # 创建API客户端
    client = GameAPIClient()
    
    # 测试用户
    demo_user = {
        "username": "demo_user",
        "email": "demo@example.com", 
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
            print(f"   当前气运: {character['luck_value']}")
        
        # 3. 获取气运系统详细信息
        print("\n🍀 获取气运系统信息...")
        luck_info_result = client.game.get_luck_info()
        if luck_info_result["success"]:
            luck_info = luck_info_result["data"]
            print(f"✅ 气运详情:")
            print(f"   当前气运: {luck_info['current_luck']}")
            print(f"   气运等级: {luck_info['luck_level']}")
            print(f"   今日可签到: {'是' if luck_info['can_sign_today'] else '否'}")
            print(f"   修炼倍率: {luck_info['cultivation_effect']['multiplier']:.2f}x")
            print(f"   突破加成: {luck_info['breakthrough_bonus']:.1%}")
            print(f"   掉落倍率: {luck_info['drop_effects']['quantity_multiplier']:.1f}x")
        
        # 4. 每日签到
        print("\n📅 每日签到...")
        sign_result = client.game.daily_sign_in()
        if sign_result["success"]:
            data = sign_result["data"]
            print(f"✅ {sign_result['message']}")
            if data.get("old_luck") is not None:
                print(f"   气运变化: {data['old_luck']} → {data['new_luck']}")
                print(f"   气运等级: {data['luck_level']}")
        else:
            print(f"⚠️  {sign_result['message']}")
        
        # 5. 演示不同气运值的影响
        print("\n🎲 气运影响演示...")
        from server.core.systems.luck_system import LuckSystem
        
        test_values = [10, 30, 50, 70, 90]
        print("气运值 | 等级 | 修炼倍率 | 突破成功率 | 掉落倍率")
        print("-" * 50)
        
        for luck_val in test_values:
            cultivation_effect = LuckSystem.calculate_luck_effect_on_cultivation(luck_val)
            breakthrough_rate = LuckSystem.calculate_luck_effect_on_breakthrough(luck_val, 0.5)
            drop_effect = LuckSystem.calculate_luck_effect_on_drops(luck_val)
            
            print(f"{luck_val:6d} | {cultivation_effect['luck_level']:4s} | "
                  f"{cultivation_effect['multiplier']:8.2f}x | "
                  f"{breakthrough_rate:10.1%} | "
                  f"{drop_effect['quantity_multiplier']:8.1f}x")
        
        print("\n🌟 气运系统功能演示完成！")
        print("\n💡 气运系统特点:")
        print("   • 每日签到获得随机气运值")
        print("   • 使用转运丹可以提升气运")
        print("   • 气运影响修炼效率、突破成功率和掉落品质")
        print("   • 高气运可能触发特殊事件（顿悟、灵气共鸣等）")
        print("   • 低气运可能导致负面事件（走火入魔、修炼受阻等）")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    await demo_luck_system()


if __name__ == "__main__":
    asyncio.run(main())
