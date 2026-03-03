"""
应用入口。在导入可能加载 oss2 的模块前过滤第三方库的 invalid escape 警告，
避免在 -W error 等环境下因 oss2 的 docstring 导致退出。
"""
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, message=r"invalid escape sequence ")

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.redis_client import init_redis, close_redis
from app.api.v1 import v1_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    logging.info("Redis 连接已建立")
    yield
    await close_redis()
    logging.info("Redis 连接已关闭")


app = FastAPI(
    title="旅行计划 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
