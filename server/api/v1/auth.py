# 注册、登录接口

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from server.database.database import get_db
from server.database.crud import UserCRUD
from server.database.models import User
from server.core.auth import AuthService, AuthenticationError
from server.core.dependencies import get_current_user, get_client_ip, get_user_agent
from shared.schemas import (
    BaseResponse, UserRegister, UserLogin, UserInfo, Token
)

router = APIRouter()


@router.get("/check-username/{username}", response_model=BaseResponse, summary="检查用户名是否可用")
async def check_username(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查用户名是否可用

    - **username**: 要检查的用户名

    返回用户名可用性信息
    """
    try:
        # 检查用户名格式
        if not username or not username.strip() or len(username) < 3 or len(username) > 20:
            return BaseResponse(
                success=False,
                message="用户名长度必须在3-20个字符之间",
                data=None
            )

        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return BaseResponse(
                success=False,
                message="用户名只能包含字母、数字和下划线",
                data=None
            )

        # 检查用户名是否已存在
        existing_user = await UserCRUD.get_user_by_username(db, username)
        if existing_user:
            return BaseResponse(
                success=False,
                message="用户名已被使用",
                data={"available": False}
            )

        return BaseResponse(
            success=True,
            message="用户名可用",
            data={"available": True}
        )

    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"检查用户名失败: {str(e)}",
            data=None
        )


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名 (3-20字符)
    - **email**: 邮箱地址
    - **password**: 密码 (6-50字符)
    """
    try:
        # 检查用户名是否已存在
        existing_user = await UserCRUD.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_email = await UserCRUD.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        user = await UserCRUD.create_user(db, user_data)

        return BaseResponse(
            success=True,
            message="注册成功",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )

    except HTTPException:
        # 重新抛出HTTP异常，不要包装
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=BaseResponse, summary="用户登录")
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回JWT访问令牌
    """
    try:
        # 验证用户凭据
        user, error_message = await AuthService.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            # 返回BaseResponse格式的错误响应
            return BaseResponse(
                success=False,
                message=error_message,
                data=None
            )

        # 检查用户是否已有活跃会话
        from server.database.crud import SessionCRUD
        active_sessions = await SessionCRUD.get_active_sessions_by_user_id(db, user.id)
        had_active_session = len(active_sessions) > 0

        # 获取客户端信息
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # 创建用户会话（会自动停用旧会话）
        access_token, expires_at = await AuthService.create_user_session(
            db, user, ip_address, user_agent
        )

        # 构造令牌响应
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int((expires_at - user.last_login).total_seconds()) if user.last_login else 3600
        )

        # 启动用户会话管理
        from server.core.user_session_manager import user_session_manager
        from server.database.crud import CharacterCRUD

        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, user.id, user.username)

        # 启动用户会话（计算离线收益）
        session_result = await user_session_manager.user_login(user.id, character.id)

        # 构造登录消息
        login_message = "登录成功"
        if had_active_session:
            login_message = "登录成功（已自动断开其他设备的连接）"

        return BaseResponse(
            success=True,
            message=login_message,
            data={
                "token": token_data.model_dump(),
                "user": UserInfo.model_validate(user).model_dump(),
                "character": {
                    "id": character.id,
                    "name": character.name,
                    "cultivation_realm": character.cultivation_realm,
                    "luck_value": character.luck_value
                },
                "session_info": session_result,
                "had_active_session": had_active_session
            }
        )

    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"登录失败: {str(e)}",
            data=None
        )


@router.get("/sessions", response_model=BaseResponse, summary="获取用户会话信息")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有活跃会话信息

    需要在请求头中提供有效的JWT令牌
    """
    try:
        from server.database.crud import SessionCRUD

        # 获取用户的所有活跃会话
        active_sessions = await SessionCRUD.get_active_sessions_by_user_id(db, current_user.id)

        sessions_data = []
        for session in active_sessions:
            sessions_data.append({
                "id": session.id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat(),
                "last_used": session.last_used.isoformat(),
                "expires_at": session.expires_at.isoformat()
            })

        return BaseResponse(
            success=True,
            message="获取会话信息成功",
            data={
                "active_sessions_count": len(active_sessions),
                "sessions": sessions_data
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话信息失败: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出

    需要在请求头中提供有效的JWT令牌
    """
    try:
        # 处理用户会话登出
        from server.core.user_session_manager import user_session_manager
        session_result = await user_session_manager.user_logout(current_user.id)

        return BaseResponse(
            success=True,
            message="登出成功",
            data=session_result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出

    需要提供有效的JWT令牌
    """
    try:
        # 从请求头获取令牌
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("缺少认证令牌")

        token = auth_header.split(" ")[1]

        # 注销用户会话
        success = await AuthService.logout_user(db, token)

        return BaseResponse(
            success=True,
            message="登出成功" if success else "登出完成",
            data=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )
