"""
生产部署网关
- 静态资源托管（用户端 + 管理后台）
- API 反向代理到后端
- SPA history 模式支持
- 健康检查

相当于简化版 Nginx
"""
import os
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, urlunparse
import urllib.request
import urllib.error

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
USER_FRONTEND_DIR = os.environ.get("USER_FRONTEND_DIR", "./frontend-user/dist")
ADMIN_FRONTEND_DIR = os.environ.get("ADMIN_FRONTEND_DIR", "./frontend-admin/dist")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class GatewayHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        return path

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/") or path == "/health" or path.startswith("/docs") or path.startswith("/redoc"):
            self._proxy_to_backend()
            return

        if path.startswith("/admin") or path == "/admin":
            self._serve_static(ADMIN_FRONTEND_DIR, path[len("/admin"):] or "/")
            return

        self._serve_static(USER_FRONTEND_DIR, path)

    def do_POST(self):
        self._proxy_to_backend()

    def do_PUT(self):
        self._proxy_to_backend()

    def do_DELETE(self):
        self._proxy_to_backend()

    def do_PATCH(self):
        self._proxy_to_backend()

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self._proxy_to_backend()
        else:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

    def _serve_static(self, base_dir, path):
        if path == "" or path == "/":
            path = "/index.html"

        file_path = os.path.join(base_dir, path.lstrip("/"))

        if os.path.isfile(file_path):
            self._send_file(file_path)
            return

        dot_index = path.rfind(".")
        slash_index = path.rfind("/")
        if dot_index > slash_index:
            self.send_error(404, "File not found")
            return

        index_path = os.path.join(base_dir, "index.html")
        if os.path.isfile(index_path):
            self._send_file(index_path)
        else:
            self.send_error(404, "File not found")

    def _send_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")

            if file_path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf")):
                self.send_header("Cache-Control", "public, max-age=2592000, immutable")

            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def _proxy_to_backend(self):
        parsed = urlparse(self.path)
        backend_url = BACKEND_URL.rstrip("/") + self.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        try:
            req = urllib.request.Request(backend_url, data=body, method=self.command)

            for header in self.headers:
                if header.lower() in ("host", "content-length", "connection"):
                    continue
                req.add_header(header, self.headers[header])

            req.add_header("X-Forwarded-For", self.client_address[0])
            req.add_header("X-Forwarded-Proto", "http")
            req.add_header("X-Real-IP", self.client_address[0])

            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(resp.status)
                for key, val in resp.getheaders():
                    if key.lower() in ("transfer-encoding", "connection", "content-encoding"):
                        continue
                    self.send_header(key, val)
                self.end_headers()

                data = resp.read()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, val in e.headers.items():
                if key.lower() in ("transfer-encoding", "connection"):
                    continue
                self.send_header(key, val)
            self.end_headers()
            body = e.read()
            if body:
                self.wfile.write(body)
        except Exception as e:
            self.send_error(502, f"Bad Gateway: {str(e)}")

    def log_message(self, format, *args):
        print(f"[Gateway] {args[0]}")


def main():
    port = int(os.environ.get("GATEWAY_PORT", "80"))
    server = ThreadedHTTPServer(("0.0.0.0", port), GatewayHandler)
    print(f"部署网关启动 - 端口 {port}")
    print(f"  用户端: http://localhost:{port}/")
    print(f"  管理后台: http://localhost:{port}/admin/")
    print(f"  API 代理: {BACKEND_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n网关停止")
        server.server_close()


if __name__ == "__main__":
    main()
