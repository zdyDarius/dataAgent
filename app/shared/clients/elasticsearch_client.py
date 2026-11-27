"""Elasticsearch 异步客户端创建。"""

from elasticsearch import AsyncElasticsearch

from app.shared.config.app_config import ESConfig


def create_elasticsearch_client(config: ESConfig) -> AsyncElasticsearch:
    """按统一配置创建 ES 客户端。

    超时必须显式配置：带 1024 维向量的 bulk 请求体积大、服务端建 HNSW 索引慢，
    默认 10 秒不够，稍一抖动就 ConnectionTimeout。

    服务端已开启 xpack.security，必须携带 basic auth，否则所有请求返回 401。
    """
    return AsyncElasticsearch(
        hosts=[f"http://{config.host}:{config.port}"],
        basic_auth=(config.user, config.password.get_secret_value()),
        request_timeout=config.request_timeout,
    )
