#!/bin/bash
# ============================================================
#  AI 驱动 Web 接口自动化测试平台 —— 一键发布到 GitHub（公开仓库）
# ============================================================
# 两种鉴权方式，脚本会自动选择：
#
#  ★ 方式 A（推荐，本机已装 gh 并已登录）：无需任何环境变量
#      gh auth login   # 首次使用先登录（浏览器授权）
#      bash publish_to_github.sh
#
#  ★ 方式 B（未装 gh，使用 Personal Access Token）：
#      GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
#      → Generate new token(classic) → 勾选 repo → Generate
#      然后在本机（具备正常公网访问的机器）执行：
#      export GITHUB_TOKEN=ghp_xxxxxxxxxxxx     # 你的 PAT
#      export GITHUB_USER=ali17788           # 你的 GitHub 用户名
#      bash publish_to_github.sh
#
# ⚠️ 注意：GitHub 自 2021-08 起已禁用「账号密码」做 git push，必须使用
#         PAT 或 gh CLI。本平台的登录密码 admin/admin123 仅用于平台本身。
# ============================================================
set -e
cd "$(dirname "$0")"

REPO_NAME="${REPO_NAME:-api-test-platform}"
REPO_DESC="${REPO_DESC:-AI 驱动 Web 接口自动化测试平台：零代码 · AI 全自动 · 接口自动化测试（Vue3+FastAPI）}"
BRANCH="${BRANCH:-main}"
VISIBILITY="${VISIBILITY:-public}"   # public / private

# ---------- 1. 确保有提交 ----------
if [ -z "$(git log -1 --oneline 2>/dev/null)" ]; then
  echo "==> 未发现提交，自动 add + commit ..."
  git add -A
  git commit -q -m "chore: initial commit — AI 驱动 Web 接口自动化测试平台" || true
fi

# ---------- 2. 选择鉴权方式 ----------
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> 检测到 gh CLI 已登录，使用 gh 方式发布（更安全，token 不出现在 URL）"
  GH_USER="$(gh api user --jq .login 2>/dev/null || true)"
  : "${GH_USER:?❌ 无法获取 gh 登录用户，请先执行 gh auth login}"
  GITHUB_USER="$GH_USER"
  USE_GH=1
else
  echo "==> 未检测到已登录的 gh CLI，回退到 Token 方式"
  : "${GITHUB_TOKEN:?❌ 请先设置环境变量 GITHUB_TOKEN（GitHub Personal Access Token，需 repo 权限）}"
  : "${GITHUB_USER:?❌ 请设置环境变量 GITHUB_USER 为你的 GitHub 用户名，例如 ali17788}"
  USE_GH=0
fi

echo "==> 仓库目标：github.com/${GITHUB_USER}/${REPO_NAME} (${VISIBILITY})"

# ---------- 3. 创建公开仓库 ----------
if [ "$USE_GH" = "1" ]; then
  if ! gh repo view "${GITHUB_USER}/${REPO_NAME}" >/dev/null 2>&1; then
    echo "==> 创建仓库（gh）..."
    gh repo create "${REPO_NAME}" --description "${REPO_DESC}" ${VISIBILITY} --source . --remote origin --push --branch "${BRANCH}" 2>&1 || {
      echo "   （gh repo create 失败，尝试仅创建不推送）"
      gh repo create "${REPO_NAME}" --description "${REPO_DESC}" ${VISIBILITY} || true
      git remote remove origin 2>/dev/null || true
      git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    }
  else
    echo "==> 仓库已存在，配置 remote 并推送..."
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
  fi
else
  echo "==> 创建公开仓库（API，若已存在将跳过）..."
  curl -sS -X POST "https://api.github.com/user/repos" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESC}\",\"homepage\":\"\",\"public\":true,\"auto_init\":false,\"has_issues\":true}" \
    -o /dev/null -w "    HTTP %{http_code}\n" || echo "   （创建请求失败，可能已存在，继续推送）"

  git remote remove origin 2>/dev/null || true
  git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
fi

# ---------- 4. 推送 ----------
git branch -M "${BRANCH}"
if [ "$USE_GH" = "1" ]; then
  # gh 已托管 remote（--source . --remote origin），直接 push
  git push -u origin "${BRANCH}" 2>&1 || gh repo sync --source "${BRANCH}" 2>&1 || true
else
  echo "==> 推送到 origin/${BRANCH} ..."
  git push -u origin "${BRANCH}"
fi

echo ""
echo "✅ 发布完成！公开仓库地址："
echo "   https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "   克隆运行："
echo "     git clone https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "     cd ${REPO_NAME} && bash start.sh"
echo "     浏览器访问 http://127.0.0.1:8000  （演示账号 admin / admin123）"
echo ""
echo "   想要公网可访问的运行实例？见 DEPLOY.md（Render / Railway 一键部署）。"
