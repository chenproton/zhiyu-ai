# 学校 AI 服务平台 — 简化版技术开发方案（Python 全栈自建）

## 一、产品概述

### 1.1 产品定位

学校 AI 服务平台是部署于校内的轻量级 AI 服务中枢，面向全校师生提供"知识沉淀 + 智能问答 + 场景化机器人"三位一体的服务。

**三大模块**：

| 模块 | 定位 | 用户群体 |
| --- | --- | --- |
| **学校知识库** | 校内专属数智资产沉淀中心，支持**知识库+文档双层级权限管控** | 全体师生（按权限访问） |
| **官方机器人** | 平台预置的复杂场景专用机器人（如教务咨询、制度查询） | 全体师生（按权限访问） |
| **自建机器人** | 师生通过简易配置快速生成的个性化 AI 对话助手 | 全体师生（按配置分享） |

### 1.2 核心价值主张

> **"让学校的每一份知识资产，都能被安全、精准、智能地复用。"**

*   **知识资产化**：将分散在各部门的文档、课件、制度沉淀为可检索、可问答的数智资产
    
*   **权限精细化**：**知识库级+文档级双层级权限体系**，确保"该看的能看到，不该看的绝对看不到"
    
*   **使用零门槛**：官方机器人开箱即用，自建机器人三步配置，无需技术背景
    
*   **答案可溯源**：每个 AI 回答都标注来源文档及具体位置，杜绝"幻觉"
    

### 1.3 目标用户画像

| 用户 | 角色 | 核心诉求 |
| --- | --- | --- |
| **校方管理员** | 平台运营者 | 一站式管理全校知识资产，精细化控制访问权限，快速上架官方机器人 |
| **院系/专业负责人** | 知识库共建者 | 邀请团队共同维护知识库，**支持文档级权限隔离**，版本可追溯 |
| **普通师生** | 知识消费者 | 像聊天一样快速获取准确答案，答案有出处可核实；**只看到自己有权查看的内容** |
| **高阶师生** | 自建机器人创作者 | 基于学校知识库快速搭建专属 AI 助手，**AI 检索范围精确到文档级别** |

### 1.4 核心使用场景

| 场景 | 用户 | 行为路径 | 价值点 |
| --- | --- | --- | --- |
| **查制度** | 学生 | 登录广场 → 搜索"请假流程" → 获得带出处（学生手册第15页）的答案 | 无需翻阅上百页文档，3秒定位 |
| **课程答疑** | 学生 | 使用老师自建的课程答疑机器人 → 提问专业问题 → 基于课程知识库回答 | 7×24 小时答疑，减轻教师负担 |
| **知识共建** | 教研室团队 | 创建专业级知识库 → 邀请成员 → 上传新版教学大纲 → 查看历史版本 | 协同维护，变更可追溯 |
| **精细化文档隔离** | 院级管理员 | 创建院级知识库 → 上传通用文档（院级可见）+ 上传软件工程专属文档（专业级可见）+ 上传实验室保密文档（岗位级可见） | **同一知识库内，不同专业/岗位人员看到不同内容，AI 问答范围自动隔离** |

---

## 二、技术栈总览

采用 **Python 全栈 + 单库架构**，极致简化部署与开发。

| 层级 | 技术选型 | 版本/说明 |
| --- | --- | --- |
| **前端** | Vue 3 + Element Plus + Vue Router + Pinia | 打包后由后端静态托管 |
| **后端** | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic | 异步 ORM，自动迁移 |
| **数据库** | PostgreSQL 15 + pgvector 插件 | 业务数据 + 向量 + 会话，一库到底 |
| **文档解析** | PyMuPDF / python-docx / beautifulsoup4 | 纯 Python，pip 安装即可 |
| **在线预览** | 后端文本提取 + 前端通用组件 | PDF 用 iframe/PDF.js；Word/txt 转 HTML/文本 |
| **Embedding** | text-embedding-v4 API（或 BGE-M3 本地过渡） | 后端异步 HTTP 调用，维度通过环境变量配置 |
| **LLM** | DeepSeek API | 流式 SSE 输出 |
| **异步任务** | FastAPI BackgroundTasks | 文档解析、向量化 |
| **文件存储** | 本地文件系统 `/data/files` | Docker 挂载卷 |
| **部署** | Docker + Docker Compose | 2 个容器：backend + postgres |

---

## 三、数据库完整设计（DDL）

所有表统一使用以下字段：

*   `id`: SERIAL PRIMARY KEY
    
