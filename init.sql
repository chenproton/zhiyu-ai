-- 启用 pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 组织架构
CREATE TABLE org (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    level INT NOT NULL CHECK (level IN (1,2,3,4)),
    parent_code VARCHAR(20),
    path VARCHAR(100) NOT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户
CREATE TABLE sys_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(50) NOT NULL,
    org_code VARCHAR(20) NOT NULL,
    scope_code VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer')),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 知识库
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

-- 协作者
CREATE TABLE kb_collaborator (
    id SERIAL PRIMARY KEY,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES sys_user(id),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('editor', 'viewer')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(kb_id, user_id)
);

-- 文档
CREATE TABLE kb_document (
    id SERIAL PRIMARY KEY,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    folder_path VARCHAR(200) DEFAULT '/',
    scope_level INT NOT NULL,
    org_code VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'parsing' CHECK (status IN ('uploading', 'parsing', 'ready', 'failed')),
    current_version INT DEFAULT 1,
    parse_error TEXT,
    created_by INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 文档版本
CREATE TABLE doc_version (
    id SERIAL PRIMARY KEY,
    doc_id INT NOT NULL REFERENCES kb_document(id) ON DELETE CASCADE,
    version_no INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    change_note TEXT,
    created_by INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 文本分块 + 向量
CREATE TABLE doc_chunk (
    id SERIAL PRIMARY KEY,
    doc_id INT NOT NULL REFERENCES kb_document(id) ON DELETE CASCADE,
    kb_id INT NOT NULL,
    content TEXT NOT NULL,
    meta JSONB DEFAULT '{}',
    embedding VECTOR(1024),
    scope_level INT NOT NULL,
    org_code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON doc_chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunk_doc ON doc_chunk(doc_id);
CREATE INDEX idx_chunk_kb ON doc_chunk(kb_id);

-- 机器人配置
CREATE TABLE bot_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar VARCHAR(200),
    prompt TEXT NOT NULL,
    welcome_msg TEXT,
    model VARCHAR(50) DEFAULT 'deepseek-chat',
    creator_id INT NOT NULL REFERENCES sys_user(id),
    share_type VARCHAR(20) DEFAULT 'private' CHECK (share_type IN ('public', 'private', 'assigned')),
    max_context_rounds INT DEFAULT 5,
    status VARCHAR(20) DEFAULT 'active',
    is_official BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 机器人关联知识库
CREATE TABLE bot_knowledge_base (
    id SERIAL PRIMARY KEY,
    bot_id INT NOT NULL REFERENCES bot_config(id) ON DELETE CASCADE,
    kb_id INT NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, kb_id)
);

-- 机器人指定可见人员
CREATE TABLE bot_assigned_user (
    id SERIAL PRIMARY KEY,
    bot_id INT NOT NULL REFERENCES bot_config(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES sys_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, user_id)
);

-- 外部智能体链接
CREATE TABLE external_agent (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(200),
    category VARCHAR(50),
    target_url VARCHAR(500) NOT NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 对话记录
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    bot_id INT REFERENCES bot_config(id),
    kb_id INT,
    user_id INT NOT NULL REFERENCES sys_user(id),
    question TEXT NOT NULL,
    answer TEXT,
    sources JSONB DEFAULT '[]',
    is_useful BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 活动/竞赛/招聘
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content TEXT NOT NULL,
    cover VARCHAR(500),
    category VARCHAR(50) NOT NULL CHECK (category IN ('competition', 'lecture', 'recruitment', 'activity')),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    organizer VARCHAR(100),
    location VARCHAR(200),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    registration_open BOOLEAN DEFAULT true,
    max_participants INT,
    created_by INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 活动报名
CREATE TABLE event_registration (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES event(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES sys_user(id),
    contact_info VARCHAR(200),
    remark TEXT,
    status VARCHAR(20) DEFAULT 'registered' CHECK (status IN ('registered', 'cancelled', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_id, user_id)
);

-- 点赞
CREATE TABLE user_like (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('kb', 'bot', 'news', 'event')),
    target_id INT NOT NULL,
    user_id INT NOT NULL REFERENCES sys_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(target_type, target_id, user_id)
);

-- 评分
CREATE TABLE user_rating (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('kb', 'bot', 'news', 'event')),
    target_id INT NOT NULL,
    user_id INT NOT NULL REFERENCES sys_user(id),
    score INT NOT NULL CHECK (score BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(target_type, target_id, user_id)
);

-- 评论
CREATE TABLE user_comment (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('kb', 'bot', 'news', 'event')),
    target_id INT NOT NULL,
    user_id INT NOT NULL REFERENCES sys_user(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_like_target ON user_like(target_type, target_id);
CREATE INDEX idx_rating_target ON user_rating(target_type, target_id);
CREATE INDEX idx_comment_target ON user_comment(target_type, target_id);

-- 系统配置
CREATE TABLE sys_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL DEFAULT '{}',
    description TEXT,
    updated_by INT REFERENCES sys_user(id),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 演示数据
INSERT INTO org (code, name, level, parent_code, path) VALUES
('10-00-00-00', 'XX大学', 1, NULL, '10-00-00-00'),
('10-01-00-00', '计算机学院', 2, '10-00-00-00', '10-00-00-00/10-01-00-00'),
('10-01-03-00', '软件工程专业', 3, '10-01-00-00', '10-00-00-00/10-01-00-00/10-01-03-00'),
('10-01-03-02', '软件工程实验室', 4, '10-01-03-00', '10-00-00-00/10-01-00-00/10-01-03-00/10-01-03-02'),
('10-01-05-00', '网络工程专业', 3, '10-01-00-00', '10-00-00-00/10-01-00-00/10-01-05-00');

-- 演示账号，密码均为 123456（bcrypt）
INSERT INTO sys_user (username, password, name, org_code, scope_code, role) VALUES
('admin', '$2b$12$ukJKDz/z7xJRMOtMjKuy0.Ul7Zq9P.2hrvPgNoxRdwVKYLMfKdz2y', '系统管理员', '10-00-00-00', '10-00-00-00', 'admin'),
('teacher01', '$2b$12$ukJKDz/z7xJRMOtMjKuy0.Ul7Zq9P.2hrvPgNoxRdwVKYLMfKdz2y', '张教授', '10-01-03-00', '10-01-03-00', 'editor'),
('student01', '$2b$12$ukJKDz/z7xJRMOtMjKuy0.Ul7Zq9P.2hrvPgNoxRdwVKYLMfKdz2y', '李同学', '10-01-03-02', '10-01-03-02', 'viewer'),
('student02', '$2b$12$ukJKDz/z7xJRMOtMjKuy0.Ul7Zq9P.2hrvPgNoxRdwVKYLMfKdz2y', '王同学', '10-01-05-00', '10-01-05-00', 'viewer');

-- 演示知识库
INSERT INTO knowledge_base (name, description, scope_level, org_code, owner_id, status) VALUES
('学校制度知识库', '校级通用制度文件', 1, '10-00-00-00', 1, 'published'),
('计算机学院资料库', '院内共享资料', 2, '10-01-00-00', 1, 'published'),
('软件工程专业资料库', '软件工程专业教学资料', 3, '10-01-03-00', 2, 'published'),
('网络工程专业资料库', '网络工程课程与实验资料', 3, '10-01-05-00', 1, 'published'),
('人工智能导论课程库', 'AI 导论课程讲义与案例', 3, '10-01-03-00', 1, 'published'),
('数据结构题库', '数据结构与算法习题与解析', 3, '10-01-03-00', 1, 'published'),
('操作系统实验手册', '操作系统实验指导与报告模板', 3, '10-01-03-00', 1, 'published'),
('计算机网络资料库', '计算机网络课程资料汇总', 3, '10-01-05-00', 1, 'published'),
('数据库原理知识库', '数据库课程笔记与实验数据', 3, '10-01-03-00', 2, 'published'),
('软件工程实践案例库', '软件工程项目实战案例', 3, '10-01-03-00', 1, 'published'),
('大学生心理健康手册', '心理健康知识与自助指南', 1, '10-00-00-00', 1, 'published'),
('就业指导资料集', '简历模板、招聘信息与面试经验', 1, '10-00-00-00', 1, 'published'),
('学科竞赛信息库', '竞赛通知、历年真题与组队信息', 1, '10-00-00-00', 1, 'published'),
('科研项目申报指南', '从选题到结题的全流程申报指导', 2, '10-01-00-00', 1, 'published'),
('创新创业政策库', '创业扶持、孵化资源与成功案例', 1, '10-00-00-00', 1, 'published'),
('教职工办事流程', '人事、财务、资产等教职工常用流程', 1, '10-00-00-00', 1, 'published'),
('党建工作资料库', '党内法规、组织生活与学习资料', 1, '10-00-00-00', 2, 'published'),
('国际交流项目库', '交换项目、留学申请与语言考试资讯', 1, '10-00-00-00', 1, 'published'),
('奖助学金政策库', '国家、学校与社会奖助政策解读', 1, '10-00-00-00', 2, 'published'),
('后勤保障服务库', '餐饮、物业、交通与医疗服务信息', 1, '10-00-00-00', 2, 'published'),
('校园文化活动库', '文艺、体育、讲座与社团活动资讯', 1, '10-00-00-00', 1, 'published'),
('实验室安全手册', '实验室准入、安全规范与应急处理指南', 1, '10-00-00-00', 1, 'published'),
('图书馆数字资源库', '整合中外文数据库、电子书与检索技巧', 1, '10-00-00-00', 2, 'published'),
('本科人才培养方案', '覆盖各专业培养方案、课程大纲与学分要求', 1, '10-00-00-00', 2, 'published'),
('学生手册汇编', '学生管理规定、奖惩办法与权益保障', 1, '10-00-00-00', 2, 'published');

-- 演示机器人
INSERT INTO bot_config (name, description, prompt, welcome_msg, creator_id, share_type, is_official, status) VALUES
('教务咨询助手', '解答学校教务制度相关问题', '你是一位学校教务咨询助手。基于提供的学校制度资料回答师生问题，必须标注信息来源。', '你好，我是教务咨询助手，请问有什么可以帮您？', 1, 'public', true, 'active'),
('软件工程课程助教', '回答软件工程课程相关问题', '你是一位软件工程课程助教。必须基于课程知识库回答学生问题，不确定时请告知联系老师。', '你好！我是软件工程课程助教，请问有什么问题？', 2, 'public', false, 'active'),
('数据结构学习助手', '辅助数据结构课程学习与算法训练', '你是一位数据结构学习助手。帮助学生理解数据结构概念、分析算法复杂度、提供编程练习建议。', '你好！我是数据结构学习助手，一起攻克算法难题吧。', 2, 'public', false, 'active'),
('计算机网络答疑机器人', '解答计算机网络课程相关问题', '你是一位计算机网络答疑机器人。用通俗易懂的方式解释网络协议、拓扑结构和网络安全问题。', '你好！我是计算机网络答疑机器人，请问有什么问题？', 2, 'public', false, 'active'),
('数据库设计助手', '辅助数据库设计与 SQL 编写', '你是一位数据库设计助手。帮助学生理解 ER 图、范式、SQL 查询优化等数据库核心知识。', '你好！我是数据库设计助手，数据库问题尽管问我。', 2, 'public', false, 'active'),
('操作系统概念讲解', '讲解操作系统核心概念与原理', '你是一位操作系统概念讲解员。用生动例子解释进程、线程、内存管理、文件系统等概念。', '你好！我是操作系统概念讲解员，请问想学什么？', 2, 'public', false, 'active'),
('AI 绘画创作助手', '基于文字描述生成创意图片提示词', '你是一位 AI 绘画创作助手。帮助用户撰写和优化 Stable Diffusion、Midjourney 等绘画提示词。', '你好！我是 AI 绘画创作助手，告诉我你想画什么。', 2, 'public', false, 'active'),
('英语写作润色机器人', '润色英语作文与学术写作', '你是一位英语写作润色机器人。帮助用户改进英语作文、论文摘要和邮件表达的语法与流畅度。', 'Hi! I am your English writing assistant. Paste your text and let me help.', 2, 'public', false, 'active'),
('考研规划师', '提供考研院校选择、复习规划建议', '你是一位考研规划师。根据学生专业和意向提供院校选择、复习计划和备考资料推荐。', '你好！我是考研规划师，你的考研目标是什么？', 2, 'public', false, 'active'),
('职业规划师', '结合专业与兴趣提供职业发展建议', '你是一位职业规划师。帮助学生认识自我、了解行业、制定职业发展路径。', '你好！我是职业规划师，聊聊你的职业想法吧。', 2, 'public', false, 'active'),
('心理咨询室', '提供情绪疏导与心理健康知识科普', '你是一位心理咨询助手。提供情绪疏导、压力管理和心理健康知识科普，必要时建议寻求专业帮助。', '你好！我是心理咨询助手，愿意倾听你的心声。', 1, 'public', true, 'active'),
('图书馆向导', '推荐馆藏资源、检索技巧与自习座位', '你是一位图书馆向导。帮助师生检索图书、推荐数据库、解答借阅规则和座位预约问题。', '你好！我是图书馆向导，需要找什么资料？', 1, 'public', true, 'active'),
('食堂推荐官', '汇聚各窗口口碑菜品，帮你告别选择困难', '你是一位食堂推荐官。根据口味偏好推荐校园食堂菜品，并告知营业时间和排队情况。', '你好！我是食堂推荐官，今天想吃什么？', 1, 'public', true, 'active'),
('社团招新助手', '介绍社团活动、报名流程与面试技巧', '你是一位社团招新助手。介绍学校各社团特色、招新时间和报名流程，帮助学生找到感兴趣的社团。', '你好！我是社团招新助手，想了解哪个社团？', 1, 'public', true, 'active'),
('运动打卡教练', '制定训练计划，记录运动数据，激励坚持', '你是一位运动打卡教练。根据学生体能目标制定训练计划，提供运动知识和打卡提醒。', '你好！我是运动打卡教练，一起动起来吧！', 1, 'public', true, 'active'),
('失物招领员', '登记失物信息，匹配招领线索', '你是一位失物招领员。帮助失主登记遗失物品信息，匹配招领线索，提供找回建议。', '你好！我是失物招领员，请描述你丢失的物品。', 2, 'public', false, 'active'),
('二手交易助手', '发布与浏览校园二手物品信息', '你是一位校园二手交易助手。帮助用户规范发布二手物品信息，提供交易安全提示。', '你好！我是二手交易助手，有什么物品要出手？', 2, 'public', false, 'active'),
('校园导航', '提供教学楼、宿舍、食堂路线指引', '你是一位校园导航助手。为师生提供校内路线指引、建筑位置和周边生活服务信息。', '你好！我是校园导航，要去哪里？', 1, 'public', true, 'active'),
('请假流程助手', '指导学生完成请假申请与审批流程', '你是一位请假流程助手。指导学生了解请假类型、填写申请、提交材料和跟踪审批进度。', '你好！我是请假流程助手，需要请假吗？', 1, 'public', true, 'active'),
('IT服务台', '解决账号、网络、软件常见问题', '你是一位 IT 服务台助手。帮助师生解决校园网、邮箱、VPN、软件安装等常见信息技术问题。', '你好！我是 IT 服务台，遇到什么技术问题？', 1, 'public', true, 'active'),
('财务小助手', '解答报销、缴费、学费相关疑问', '你是一位财务小助手。解答学费缴纳、报销流程、奖助学金发放等财务相关问题。', '你好！我是财务小助手，有什么财务问题？', 1, 'public', true, 'active'),
('班级小管家', '管理班级通知、作业提醒与投票收集', '你是一位班级小管家。帮助班委发布通知、收集作业、组织投票和整理班级活动信息。', '你好！我是班级小管家，有什么班级事务需要处理？', 2, 'public', false, 'active'),
('古诗小达人', '诗词赏析、典故解读、飞花令对战', '你是一位古诗小达人。帮助学生赏析古诗词、解读典故，还可以陪你玩飞花令。', '你好！我是古诗小达人，今日想读哪首诗？', 2, 'public', false, 'active'),
('面试模拟官', '模拟真实面试场景，提升应答能力', '你是一位面试模拟官。根据目标岗位模拟面试问题，提供回答建议和点评。', '你好！我是面试模拟官，准备面试哪个岗位？', 2, 'public', false, 'active'),
('校园摄影师', '分享校园风光与拍摄技巧，发现身边的美', '你是一位校园摄影助手。分享校园拍摄机位、构图技巧和后期修图建议。', '你好！我是校园摄影助手，想拍出好看的校园照片吗？', 2, 'public', false, 'active');

INSERT INTO bot_knowledge_base (bot_id, kb_id) VALUES
(1,1),(2,3),(3,5),(4,8),(5,9),(6,7),(7,1),(8,1),(9,13),(10,13),(11,11),(12,12),(13,20),(14,20),(15,11),(16,1),(17,1),(18,1),(19,1),(20,2),(21,2),(22,24),(23,24),(24,13),(25,15);

-- 演示外部智能体
INSERT INTO external_agent (name, description, category, target_url, sort_order) VALUES
('智慧校园门户', '学校官方智慧校园入口', 'business', 'https://example.com/campus', 1),
('图书馆检索', '在线图书馆资源检索', 'data', 'https://example.com/library', 2);

-- 演示活动与竞赛
INSERT INTO event (title, summary, content, cover, category, status, organizer, location, start_time, end_time, registration_open, max_participants, created_by) VALUES
('2026 全国大学生 AI 创新应用大赛', '面向全国高校学生的 AI 应用创新竞赛，优秀作品可获孵化支持。', '面向全国高校学生的 AI 应用创新竞赛，优秀作品可获孵化支持。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/1.jpg', 'competition', 'published', '校团委', '大学生活动中心', '2026-07-10 09:00:00', '2026-07-12 18:00:00', true, 200, 1),
('人工智能前沿讲座：大模型与教育变革', '邀请知名专家分享大模型技术进展及其对教育的影响。', '邀请知名专家分享大模型技术进展及其对教育的影响。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/2.jpg', 'lecture', 'published', '计算机学院', '图书馆报告厅', '2026-07-15 14:00:00', '2026-07-15 16:30:00', true, 300, 1),
('2026 届毕业生夏季招聘会', '汇聚百家优质企业，为毕业生提供就业岗位。', '汇聚百家优质企业，为毕业生提供就业岗位。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/3.jpg', 'recruitment', 'published', '招生就业处', '体育馆主馆', '2026-07-05 09:00:00', '2026-07-05 16:00:00', true, 1000, 1),
('校园 AI 创意市集', '展示师生 AI 创意作品，体验智能应用。', '展示师生 AI 创意作品，体验智能应用。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/4.jpg', 'activity', 'published', '信息中心', '梧桐大道', '2026-07-08 10:00:00', '2026-07-08 18:00:00', true, 500, 1),
('数据结构与算法编程挑战赛', '提升学生算法能力，选拔省赛国赛选手。', '提升学生算法能力，选拔省赛国赛选手。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/5.jpg', 'competition', 'published', 'ACM 协会', '计算机楼 301', '2026-07-20 13:00:00', '2026-07-20 17:00:00', true, 150, 1),
('AI 绘画工作坊', '学习 Stable Diffusion 提示词工程与图像创作。', '学习 Stable Diffusion 提示词工程与图像创作。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/6.jpg', 'lecture', 'published', '艺术学院', '艺术楼 202', '2026-07-22 14:00:00', '2026-07-22 17:00:00', true, 80, 1),
('计算机学院 2026 暑期实习双选会', '为计算机相关专业学生提供实习岗位。', '为计算机相关专业学生提供实习岗位。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/7.jpg', 'recruitment', 'published', '计算机学院', '计算机楼大厅', '2026-07-25 09:00:00', '2026-07-25 12:00:00', true, 400, 1),
('新生 AI 体验日', '面向新生的 AI 产品体验与互动活动。', '面向新生的 AI 产品体验与互动活动。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/8.jpg', 'activity', 'published', '信息中心', '图书馆广场', '2026-08-28 09:00:00', '2026-08-28 17:00:00', true, 800, 1),
('智能机器人设计大赛', '机器人设计与编程竞赛，激发工程实践热情。', '机器人设计与编程竞赛，激发工程实践热情。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/9.jpg', 'competition', 'published', '工程训练中心', '工训楼 105', '2026-08-05 08:00:00', '2026-08-06 18:00:00', true, 120, 1),
('学术论文写作与 AI 工具应用讲座', '提升学生学术写作能力与 AI 工具使用规范意识。', '提升学生学术写作能力与 AI 工具使用规范意识。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/10.jpg', 'lecture', 'published', '图书馆', '图书馆 501', '2026-08-12 15:00:00', '2026-08-12 17:00:00', true, 200, 1),
('互联网大厂校园宣讲会', '头部互联网企业到校宣讲招聘。', '头部互联网企业到校宣讲招聘。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/11.jpg', 'recruitment', 'published', '招生就业处', '学术报告厅', '2026-08-18 14:00:00', '2026-08-18 17:00:00', true, 600, 1),
('AI 伦理与治理圆桌论坛', '探讨 AI 伦理、算法公平与数据治理议题。', '探讨 AI 伦理、算法公平与数据治理议题。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/12.jpg', 'activity', 'published', '马克思主义学院', '行政楼 305', '2026-08-22 14:00:00', '2026-08-22 17:00:00', true, 100, 1),
('创新创业项目路演大赛', '选拔优秀创新创业项目进行路演与融资对接。', '选拔优秀创新创业项目进行路演与融资对接。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/13.jpg', 'competition', 'published', '创新创业学院', '科创园路演厅', '2026-09-05 13:00:00', '2026-09-05 18:00:00', true, 200, 1),
('Python 与数据分析入门培训', '面向零基础学生的 Python 与数据分析入门课程。', '面向零基础学生的 Python 与数据分析入门课程。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/14.jpg', 'lecture', 'published', '数据科学协会', '理科楼 405', '2026-09-10 18:30:00', '2026-09-10 21:00:00', true, 120, 1),
('金融科技企业专场招聘会', '银行、证券、保险等金融机构到校招聘。', '银行、证券、保险等金融机构到校招聘。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/15.jpg', 'recruitment', 'published', '招生就业处', '经管楼报告厅', '2026-09-15 14:00:00', '2026-09-15 17:00:00', true, 400, 1),
('校园 AI 马拉松 Hackathon', '48 小时 AI 应用开发挑战赛。', '48 小时 AI 应用开发挑战赛。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/16.jpg', 'activity', 'published', '团委', '创客空间', '2026-09-20 09:00:00', '2026-09-21 21:00:00', true, 160, 1),
('全国大学生数学建模竞赛校内选拔', '选拔数学建模竞赛参赛队伍。', '选拔数学建模竞赛参赛队伍。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/17.jpg', 'competition', 'published', '数学学院', '数学楼 201', '2026-09-25 08:00:00', '2026-09-25 20:00:00', true, 100, 1),
('AI 助力科研：文献检索与分析工具培训', '介绍 AI 文献助手、知识图谱等科研工具。', '介绍 AI 文献助手、知识图谱等科研工具。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/18.jpg', 'lecture', 'published', '科研处', '图书馆报告厅', '2026-09-28 14:00:00', '2026-09-28 16:30:00', true, 250, 1),
('教育行业专场招聘会', '中小学校、教育机构到校招聘师范类毕业生。', '中小学校、教育机构到校招聘师范类毕业生。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/19.jpg', 'recruitment', 'published', '招生就业处', '师范楼大厅', '2026-10-10 09:00:00', '2026-10-10 12:00:00', true, 300, 1),
('智慧校园开放体验周', '一周时间体验学校各类智慧校园服务。', '一周时间体验学校各类智慧校园服务。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/20.jpg', 'activity', 'published', '信息中心', '校园各点位', '2026-10-15 09:00:00', '2026-10-21 17:00:00', true, 2000, 1),
('网络安全技能竞赛', 'CTF 形式的网络安全技能竞赛。', 'CTF 形式的网络安全技能竞赛。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/21.jpg', 'competition', 'published', '网络工程协会', '网络楼 302', '2026-10-25 09:00:00', '2026-10-25 17:00:00', true, 120, 1),
('大模型应用开发实战工作坊', '手把手教学大模型应用开发。', '手把手教学大模型应用开发。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/22.jpg', 'lecture', 'published', 'AI 学院', 'AI 楼 601', '2026-10-28 14:00:00', '2026-10-28 18:00:00', true, 80, 1),
('智能制造企业专场招聘会', '智能制造、工业互联网领域企业招聘。', '智能制造、工业互联网领域企业招聘。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/23.jpg', 'recruitment', 'published', '招生就业处', '工科楼大厅', '2026-11-05 14:00:00', '2026-11-05 17:00:00', true, 350, 1),
('校园 AI 歌手大赛', 'AI 辅助音乐创作与演唱展示活动。', 'AI 辅助音乐创作与演唱展示活动。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/24.jpg', 'activity', 'published', '学生会', '大学生活动中心', '2026-11-11 18:00:00', '2026-11-11 21:00:00', true, 500, 1),
('程序设计天梯赛校内选拔', '选拔程序设计竞赛队员。', '选拔程序设计竞赛队员。 欢迎广大师生踊跃报名参加，具体安排请留意后续通知。', 'https://example.com/event/25.jpg', 'competition', 'published', 'ACM 协会', '计算机楼 401', '2026-11-18 13:00:00', '2026-11-18 17:00:00', true, 150, 1);

