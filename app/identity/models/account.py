### 3.6 models/account.py

# 文件：app/identity/models/account.py
"""由初始化脚本创建的预定义用户。"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import AuthBase


class User(AuthBase):
    """用于选择查询身份和隔离会话的预定义用户。"""

    __tablename__ = "users"  # 子表：一行 = 一个人

    # autoincrement=False：ID 由脚本写死 1/2/3，重跑脚本 ID 不变
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    # 前端下拉框展示的名字
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # 外键指向主表主键：角色下还有用户时，数据库禁止删这个角色
    doris_role_name: Mapped[str] = mapped_column(
        ForeignKey("doris_query_identities.role_name", ondelete="RESTRICT"),
        nullable=False,
    )