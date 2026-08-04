"""
用户管理 API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.user import UserCreate, UserUpdate, UserResponse, ChangePassword
from ....schemas.common import Response, PaginatedResponse, PaginatedData
from ....models import User
from ....services.user import UserService
from ....api.deps import get_current_admin_user

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserResponse])
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户列表（分页、搜索、筛选）

    Args:
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        status: 状态筛选
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        PaginatedResponse[UserResponse]: 分页用户列表
    """
    result = await UserService.get_users_list(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status
    )

    return PaginatedResponse(
        data=PaginatedData(
            list=[UserResponse(**user) for user in result["list"]],
            page=result["page"],
            page_size=result["page_size"],
            total=result["total"]
        )
    )


@router.post("", response_model=Response[UserResponse])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    创建用户

    Args:
        user_data: 用户创建数据
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        Response[UserResponse]: 创建的用户信息
    """
    try:
        user = await UserService.create_user(db, user_data)

        return Response(
            message="创建成功",
            data=UserResponse(
                id=user.id,
                username=user.username,
                real_name=user.real_name,
                email=user.email,
                role_ids=[role.id for role in user.roles],
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=Response[UserResponse])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取用户详情

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        Response[UserResponse]: 用户信息
    """
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return Response(
        data=UserResponse(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            email=user.email,
            role_ids=[role.id for role in user.roles],
            status=user.status,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    )


@router.put("/{user_id}", response_model=Response[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新用户信息

    Args:
        user_id: 用户ID
        user_data: 用户更新数据
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        Response[UserResponse]: 更新后的用户信息
    """
    try:
        user = await UserService.update_user(db, user_id, user_data)

        return Response(
            message="更新成功",
            data=UserResponse(
                id=user.id,
                username=user.username,
                real_name=user.real_name,
                email=user.email,
                role_ids=[role.id for role in user.roles],
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}/password", response_model=Response)
async def change_user_password(
    user_id: int,
    password_data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    修改用户密码

    Args:
        user_id: 用户ID
        password_data: 密码数据
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        Response: 成功响应
    """
    try:
        await UserService.change_password(db, user_id, password_data)
        return Response(message="密码修改成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    删除用户

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前管理员用户

    Returns:
        Response: 成功响应
    """
    try:
        await UserService.delete_user(db, user_id)
        return Response(message="删除成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )