#!/bin/bash
#
# deploydemo.sh - 前端演示环境一键部署脚本
# 将本项目的纯前端产物部署到 demo2.zhiyu.com.cn，API 复用当前后端服务器
#
set -euo pipefail

# ==================== 演示环境配置（可通过环境变量覆盖） ====================
DEMO_HOST="${DEMO_HOST:-demo2.zhiyu.com.cn}"
DEMO_USER="${DEMO_USER:-root}"
DEMO_PASS="${DEMO_PASS:-lEL9cHcBQMjCEqp6}"
OLD_IP="${OLD_IP:-111.170.170.202}"

# ==================== 项目配置（每个项目只需改这里） ====================
SITE_NAME="zhiyu-ai"
PORT=3008
# 后端服务器地址（当前服务器）
BACKEND_URL="${BACKEND_URL:-http://111.170.170.202:8000}"

# ==================== 自动推导 ====================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_BASE="/var/www"
REMOTE_DIR="$REMOTE_BASE/$SITE_NAME"
LOCAL_BUILD_DIR="$SCRIPT_DIR/.deploy"
LOCAL_PUBLIC_DIR="$LOCAL_BUILD_DIR/public"
SSH_PORT="${SSH_PORT:-22}"

# 本地构建产物备份目录（放在 /tmp 下，避免污染源码）
LOCAL_BUILD_BACKUP_DIR="/tmp/${SITE_NAME}-local-build-backup"

# 安全提示
if [ -z "${DEMO_PASS:-}" ]; then
  echo "❌ 错误：未设置 DEMO_PASS 环境变量且脚本默认密码为空"
  exit 1
fi

# 检查 sshpass
if ! command -v sshpass &>/dev/null; then
  echo "❌ 未检测到 sshpass，请先安装："
  echo "   Debian/Ubuntu: sudo apt-get install -y sshpass"
  exit 1
fi

# 通过环境变量传密码，避免出现在进程列表
export SSHPASS="$DEMO_PASS"
SSH_CMD="sshpass -e ssh"
SCP_CMD="sshpass -e scp"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -p $SSH_PORT"

cd "$SCRIPT_DIR"

# ==================== IP 替换与还原 ====================
backup_files=()

replace_ip() {
  local old="$1" new="$2"
  local files
  local old_pattern
  old_pattern=$(sed 's/\./\\./g' <<< "$old")

  mapfile -t files < <(grep -rlF \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.next \
    --exclude-dir=.deploy \
    --exclude-dir=.deploy-local \
    --exclude-dir=dist \
    --exclude-dir=venv \
    --exclude-dir=uploads \
    --exclude-dir=__pycache__ \
    --exclude='*.demo-bak' \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='deploydemo.sh' \
    --exclude='deploy.sh' \
    --exclude='deploycom.sh' \
    --exclude='deploy.ps1' \
    --exclude='*.tar.gz' \
    "$old" . 2>/dev/null || true)

  for f in "${files[@]}"; do
    if [ -f "$f" ]; then
      cp "$f" "$f.demo-bak"
      backup_files+=("$f")
      sed -i "s/$old_pattern/$new/g" "$f"
      echo "  已替换: $f"
    fi
  done
}