*   `created_at`: TIMESTAMP DEFAULT NOW()
    
*   `updated_at`: TIMESTAMP DEFAULT NOW()
    

### 3.1 组织架构（自建简化版）

```sql
CREATE TABLE org (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,        -- 如 10-01-03-02
    name VARCHAR(100) NOT NULL,
    level INT NOT NULL CHECK (level IN (1,2,3,4)),  -- 1校级 2院级 3专业级 4岗位级
    parent_code VARCHAR(20),
    path VARCHAR(100) NOT NULL,              -- 层级路径，如 10/10-01/10-01-03/10-01-03-02
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 插入演示数据
INSERT INTO org (code, name, level, parent_code, path) VALUES
('10-00-00-00', 'XX大学', 1, NULL, '10-00-00-00'),
('10-01-00-00', '计算机学院', 2, '10-00-00-00', '10-00-00-00/10-01-00-00'),
('10-01-03-00', '软件工程专业', 3, '10-01-00-00', '10-00-00-00/10-01-00-00/10-01-03-00'),
('10-01-03-02', '软件工程实验室', 4, '10-01-03-00', '10-00-00-00/10-01-00-00/10-01-03-00/10-01-03-02'),
('10-01-05-00', '网络工程专业', 3, '10-01-00-00', '10-00-00-00/10-01-00-00/10-01-05-00');

```

### 3.2 用户

```sql
CREATE TABLE sys_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,          -- bcrypt 哈希
    name VARCHAR(50) NOT NULL,
    org_code VARCHAR(20) NOT NULL,
    scope_code VARCHAR(20) NOT NULL,         -- 权限层级编码
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer')),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 演示账号
INSERT INTO sys_user (username, password, name, org_code, scope_code, role) VALUES
('admin', '$2b$12$...', '系统管理员', '10-00-00-00', '10-00-00-00', 'admin'),
('teacher01', '$2b$12$...', '张教授', '10-01-03-00', '10-01-03-00', 'editor'),
('student01', '$2b$12$...', '李同学', '10-01-03-02', '10-01-03-02', 'viewer'),
('student02', '$2b$12$...', '王同学', '10-01-05-00', '10-01-05-00', 'viewer');

```

### 3.3 知识库

```sql
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    scope_level INT NOT NULL CHECK (scope_level IN (1,2,3,4)),
    org_code VARCHAR(20) NOT NULL,
    owner_id INT NOT NULL REFERENCES sys_user(id),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    doc_count INT DEFAULT 0,
    total_pages INT DEFAULT 0,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

```

### 3.4 协作者

```sql
CREATE TABLE kb_collaborator (
    id SERIAL PRIMARY KEY,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES sys_user(id),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('editor', 'viewer')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(kb_id, user_id)
);

```

### 3.5 文档（核心：支持文档级独立权限）

```sql
CREATE TABLE kb_document (
    id SERIAL PRIMARY KEY,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,         -- 本地存储路径 /data/files/{kb_id}/{doc_id}/{filename}
    file_size BIGINT,
    file_type VARCHAR(50),                   -- pdf/docx/txt/png 等
    folder_path VARCHAR(200) DEFAULT '/',    -- 文件夹路径，如 /教学资料/2026春季/
    scope_level INT NOT NULL,                -- ⭐ 文档独立权限层级
    org_code VARCHAR(20) NOT NULL,         -- ⭐ 文档所属组织
    status VARCHAR(20) DEFAULT 'parsing' CHECK (status IN ('uploading', 'parsing', 'ready', 'failed')),
    current_version INT DEFAULT 1,
    parse_error TEXT,                      -- 解析失败原因
    created_by INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 约束：文档权限不能高于知识库权限（数字越大范围越窄，所以文档 >= 知识库）
    CONSTRAINT doc_scope_check CHECK (scope_level >= (SELECT scope_level FROM knowledge_base WHERE id = kb_id))
);

```

### 3.6 文档版本

```sql
CREATE TABLE doc_version (
    id SERIAL PRIMARY KEY,
    doc_id INT NOT NULL REFERENCES kb_document(id) ON DELETE CASCADE,
    version_no INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    change_note TEXT,
    created_by INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW()
);

```

### 3.7 文本分块 + 向量（核心表）

```sql
-- 启用 pgvector
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE doc_chunk (
    id SERIAL PRIMARY KEY,
    doc_id INT NOT NULL REFERENCES kb_document(id) ON DELETE CASCADE,
    kb_id INT NOT NULL,
    content TEXT NOT NULL,
    meta JSONB DEFAULT '{}',                 -- {page: 15, paragraph: 3, chapter: "第二章", total_pages: 120}
    embedding VECTOR(1024),                  -- 维度通过环境变量配置，默认 1024
    scope_level INT NOT NULL,              -- 冗余：加速权限过滤
    org_code VARCHAR(20) NOT NULL,         -- 冗余：加速权限过滤
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW 索引（pgvector 高性能近似最近邻搜索）
CREATE INDEX ON doc_chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunk_doc ON doc_chunk(doc_id);
CREATE INDEX idx_chunk_kb ON doc_chunk(kb_id);

```

### 3.8 机器人配置（自建引擎，替代 Dify）

```sql
CREATE TABLE bot_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar VARCHAR(200),
    prompt TEXT NOT NULL,                    -- 系统提示词
    welcome_msg TEXT,
    model VARCHAR(50) DEFAULT 'deepseek-chat',
    creator_id INT NOT NULL REFERENCES sys_user(id),
    share_type VARCHAR(20) DEFAULT 'private' CHECK (share_type IN ('public', 'private', 'assigned')),
    max_context_rounds INT DEFAULT 5,
    status VARCHAR(20) DEFAULT 'active',
    is_official BOOLEAN DEFAULT false,       -- ⭐ true 表示官方预置机器人
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 机器人关联知识库（多对多，替代数组字段）
CREATE TABLE bot_knowledge_base (
    id SERIAL PRIMARY KEY,
    bot_id INT NOT NULL REFERENCES bot_config(id) ON DELETE CASCADE,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, kb_id)
);

-- 机器人指定可见人员（share_type=assigned 时生效）
CREATE TABLE bot_assigned_user (
    id SERIAL PRIMARY KEY,
    bot_id INT NOT NULL REFERENCES bot_config(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES sys_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, user_id)
);

```

### 3.9 外部智能体链接（仅配置，无业务逻辑）

```sql
CREATE TABLE external_agent (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(200),
    category VARCHAR(50),                    -- business/consult/teaching/data
    target_url VARCHAR(500) NOT NULL,        -- 跳转链接
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

```

### 3.10 对话记录

```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    bot_id INT REFERENCES bot_config(id),    -- NULL 表示直接知识库问答
    kb_id INT,
    user_id INT NOT NULL REFERENCES sys_user(id),
    question TEXT NOT NULL,
    answer TEXT,

    sources JSONB DEFAULT '[ ]',             -- 引用溯源信息 [{doc_name, page, content}]

    is_useful BOOLEAN,                     -- 用户反馈：有用/无用
    created_at TIMESTAMP DEFAULT NOW()
);

```
---

## 四、后端项目结构

```plaintext
backend/
├── main.py                    # FastAPI 入口，挂载静态文件，CORS，异常处理
├── config.py                  # 环境变量配置（Pydantic Settings）
├── database.py                # SQLAlchemy 引擎、Session、异步连接
├── models/                    # SQLAlchemy ORM 模型（与 DDL 一一对应）
│   ├── __init__.py
│   ├── user.py
│   ├── org.py
│   ├── kb.py
│   ├── document.py
│   ├── chunk.py
│   └── bot.py
├── schemas/                   # Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py
│   ├── org.py
│   ├── kb.py
│   ├── document.py
│   ├── search.py
│   ├── chat.py
│   └── bot.py
├── routers/                   # API 路由（按模块拆分）
│   ├── __init__.py
│   ├── auth.py                # POST /api/v1/auth/login, /register
│   ├── org.py                 # 组织架构 CRUD（自建维护）
│   ├── kb.py                  # 知识库管理 + 协作者
│   ├── document.py            # 文档上传/解析/版本/权限/预览
│   ├── search.py              # ⭐ 搜索网关（统一检索接口）
│   ├── chat.py                # RAG 对话 + SSE 流式（自建机器人引擎）
│   ├── bot.py                 # 自建机器人 + 官方机器人管理
│   ├── external_agent.py      # 外部智能体链接配置
│   └── admin.py               # 管理后台
├── services/                  # 业务逻辑层
│   ├── __init__.py
│   ├── parser.py              # 文档解析（PDF/Word/txt）
│   ├── embedding.py           # 调用 Embedding API
│   ├── rag.py                 # ⭐ 检索 + 权限过滤 + 溯源组装
│   ├── llm.py                 # DeepSeek API 封装（SSE 流式）
│   ├── bot_engine.py          # ⭐ 机器人配置加载 + Prompt 组装
│   ├── permission.py          # 四级权限校验工具函数
│   └── preview.py             # ⭐ 文档预览（Word/PDF/txt 转 HTML/文本）
├── utils/
│   ├── __init__.py
│   ├── security.py            # JWT 生成/校验、密码哈希
│   └── file.py                # 文件保存、路径生成
├── alembic/                   # 数据库迁移
│   └── versions/
├── static/                    # Vue 打包后的前端文件（dist/）
├── uploads/                   # 文件存储目录（Docker 挂载 /data/files）
└── requirements.txt

```
---

