# 文件：app/identity/repositories/identity.py
"""身份模块的 PG 仓储：users 与 doris_query_identities 两张表的只读查询。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.account import User
from app.identity.models.doris import DorisQueryIdentity


class IdentityPGRepo:
    """读取用户及 Doris 查询身份。"""

    def __init__(self, session: AsyncSession) -> None:
        """绑定身份数据库会话。"""
        # 会话由调用方创建和关闭，仓储不自己开连接、不管事务
        self._session = session

    async def list_users(self) -> list[User]:
        """按 ID 升序读取用户列表。"""
        # 提示：select 拼条件 + session.scalars 取多行 + order_by 保证顺序
        return (await self._session.scalars(select(User).order_by(User.id.asc()))).all()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """按主键读取用户。"""
        # 提示：scalar 取单行；用 execution_options(populate_existing=True) 强制回库
        return await self._session.scalar(select(User).where(User.id == user_id))

    async def get_query_identity(
        self,
        role_name: str,
    ) -> DorisQueryIdentity | None:
        """按 Doris 角色读取查询账号和凭据。"""
        # 提示：按主键等值查询，一行或 None
        return (await self._session.scalar(select(DorisQueryIdentity).where(
            DorisQueryIdentity.role_name == role_name,
        )))