#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证系统测试脚本
测试第三步骤完成的用户认证系统
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from server.database.database import init_database


async def test_auth_api():
    """测试认证API接口"""
    print("🚀 开始测试认证API...")
    
    # 初始化数据库
    await init_database()
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. 测试用户注册
            print("\n📝 测试用户注册...")
            timestamp = datetime.now().strftime('%H%M%S')
            register_data = {
                "username": f"user_{timestamp}",
                "email": f"user_{timestamp}@example.com",
                "password": "test123456"
            }
            
            response = await client.post(f"{base_url}/api/v1/auth/register", json=register_data)
            print(f"注册响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 注册成功: {result['message']}")
                print(f"   用户ID: {result['data']['user_id']}")
                print(f"   用户名: {result['data']['username']}")
            else:
                print(f"❌ 注册失败: {response.text}")
                return
            
            # 2. 测试用户登录
            print("\n🔐 测试用户登录...")
            login_data = {
                "username": register_data["username"],
                "password": "test123456"
            }
            
            response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
            print(f"登录响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 登录成功: {result['message']}")
                
                token_info = result['data']['token']
                user_info = result['data']['user']
                
                print(f"   访问令牌: {token_info['access_token'][:50]}...")
                print(f"   令牌类型: {token_info['token_type']}")
                print(f"   过期时间: {token_info['expires_in']}秒")
                print(f"   用户信息: {user_info['username']} ({user_info['email']})")
                
                access_token = token_info['access_token']
            else:
                print(f"❌ 登录失败: {response.text}")
                return
            
            # 3. 测试获取用户信息（需要认证）
            print("\n👤 测试获取用户信息...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = await client.get(f"{base_url}/api/v1/user/me", headers=headers)
            print(f"获取用户信息响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 获取用户信息成功: {result['message']}")
                user_data = result['data']
                print(f"   用户ID: {user_data['id']}")
                print(f"   用户名: {user_data['username']}")
                print(f"   邮箱: {user_data['email']}")
                print(f"   创建时间: {user_data['created_at']}")
                print(f"   账户状态: {'活跃' if user_data['is_active'] else '禁用'}")
            else:
                print(f"❌ 获取用户信息失败: {response.text}")
            
            # 4. 测试创建角色
            print("\n🧙 测试创建角色...")
            character_data = {
                "name": "测试修仙者",
                "spiritual_root": "单灵根"
            }
            
            response = await client.post(f"{base_url}/api/v1/user/characters", json=character_data, headers=headers)
            print(f"创建角色响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 创建角色成功: {result['message']}")
                char_data = result['data']
                print(f"   角色ID: {char_data['id']}")
                print(f"   角色名: {char_data['name']}")
                print(f"   灵根: {char_data['spiritual_root']}")
                print(f"   境界: {char_data['cultivation_realm']}")
                print(f"   修为: {char_data['cultivation_exp']}")
                print(f"   气运: {char_data['luck_value']}")
                
                # 显示角色属性
                attrs = char_data['attributes']
                print(f"   生命值: {attrs['hp']}")
                print(f"   物攻: {attrs['physical_attack']}")
                print(f"   法攻: {attrs['magic_attack']}")
                print(f"   物防: {attrs['physical_defense']}")
                print(f"   法防: {attrs['magic_defense']}")
                
                character_id = char_data['id']
            else:
                print(f"❌ 创建角色失败: {response.text}")
                character_id = None
            
            # 5. 测试获取角色列表
            print("\n📋 测试获取角色列表...")
            response = await client.get(f"{base_url}/api/v1/user/characters", headers=headers)
            print(f"获取角色列表响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 获取角色列表成功: {result['message']}")
                data = result['data']
                print(f"   角色总数: {data['total']}")
                print(f"   最大角色数: {data['max_characters']}")
                
                for i, char in enumerate(data['characters'], 1):
                    print(f"   角色{i}: {char['name']} (境界: {char['cultivation_realm']}, 修为: {char['cultivation_exp']})")
            else:
                print(f"❌ 获取角色列表失败: {response.text}")
            
            # 6. 测试获取角色详细信息
            if character_id:
                print(f"\n🔍 测试获取角色详细信息 (ID: {character_id})...")
                response = await client.get(f"{base_url}/api/v1/user/characters/{character_id}", headers=headers)
                print(f"获取角色详情响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 获取角色详情成功: {result['message']}")
                    char_data = result['data']
                    print(f"   详细属性已获取，角色名: {char_data['name']}")
                else:
                    print(f"❌ 获取角色详情失败: {response.text}")
            
            # 7. 测试用户登出
            print("\n🚪 测试用户登出...")
            response = await client.post(f"{base_url}/api/v1/auth/logout", headers=headers)
            print(f"登出响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 登出成功: {result['message']}")
            else:
                print(f"❌ 登出失败: {response.text}")
            
            # 8. 测试登出后访问受保护资源
            print("\n🔒 测试登出后访问受保护资源...")
            response = await client.get(f"{base_url}/api/v1/user/me", headers=headers)
            print(f"访问受保护资源响应状态: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ 正确拒绝了无效令牌的访问")
            else:
                print(f"❌ 应该拒绝访问，但返回了: {response.status_code}")
            
            print("\n🎉 认证系统测试完成！")
            
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 气运修仙游戏 - 认证系统测试")
    print("=" * 60)
    
    # 运行异步测试
    asyncio.run(test_auth_api())
    
    print("\n" + "=" * 60)
    print("✨ 第三步骤：用户认证系统 - 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
