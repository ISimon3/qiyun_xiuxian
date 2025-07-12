# 测试数据模型扩展

import asyncio
import httpx
import json
from typing import Dict, Any


class GameDataModelTester:
    """游戏数据模型测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.character_id = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始测试游戏数据模型扩展...")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. 初始化游戏数据
                await self.test_data_initialization()
                
                # 2. 测试用户注册和登录
                await self.test_user_auth(client)
                
                # 3. 测试角色创建（包含初始装备）
                await self.test_character_creation(client)
                
                # 4. 测试背包系统
                await self.test_inventory_system(client)
                
                # 5. 测试装备系统
                await self.test_equipment_system(client)
                
                # 6. 测试角色属性计算
                await self.test_attribute_calculation(client)
                
                print("\n" + "=" * 60)
                print("✅ 所有测试完成！")
                
            except Exception as e:
                print(f"\n❌ 测试过程中出现错误: {e}")
                import traceback
                traceback.print_exc()
    
    async def test_data_initialization(self):
        """测试数据初始化"""
        print("\n📊 测试数据初始化...")
        
        try:
            from server.database.init_data import DataInitializer
            initializer = DataInitializer()
            await initializer.initialize_all_data()
            print("✅ 数据初始化测试通过")
        except Exception as e:
            print(f"❌ 数据初始化失败: {e}")
    
    async def test_user_auth(self, client: httpx.AsyncClient):
        """测试用户认证"""
        print("\n🔐 测试用户认证...")
        
        # 注册用户（使用随机用户名避免冲突）
        import random
        random_suffix = random.randint(10000, 99999)
        register_data = {
            "username": f"testuser_{random_suffix}",
            "email": f"testuser_{random_suffix}@example.com",
            "password": "testpass123"
        }
        
        response = await client.post(f"{self.base_url}/api/v1/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ 用户注册成功")
        else:
            print(f"⚠️  用户可能已存在: {response.status_code}")
        
        # 登录用户
        login_data = {
            "username": register_data["username"],
            "password": "testpass123"
        }
        
        response = await client.post(f"{self.base_url}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            self.token = result['data']['token']['access_token']
            print("✅ 用户登录成功")
        else:
            raise Exception(f"登录失败: {response.text}")
    
    async def test_character_creation(self, client: httpx.AsyncClient):
        """测试角色获取（自动创建）"""
        print("\n👤 测试角色获取...")

        headers = {"Authorization": f"Bearer {self.token}"}

        # 获取角色信息（如果不存在会自动创建）
        response = await client.get(f"{self.base_url}/api/v1/user/character", headers=headers)

        if response.status_code == 200:
            result = response.json()
            char_data = result['data']
            self.character_id = char_data['id']

            print(f"✅ 获取角色成功: {char_data['name']}")
            print(f"   角色ID: {char_data['id']}")
            print(f"   灵根: {char_data['spiritual_root']}")
            print(f"   境界: {char_data['cultivation_realm']}")

            # 显示角色属性
            attrs = char_data['attributes']
            print(f"   生命值: {attrs['hp']}")
            print(f"   物攻: {attrs['physical_attack']}")
            print(f"   法攻: {attrs['magic_attack']}")
            print(f"   物防: {attrs['physical_defense']}")
            print(f"   法防: {attrs['magic_defense']}")
            print(f"   暴击率: {attrs['critical_rate']}%")
            print(f"   暴击倍数: {attrs['critical_damage']}%")

        else:
            raise Exception(f"获取角色失败: {response.text}")
    
    async def test_inventory_system(self, client: httpx.AsyncClient):
        """测试背包系统"""
        print("\n🎒 测试背包系统...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 获取角色背包
        response = await client.get(
            f"{self.base_url}/api/v1/inventory/inventory",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            items_data = result['data']
            
            print(f"✅ 背包获取成功，共{items_data['total_items']}个物品")
            
            # 显示前几个物品
            for i, item in enumerate(items_data['items'][:5], 1):
                item_info = item['item_info']
                print(f"   {i}. {item_info['name']} x{item['quantity']} ({item_info['quality']})")
            
            if len(items_data['items']) > 5:
                print(f"   ... 还有{len(items_data['items']) - 5}个物品")
                
        else:
            print(f"❌ 背包获取失败: {response.text}")
    
    async def test_equipment_system(self, client: httpx.AsyncClient):
        """测试装备系统"""
        print("\n⚔️ 测试装备系统...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 获取角色装备
        response = await client.get(
            f"{self.base_url}/api/v1/inventory/equipment",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            equipment_data = result['data']
            
            print("✅ 装备信息获取成功")
            
            # 显示装备信息
            equipment = equipment_data.get('equipment')
            if equipment:
                for slot, item in equipment.items():
                    if item:
                        eq_info = item['equipment_info']
                        print(f"   {slot}: {eq_info['name']} ({eq_info['quality']})")
                        
                        # 显示装备属性
                        attrs = eq_info['attributes']
                        attr_strs = []
                        for attr_name, value in attrs.items():
                            if value > 0:
                                if attr_name in ['critical_rate', 'critical_damage']:
                                    attr_strs.append(f"{attr_name}+{value:.1f}%")
                                elif attr_name == 'cultivation_speed':
                                    attr_strs.append(f"{attr_name}+{value:.2f}x")
                                else:
                                    attr_strs.append(f"{attr_name}+{value}")
                        
                        if attr_strs:
                            print(f"      属性: {', '.join(attr_strs)}")
                        print(f"      品质波动: {eq_info['attribute_variation']:.2f}")
            else:
                print("   无装备信息")
                
        else:
            print(f"❌ 装备信息获取失败: {response.text}")
    
    async def test_attribute_calculation(self, client: httpx.AsyncClient):
        """测试属性计算"""
        print("\n🧮 测试属性计算...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 获取角色详细信息
        response = await client.get(
            f"{self.base_url}/api/v1/user/character/detail",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            char_data = result['data']
            
            print("✅ 属性计算测试通过")
            
            # 显示最终属性
            attrs = char_data['attributes']
            training_attrs = char_data['training_attributes']
            
            print("   最终属性:")
            print(f"     生命值: {attrs['hp']}")
            print(f"     物理攻击: {attrs['physical_attack']}")
            print(f"     法术攻击: {attrs['magic_attack']}")
            print(f"     物理防御: {attrs['physical_defense']}")
            print(f"     法术防御: {attrs['magic_defense']}")
            print(f"     暴击率: {attrs['critical_rate']:.1f}%")
            print(f"     暴击倍数: {attrs['critical_damage']:.1f}%")
            print(f"     修炼速度: {attrs['cultivation_speed']:.2f}x")
            print(f"     气运加成: {attrs['luck_bonus']}")
            
            print("   修习属性:")
            for attr_name, value in training_attrs.items():
                if value > 0:
                    print(f"     {attr_name}: +{value}")
                    
        else:
            print(f"❌ 属性计算测试失败: {response.text}")


async def main():
    """主函数"""
    tester = GameDataModelTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
