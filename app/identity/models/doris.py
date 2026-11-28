"""Doris 查询账号存储与连接凭据模型。"""

from dataclasses import dataclass, field

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import AuthBase


class DorisQueryIdentity(AuthBase):
    """Doris 角色关联的查询账号、凭据和工作组。"""

    __tablename__ = "doris_query_identities"  # 主表：一行 = 一个 Doris 角色
    # 主键，同时也是 users 表外键指向的目标
    # 字符串是65535 字节 utf8-md4 65535/4
    role_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    # 中文备注，只给人看，代码不读
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    # 真实存在于 Doris 的登录账号；unique 防止两个角色共用一个账号导致权限串台
    query_user: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    # Fernet 密文（约 140 字符），明文只在建立连接那一瞬间解密出来
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    # Doris 资源组，限制该账号可占用的 CPU/内存份额
    workload_group: Mapped[str] = mapped_column(String(128), nullable=False)

# 冻结 / 不能动态负值。
# 查询到信息的时候，传递给内部的调用工具agent 内到内 不需要继承数据库 不需要继承BaseModel
@dataclass(frozen=True, slots=True)
class ResolvedQueryPrincipal:
    """一次 Doris 查询的"通行证"：解密完成的角色、账号和明文密码。

    与 DorisQueryIdentity 是同一信息的两个形态：表实体存密文（落库形态），
    这个 dataclass 是解密后的内存形态（执行器连库用的形态）。
    由 IdentityService.get_query_principal 组装返回，查询模块每次执行
    SQL 前拿它开连接；只活在内存里，不落库、不进日志。

    frozen=True：字段不可变——拿到手后没人能中途换账号，可以放心传递
    slots=True：属性固定为这三个，省内存，也禁止运行时动态挂属性
    """
    # 数据角色名，与 users.doris_role_name 一致（如 dataagent_growth）
    role_name: str
    # Doris 查询账号名，用来建立连接的用户名
    query_user: str
    # repr=False： 对象被打印进日志时不会带出明文密码
    password: str = field(repr=False)