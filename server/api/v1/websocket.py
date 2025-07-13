# WebSocket通信管理

import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.crud import UserCRUD, CharacterCRUD, ChatCRUD
from server.core.dependencies import get_current_user
from server.core.auth import AuthService
from shared.schemas import BaseResponse

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接：{character_id: websocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # 存储用户信息：{character_id: user_info}
        self.user_info: Dict[int, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, character_id: int, user_info: Dict[str, Any]):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[character_id] = websocket
        self.user_info[character_id] = user_info
        print(f"🔗 用户 {user_info.get('username')} (角色ID: {character_id}) 已连接WebSocket")

    def disconnect(self, character_id: int):
        """断开WebSocket连接"""
        if character_id in self.active_connections:
            user_info = self.user_info.get(character_id, {})
            username = user_info.get('username', 'Unknown')
            print(f"🔌 用户 {username} (角色ID: {character_id}) 已断开WebSocket连接")

            del self.active_connections[character_id]
            if character_id in self.user_info:
                del self.user_info[character_id]

    async def send_personal_message(self, message: str, character_id: int):
        """发送个人消息"""
        if character_id in self.active_connections:
            websocket = self.active_connections[character_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"❌ 发送个人消息失败: {e}")
                self.disconnect(character_id)

    async def broadcast_to_channel(self, message: str, channel: str = "WORLD", exclude_character: Optional[int] = None):
        """向频道广播消息"""
        disconnected_characters = []

        for character_id, websocket in self.active_connections.items():
            if exclude_character and character_id == exclude_character:
                continue

            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"❌ 广播消息失败 (角色ID: {character_id}): {e}")
                disconnected_characters.append(character_id)

        # 清理断开的连接
        for character_id in disconnected_characters:
            self.disconnect(character_id)

    def get_online_count(self) -> int:
        """获取在线人数"""
        return len(self.active_connections)

    def get_online_users(self) -> List[Dict[str, Any]]:
        """获取在线用户列表"""
        return [
            {
                "character_id": character_id,
                "username": user_info.get("username", "Unknown"),
                "character_name": user_info.get("character_name", "Unknown")
            }
            for character_id, user_info in self.user_info.items()
        ]


# 全局连接管理器
manager = ConnectionManager()


