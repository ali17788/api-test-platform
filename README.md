# AI驱动Web接口自动化测试平台

> 零代码 · AI全自动 · 可视化 —— 依据《AI驱动Web接口自动化测试工具产品开发文档》与《UI产品设计文档》完整实现

---

## 一、快速启动

### 方式一：一键脚本（推荐）

```bash
cd api-test-platform
bash start.sh           # Windows 可用 Git Bash 执行
```

脚本会自动完成：创建虚拟环境 → 安装依赖 → 构建前端 → 启动服务（含演示 Mock 接口服务）。

### 方式二：手动启动

```bash
# 后端（FastAPI）
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd backend && python app.py          # http://127.0.0.1:8000

# 前端（开发模式，另开终端）
cd frontend && npm install && npm run dev   # http://127.0.0.1:5173

# 演示接口服务（可选，用于验证执行引擎）
python mock_api.py                    # http://127.0.0.1:8099
```

生产模式下前端执行 `npm run build` 输出到 `web/`，由后端直接托管，访问 `http://127.0.0.1:8000` 即可使用完整系统。

**演示账号：admin / admin123**

---

## 二、技术架构

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 展示层 | Vue3 + Vite + Element Plus + ECharts | 顶部导航 + 左侧菜单 + 主内容区后台布局，主题蓝 #1677FF |
| 业务层 | Python FastAPI | 项目管理 / 环境配置 / 接口解析 / 用例管理 / 报告生成 |
| AI 能力层 | OpenAI 兼容协议（DeepSeek / GPT / 通义千问等） | 用例智能生成、文档整理；无 Key 时自动降级内置规则引擎 |
| 执行引擎层 | Requests + 线程池 | 自动发请求、自动断言、超时重试、实时日志、随时终止 |
| 数据持久层 | SQLite（可平滑切换 MySQL） | 项目/环境/接口/用例/执行记录/报告数据 |
| 文档处理 | python-docx / ReportLab / openpyxl | Word、PDF、Excel 导出 |

目录结构：

```
api-test-platform/
├── backend/                 # FastAPI 后端服务
│   ├── app.py               # 服务入口（API + 前端静态托管）
│   ├── db.py                # SQLite 建库建表与种子数据
│   ├── auth.py  projects.py apis.py  cases.py
│   ├── ai.py  execution.py  reports.py  dashboard.py
│   └── services/
│       ├── parser.py        # OpenAPI / Postman 文档解析
│       ├── ai_client.py     # 大模型对接 + 规则引擎兜底
│       ├── executor.py      # 自动化执行引擎
│       └── exporter.py      # Word / PDF / Excel 导出
├── frontend/                # Vue3 前端工程（构建产物输出到 web/）
│   └── src/
│       ├── layout/Layout.vue
│       └── views/           # 11 个功能页面
├── web/                     # 前端构建产物（由后端托管）
├── mock_api.py              # 演示用本地 Mock 接口服务
├── seed_demo.py             # 演示数据初始化脚本
├── e2e_test.py              # 端到端冒烟测试
└── start.sh                 # 一键启动脚本
```

---

## 三、功能清单（对照产品文档）

