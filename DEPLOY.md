# 部署指南（公网可访问的运行实例）

本指南帮助你在 **Render** 或 **Railway** 上一键部署本项目，得到一个任何人都能通过网址访问的运行实例。
前端已预构建在 `web/` 目录并随仓库提交，**运行时无需 Node.js**；后端用 FastAPI 托管页面与 API。

> 前置：仓库已推送到 GitHub（见 `publish_to_github.sh` 或下方「第一步」）。

---

## 第一步：先把仓库推到 GitHub（公开）

任选一种鉴权方式，在本机（有公网）执行：

- **方式 A（已装 `gh` 并登录）**：`bash publish_to_github.sh`
- **方式 B（用 Token）**：
  ```bash
  export GITHUB_TOKEN=ghp_你的PAT
  export GITHUB_USER=elsa_li9090
  bash publish_to_github.sh
  ```
完成后仓库地址：`https://github.com/elsa_li9090/api-test-platform`

---

## 第二步：部署到 Render（推荐，免费层可用）

1. 打开 https://render.com → 注册/登录（可用 GitHub 账号授权）。
2. 控制台 → **New** → **Blueprint**。
3. 连接 GitHub 仓库 `elsa_li9090/api-test-platform`，Render 会自动读取仓库根目录的 **`render.yaml`**。
4. 确认配置：
   - Runtime: Python 3.11
   - Build: 自动 `pip install -r requirements.txt`
   - Start: `bash start_server.sh`
   - Health Check: `/api/health`
5. 点击 **Apply** / **Deploy**。约 1–2 分钟构建完成。
6. 部署完成后，Render 会分配一个 `https://api-test-platform-xxxx.onrender.com` 的公网地址。
   打开即可访问，演示账号 **admin / admin123**。

> 免费层说明：Render 免费实例在闲置一段时间后会「休眠」，首次访问可能需等待十几秒唤醒，属正常现象。

---

## 第三步（备选）：部署到 Railway

1. 打开 https://railway.app → 用 GitHub 登录。
2. **New Project** → **Deploy from GitHub repo** → 选择 `api-test-platform`。
3. Railway 读取仓库根目录的 **`railway.json`**（Nixpacks 构建 + `bash start_server.sh` 启动）。
4. 在 Variables 中添加（可选）：
   - `PORT`：Railway 自动注入，无需手动填。
   - `OPENAI_API_KEY` / `OPENAI_BASE_URL`：如需开启 AI 联网用例生成（留空则走内置规则引擎）。
5. 点击 **Deploy**。完成后在项目的 **Settings → Domains** 中生成公网域名（如 `https://api-test-platform.up.railway.app`）。

---

## 关键说明

- **端口与绑定**：后端 `backend/app.py` 读取环境变量 `PORT`（云端自动注入）并绑定 `0.0.0.0`，无需任何改动即可适配上述平台。
- **数据库**：使用内置 SQLite，文件位于 `backend/data/platform.db`（已加入 `.gitignore`，不会进入仓库）。首次启动 `init_db()` 会自动建表并写入演示数据，无需手动迁移。
- **演示数据**：首次运行会自动创建管理员 `admin / admin123` 及三个内置角色（超级管理员 / 测试工程师 / 只读访客）。
- **AI 用例生成**：未配置 `OPENAI_API_KEY` 时，平台自动降级为「规则引擎」生成用例，不影响其它功能。
- **静态资源**：`web/` 已构建并入库，后端 `app.py` 直接托管，因此部署环境不需要 Node.js 与 npm。
- **自定义域名**：Render / Railway 均支持绑定你自己的域名（在平台 Domain 设置中添加并配置 CNAME）。

---

## 常见问题

- **构建报 `int | None` 语法错误**：说明部署环境 Python < 3.10。请在平台指定 **Python 3.10+**（Render 已设为 3.11，Railway Nixpacks 默认亦可）。
- **访问 502 / 健康检查失败**：确认启动命令为 `bash start_server.sh`（而非 `start.sh`），后者会尝试重建前端。
- **页面空白 / 菜单不显示**：多为旧浏览器缓存，硬刷新（Cmd/Ctrl+Shift+R）并重登即可。
- **数据持久化**：SQLite 文件写在实例磁盘，免费层实例重建/休眠可能清空数据；如需持久化，请挂载 Render/Railway 的磁盘，或改用外部数据库（Postgres）。

---

## 本地运行（非云端）

```bash
git clone https://github.com/elsa_li9090/api-test-platform.git
cd api-test-platform
bash start.sh          # 自动建 venv、装依赖、构建前端（仅首次）、启动
# 浏览器访问 http://127.0.0.1:8000   （admin / admin123）
```