## 五、核心 API 接口设计

### 5.1 认证模块

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/auth/login` | POST | 用户名密码登录，返回 JWT + 用户信息 |
| `/api/v1/auth/register` | POST | 注册（演示系统开放注册，可选组织） |
| `/api/v1/auth/me` | GET | 获取当前登录用户信息 |

**请求/响应示例：**

```json
// POST /api/v1/auth/login
{
  "username": "student01",
  "password": "123456"
}

// 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 3,
    "name": "李同学",
    "org_code": "10-01-03-02",
    "scope_code": "10-01-03-02",
    "role": "viewer"
  }
}

```

### 5.2 组织架构（自建维护）

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/org/tree` | GET | 获取完整组织架构树 |
| `/api/v1/org` | POST | 创建组织节点（管理员） |
| `/api/v1/org/{id}` | PUT/DELETE | 修改/删除 |

> 演示系统通过管理后台手动维护组织架构，无需 LDAP/SSO 同步。

### 5.3 知识库管理

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/kb` | GET | 知识库广场列表（按权限过滤） |
| `/api/v1/kb` | POST | 创建知识库 |
| `/api/v1/kb/{id}` | GET | 知识库详情 + 文档列表（已按文档权限过滤） |
| `/api/v1/kb/{id}/collaborators` | GET/POST/DELETE | 协作者管理 |
| `/api/v1/kb/{id}/preview` | POST | 效果预览（输入问题，返回检索片段） |

**创建知识库请求：**

```json
{
  "name": "计算机学院资料库",
  "description": "院内共享资料",
  "scope_level": 2,          // 院级
  "org_code": "10-01-00-00"
}

```

### 5.4 文档管理（核心）

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/kb/{kb_id}/documents` | GET | 文档列表（按 folder\_path 树形或平铺） |
| `/api/v1/kb/{kb_id}/documents` | POST | 上传文档 ⭐ 需传 `scope_level` 和 `org_code` |
| `/api/v1/documents/{id}` | GET | 文档详情 + 版本历史 |
| `/api/v1/documents/{id}` | PUT | 修改文档信息（含权限） |
| `/api/v1/documents/{id}/versions` | GET | 版本历史 |
| `/api/v1/documents/{id}/rollback` | POST | 回滚到指定版本 |
| `/api/v1/documents/{id}/preview` | GET | 在线预览（返回 HTML/文本/PDF 流） |
| `/api/v1/documents/{id}/download` | GET | 下载原始文件 |

**上传文档请求（multipart/form-data）：**

```plaintext
file: [二进制文件]
scope_level: 3              // ⭐ 文档独立权限：专业级
org_code: "10-01-03-00"     // ⭐ 所属组织：软件工程专业
folder_path: "/教学资料/"

```

**文档权限校验规则（后端硬编码）：**

```python
# 上传/修改时校验
if doc_scope_level < kb_scope_level:
    raise HTTPException(400, "文档权限范围不能大于知识库权限范围")
# 即：院级知识库(2)内，文档只能是院级(2)/专业级(3)/岗位级(4)，不能设为校级(1)

```

**在线预览方案：**

| 文件类型 | 后端处理 | 前端展示 |
| --- | --- | --- |
| **PDF** | 返回文件流 `Content-Type: application/pdf` | `<iframe src="...">` 或 PDF.js |
| **Word (docx)** | `python-docx` 提取文本 + 基础样式 → 返回 HTML 字符串 | `v-html` 渲染或富文本组件 |
| **txt** | 直接读取文本内容返回 | `<pre>` 标签或文本组件 |
| **其他** | 不支持预览，提示下载 | \- |

