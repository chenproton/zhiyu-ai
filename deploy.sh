#!/bin/bash
#
# deploy.sh - 本地前端部署脚本
# 在本机启动一个纯前端 Web 服务，API 复用本地后端
#
set -euo pipefail

# ==================== 本地配置（可通过环境变量覆盖） ====================
SITE_NAME="${SITE_NAME:-zhiyu-ai}"
PORT="${PORT:-3008}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"

# ==================== 自动推导 ====================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$SCRIPT_DIR/.deploy-local"
LOCAL_PUBLIC_DIR="$LOCAL_DIR/public"

# ==================== 主流程 ====================
echo ""
echo "🚀 启动本地前端部署: [$SITE_NAME] -> http://127.0.0.1:$PORT"
echo "   API 后端: $BACKEND_URL"
echo ""

echo "[1/3] 准备本地前端产物..."
rm -rf "$LOCAL_DIR"
mkdir -p "$LOCAL_PUBLIC_DIR"
cp -a "$SCRIPT_DIR/backend/static/." "$LOCAL_PUBLIC_DIR/"
cp "$SCRIPT_DIR/server.js" "$LOCAL_DIR/server.js"
echo "  已复制 backend/static/* 和 server.js 到 $LOCAL_DIR"

echo ""
echo "[2/3] 启动服务..."
cd "$LOCAL_DIR"

NODE_BIN=$(command -v node || echo "/usr/local/bin/node")
if [ ! -x "$NODE_BIN" ]; then
  echo "❌ 未找到 node，请先安装 Node.js"
  exit 1
fi

if command -v pm2 &>/dev/null; then
  # 使用 pm2 管理，方便后续重启/停止
  pm2 delete "$SITE_NAME" &>/dev/null || true
  PORT="$PORT" BACKEND_URL="$BACKEND_URL" HOSTNAME="0.0.0.0" pm2 start server.js \
    --name "$SITE_NAME" \
    --interpreter "$NODE_BIN" \
    --restart-delay 3000
  pm2 save > /dev/null
  echo "  已使用 pm2 启动: pm2 logs $SITE_NAME"
else
  # 直接后台启动
  nohup env PORT="$PORT" BACKEND_URL="$BACKEND_URL" HOSTNAME="0.0.0.0" "$NODE_BIN" server.js > "$LOCAL_DIR/server.log" 2>&1 &
  echo "  已后台启动（无 pm2）: tail -f $LOCAL_DIR/server.log"
fi

echo ""
echo "[3/3] 等待服务就绪..."
sleep 2

echo ""
echo "✨ [$SITE_NAME] 本地前端部署完成！"
echo "   访问地址: http://127.0.0.1:$PORT"
echo "   API 后端: $BACKEND_URL"
echo ""
