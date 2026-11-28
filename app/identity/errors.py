# 文件：app/identity/errors.py
"""用户选择与 Doris 查询身份异常。"""

from http import HTTPStatus

from app.shared.errors.base import ProblemError


class UserSelectionRequiredError(ProblemError):
    """请求未选择用户或所选用户不存在。"""

    # 三个类属性由 ProblemError 读取，拼成 application/problem+json 响应体
    type = "user-selection-required"  # 机器读的错误标识
    title = "未选择有效用户"  # 人读的标题，前端可直接展示
    status = HTTPStatus.UNAUTHORIZED  # 401：没给身份，或者给的身份无效


# 下面两个是服务端问题（数据没配全、密钥不对），继承 RuntimeError，全局处理器映射成 500
class QueryPrincipalNotConfiguredError(RuntimeError):
    """用户绑定的角色缺少查询身份。"""


class DorisCredentialError(RuntimeError):
    """Doris 查询凭据无法解密。"""