async def get_current_character_from_websocket(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """从WebSocket获取当前角色信息"""
    try:
        # 验证token并获取用户信息
        user = await AuthService.verify_user_session(db, token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return None, None

        # 获取角色信息
        character = await CharacterCRUD.get_or_create_character(db, user.id, user.username)
        if not character:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Character not found")
            return None, None

        user_info = {
            "user_id": user.id,
            "username": user.username,
            "character_id": character.id,
            "character_name": character.name
        }

        return character, user_info

    except Exception as e:
        print(f"❌ WebSocket认证失败: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication failed")
        return None, None


@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket连接端点"""
    character, user_info = await get_current_character_from_websocket(websocket, token, db)
    if not character or not user_info:
        return

    character_id = character.id

    # 建立连接
    await manager.connect(websocket, character_id, user_info)

    # 发送连接成功消息
    welcome_message = {
        "type": "system",
        "channel": "SYSTEM",
        "content": f"欢迎 {user_info['character_name']} 进入聊天室！",
        "timestamp": datetime.now().isoformat()
    }
    await manager.send_personal_message(json.dumps(welcome_message), character_id)

    # 广播用户上线消息
    online_message = {
        "type": "system",
        "channel": "WORLD",
        "content": f"玩家 {user_info['character_name']} 上线了！",
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_channel(json.dumps(online_message), exclude_character=character_id)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 处理消息
            await handle_websocket_message(db, character, user_info, message_data)

    except WebSocketDisconnect:
        # 处理断开连接
        manager.disconnect(character_id)

        # 广播用户下线消息
        offline_message = {
            "type": "system",
            "channel": "WORLD",
            "content": f"玩家 {user_info['character_name']} 下线了！",
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_channel(json.dumps(offline_message))

    except Exception as e:
        print(f"❌ WebSocket错误: {e}")
        manager.disconnect(character_id)


async def handle_websocket_message(
    db: AsyncSession,
    character: Any,
    user_info: Dict[str, Any],
    message_data: Dict[str, Any]
):
    """处理WebSocket消息"""
    try:
        message_type = message_data.get("type", "chat")

        if message_type == "chat":
            await handle_chat_message(db, character, user_info, message_data)
        elif message_type == "ping":
            await handle_ping_message(character.id)
        elif message_type == "get_history":
            await handle_get_history(db, character.id, message_data)
        else:
            print(f"⚠️ 未知消息类型: {message_type}")

    except Exception as e:
        print(f"❌ 处理WebSocket消息失败: {e}")


async def handle_chat_message(
    db: AsyncSession,
    character: Any,
    user_info: Dict[str, Any],
    message_data: Dict[str, Any]
):
    """处理聊天消息"""
    channel = message_data.get("channel", "WORLD")
    content = message_data.get("content", "").strip()

    if not content:
        return

    # 内容长度限制
    if len(content) > 500:
        error_message = {
            "type": "error",
            "content": "消息内容过长，请控制在500字符以内",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), character.id)
        return

    # 保存消息到数据库
    try:
        db_message = await ChatCRUD.create_message(
            db=db,
            character_id=character.id,
            channel=channel,
            content=content,
            message_type="NORMAL"
        )

        # 构造广播消息
        broadcast_message = {
            "type": "chat",
            "channel": channel,
            "character_id": character.id,
            "character_name": user_info["character_name"],
            "content": content,
            "timestamp": db_message.created_at.isoformat(),
            "message_id": db_message.id
        }

        # 广播消息
        if channel == "WORLD":
            await manager.broadcast_to_channel(json.dumps(broadcast_message))
        else:
            # 其他频道的处理逻辑可以在这里扩展
            await manager.broadcast_to_channel(json.dumps(broadcast_message))

    except Exception as e:
        print(f"❌ 保存聊天消息失败: {e}")
        error_message = {
            "type": "error",
            "content": "消息发送失败，请稍后重试",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), character.id)


async def handle_ping_message(character_id: int):
    """处理心跳消息"""
    pong_message = {
        "type": "pong",
        "timestamp": datetime.now().isoformat()
    }
    await manager.send_personal_message(json.dumps(pong_message), character_id)


async def handle_get_history(
    db: AsyncSession,
    character_id: int,
    message_data: Dict[str, Any]
):
    """处理获取历史消息请求"""
    try:
        channel = message_data.get("channel", "WORLD")
        limit = min(message_data.get("limit", 50), 100)  # 最多100条

        # 获取历史消息
        messages = await ChatCRUD.get_recent_messages(db, channel, limit)

        # 构造历史消息响应
        history_data = {
            "type": "history",
            "channel": channel,
            "messages": [
                {
                    "character_id": msg.character_id,
                    "character_name": msg.character.name,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "message_id": msg.id
                }
                for msg in messages
            ]
        }

        await manager.send_personal_message(json.dumps(history_data), character_id)

    except Exception as e:
        print(f"❌ 获取历史消息失败: {e}")
        error_message = {
            "type": "error",
            "content": "获取历史消息失败",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), character_id)


# HTTP API端点

@router.get("/online-users")
async def get_online_users():
    """获取在线用户列表"""
    try:
        online_users = manager.get_online_users()
        return BaseResponse(
            success=True,
            message="获取在线用户成功",
            data={
                "online_count": manager.get_online_count(),
                "users": online_users
            }
        )
    except Exception as e:
        print(f"❌ 获取在线用户失败: {e}")
        return BaseResponse(
            success=False,
            message="获取在线用户失败"
        )


@router.get("/chat-history/{channel}")
async def get_chat_history(
    channel: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取聊天历史记录"""
    try:
        # 限制查询数量
        limit = min(limit, 100)

        # 获取历史消息
        messages = await ChatCRUD.get_recent_messages(db, channel, limit)

        # 格式化消息数据
        formatted_messages = [
            {
                "id": msg.id,
                "character_id": msg.character_id,
                "character_name": msg.character.name,
                "content": msg.content,
                "message_type": msg.message_type,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]

        return BaseResponse(
            success=True,
            message="获取聊天历史成功",
            data={
                "channel": channel,
                "messages": formatted_messages
            }
        )

    except Exception as e:
        print(f"❌ 获取聊天历史失败: {e}")
        return BaseResponse(
            success=False,
            message="获取聊天历史失败"
        )
