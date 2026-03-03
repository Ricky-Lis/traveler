"""
应用配置：优先从环境变量和 .env 文件读取，不包含任何真实密钥默认值。
部署/本地开发时请复制 .env.example 为 .env 并填写实际配置。
"""
from functools import lru_cache
from urllib.parse import quote

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MySQL（密码等敏感项无默认值，必须通过 .env 或环境变量设置）
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "travel"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 1

    # JWT（SECRET_KEY 必须自行设置，不要使用默认值）
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # SMTP
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Aliyun OSS
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_ENDPOINT: str = "oss-cn-shenzhen.aliyuncs.com"
    OSS_CDN_DOMAIN: str = ""

    # 高德 Web 服务（逆地理编码，可选）
    AMAP_WEB_SERVICE_KEY: str = ""

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        host_port_db = f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            user = quote(self.REDIS_USERNAME, safe="")
            pw = quote(self.REDIS_PASSWORD, safe="")
            return f"redis://{user}:{pw}@{host_port_db}"
        if self.REDIS_PASSWORD:
            pw = quote(self.REDIS_PASSWORD, safe="")
            return f"redis://:{pw}@{host_port_db}"
        return f"redis://{host_port_db}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
