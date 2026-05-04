import os
import threading
import mimetypes
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

class StaticServerThread(threading.Thread):
    def __init__(self, path, port=8888):
        super().__init__()
        self.path = path
        self.port = port
        self.daemon = True
        self.running = False
        self._bind_success = threading.Event()

    def run(self):
        mimetypes.add_type('application/javascript', '.js')
        mimetypes.add_type('text/css', '.css')
        mimetypes.add_type('application/json', '.json')
        
        # 使用 directory 参数运行，避免 os.chdir 干扰全局路径
        handler_class = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=self.path, **kwargs)
        
        for port in range(self.port, self.port + 10):
            try:
                with TCPServer(("127.0.0.1", port), handler_class) as httpd:
                    self.port = port
                    self.running = True
                    print(f"[系统] 静态资源服务器已启动: http://127.0.0.1:{self.port}", flush=True)
                    self._bind_success.set()
                    httpd.serve_forever()
                    break
            except:
                continue
        
        if not self.running:
            print(f"[系统错误] 静态服务器启动失败", flush=True)
            self._bind_success.set()
