# FastAPI依赖注入

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.models import User
from server.core.auth import AuthService, AuthenticationError


# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    if not credentials:
        raise AuthenticationError("缺少认证令牌")
    
    token = credentials.credentials
    
    # 验证用户会话
    user = await AuthService.verify_user_session(db, token)
    if not user:
        raise AuthenticationError("无效的认证令牌")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，不强制认证）"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        user = await AuthService.verify_user_session(db, token)
        return user if user and user.is_active else None
    except Exception:
        return None


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 优先从X-Forwarded-For头获取（代理环境）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 从X-Real-IP头获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接从客户端获取
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理字符串"""
    return request.headers.get("User-Agent", "unknown")
