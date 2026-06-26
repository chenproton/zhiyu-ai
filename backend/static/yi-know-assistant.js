(function () {
  'use strict';

  const SVG = {
    book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    bot: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    external: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
    sparkles: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    layoutGrid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    chevronRight: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
    messageCircle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
    loader2: '<svg class="yka-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>',
  };

  const COLORS = {
    amber: { bg: '#fffbeb', text: '#d97706', border: '#fde68a' },
    emerald: { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' },
    blue: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
    rose: { bg: '#fff1f2', text: '#e11d48', border: '#fecdd3' },
    indigo: { bg: '#eef2ff', text: '#4f46e5', border: '#c7d2fe' },
    cyan: { bg: '#ecfeff', text: '#0891b2', border: '#a5f3fc' },
    violet: { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe' },
    fuchsia: { bg: '#fdf4ff', text: '#c026d3', border: '#f5d0fe' },
    purple: { bg: '#faf5ff', text: '#9333ea', border: '#e9d5ff' },
  };

  const COLOR_KEYS = Object.keys(COLORS);
  const API_BASE = (typeof API !== 'undefined' ? API : '') || '';

  function getToken() {
    if (typeof token !== 'undefined' && token) return token;
    try {
      return localStorage.getItem('token') || '';
    } catch (e) {
      return '';
    }
  }

  async function apiRequest(path) {
    const headers = {};
    const t = getToken();
    if (t) headers['Authorization'] = `Bearer ${t}`;
    const res = await fetch(`${API_BASE}${path}`, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json();
  }

  function mapKb(kb, index) {
    const tags = [];
    if (kb.org_name) tags.push(kb.org_name);
    if (kb.status === 'published') tags.push('已发布');
    else if (kb.status) tags.push(kb.status);
    return {
      id: `kb-${kb.id}`,
      category: 'knowledge',
      title: kb.name || '未命名知识库',
      desc: kb.description || '暂无描述',
      tags,
      icon: 'book',
      color: COLOR_KEYS[index % COLOR_KEYS.length],
      originalId: kb.id,
      originalType: 'kb',
    };
  }

  function mapBot(bot, index) {
    const tags = [];
    if (bot.is_official) tags.push('官方');
    else if (bot.share_type === 'public') tags.push('公开');
    else if (bot.share_type) tags.push(bot.share_type);
    if (bot.status === 'active') tags.push('已上架');
    else if (bot.status) tags.push(bot.status);
    return {
      id: `bot-${bot.id}`,
      category: 'agent',
      title: bot.name || '未命名智能体',
      desc: bot.description || '暂无描述',
      tags,
      icon: 'bot',
      color: COLOR_KEYS[(index + 4) % COLOR_KEYS.length],
      originalId: bot.id,
      originalType: 'bot',
    };
  }

  async function loadResources() {
    const t = getToken();
    if (!t) {
      return { resources: RESOURCES, source: 'mock' };
    }
    try {
      const [kbs, bots] = await Promise.all([
        apiRequest('/api/v1/kb').catch(() => []),
        apiRequest('/api/v1/bots/public').catch(() => []),
      ]);
      const platforms = RESOURCES.filter((r) => r.category === 'platform');
      const kbResources = (Array.isArray(kbs) ? kbs : []).map(mapKb);
      const botResources = (Array.isArray(bots) ? bots : []).map(mapBot);
      return {
        resources: [...kbResources, ...botResources, ...platforms],
        source: 'real',
      };
    } catch (e) {
      return { resources: RESOURCES, source: 'mock' };
    }
  }

  const RESOURCES = [
    { id: 'finance-kb', category: 'knowledge', title: '金融专业知识库', desc: '覆盖银行、证券、保险等金融岗位核心知识与案例。', tags: ['金融', '专业'], icon: 'book', color: 'amber' },
    { id: 'logistics-kb', category: 'knowledge', title: '物流专业知识库', desc: '仓储、运输、供应链管理等物流领域知识沉淀。', tags: ['物流', '专业'], icon: 'book', color: 'emerald' },
    { id: 'cnc-kb', category: 'knowledge', title: '数控实训知识库', desc: '数控加工、设备操作与维护等实训资源汇总。', tags: ['数控', '实训'], icon: 'book', color: 'blue' },
    { id: 'hotel-kb', category: 'knowledge', title: '酒店管理案例库', desc: '前厅、客房、餐饮等酒店服务真实教学案例。', tags: ['酒店', '案例'], icon: 'book', color: 'rose' },
    { id: 'position-agent', category: 'agent', title: '岗位批量创建助手', desc: '根据专业方向快速生成岗位能力模型与任务。', tags: ['岗位', '创建'], icon: 'bot', color: 'indigo' },
    { id: 'scene-agent', category: 'agent', title: '场景批量创建助手', desc: '智能拆解岗位任务，生成配套实践场景。', tags: ['场景', '创建'], icon: 'bot', color: 'cyan' },
    { id: 'qa-robot', category: 'agent', title: '课程答疑机器人', desc: '7×24 小时解答课程知识点与学习路径问题。', tags: ['答疑', '课程'], icon: 'bot', color: 'violet' },
    { id: 'custom-robot', category: 'agent', title: '师生自建机器人', desc: '支持师生自定义知识库，打造专属智能体。', tags: ['自建', '自定义'], icon: 'bot', color: 'fuchsia' },
    { id: 'brand-platform', category: 'platform', title: '产业联盟与品牌运营平台', desc: '校企合作单位、重点项目与专家资源统一展示。', tags: ['校企', '品牌'], icon: 'external', color: 'rose', platformId: 'alliance' },
    { id: 'career-platform', category: 'platform', title: '职业岗位学习平台', desc: '岗位能力模型、典型任务与证书要求一站呈现。', tags: ['岗位', '学习'], icon: 'external', color: 'purple', platformId: 'career' },
    { id: 'scene-platform', category: 'platform', title: '实践场景学习平台', desc: '按专业浏览已发布实践场景，一键进入详情。', tags: ['场景', '实训'], icon: 'external', color: 'cyan', platformId: 'scene' },
    { id: 'eval-platform', category: 'platform', title: '能力测评认证平台', desc: '能力画像对比认证标准，推荐测评与练习资源。', tags: ['测评', '认证'], icon: 'external', color: 'emerald', platformId: 'ability' },
  ];

  const QUICK_ACTIONS = [
    { id: 'create-position', label: '我要建岗位', icon: 'plus', href: 'http://111.170.170.202:3002/positions', color: 'purple' },
    { id: 'create-scene', label: '我要建场景', icon: 'plus', href: 'http://111.170.170.202:3003/', color: 'cyan' },
    { id: 'ai-create-position', label: '我要 AI 帮我建岗位', icon: 'sparkles', href: 'http://111.170.170.202:5000/', color: 'indigo' },
  ];

  const PROMPT_TAGS = [
    { label: '建岗位', value: '我要建岗位' },
    { label: '建场景', value: '我要建场景' },
    { label: 'AI建岗', value: '我要AI帮我建岗位' },
    { label: '网络安全', value: '我想做网络安全工程师，需要学什么？' },
    { label: '实训场景', value: '信息安全专业有哪些实训场景？' },
    { label: '岗位认证', value: '我距离岗位认证还差哪些能力？' },
    { label: '校企合作', value: '我们学校有哪些校企合作单位？' },
  ];

  const CATEGORY_META = {
    knowledge: { label: '学校知识库', icon: 'book', color: '#d97706' },
    agent: { label: '智能体助手', icon: 'bot', color: '#4f46e5' },
    platform: { label: '外部教学平台', icon: 'external', color: '#0891b2' },
  };

  const APP_MODULES = {
    alliance: [
      { id: 'alliance-1', title: '产教融合管理', desc: '产教资源协同对接中枢', href: 'http://111.170.170.202:3004/admin' },
      { id: 'alliance-2', title: '品牌运营管理', desc: '品牌资产配置与发布管理', href: 'http://111.170.170.202:3004/admin/brands' },
      { id: 'alliance-3', title: '就业服务管理', desc: '就业项目与岗位推荐管理', href: 'http://111.170.170.202:3004/admin/employment' },
      { id: 'alliance-4', title: '【企业端】服务平台', desc: '企业合作伙伴登录入口', href: 'http://111.170.170.202:3004/partner/login' },
    ],
    career: [
      { id: 'career-1', title: '岗位资源管理', desc: '职业岗位资源与能力模型管理', href: 'http://111.170.170.202:3002/positions' },
      { id: 'career-2', title: '批次分组管理', desc: '批次分组与审批关联管理', href: 'http://111.170.170.202:3002/batches' },
      { id: 'career-3', title: '审批流程管理', desc: '审批流模板预设与配置', href: 'http://111.170.170.202:3002/workflows' },
    ],
    scene: [
      { id: 'scene-1', title: '场景资源管理', desc: '实践场景资源总览与管理', href: 'http://111.170.170.202:3003/' },
      { id: 'scene-2', title: '批次分组管理', desc: '批次分组与审批关联管理', href: 'http://111.170.170.202:3003/batches' },
      { id: 'scene-3', title: '审批流程管理', desc: '审批流模板预设配置', href: 'http://111.170.170.202:3003/workflows' },
    ],
    ability: [
      { id: 'ability-1', title: '通用测评管理', desc: '测评题库与通用测评管理', href: 'http://111.170.170.202:3005/question-banks' },
      { id: 'ability-2', title: '岗位认定管理', desc: '岗位能力模型与认定管理', href: 'http://111.170.170.202:3005/job-ability' },
      { id: 'ability-3', title: '测评方式库', desc: '能力测评方法与量规配置', href: 'http://111.170.170.202:3005/evaluation-methods' },
      { id: 'ability-4', title: '毕业设计管理', desc: '毕业设计选题与评审管理', href: 'http://111.170.170.202:3005/graduation-project/topics' },
      { id: 'ability-5', title: '学生画像管理', desc: '学生能力画像与成长档案', href: 'http://111.170.170.202:3005/student-portrait/portraits' },
    ],
  };

  let state = {
    open: false,
    activeTab: 'all',
    expandedIds: new Set(),
    messages: [],
    input: '',
    typing: false,
    resources: RESOURCES,
    loading: true,
    error: null,
    dataSource: 'mock',
  };
  let els = {};

  function getIcon(name) {
    return SVG[name] || SVG.layoutGrid;
  }

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function getFilteredResources() {
    const q = state.input.trim().toLowerCase();
    return state.resources.filter((r) => {
      const matchesCategory = state.activeTab === 'all' || r.category === state.activeTab;
      const matchesQuery = !q ||
        r.title.toLowerCase().includes(q) ||
        r.desc.toLowerCase().includes(q) ||
        (r.tags || []).some((t) => t.toLowerCase().includes(q));
      return matchesCategory && matchesQuery;
    });
  }

  function findResourcesByIds(ids) {
    return ids
      .map((id) => state.resources.find((r) => r.id === id))
      .filter(Boolean);
  }

  function findResourcesByKeywords(keywords) {
    return state.resources.filter((r) => {
      const text = `${r.title} ${r.desc} ${(r.tags || []).join(' ')}`.toLowerCase();
      return keywords.some((kw) => text.includes(kw));
    });
  }

  function generateReply(question) {
    let reply = '';
    let recommendations = [];
    let quickActions;
    const q = question.toLowerCase();

    if (q.includes('我要建岗位')) {
      reply = '已为你找到岗位管理入口，点击即可进入岗位新建页面。';
      quickActions = QUICK_ACTIONS.filter((a) => a.id === 'create-position');
    } else if (q.includes('我要建场景')) {
      reply = '已为你找到新建场景入口，点击即可进入场景新建页面。';
      quickActions = QUICK_ACTIONS.filter((a) => a.id === 'create-scene');
    } else if (q.includes('我要ai帮我建岗位')) {
      reply = '已为你唤起 AI 智能体，点击即可使用 AI 辅助创建岗位。';
      quickActions = QUICK_ACTIONS.filter((a) => a.id === 'ai-create-position');
    } else if (q.includes('网络安全工程师') || q.includes('岗位')) {
      reply = '推荐你进入【职业岗位学习平台】查看相关岗位。你可以从知识库中学习岗位标准，或使用智能体辅助创建岗位能力模型。';
      recommendations = findResourcesByIds(['career-platform'])
        .concat(findResourcesByKeywords(['岗位', '职业', '能力']))
        .slice(0, 3);
    } else if (q.includes('实训场景') || q.includes('信息安全')) {
      reply = '已为你找到实践场景相关资源，包括教学平台、实训知识库和场景创建智能体，你可以直接点击查看详情。';
      recommendations = findResourcesByIds(['scene-platform'])
        .concat(findResourcesByKeywords(['场景', '实训', '实践']))
        .slice(0, 3);
    } else if (q.includes('岗位认证') || q.includes('能力')) {
      reply = '已为你推荐能力测评与认证相关资源，点击卡片即可进入对应平台或智能体。';
      recommendations = findResourcesByIds(['eval-platform'])
        .concat(findResourcesByKeywords(['测评', '认证', '能力', '答疑']))
        .slice(0, 3);
    } else if (q.includes('校企合作') || q.includes('合作单位')) {
      reply = '你可以在【产业联盟与品牌运营平台】查看校企合作单位、重点项目成果及专家资源。';
      recommendations = findResourcesByIds(['brand-platform'])
        .concat(findResourcesByKeywords(['校企', '合作', '产业', '品牌']))
        .slice(0, 3);
    } else {
      reply = '我帮你找到了一些相关资源，你可以点击卡片快速查看。如需更精准的推荐，可以补充专业、年级或目标岗位。';
      recommendations = state.resources.filter((r) => {
        return (
          r.title.toLowerCase().includes(q) ||
          r.desc.toLowerCase().includes(q) ||
          (r.tags || []).some((t) => t.toLowerCase().includes(q))
        );
      }).slice(0, 4);
      if (recommendations.length === 0) {
        recommendations = state.resources.slice(0, 3);
      }
    }
    return { reply, recommendations, quickActions };
  }

  function renderResourceItem(r) {
    const isExpandable = r.category === 'platform';
    const isClickable = r.originalType === 'kb' || r.originalType === 'bot';
    const expanded = state.expandedIds.has(r.id);
    const c = COLORS[r.color] || COLORS.indigo;
    const tagsHtml = (r.tags || []).map((t) => `<span class="yka-tag">${escapeHtml(t)}</span>`).join('');
    const expandHtml = isExpandable && expanded ? renderModules(r) : '';
    let onclick = '';
    let cls = '';
    if (isExpandable) {
      cls = 'expandable';
      onclick = `onclick="YKA.toggleExpand('${r.id}')"`;
    } else if (isClickable) {
      cls = 'clickable';
      if (r.originalType === 'kb') onclick = `onclick="YKA.openKnowledgeBase(${r.originalId})"`;
      else if (r.originalType === 'bot') onclick = `onclick="YKA.openBot(${r.originalId})"`;
    } else {
      cls = 'non-expand';
    }
    return `
      <div class="yka-resource ${cls}" ${onclick}>
        <button class="yka-resource-btn" type="button" ${isExpandable || isClickable ? '' : 'disabled'}>
          <div class="yka-resource-main">
            <div class="yka-icon-box" style="background:${c.bg};color:${c.text};border-color:${c.border}">
              ${getIcon(r.icon)}
            </div>
            <div class="yka-resource-body">
              <h4 class="yka-resource-title">${escapeHtml(r.title)}</h4>
              <p class="yka-resource-desc">${escapeHtml(r.desc)}</p>
              <div class="yka-resource-tags">${tagsHtml}</div>
            </div>
          </div>
        </button>
        ${expandHtml}
      </div>
    `;
  }

  function renderModules(r) {
    const modules = (r.platformId && APP_MODULES[r.platformId]) || [];
    if (modules.length === 0) {
      return `<div class="yka-modules"><div class="yka-module-empty">暂无模块配置</div></div>`;
    }
    const items = modules.map((m) => {
      if (!m.href) {
        return `<div class="yka-module-link disabled"><span>${getIcon('layoutGrid')}</span><span class="yka-resource-title">${escapeHtml(m.title)}</span></div>`;
      }
      return `<a class="yka-module-link" href="${escapeHtml(m.href)}" target="_blank" rel="noopener noreferrer"><span>${getIcon('external')}</span><span class="yka-resource-title">${escapeHtml(m.title)}</span></a>`;
    }).join('');
    return `<div class="yka-modules"><div class="yka-module-grid">${items}</div></div>`;
  }

  function renderGroupedResources(list) {
    const cats = Object.keys(CATEGORY_META);
    let html = '';
    cats.forEach((cat) => {
      const items = list.filter((r) => r.category === cat);
      if (items.length === 0) return;
      const meta = CATEGORY_META[cat];
      html += `
        <div class="yka-category-header">
          <span style="color:${meta.color}">${getIcon(meta.icon)}</span>
          <span class="yka-category-label">${escapeHtml(meta.label)}</span>
        </div>
        <div>${items.map(renderResourceItem).join('')}</div>
      `;
    });
    if (list.length === 0) {
      html += '<div class="yka-empty">未找到相关资源，换个关键词试试</div>';
    }
    return html;
  }

  function renderFlatResources(list) {
    if (list.length === 0) return '<div class="yka-empty">未找到相关资源</div>';
    return list.map(renderResourceItem).join('');
  }

  function renderChatMessages() {
    let html = '';
    state.messages.forEach((msg) => {
      const isUser = msg.role === 'user';
      const quickActions = msg.quickActions && msg.quickActions.length > 0
        ? `<div class="yka-msg-actions">${msg.quickActions.map((a) => {
            const c = COLORS[a.color] || COLORS.indigo;
            return `<a class="yka-quick-action" href="${escapeHtml(a.href)}" target="_blank" rel="noopener noreferrer" style="background:${c.bg};color:${c.text};border-color:${c.border}">
              ${getIcon(a.icon)}<span>${escapeHtml(a.label)}</span>${getIcon('external')}
            </a>`;
          }).join('')}</div>`
        : '';
      const recs = msg.recommendations && msg.recommendations.length > 0
        ? `<div class="yka-rec-section">
            <div class="yka-rec-section-title">为你推荐：</div>
            ${msg.recommendations.map((r) => {
              const meta = CATEGORY_META[r.category];
              return `<div class="yka-rec-item" onclick="YKA.openResource('${r.id}')">
                <span style="color:${meta.color}">${getIcon(meta.icon)}</span>
                <span class="yka-rec-title">${escapeHtml(r.title)}</span>
              </div>`;
            }).join('')}
           </div>`
        : '';
      html += `
        <div class="yka-msg ${isUser ? 'user' : 'assistant'}">
          ${isUser ? '' : `<div class="yka-msg-assistant-avatar">${getIcon('sparkles')}</div>`}
          <div class="yka-msg-bubble">
            <div>${escapeHtml(msg.content)}</div>
            ${quickActions}
            ${recs}
          </div>
        </div>
      `;
    });
    if (state.typing) {
      html += `
        <div class="yka-msg assistant">
          <div class="yka-msg-assistant-avatar">${getIcon('sparkles')}</div>
          <div class="yka-msg-bubble">正在思考…</div>
        </div>
      `;
    }
    return html;
  }

  function renderContent() {
    if (!els.content) return;
    if (state.loading) {
      els.content.innerHTML = `<div class="yka-loading"><div class="yka-loading-spinner">${getIcon('loader2')}</div><p>正在加载资源…</p></div>`;
      return;
    }
    const isChatMode = state.messages.length > 0 || state.typing;
    if (isChatMode) {
      els.content.innerHTML = `
        <div class="yka-chat">
          <div class="yka-chat-header">
            <div class="yka-chat-header-left">${getIcon('messageCircle')}<span>AI 引导对话（演示）</span></div>
            <button class="yka-chat-back" type="button" onclick="YKA.closeChat()" title="返回导航面板">${getIcon('x')}</button>
          </div>
          <div class="yka-chat-messages">${renderChatMessages()}</div>
        </div>
      `;
    } else if (state.activeTab === 'all') {
      els.content.innerHTML = `<div class="yka-scroll">${renderGroupedResources(getFilteredResources())}</div>`;
    } else {
      els.content.innerHTML = `<div class="yka-scroll">${renderFlatResources(getFilteredResources())}</div>`;
    }
    scrollToBottom();
  }

  function scrollToBottom() {
    const scroller = els.content.querySelector('.yka-chat-messages') || els.content.querySelector('.yka-scroll');
    if (scroller) scroller.scrollTop = scroller.scrollHeight;
  }

  function updateFab() {
    if (!els.fab) return;
    els.fab.className = `yka-fab ${state.open ? 'open' : 'closed'}`;
    els.fab.innerHTML = `${getIcon('sparkles')}<span>YI KNOW 教学智能助理</span>${state.open ? getIcon('x') : getIcon('chevronRight')}`;
  }

  function updateTabs() {
    if (!els.tabs) return;
    els.tabs.querySelectorAll('.yka-tab').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === state.activeTab);
    });
  }

  function updatePrompts() {
    if (!els.prompts) return;
    const isChatMode = state.messages.length > 0 || state.typing;
    els.prompts.style.display = isChatMode ? 'none' : 'block';
  }

  function handleOpenChange(nextOpen) {
    state.open = nextOpen;
    if (!nextOpen) {
      state.input = '';
      state.messages = [];
      state.typing = false;
      state.expandedIds = new Set();
      state.activeTab = 'all';
      if (els.input) els.input.value = '';
    }
    updateFab();
    updateTabs();
    updatePrompts();
    renderContent();
    if (els.panel) els.panel.style.display = nextOpen ? 'flex' : 'none';
  }

  function handleTab(tab) {
    state.activeTab = tab;
    state.input = '';
    if (els.input) els.input.value = '';
    updateTabs();
    renderContent();
  }

  function handleInput(val) {
    state.input = val;
    if (state.messages.length === 0 && !state.typing) {
      renderContent();
    }
  }

  function handleSend() {
    const question = state.input.trim();
    if (!question || state.typing) return;
    const userMsg = { id: Date.now().toString(), role: 'user', content: question };
    state.messages.push(userMsg);
    state.input = '';
    if (els.input) els.input.value = '';
    state.typing = true;
    updatePrompts();
    if (window.ykaUpdateSend) window.ykaUpdateSend();
    renderContent();

    setTimeout(() => {
      const { reply, recommendations, quickActions } = generateReply(question);
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: reply,
        recommendations,
        quickActions,
      };
      state.messages.push(assistantMsg);
      state.typing = false;
      if (window.ykaUpdateSend) window.ykaUpdateSend();
      renderContent();
    }, 800);
  }

  function createFab() {
    const btn = document.createElement('button');
    btn.id = 'yka-fab';
    btn.className = 'yka-fab closed';
    btn.setAttribute('aria-label', 'YI KNOW 教学智能助理');
    btn.onclick = () => handleOpenChange(!state.open);
    document.body.appendChild(btn);
    els.fab = btn;
    updateFab();
  }

  function createPanel() {
    const panel = document.createElement('div');
    panel.className = 'yka-panel';
    panel.style.display = 'none';
    panel.innerHTML = `
      <div class="yka-header">
        <div class="yka-header-left">
          <div class="yka-avatar">${getIcon('sparkles')}</div>
          <div>
            <h3 class="yka-title">YI KNOW</h3>
            <p class="yka-subtitle">职业教育场景化教学智能助理</p>
          </div>
        </div>
        <button class="yka-close" type="button" onclick="YKA.closePanel()">${getIcon('x')}</button>
      </div>
      <div class="yka-tabs">
        <button class="yka-tab active" data-tab="all" type="button">全部</button>
        <button class="yka-tab" data-tab="knowledge" type="button">知识库</button>
        <button class="yka-tab" data-tab="agent" type="button">智能体</button>
        <button class="yka-tab" data-tab="platform" type="button">教学平台</button>
      </div>
      <div class="yka-content"></div>
      <div class="yka-separator"></div>
      <div class="yka-bottom">
        <div class="yka-prompts">
          <div class="yka-prompts-header">${getIcon('sparkles')}<span>示例问题：</span></div>
          <div class="yka-prompt-list">
            ${PROMPT_TAGS.map((t) => `<button class="yka-prompt-chip" type="button" onclick="YKA.fillPrompt('${escapeHtml(t.value)}')">${escapeHtml(t.label)}</button>`).join('')}
          </div>
        </div>
        <div class="yka-input-row">
          <div class="yka-input-wrap">
            ${getIcon('search')}
            <input class="yka-input" type="text" placeholder="输入问题或搜索资源，例如：金融专业岗位标准">
          </div>
          <button class="yka-send" type="button" disabled>${getIcon('send')}</button>
        </div>
      </div>
    `;
    document.body.appendChild(panel);
    els.panel = panel;
    els.content = panel.querySelector('.yka-content');
    els.tabs = panel.querySelector('.yka-tabs');
    els.prompts = panel.querySelector('.yka-prompts');
    els.input = panel.querySelector('.yka-input');
    els.send = panel.querySelector('.yka-send');

    els.tabs.querySelectorAll('.yka-tab').forEach((btn) => {
      btn.addEventListener('click', () => handleTab(btn.dataset.tab));
    });

    els.input.addEventListener('input', (e) => handleInput(e.target.value));
    els.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    els.send.addEventListener('click', handleSend);

    function updateSend() {
      els.send.disabled = !state.input.trim() || state.typing;
    }
    els.input.addEventListener('input', updateSend);
    window.ykaUpdateSend = updateSend;
    updateSend();
  }

  async function init() {
    if (document.getElementById('yka-fab')) return;
    createFab();
    createPanel();
    renderContent();
    const { resources, source } = await loadResources();
    state.resources = resources;
    state.dataSource = source;
    state.loading = false;
    renderContent();
  }

  window.YKA = {
    toggleExpand(id) {
      const next = new Set(state.expandedIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      state.expandedIds = next;
      renderContent();
    },
    fillPrompt(value) {
      state.input = value;
      if (els.input) els.input.value = value;
      if (els.send) els.send.disabled = false;
      if (state.messages.length === 0 && !state.typing) renderContent();
    },
    openResource(id) {
      const r = state.resources.find((x) => x.id === id);
      if (!r) return;
      if (r.category === 'platform' && r.platformId) {
        state.activeTab = 'platform';
        state.expandedIds = new Set([id]);
      } else if (r.originalType === 'kb') {
        this.openKnowledgeBase(r.originalId);
        return;
      } else if (r.originalType === 'bot') {
        this.openBot(r.originalId);
        return;
      } else {
        state.activeTab = r.category;
      }
      state.messages = [];
      state.typing = false;
      updateTabs();
      updatePrompts();
      renderContent();
    },
    openKnowledgeBase(id) {
      if (typeof navigate === 'function') {
        navigate('kb', { id });
        this.closePanel();
      } else {
        window.location.hash = `#/kb/${id}`;
        this.closePanel();
      }
    },
    openBot(id) {
      if (typeof navigate === 'function') {
        navigate('bot', { id });
        this.closePanel();
      } else {
        window.location.hash = `#/bot/${id}`;
        this.closePanel();
      }
    },
    closeChat() {
      state.messages = [];
      state.typing = false;
      state.input = '';
      if (els.input) els.input.value = '';
      updatePrompts();
      renderContent();
    },
    closePanel() {
      handleOpenChange(false);
    },
    openPanel() {
      handleOpenChange(true);
    },
    togglePanel() {
      handleOpenChange(!state.open);
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