### 5.5 搜索网关（⭐ 核心接口）

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/search` | POST | 统一检索接口，供内部 RAG 调用 |

**请求：**

```json
{
  "query": "请假流程需要什么材料",
  "kb_ids": [1, 2],          // 指定搜索的知识库范围
  "top_k": 5                 // 返回片段数量
}

```

**响应：**

```json
{
  "chunks": [
    {
      "content": "学生请假需提交书面申请...",
      "meta": {"page": 15, "paragraph": 3, "chapter": "第三章第二节"},
      "doc_id": 12,
      "doc_name": "学生手册2026版.pdf",
      "kb_id": 1,
      "score": 0.89
    }
  ],
  "total": 5
}

```

**后端搜索逻辑（修正版）：**

```python
async def search(query: str, user: User, kb_ids: list[int], top_k: int = 5):
    # 1. 获取 query 的 embedding
    query_vec = await get_embedding(query)
    
    # 2. 解析用户层级
    user_level = get_level_from_scope(user.scope_code)  # 1/2/3/4
    user_org_prefix = get_org_prefix(user.scope_code, user_level)  # 如 "10-01"
    
    # 3. 先过滤知识库权限（用户只能搜自己可见的知识库）
    # 规则：知识库 scope_level >= user_level（上级可看下级知识库，数字越大范围越窄）
    allowed_kb_ids = await filter_kb_by_permission(user, kb_ids)
    
    # 4. ⭐ pgvector 检索 + 双重权限过滤 SQL（修正后）
    sql = """
    SELECT 
        c.id, c.content, c.meta, c.doc_id, c.kb_id,
        d.name as doc_name, d.scope_level, d.org_code,
        1 - (c.embedding <=> :query_vec) AS score
    FROM doc_chunk c
    JOIN kb_document d ON c.doc_id = d.id
    JOIN knowledge_base kb ON c.kb_id = kb.id
    WHERE c.kb_id = ANY(:kb_ids)
      AND d.status = 'ready'
      AND kb.status = 'published'
      AND (
          -- ⭐ 文档权限 >= 用户层级（上级可看下级，数字越大范围越窄）
          d.scope_level >= :user_level
          -- 且组织前缀匹配（确保是同一条分支）
          AND d.org_code LIKE :user_org_prefix || '%'
      )
    ORDER BY c.embedding <=> :query_vec
    LIMIT :top_k;
    """
    
    # user_org_prefix 生成规则：根据用户层级截取
    # 校级(10-00-00-00) -> 前缀 "10"（看全校）
    # 院级(10-01-00-00) -> 前缀 "10-01"（看本院）
    # 专业级(10-01-03-00) -> 前缀 "10-01-03"（看本专业）
    # 岗位级(10-01-03-02) -> 前缀 "10-01-03-02"（只看本岗位）
    
    return await db.fetch(sql, ...)

```

### 5.6 RAG 对话（自建机器人引擎）

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/chat` | POST | 通用对话（SSE 流式） |
| `/api/v1/chat/bot/{bot_id}` | POST | 通过机器人对话（SSE 流式） |

**请求：**

```json
{
  "question": "请假流程需要什么材料",
  "kb_ids": [1],             // 通用对话时指定
  "history": [               // 可选：上下文
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}

```

**SSE 流式响应格式：**

```plaintext
data: {"type": "thinking", "content": "正在检索相关资料..."}

data: {"type": "source", "content": [{"doc_name": "学生手册2026版", "page": 15}]}

data: {"type": "answer", "content": "根据《学生手册2026版》第15页规定..."}

data: {"type": "done", "content": "【来源：《学生手册2026版》第15页】"}

```

**后端 RAG 流程（自建引擎）：**

```python
async def chat_stream(request: ChatRequest, user: User, bot_id: int = None):
    # 1. 加载机器人配置（如果是机器人对话）
    bot = None
    kb_ids = request.kb_ids
    system_prompt = "你是一位学校智能助手。基于以下资料回答问题。"
    
    if bot_id:
        bot = await load_bot_config(bot_id, user)
        if not bot:
            raise HTTPException(404, "机器人不存在或无权访问")
        kb_ids = bot.kb_ids  # 从 bot_knowledge_base 关联表获取
        system_prompt = bot.prompt
    
    # 2. 检索（已带权限过滤）
    chunks = await search(request.question, user, kb_ids, top_k=5)
    
    if not chunks:
        yield format_sse("answer", "您当前权限范围内无相关资料，如需更多信息请联系管理员。")
        yield format_sse("done", "")
        return
    
    # 3. 组装 Prompt（带溯源指令）
    context = "\n\n".join([
        f"[来源：{c['doc_name']} 第{c['meta'].get('page', 'N')}页]\n{c['content']}"
        for c in chunks
    ])
    
    full_prompt = f"""{system_prompt}

规则：
1. 必须基于提供的资料回答，不确定时明确告知
2. 每个关键信息必须标注来源，格式：【来源：《文档名》第X页】
3. 如果资料不足以回答，说"根据现有资料无法完全回答"

资料：
{context}"""

    # 4. 调 DeepSeek API（SSE 流式）
    async for token in stream_deepseek(full_prompt, request.question, request.history):
        yield format_sse("answer", token)
    
    # 5. 返回溯源信息
    sources = [{"doc_name": c["doc_name"], "page": c["meta"].get("page"), "content": c["content"][:200]} for c in chunks]
    yield format_sse("done", json.dumps({"sources": sources}))

```

