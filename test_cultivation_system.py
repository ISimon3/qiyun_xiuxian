#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修炼系统功能测试脚本
测试步骤7完成的修炼系统实现
"""

import asyncio
import sys
import os
import httpx
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.database.database import init_database, get_db_session
from server.database.crud import UserCRUD, CharacterCRUD
from server.database.init_data import DataInitializer
from server.core.systems.cultivation_system import CultivationSystem
from shared.schemas import UserRegister


class CultivationSystemTester:
    """修炼系统测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user = {
            "username": "cult_test_user",
            "email": "cultivation_test@example.com",
            "password": "test123456"
        }
        self.token = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始测试修炼系统...")
        print("=" * 60)
        
        try:
            # 1. 初始化数据
            await self.test_data_initialization()
            
            # 2. 测试用户注册和登录
            await self.test_user_auth()
            
            # 3. 测试修炼状态获取
            await self.test_cultivation_status()
            
            # 4. 测试开始修炼
            await self.test_start_cultivation()
            
            # 5. 测试修炼周期
            await self.test_cultivation_cycles()
            
            # 6. 测试手动突破
            await self.test_manual_breakthrough()
            
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
                self.token = result["data"]["token"]["access_token"]
                print("✅ 用户登录成功")
            else:
                raise Exception(f"登录失败: {response.text}")
    
    async def test_cultivation_status(self):
        """测试修炼状态获取"""
        print("\n📊 测试修炼状态获取...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/game/cultivation-status",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    data = result["data"]
                    print("✅ 获取修炼状态成功")
                    print(f"   当前境界: {data['current_realm_name']} ({data['current_realm']})")
                    print(f"   当前修为: {data['current_exp']}")
                    print(f"   修炼方向: {data['focus_name']}")
                    print(f"   是否在修炼: {data['is_cultivating']}")
                    print(f"   可否突破: {data['can_breakthrough']}")
                    if data['can_breakthrough']:
                        print(f"   突破成功率: {data['breakthrough_rate']:.1%}")
                else:
                    print(f"❌ 获取修炼状态失败: {result['message']}")
            else:
                print(f"❌ 获取修炼状态请求失败: {response.text}")
    
    async def test_start_cultivation(self):
        """测试开始修炼"""
        print("\n🧘 测试开始修炼...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试不同的修炼方向
        cultivation_focuses = ["HP", "PHYSICAL_ATTACK", "MAGIC_ATTACK"]
        
        for focus in cultivation_focuses:
            async with httpx.AsyncClient() as client:
                data = {"cultivation_focus": focus}
                response = await client.post(
                    f"{self.base_url}/api/v1/game/start-cultivation",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        print(f"✅ 开始修炼成功 - 方向: {result['data']['focus_name']}")
                    else:
                        print(f"❌ 开始修炼失败: {result['message']}")
                else:
                    print(f"❌ 开始修炼请求失败: {response.text}")
                
                # 短暂等待
                await asyncio.sleep(0.5)
    
    async def test_cultivation_cycles(self):
        """测试修炼周期"""
        print("\n⏰ 测试修炼周期...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 执行几次强制修炼周期来测试
        for i in range(3):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/game/force-cultivation-cycle",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        data = result["data"]
                        print(f"✅ 修炼周期 {i+1} 完成")
                        print(f"   修为获得: +{data.get('exp_gained', 0)}")
                        print(f"   属性获得: {data.get('focus_name', '')} +{data.get('attribute_gained', 0)}")
                        print(f"   气运倍率: {data.get('luck_multiplier', 1.0):.2f}x")
                        
                        if data.get('luck_effect'):
                            print(f"   气运影响: {data['luck_effect']}")
                        
                        if data.get('special_event'):
                            print(f"   特殊事件: {data['special_event']}")
                    else:
                        print(f"❌ 修炼周期 {i+1} 失败: {result['message']}")
                else:
                    print(f"❌ 修炼周期 {i+1} 请求失败: {response.text}")
                
                # 等待一秒
                await asyncio.sleep(1)
    
    async def test_manual_breakthrough(self):
        """测试手动突破"""
        print("\n⚡ 测试手动突破...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 先给角色增加一些修为，确保可以突破
        async with get_db_session() as db:
            user = await UserCRUD.get_user_by_username(db, self.test_user["username"])
            character = await CharacterCRUD.get_or_create_character(db, user.id, user.username)
            
            # 增加修为到足够突破的程度
            character.cultivation_exp += 1000
            await db.commit()
            print("✅ 已增加修为，准备测试突破")
        
        # 尝试手动突破
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/game/manual-breakthrough",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result["data"]
                
                if result["success"]:
                    print("✅ 手动突破成功")
                    print(f"   境界变化: {data.get('old_realm', 0)} → {data.get('new_realm', 0)}")
                    print(f"   成功率: {data.get('success_rate', 0):.1%}")
                    print(f"   消耗修为: {data.get('exp_consumed', 0)}")
                else:
                    print("⚠️  手动突破失败")
                    print(f"   失败原因: {result['message']}")
                    print(f"   成功率: {data.get('success_rate', 0):.1%}")
                    if data.get('exp_loss'):
                        print(f"   修为损失: {data['exp_loss']}")
            else:
                print(f"❌ 手动突破请求失败: {response.text}")


async def main():
    """主函数"""
    tester = CultivationSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
