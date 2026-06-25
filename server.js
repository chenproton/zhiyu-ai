const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};

const backend = url.parse(BACKEND_URL);

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  // 代理 API 请求到后端服务器
  if (req.url.startsWith('/api/')) {
    const proxyReq = http.request(
      {
        hostname: backend.hostname,
        port: backend.port,
        path: req.url,
        method: req.method,
        headers: { ...req.headers, host: backend.host },
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res);
      }
    );
    proxyReq.on('error', (e) => {
      console.error('Proxy error:', e.message);
      res.writeHead(502);
      res.end('Bad Gateway: ' + e.message);
    });
    req.pipe(proxyReq);
    return;
  }

  // 静态文件服务，找不到则回退到 index.html（SPA）
  // 产物放在 public/ 根目录，HTML 中统一使用 /static/ 路径以复用后端静态目录
  let target = req.url === '/' ? 'index.html' : req.url;
  if (target.startsWith('/static/')) {
    target = target.slice('/static/'.length);
  }
  const filePath = path.join(PUBLIC_DIR, target);
  fs.stat(filePath, (err, stats) => {
    if (!err && stats.isFile()) {
      sendFile(res, filePath);
    } else {
      sendFile(res, path.join(PUBLIC_DIR, 'index.html'));
    }
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Frontend running on port ${PORT}, proxying API to ${BACKEND_URL}`);
});