### 5.7 机器人管理（自建引擎）

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/bots` | GET | 我的机器人列表 + 官方机器人列表 |
| `/api/v1/bots` | POST | 创建机器人 |
| `/api/v1/bots/{id}` | GET/PUT/DELETE | 详情/修改/删除 |
| `/api/v1/bots/{id}/preview` | POST | 预览测试 |
| `/api/v1/bots/public` | GET | 广场公开机器人列表 |
| `/api/v1/bots/official` | GET | 官方预置机器人列表（管理员维护） |

**创建机器人请求：**

```json
{
  "name": "软件工程课程助教",
  "description": "回答课程相关问题",
  "prompt": "你是一位软件工程课程助教。必须基于知识库回答，不确定时告知学生联系老师。",
  "welcome_msg": "你好！我是软件工程课程助教，请问有什么问题？",
  "model": "deepseek-chat",
  "kb_ids": [3, 4],
  "share_type": "public"     // public/private/assigned
}

```
> **官方机器人**：管理员在后台设置 `is_official=true`，直接出现在广场，无需审核流程。

### 5.8 外部智能体

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/external-agents` | GET | 广场外部智能体列表 |
| `/api/v1/external-agents` | POST | 管理员添加链接（管理员） |

**前端行为：** 点击卡片直接 `window.open(target_url)` 跳转，不经过后端业务逻辑。

---

## 六、关键业务逻辑详解

### 6.1 四级权限校验工具（修正版）

```python
# services/permission.py

def get_level_from_scope(scope_code: str) -> int:
    """从 scope_code 解析层级"""
    parts = scope_code.split('-')
    if parts[1] == '00' and parts[2] == '00' and parts[3] == '00':
        return 1  # 校级
    elif parts[2] == '00' and parts[3] == '00':
        return 2  # 院级
    elif parts[3] == '00':
        return 3  # 专业级
    else:
        return 4  # 岗位级

def get_org_prefix(scope_code: str, level: int) -> str:
    """获取组织前缀，用于 SQL LIKE 匹配"""
    parts = scope_code.split('-')
    if level == 1:
        return parts[0]  # "10"
    elif level == 2:
        return f"{parts[0]}-{parts[1]}"  # "10-01"
    elif level == 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"  # "10-01-03"
    else:
        return scope_code  # "10-01-03-02"

def can_access(user_scope: str, target_scope: str) -> bool:
    """判断用户是否能访问目标层级资源"""
    user_level = get_level_from_scope(user_scope)
    target_level = get_level_from_scope(target_scope)
    
    # 上级可看下级，同级需完全匹配，下级不可看上级
    if user_level < target_level:
        return target_scope.startswith(get_org_prefix(user_scope, user_level))
    elif user_level == target_level:
        return user_scope == target_scope
    else:
        return False

# 知识库/文档 SQL 过滤条件生成
def build_permission_filter(user_scope: str, table_alias: str = "d") -> tuple:
    """返回 (scope_level, org_prefix) 用于 SQL 参数绑定"""
    user_level = get_level_from_scope(user_scope)
    user_org_prefix = get_org_prefix(user_scope, user_level)
    return user_level, user_org_prefix

```

### 6.2 文档解析服务

