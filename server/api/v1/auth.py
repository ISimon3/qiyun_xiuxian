# 注册、登录接口

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from server.database.database import get_db
from server.database.crud import UserCRUD
from server.core.auth import AuthService, AuthenticationError
from server.core.dependencies import get_current_user, get_client_ip, get_user_agent
from shared.schemas import (
    BaseResponse, UserRegister, UserLogin, UserInfo, Token
)

router = APIRouter()


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
        user = await AuthService.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise AuthenticationError("用户名或密码错误")

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )

        # 获取客户端信息
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # 创建用户会话
        access_token, expires_at = await AuthService.create_user_session(
            db, user, ip_address, user_agent
        )

        # 构造令牌响应
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int((expires_at - user.last_login).total_seconds()) if user.last_login else 3600
        )

        return BaseResponse(
            success=True,
            message="登录成功",
            data={
                "token": token_data.model_dump(),
                "user": UserInfo.model_validate(user).model_dump()
            }
        )

    except AuthenticationError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
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
