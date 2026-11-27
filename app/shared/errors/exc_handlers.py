"""FastAPI 全局异常处理器。
统一把所有异常输出为标准 problem+json 格式，方便前端统一解析错误，同时区分日志等级。
"""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException
from starlette.types import ExceptionHandler

from app.shared.errors.base import ProblemError


def _build_response(
    request: Request,
    exc: ProblemError,
    *,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """构造 Problem Details 规范的错误响应体。"""
    return JSONResponse(
        status_code=exc.status,
        content=exc.to_problem(instance=request.url.path),
        headers=headers,
        media_type="application/problem+json",
    )


def _log_problem(exc: ProblemError, source: Exception) -> None:
    """按状态码分级打印日志：5xx错误打error堆栈，4xx只打warning不抛堆栈。"""
    context = {
        "problem_type": exc.type,
        "status": exc.status,
        "exc_type": type(source).__name__,
        "detail": exc.detail,
    }
    if exc.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.opt(exception=source).error(exc.title, **context)
    else:
        logger.warning(exc.title, **context)


def _problem_error_handler(request: Request, exc: ProblemError) -> JSONResponse:
    """处理项目自定义业务异常 ProblemError。"""
    _log_problem(exc, exc)
    retry_after = exc.extensions.get("retry_after_seconds")
    headers = (
        {"Retry-After": str(retry_after)}
        if exc.status == HTTPStatus.TOO_MANY_REQUESTS
        and isinstance(retry_after, int)
        and retry_after > 0
        else None
    )
    return _build_response(request, exc, headers=headers)


def _validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求参数校验失败（422），把校验错误整理进problem扩展字段。"""
    errors: list[dict[str, Any]] = [
        {
            "type": error["type"],
            "location": list(error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    problem = ProblemError(
        title="参数校验失败",
        detail="请求参数不符合接口要求",
        type="validation-error",
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        extensions={"errors": errors},
    )
    _log_problem(problem, exc)
    return _build_response(request, problem)


def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理FastAPI原生HTTPException，统一包装成problem格式。"""
    detail = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    try:
        title = HTTPStatus(exc.status_code).phrase
    except ValueError:
        title = "HTTP 请求错误"
    problem = ProblemError(
        title=title,
        detail=detail,
        status=exc.status_code,
        type=f"http-{exc.status_code}",
        extensions=(
            {"errors": exc.detail} if isinstance(exc.detail, (list, dict)) else None
        ),
    )
    _log_problem(problem, exc)
    return _build_response(request, problem, headers=exc.headers)


def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底处理器：捕获所有前面没有匹配到的未知异常。
    重点：对客户端屏蔽内部报错细节，只返回通用500错误，完整堆栈记录在服务端日志。
    """
    problem = ProblemError()
    _log_problem(problem, exc)
    return _build_response(request, problem)


def register_exception_handlers(app: FastAPI) -> None:
    """批量注册全部异常处理器。
    注册顺序：从具体异常 → 通用异常，越靠后越通用。
    """
    # 自定义业务异常
    app.add_exception_handler(
        ProblemError,
        cast(ExceptionHandler, _problem_error_handler),
    )
    # 参数校验异常
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, _validation_error_handler),
    )
    # FastAPI原生HTTP异常
    app.add_exception_handler(
        HTTPException,
        cast(ExceptionHandler, _http_exception_handler),
    )
    # 兜底：所有其它未捕获的Exception，全局最后一道防线
    app.add_exception_handler(
        Exception,
        cast(ExceptionHandler, _unhandled_exception_handler),
    )