"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import API_PREFIX, CORS_ORIGINS
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("✓ Agent API服务已启动")
    yield
    # 关闭时清理资源
    print("Agent API服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="盘古教育Agent API",
    description="基于华为盘古Embedded 7B模型的教育问答Agent后端服务",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "code": "INTERNAL_ERROR"
        }
    )


# 注册路由
from api.routes import chat, user, session, tools, health

app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["Chat"])
app.include_router(user.router, prefix=API_PREFIX, tags=["User"])
app.include_router(session.router, prefix=API_PREFIX, tags=["Session"])
app.include_router(tools.router, prefix=API_PREFIX, tags=["Tools"])


# 根路由
@app.get("/")
async def root():
    return {
        "service": "盘古教育Agent API",
        "version": "2.0.0",
        "docs": "/docs"
    }
