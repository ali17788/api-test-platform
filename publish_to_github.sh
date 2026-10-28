#!/bin/bash
# ============================================================
#  AI 驱动 Web 接口自动化测试平台 —— 一键发布到 GitHub（公开仓库）
# ============================================================
# 用法：
#   1) 在 GitHub 生成 Personal Access Token（需 repo 权限）：
#      GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
#      → Generate new token(classic) → 勾选 repo → Generate
#   2) 在本机（具备正常公网访问的机器）执行：
#      export GITHUB_TOKEN=ghp_xxxxxxxxxxxx     # 你的 PAT
#      export GITHUB_USER=elsa_li9090           # 你的 GitHub 用户名
#      bash publish_to_github.sh
#
# ⚠️ 注意：GitHub 自 2021-08 起已禁用「账号密码」做 git push，必须使用 PAT。
#         本平台的登录密码 admin/admin123 仅用于平台本身，不能用于 git。
# ============================================================
set -e
cd "$(dirname "$0")"

# ---------- 参数 ----------
: "${GITHUB_TOKEN:?❌ 请先设置环境变量 GITHUB_TOKEN（GitHub Personal Access Token，需 repo 权限）}"
: "${GITHUB_USER:?❌ 请设置环境变量 GITHUB_USER 为你的 GitHub 用户名，例如 elsa_li9090}"
REPO_NAME="${REPO_NAME:-api-test-platform}"
REPO_DESC="${REPO_DESC:-AI 驱动 Web 接口自动化测试平台：零代码 · AI 全自动 · 接口自动化测试（Vue3+FastAPI）}"
BRANCH="${BRANCH:-main}"

echo "==> 仓库目标：github.com/${GITHUB_USER}/${REPO_NAME} (public)"

# ---------- 1. 确保有提交 ----------
if [ -z "$(git log -1 --oneline 2>/dev/null)" ]; then
  echo "==> 未发现提交，自动 add + commit ..."
  git add -A
  git commit -q -m "chore: initial commit — AI 驱动 Web 接口自动化测试平台" || true
fi

# ---------- 2. 创建公开仓库（已存在则忽略）----------
echo "==> 创建公开仓库（若已存在将跳过）..."
curl -sS -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESC}\",\"homepage\":\"\",\"public\":true,\"auto_init\":false,\"has_issues\":true}" \
  -o /dev/null -w "    HTTP %{http_code}\n" || echo "   （创建请求失败，可能已存在，继续推送）"

# ---------- 3. 配置 remote 并推送 ----------
git remote remove origin 2>/dev/null || true
git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git branch -M "${BRANCH}"
echo "==> 推送到 origin/${BRANCH} ..."
git push -u origin "${BRANCH}"

echo ""
echo "✅ 发布完成！公开仓库地址："
echo "   https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "   克隆运行："
echo "     git clone https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "     cd ${REPO_NAME} && bash start.sh"
echo "     浏览器访问 http://127.0.0.1:8000  （演示账号 admin / admin123）"
