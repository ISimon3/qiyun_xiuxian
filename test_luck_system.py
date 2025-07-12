#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
气运系统功能测试脚本
测试步骤6完成的气运系统实现
"""

import asyncio
import sys
import os
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.database.database import init_database, get_db_session
from server.database.crud import UserCRUD, CharacterCRUD, ItemCRUD, InventoryCRUD
from server.database.init_data import DataInitializer
from server.core.systems.luck_system import LuckSystem
from shared.schemas import UserRegister


class LuckSystemTester:
    """气运系统测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user = {
            "username": "luck_test_user",
            "email": "luck_test@example.com",
            "password": "test123456"
        }
        self.token = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始测试气运系统...")
        print("=" * 60)
        
        try:
            # 1. 初始化数据
            await self.test_data_initialization()
            
            # 2. 测试用户注册和登录
            await self.test_user_auth()
            
            # 3. 测试每日签到
            await self.test_daily_sign_in()
            
            # 4. 测试气运道具使用
            await self.test_luck_items()
            
            # 5. 测试气运系统信息获取
            await self.test_luck_info()
            
            # 6. 测试气运影响计算
            await self.test_luck_effects()
            
            print("\n" + "=" * 60)
            print("✅ 所有测试完成！")
            
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_data_initialization(self):
        """测试数据初始化"""
        print("\n📊 测试数据初始化...")
        
        # 初始化数据库
        await init_database()
        print("✅ 数据库初始化成功")
        
        # 初始化游戏数据
        initializer = DataInitializer()
        await initializer.initialize_all_data()
        print("✅ 游戏数据初始化成功")
    
    async def test_user_auth(self):
        """测试用户认证"""
        print("\n👤 测试用户认证...")
        
        async with httpx.AsyncClient() as client:
            # 注册用户
            register_data = UserRegister(**self.test_user)
            response = await client.post(
                f"{self.base_url}/api/v1/auth/register",
                json=register_data.model_dump()
            )
            
            if response.status_code == 200:
                print("✅ 用户注册成功")
            else:
                print("⚠️  用户可能已存在，继续测试...")
            
            # 登录获取token
            login_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"登录响应: {result}")  # 调试信息
                # 根据实际响应结构获取token
                if "data" in result and "token" in result["data"]:
                    self.token = result["data"]["token"]["access_token"]
                elif "data" in result and "access_token" in result["data"]:
                    self.token = result["data"]["access_token"]
                else:
                    raise Exception(f"无法从响应中获取token: {result}")
                print("✅ 用户登录成功")
            else:
                raise Exception(f"登录失败: {response.text}")
    
    async def test_daily_sign_in(self):
        """测试每日签到"""
        print("\n📅 测试每日签到...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            # 第一次签到
            response = await client.post(
                f"{self.base_url}/api/v1/game/daily-sign",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    data = result["data"]
                    print(f"✅ 每日签到成功")
                    print(f"   气运变化: {data.get('old_luck', 0)} → {data['new_luck']}")
                    print(f"   气运等级: {data['luck_level']}")
                else:
                    print(f"⚠️  {result['message']}")
            else:
                print(f"❌ 签到请求失败: {response.text}")
            
            # 再次签到（应该失败）
            response = await client.post(
                f"{self.base_url}/api/v1/game/daily-sign",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result["success"]:
                    print("✅ 重复签到正确被拒绝")
                else:
                    print("⚠️  重复签到应该被拒绝")
    
    async def test_luck_items(self):
        """测试气运道具使用"""
        print("\n💊 测试气运道具使用...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 首先给用户添加一些转运丹
        async with get_db_session() as db:
            user = await UserCRUD.get_user_by_username(db, self.test_user["username"])
            character = await CharacterCRUD.get_or_create_character(db, user.id, user.username)
            
            # 获取转运丹物品
            luck_items = await ItemCRUD.search_items(db, "转运丹")
            luck_item = None
            for item in luck_items:
                if item.name == "转运丹":
                    luck_item = item
                    break
            
            if luck_item:
                # 添加到背包
                await InventoryCRUD.add_item_to_inventory(db, character.id, luck_item.id, 5)
                print(f"✅ 已添加 {luck_item.name} x5 到背包")
                
                # 测试使用道具
                async with httpx.AsyncClient() as client:
                    use_data = {
                        "item_id": luck_item.id,
                        "quantity": 2
                    }
                    response = await client.post(
                        f"{self.base_url}/api/v1/game/use-luck-item",
                        headers=headers,
                        json=use_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result["success"]:
                            data = result["data"]
                            print(f"✅ 使用{luck_item.name}成功")
                            print(f"   气运变化: {data.get('old_luck', 0)} → {data['new_luck']}")
                            print(f"   气运加成: +{data['luck_bonus']}")
                        else:
                            print(f"❌ 使用道具失败: {result['message']}")
                    else:
                        print(f"❌ 使用道具请求失败: {response.text}")
            else:
                print("⚠️  未找到转运丹物品")
    
    async def test_luck_info(self):
        """测试气运信息获取"""
        print("\n📊 测试气运信息获取...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/game/luck-info",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    data = result["data"]
                    print("✅ 获取气运信息成功")
                    print(f"   当前气运: {data['current_luck']}")
                    print(f"   气运等级: {data['luck_level']}")
                    print(f"   今日可签到: {data['can_sign_today']}")
                    print(f"   修炼倍率: {data['cultivation_effect']['multiplier']:.2f}x")
                    print(f"   突破加成: {data['breakthrough_bonus']:.1%}")
                else:
                    print(f"❌ 获取气运信息失败: {result['message']}")
            else:
                print(f"❌ 获取气运信息请求失败: {response.text}")
    
    async def test_luck_effects(self):
        """测试气运影响计算"""
        print("\n🎲 测试气运影响计算...")
        
        # 测试不同气运值的影响
        test_luck_values = [10, 30, 50, 70, 90]
        
        for luck_value in test_luck_values:
            print(f"\n   测试气运值: {luck_value}")
            
            # 修炼影响
            cultivation_effect = LuckSystem.calculate_luck_effect_on_cultivation(luck_value)
            print(f"     修炼倍率: {cultivation_effect['multiplier']:.2f}x")
            print(f"     特殊事件概率: {cultivation_effect['special_event_chance']:.1%}")
            
            # 突破影响
            breakthrough_rate = LuckSystem.calculate_luck_effect_on_breakthrough(luck_value, 0.5)
            print(f"     突破成功率: {breakthrough_rate:.1%}")
            
            # 掉落影响
            drop_effect = LuckSystem.calculate_luck_effect_on_drops(luck_value)
            print(f"     掉落倍率: {drop_effect['quantity_multiplier']:.1f}x")
        
        print("✅ 气运影响计算测试完成")


async def main():
    """主函数"""
    tester = LuckSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