restore_ip() {
  if [ ${#backup_files[@]} -eq 0 ]; then
    return 0
  fi
  echo ""
  echo ">>> 还原源码中的 IP 配置..."
  for f in "${backup_files[@]}"; do
    mv "$f.demo-bak" "$f"
    echo "  已还原: $f"
  done
}

backup_local_build() {
  if [ -d "$LOCAL_BUILD_DIR" ]; then
    echo ">>> 备份本地构建产物到 $LOCAL_BUILD_BACKUP_DIR ..."
    rm -rf "$LOCAL_BUILD_BACKUP_DIR"
    cp -a "$LOCAL_BUILD_DIR" "$LOCAL_BUILD_BACKUP_DIR"
  fi
}

restore_local_build() {
  if [ -n "${LOCAL_BUILD_BACKUP_DIR:-}" ] && [ -d "$LOCAL_BUILD_BACKUP_DIR" ]; then
    echo ""
    echo ">>> 还原本地构建产物..."
    rm -rf "$LOCAL_BUILD_DIR"
    cp -a "$LOCAL_BUILD_BACKUP_DIR" "$LOCAL_BUILD_DIR"
    rm -rf "$LOCAL_BUILD_BACKUP_DIR"
    # 重启本地 PM2 服务
    if command -v pm2 &>/dev/null; then
      pm2 restart "$SITE_NAME" --update-env >/dev/null 2>&1 || true
    fi
  fi
}

# 脚本退出时还原源码 IP 和本地构建产物
trap 'restore_ip; restore_local_build' EXIT

# 清理上次残留的备份文件
find . -maxdepth 3 -name '*.demo-bak' -type f -delete 2>/dev/null || true

# ==================== 主流程 ====================
echo ""
echo "🚀 启动前端演示环境部署: [$SITE_NAME] -> http://$DEMO_HOST:$PORT"
echo "   API 后端: $BACKEND_URL"
echo ""

echo "[1/5] 替换源码中的旧 IP ($OLD_IP -> $DEMO_HOST)..."
replace_ip "$OLD_IP" "$DEMO_HOST"

echo ""
echo "[1.5/5] 备份本地构建产物..."
backup_local_build

echo ""
echo "[2/5] 准备本地前端产物..."
rm -rf "$LOCAL_BUILD_DIR"
mkdir -p "$LOCAL_PUBLIC_DIR"
cp -a "$SCRIPT_DIR/backend/static/." "$LOCAL_PUBLIC_DIR/"
cp "$SCRIPT_DIR/server.js" "$LOCAL_BUILD_DIR/server.js"
echo "  已复制 backend/static/* 和 server.js 到 $LOCAL_BUILD_DIR"

echo ""
echo "[3/5] 上传产物到远程服务器 $DEMO_HOST..."
$SSH_CMD $SSH_OPTS "$DEMO_USER@$DEMO_HOST" \
  "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR && chown $DEMO_USER:$DEMO_USER $REMOTE_DIR"

rsync -az --delete \
  -e "$SSH_CMD $SSH_OPTS" \
  --timeout=300 \
  "$LOCAL_BUILD_DIR/" \
  "$DEMO_USER@$DEMO_HOST:$REMOTE_DIR/"

echo ""
echo "[4/5] 远程启动服务..."
$SSH_CMD $SSH_OPTS "$DEMO_USER@$DEMO_HOST" \
  "export SITE_NAME='$SITE_NAME'; export PORT='$PORT'; export BACKEND_URL='$BACKEND_URL'; export REMOTE_DIR='$REMOTE_DIR'; bash -s" << 'REMOTE_EOF'
  set -e
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

  NODE_BIN=$(command -v node || echo "/usr/local/bin/node")
  if [ ! -x "$NODE_BIN" ]; then
    echo "❌ 远程服务器未找到 node，请先安装 Node.js"
    exit 1
  fi

  # 自动安装 pm2（未安装时）
  if ! command -v pm2 &>/dev/null; then
    echo ">>> 远程安装 pm2..."
    "$NODE_BIN" "$(command -v npm || echo '/usr/local/bin/npm')" install -g pm2
  fi

  # 彻底删除旧进程防止残留
  pm2 delete "$SITE_NAME" &>/dev/null || true

  cd "$REMOTE_DIR"

  # 启动新进程
  PORT="$PORT" BACKEND_URL="$BACKEND_URL" HOSTNAME="0.0.0.0" pm2 start server.js \
    --name "$SITE_NAME" \
    --interpreter "$NODE_BIN" \
    --restart-delay 3000

  pm2 save > /dev/null
REMOTE_EOF

echo ""
echo "[5/5] 等待服务就绪..."
sleep 2
$SSH_CMD $SSH_OPTS "$DEMO_USER@$DEMO_HOST" \
  "pm2 restart '$SITE_NAME' --update-env" >/dev/null 2>&1 || true

echo ""
echo "✨ [$SITE_NAME] 前端演示环境部署完成！"
echo "   访问地址: http://$DEMO_HOST:$PORT"
echo "   API 代理: $BACKEND_URL"
echo ""
