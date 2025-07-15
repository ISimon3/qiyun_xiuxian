# JWT认证工具模块

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import settings
from server.database.crud import UserCRUD, SessionCRUD
from server.database.models import User


class JWTManager:
    """JWT令牌管理器"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, str, datetime]:
        """
        创建访问令牌
        返回: (token, jti, expires_at)
        """
        to_encode = data.copy()
        
        # 设置过期时间
        now = datetime.utcnow()
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 生成唯一的JWT ID
        jti = str(uuid.uuid4())

        # 添加标准声明 (使用时间戳)
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "jti": jti,
            "type": "access"
        })
        
        # 编码JWT
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return encoded_jwt, jti, expire
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            print(f"JWT验证错误: {e}")  # 临时调试信息
            return None
    
    @staticmethod
    def extract_user_id(token: str) -> Optional[int]:
        """从令牌中提取用户ID"""
        payload = JWTManager.verify_token(token)
        if payload:
            user_id_str = payload.get("sub")
            return int(user_id_str) if user_id_str else None
        return None
    
    @staticmethod
    def extract_jti(token: str) -> Optional[str]:
        """从令牌中提取JWT ID"""
        payload = JWTManager.verify_token(token)
        if payload:
            return payload.get("jti")
        return None


class AuthService:
    """认证服务"""
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> tuple[Optional[User], str]:
        """
        用户认证

        Returns:
            tuple[Optional[User], str]: (用户对象, 错误消息)
        """
        return await UserCRUD.authenticate_user(db, username, password)
    
    @staticmethod
    async def create_user_session(
        db: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> tuple[str, datetime]:
        """
        创建用户会话
        返回: (access_token, expires_at)
        """
        # 检查用户是否已有活跃会话，如果有则停用旧会话（防止重复登录）
        active_sessions = await SessionCRUD.get_active_sessions_by_user_id(db, user.id)
        if active_sessions:
            print(f"用户 {user.username} 已有 {len(active_sessions)} 个活跃会话，将停用旧会话")
            await SessionCRUD.deactivate_user_sessions(db, user.id)

        # 创建JWT令牌
        token_data = {"sub": str(user.id), "username": user.username}
        access_token, jti, expires_at = JWTManager.create_access_token(token_data)

        # 保存会话到数据库
        await SessionCRUD.create_session(
            db, user.id, jti, expires_at, ip_address, user_agent
        )

        # 更新用户最后登录时间
        await UserCRUD.update_user_login_time(db, user.id)

        return access_token, expires_at
    
    @staticmethod
    async def verify_user_session(db: AsyncSession, token: str) -> Optional[User]:
        """验证用户会话"""
        # 验证JWT令牌
        payload = JWTManager.verify_token(token)
        if not payload:
            return None
        
        user_id_str = payload.get("sub")
        jti = payload.get("jti")

        if not user_id_str or not jti:
            return None

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None
        
        # 检查会话是否存在且有效
        session = await SessionCRUD.get_session_by_jti(db, jti)
        if not session or not session.is_active:
            return None
        
        # 检查会话是否过期
        if session.expires_at < datetime.utcnow():
            await SessionCRUD.deactivate_session(db, jti)
            return None
        
        # 获取用户信息
        user = await UserCRUD.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        
        # 更新会话活跃时间
        await SessionCRUD.update_session_activity(db, jti)
        
        return user
    
    @staticmethod
    async def logout_user(db: AsyncSession, token: str) -> bool:
        """用户登出"""
        jti = JWTManager.extract_jti(token)
        if jti:
            return await SessionCRUD.deactivate_session(db, jti)
        return False
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """清理过期会话"""
        return await SessionCRUD.cleanup_expired_sessions(db)


# 认证异常
class AuthenticationError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