```python
# services/parser.py

async def parse_file(file_path: str, file_type: str) -> list[dict]:
    """
    解析文件，返回分块列表
    每个块: {content: str, meta: {page: int, ...}}
    """
    if file_type == 'pdf':
        return parse_pdf(file_path)
    elif file_type in ['doc', 'docx']:
        return parse_word(file_path)
    elif file_type == 'txt':
        return parse_txt(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

def parse_pdf(file_path: str) -> list[dict]:
    import fitz  # PyMuPDF
    doc = fitz.open(file_path)

    chunks = [ ]

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            chunks.append({
                "content": text,
                "meta": {"page": page_num + 1, "type": "pdf"}
            })
    return chunks

def parse_word(file_path: str) -> list[dict]:
    from docx import Document
    doc = Document(file_path)

    chunks = [ ]

    for i, para in enumerate(doc.paragraphs, 1):
        if para.text.strip():
            chunks.append({
                "content": para.text,
                "meta": {"paragraph": i, "type": "docx"}
            })
    return chunks

def parse_txt(file_path: str) -> list[dict]:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = [ ]

    paragraphs = text.split('\n\n')
    for i, p in enumerate(paragraphs, 1):
        if p.strip():
            chunks.append({
                "content": p.strip(),
                "meta": {"paragraph": i, "type": "txt"}
            })
    return chunks

```

### 6.3 文档预览服务

```python
# services/preview.py

from fastapi.responses import HTMLResponse, FileResponse
from docx import Document
import fitz

async def generate_preview(file_path: str, file_type: str):
    """生成预览内容"""
    if file_type == 'pdf':
        # 直接返回文件流，前端用 iframe/PDF.js 渲染
        return FileResponse(file_path, media_type="application/pdf")
    
    elif file_type in ['doc', 'docx']:
        # 提取文本 + 基础 HTML 包装
        doc = Document(file_path)
        html_parts = ['<<div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px;">']
        for para in doc.paragraphs:
            if para.text.strip():
                html_parts.append(f"<p>{para.text}</p>")
        html_parts.append('</div>')
        return HTMLResponse(content="".join(html_parts))
    
    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html = f'<pre style="white-space: pre-wrap; padding: 20px;">{content}</pre>'
        return HTMLResponse(content=html)
    
    else:
        raise HTTPException(400, "该文件类型暂不支持在线预览，请下载查看")

```

### 6.4 版本对比

```python
# 使用 Python 内置 difflib
import difflib

def compare_versions(old_text: str, new_text: str) -> str:
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        lineterm=''
    )
    return '\n'.join(diff)

```
---

## 七、前端页面结构

```plaintext
src/
├── api/                       # Axios 封装，按模块分文件
│   ├── auth.ts
│   ├── kb.ts
│   ├── document.ts
│   ├── search.ts
│   ├── chat.ts
│   └── bot.ts
├── components/
│   ├── Layout.vue             # 主布局：侧边栏 + 顶部导航
│   ├── KnowledgeCard.vue      # 知识库广场卡片
│   ├── DocumentList.vue       # 文档列表（树形/平铺）
│   ├── ChatWindow.vue         # 对话窗口（SSE 接收）
│   ├── SourcePopover.vue      # 引用溯源悬浮卡片
│   ├── BotForm.vue            # 机器人配置表单
│   └── PreviewPanel.vue       # ⭐ 文档预览面板（PDF/Word/txt）
├── views/
│   ├── Login.vue
│   ├── Plaza.vue              # 广场首页（知识库 + 外部智能体 + 官方机器人）
│   ├── KnowledgeBaseDetail.vue # 知识库详情（文档列表 + 内嵌问答）
│   ├── KnowledgeBaseManage.vue # 知识库管理（创建/编辑/协作者）
│   ├── DocumentUpload.vue     # 文档上传（含权限选择）
│   ├── DocumentVersion.vue    # 文档版本历史 + 对比
│   ├── Workshop.vue           # 工坊（自建机器人列表 + 创建）
│   ├── BotChat.vue            # 机器人对话页
│   ├── Admin/
│   │   ├── UserManage.vue
│   │   ├── OrgManage.vue      # ⭐ 组织架构管理（自建）
│   │   └── BotManage.vue      # ⭐ 官方机器人管理
│   └── Profile.vue
├── stores/
│   ├── user.ts                # Pinia：用户信息 + scope_code
│   └── chat.ts                # Pinia：对话历史缓存
├── router/
│   └── index.ts               # 路由守卫：权限校验
├── utils/
│   ├── request.ts             # Axios 拦截器（JWT、错误处理）
│   └── permission.ts          # 前端权限判断工具
└── App.vue

```

**预览组件实现要点：**