| 模块 | 页面/能力 | 状态 |
|------|-----------|------|
| 基础 | 用户登录登出、简单权限、操作日志溯源 | ✅ |
| 项目管理 | 增删改查、搜索、进入项目自动数据隔离、删除二次确认 | ✅ |
| 环境配置 | 多环境、域名、全局请求头（KV 动态增删）、超时、重试、默认环境高亮 | ✅ |
| 接口文档解析 | 拖拽上传 5 类格式：OpenAPI/Swagger(json,yaml)、Postman Collection、PDF、HTML、Markdown/文本；解析进度、成功条数提示、失败原因 | ✅ |
| 接口管理 | 列表分页、GET/POST/PUT/DELETE 彩色标签、查看/编辑/删除/生成用例、手动录入 | ✅ |
| AI 用例生成 | 单接口/全项目批量、仅正向/全量（正向+反向+边界+异常）、实时进度条与当前接口名、结果统计 | ✅ |
| 用例管理 | 多条件筛选、优先级、批量执行/删除、单条执行、AI 整理文档、在线文档预览 | ✅ |
| 测试执行 | 环境/范围/超时/重试配置、实时进度、实时统计、黑底实时日志面板、终止任务、失败重跑 | ✅ |
| 测试报告 | 报告列表、六维概览、通过率饼图、模块成功率柱状图、用例详情展开（请求/响应/断言/失败原因） | ✅ |
| 导出 | 用例文档 Word/PDF/Excel；测试报告 HTML/PDF/Excel | ✅ |
| 首页仪表盘 | 四宫格统计、7 日执行趋势、用例状态饼图、最近任务（快速查看报告） | ✅ |
| 系统 AI 配置 | 模型选择、API Key、BaseURL、超时、连通性测试、全局生效 | ✅ |

---

## 四、核心业务流程

```
新建项目 → 上传接口文档（自动解析）→ 配置测试环境 → AI 批量生成用例
        → AI 整理标准化用例文档 → 一键批量执行（自动断言）→ 生成可视化报告
        → 在线查看 / 导出 Word·PDF·Excel
```

**AI 能力说明**：在「系统AI配置」中填入任意 OpenAI 兼容模型的 API Key 与 BaseURL（如 DeepSeek），用例生成即切换为大模型智能生成；未配置 Key 时自动降级为内置规则引擎，按参数类型推导正向/反向/边界/异常用例，保证任何环境都能完整体验全流程。

**PDF / HTML 文档解析说明**：这两类为非结构化文档，采用启发式解析引擎识别：

- 接口识别：`GET /api/users` 这类「方法 + 路径」行；或 `接口名称 / 接口路径 / 请求方式` 标签式字段；或从表格行中提取。
- 参数识别：含「参数名 / 类型 / 必填 / 说明」表头的表格，按列映射取值；GET/DELETE 归入 Query 参数，其余归入请求体。
- 标题还原：PDF 抽取后会丢失层级，引擎按「编号标题（3.1 xxx）→ 接口名」「短标题 → 模块名」还原归属。
- 限制：仅支持文本版 PDF（由 Word/Markdown 导出），扫描件图片版无法提取文本；样例见 `docs/samples/`。

**接口文档自动解析样例**：`docs/samples/` 下提供 4 份样例文档（PDF、HTML 表格型、HTML 标签型、Markdown），可直接上传验证。

---

## 五、验证

```bash
python mock_api.py &          # 启动演示接口服务
cd backend && python app.py & # 启动平台服务
python e2e_test.py            # 端到端冒烟测试（11 组用例，覆盖全流程与导出）
python seed_demo.py           # 一键生成演示数据（项目+环境+接口+用例+执行报告）
python test_parser_formats.py # PDF/HTML/Markdown 解析引擎测试（含样例文档生成）
python test_upload_exec.py    # 上传解析 + 用例执行域名拼接端到端回归
```

测试覆盖：登录、项目、环境、OpenAPI 解析、AI 用例生成、文档整理、批量执行与断言、实时日志、报告统计、6 种格式导出、仪表盘聚合、AI 连通性；
另有 PDF/HTML 文档解析与「执行 URL 域名拼接」专项回归。

---

## 六、UI 规范落地

严格遵循 UI 设计文档：主色 #1677FF、成功 #00B42A、失败 #F53F3F、待执行 #FF7D00、跳过 #86909C；文字三级 #1D2129/#4E5969/#86909C；背景 #F5F7FA、卡片 #FFFFFF、边框 #E5E6EB；圆角 8px、间距 20/24px、按钮圆角 6px、表单高度 36px、表格表头 #F5F7FA、列表默认 10 条分页、弹窗「取消+确定」、空状态统一「暂无数据」。

