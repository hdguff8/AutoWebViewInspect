import threading
import socket
import select
import re

class WSProxyThread(threading.Thread):
    """WebSocket 代理：在 TCP 层面拦截握手并替换 Origin 头部，彻底解决 403 问题"""
    def __init__(self, start_port=9223, target_port=9222):
        super().__init__()
        self.listen_port = start_port
        self.target_port = target_port
        self.daemon = True
        self.running = False
        self._bind_success = threading.Event()

    def run(self):
        # 尝试多个端口，直到成功绑定
        server = None
        for port in range(self.listen_port, self.listen_port + 100):
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("127.0.0.1", port))
                server.listen(20)
                self.listen_port = port
                self.running = True
                print(f"[系统] WebSocket 代理已就绪: 127.0.0.1:{self.listen_port} -> 127.0.0.1:{self.target_port}", flush=True)
                self._bind_success.set()
                break
            except Exception:
                if server:
                    server.close()
                continue
        
        if not self.running:
            print(f"[系统错误] 代理服务器启动失败: 无法绑定到任何可用端口", flush=True)
            self._bind_success.set()
            return

        while True:
            try:
                client_sock, addr = server.accept()
                threading.Thread(target=self.handle_connection, args=(client_sock,), daemon=True).start()
            except:
                break

    def handle_connection(self, client_sock):
        target_sock = None
        try:
            client_addr = client_sock.getpeername()
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.settimeout(5.0)
            target_sock.connect(("127.0.0.1", self.target_port))

            client_sock.settimeout(2.0)
            try:
                data = client_sock.recv(65536)
            except socket.timeout:
                return

            if not data:
                return

            if b"Upgrade: websocket" in data or b"GET " in data:
                # 策略：完全删除 Origin 头部，并伪装 Host 绕过 403 校验
                data = re.sub(b"(?i)Origin:.*?\r\n", b"", data)
                data = re.sub(b"(?i)Host:.*?\r\n", b"Host: 127.0.0.1:9222\r\n", data)
                data = re.sub(b"(?i)Referer:.*?\r\n", b"", data)
                
                if b"\r\n\r\n" not in data:
                    data = data.rstrip() + b"\r\n\r\n"

            target_sock.sendall(data)

            # 透明转发
            inputs = [client_sock, target_sock]
            while True:
                readable, _, _ = select.select(inputs, [], [], 0.5)
                if not readable:
                    continue
                for s in readable:
                    payload = s.recv(65536)
                    if not payload:
                        return
                    if s is client_sock:
                        target_sock.sendall(payload)
                    else:
                        client_sock.sendall(payload)
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
                if target_sock: target_sock.close()
            except:
                pass