| 类型 | 前端组件 | 实现方式 |
| --- | --- | --- |
| PDF | `<iframe>` 或 PDF.js | `<iframe :src="previewUrl" width="100%" height="600px">` |
| Word/txt | `<div v-html="htmlContent">` | 后端返回 HTML 字符串，前端直接渲染 |

---

## 八、Docker Compose 部署配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:v0.5.1
    container_name: schoolai-db
    environment:
      POSTGRES_USER: ai
      POSTGRES_PASSWORD: ai123
      POSTGRES_DB: school_ai
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai -d school_ai"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: schoolai-api
    environment:
      DATABASE_URL: postgresql+asyncpg://ai:ai123@postgres:5432/school_ai
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
      EMBEDDING_API_KEY: ${EMBEDDING_API_KEY}
      EMBEDDING_API_URL: ${EMBEDDING_API_URL:-https://api.example.com/v1/embeddings}
      EMBEDDING_DIMENSION: ${EMBEDDING_DIMENSION:-1024}  # ⭐ 向量维度可配置
      FILE_STORAGE_PATH: /data/files
      JWT_SECRET: ${JWT_SECRET:-school-ai-secret-key-change-in-production}
      JWT_ALGORITHM: HS256
      JWT_EXPIRE_MINUTES: 1440
    volumes:
      - file_storage:/data/files
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pg_data:
  file_storage:

```
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```
```txt
# backend/requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.0
pydantic-settings==2.2.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
aiofiles==23.2.1
httpx==0.27.0
PyMuPDF==1.24.5
python-docx==1.1.2
beautifulsoup4==4.12.3
requests==2.32.0
numpy==1.26.4

```
---

## 九、开发里程碑（2 周演示版）

| 阶段 | 交付物 | 验收标准 |
| --- | --- | --- |
| **S1 骨架** | Docker 跑通；登录/组织架构 CRUD；基础 CRUD | 能登录，能看到组织架构树，能增删改组织 |
| **S2 知识库** | 知识库创建/广场；文档上传/解析（PDF/Word/txt）；文件夹 | 能上传 PDF/Word/txt，解析状态显示 ready |
| **S3 权限** | ⭐ 文档级权限设置；搜索网关双重过滤；权限预览 | 同库不同文档，不同用户看到不同内容；搜索 SQL 验证正确 |
| **S4 RAG** | 向量化接入；RAG 对话；引用溯源；SSE 流式 | 提问能返回答案+【来源：《文档名》第X页】 |
| **S5 前端** | 广场/知识库详情/对话页/工坊页面；在线预览 | 界面完整，PDF/Word/txt 预览正常 |
| **S6 机器人** | 自建机器人三步创建；官方机器人管理；关联知识库；广场展示 | 创建机器人后能对话，且按权限过滤 |
| **S7 版本** | 文档版本历史；回滚；对比 | 上传同名文件自动递增版本号 |
| **S8 集成** | 外部智能体链接；演示数据灌入；全流程联调 | 演示账号能走完完整流程 |

---

## 十、AI 开发提示（编码规范）

1.  **所有数据库操作使用 SQLAlchemy 2.0 异步模式**（`async_session` + `await session.execute()`）
    
2.  **所有权限判断统一调用** `**services/permission.py**` **工具函数**，禁止在路由层硬编码权限逻辑。特别注意：
    
    *   `scope_level` 数字越小权限范围越大（1校级 > 2院级 > 3专业级 > 4岗位级）
        
    *   SQL 过滤条件：`d.scope_level >= :user_level`（上级可看下级）
        
    *   必须同时带 `org_code LIKE` 前缀匹配（确保同级隔离）
        
3.  **文档解析异常必须捕获并写入** `**kb_document.parse_error**`，不阻断其他文档处理
    
4.  **Embedding 调用使用** `**httpx.AsyncClient**`，设置 30 秒超时，失败时重试 1 次。维度从环境变量 `EMBEDDING_DIMENSION` 读取，默认 1024
    
5.  **DeepSeek API 调用使用 SSE 流式**，支持前端实时打字机效果
    
6.  **前端路由守卫**：未登录跳登录页；管理员路由校验 `role === 'admin'`
    
7.  **文件上传限制**：单文件最大 50MB，禁止 `.exe/.bat/.sh` 等可执行文件
    
8.  **机器人引擎**：所有对话统一走 `chat.py` 路由，通过 `bot_id` 区分官方/自建机器人，Prompt 组装逻辑集中在 `services/bot_engine.py`
    
9.  **在线预览**：PDF 返回文件流；Word/txt 返回 HTMLResponse，禁止返回可执行内容