---

## 七、用户与权限（RBAC）

平台内置基于「角色 + 菜单权限」的访问控制，管理员可在「用户与权限」页面对团队成员进行账号与权限管理。

**权限模型**

- **菜单（Menu）**：平台功能的最小权限单元，对应左侧侧边栏的每一个入口（共 10 个：首页仪表盘、项目管理、环境配置、接口管理、AI用例生成、用例管理、测试执行、测试报告、系统AI配置、用户与权限）。
- **角色（Role）**：聚合一组菜单权限，可被多名用户复用。内置三个角色（不可删除）：
  - 超级管理员 `admin`：拥有全部菜单与系统配置权限；
  - 测试工程师 `tester`：可参与测试全流程，无系统配置与用户管理权限；
  - 只读访客 `viewer`：仅可浏览项目、接口、用例与测试报告。
- **用户（User）**：绑定一个角色，并可在此基础上单独勾选/微调菜单权限（落库到 `users.menu_keys`）。最终可见菜单 = 用户自身 `menu_keys`（优先）；若为空则回退取所属角色的 `menu_keys`。
- **入口保护**：仅拥有 `users` 菜单权限的账号（默认即超级管理员）可调用用户/角色管理接口；其余账号既看不到入口，直访接口也会被 403 拦截。

**配置路径**：登录 admin → 左侧「用户与权限」→「角色管理」勾选可访问菜单 → 「用户管理」新建用户并分配角色（必要时单独微调菜单权限）。

> 安全约束：至少保留一名管理员；不能禁用/删除最后一个管理员，也不能修改自己的角色。生产环境请务必在首次登录后修改 admin 默认密码。

---

## 八、开源发布与部署

本仓库为纯源码仓库，发布到 GitHub 后即可公开访问。推荐发布流程：

```bash
# 1. 在 GitHub 上创建公开仓库（不要勾选自动生成 README/.gitignore）
# 2. 在本机执行项目根目录下的发布脚本（需 Personal Access Token，见下方说明）
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx   # 你的 PAT（repo 权限）
bash publish_to_github.sh              # 自动创建公开仓库并推送当前提交
```

> ⚠️ **关于认证**：GitHub 自 2021-08 起**已禁用账号密码**进行命令行 `git push`，必须使用 **Personal Access Token（PAT）**。
> 获取方式：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾选 `repo` 权限。
> 本项目的登录密码（admin/admin123）仅为平台演示账号，**不能**用于 git 推送。

克隆后本地运行：

```bash
git clone https://github.com/<你的用户名>/<仓库名>.git
cd <仓库名>
bash start.sh          # 自动建 venv、装依赖、构建前端、启动服务
# 浏览器访问 http://127.0.0.1:8000  （演示账号 admin / admin123）
```

如需将可运行系统对外提供公网访问，可将后端部署到 Railway / Render / Fly.io 等支持 Python 的 PaaS，并将前端 `web/` 一并托管（前端已构建并由后端静态托管）。GitHub 仓库本身仅提供源码与文档的公开访问。

---

## 九、免责声明与开源合规

- 本软件按 **MIT 许可证** 开源发布（见 `LICENSE`），仅供学习、演示与内部测试使用，**不提供任何明示或暗示的担保**。
- 演示账号 `admin / admin123` 为初始测试凭据，生产环境请立即修改；请勿在公开仓库提交任何真实 API Key、数据库或敏感数据（仓库已通过 `.gitignore` 排除 `*.db`、`.env` 等）。
- 平台 AI 用例生成依赖你自建的 OpenAI 兼容模型服务，相关密钥由使用者自行配置与保管。
- 使用本工具执行接口测试时，请仅对**你拥有合法权限**的系统与目标接口进行测试，遵守所在组织的安全规范与法律法规。
- 文档说明书详见 `docs/使用说明书.md`（含 PDF 版 `docs/使用说明书.pdf`）。
