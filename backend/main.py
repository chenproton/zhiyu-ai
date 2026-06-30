from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from sqlalchemy import select

from database import AsyncSessionLocal
from models import ExternalAgent
from routers import auth, org, kb, document, search, chat, bot, external_agent, admin, events, interactions, config

app = FastAPI(title="学校 AI 服务平台", version="0.1.0")


OFFICIAL_AGENTS = [
    {'name': '岗位 AI 辅助生成', 'description': '基于 AI 辅助生成岗位能力模型与任务描述。', 'target_url': 'http://demo2.zhiyu.com.cn:5000/job_ai', 'category': 'AI生成', 'sort_order': 1},
    {'name': '场景 AI 辅助生成', 'description': '基于 AI 辅助生成教学实践场景与任务设计。', 'target_url': 'http://demo2.zhiyu.com.cn:5000/scene_ai', 'category': 'AI生成', 'sort_order': 2},
]


@app.on_event("startup")
async def seed_official_agents():
    """首次启动时插入默认官方智能体；已存在的记录不会被覆盖，支持后台手动编辑。"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ExternalAgent))
        existing = {a.target_url: a for a in result.scalars().all()}
        for item in OFFICIAL_AGENTS:
            if item['target_url'] in existing:
                continue
            if any(a.name == item['name'] for a in existing.values()):
                continue
            db.add(ExternalAgent(**item, is_active=True))
        await db.commit()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(org.router)
app.include_router(kb.router)
app.include_router(document.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(bot.router)
app.include_router(external_agent.router)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(interactions.router)
app.include_router(config.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "学校 AI 服务平台 API 已运行"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
