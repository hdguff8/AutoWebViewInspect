import subprocess
import re
import time
import os
import sys
from core.utils import get_resource_path

class ADBDebuggerBridge:
    def __init__(self, start_port=9222):
        self.start_port = start_port
        self.active_forwards = {}  # 存储设备PID与本地端口的映射
        
        # 设置本地 ADB 路径
        self.builtin_adb = os.path.join(get_resource_path("adb"), "adb.exe")
        self.adb_path = self.builtin_adb if os.path.exists(self.builtin_adb) else "adb"
        
        # 记录一下使用的是哪个 ADB
        self.logger(f"初始化 ADB 路径: {self.adb_path}", "DEBUG")

    def get_adb_version(self):
        """获取当前 ADB 的版本信息"""
        output = self.run_cmd(['adb', 'version'])
        if not output: return "未知版本"
        match = re.search(r'Version\s+([\d\.]+)', output)
        return match.group(1) if match else "未知版本"

    def set_adb_mode(self, use_builtin=True):
        """设置 ADB 运行模式：内置或系统"""
        if use_builtin and os.path.exists(self.builtin_adb):
            self.adb_path = self.builtin_adb
        else:
            self.adb_path = "adb"
        version = self.get_adb_version()
        self.logger(f"已切换 ADB 模式, 当前路径: {self.adb_path}, 版本: {version}", "INFO")
        return version

    def logger(self, content, level="INFO"):
        """调用全局 LogStream 进行显式等级日志记录"""
        if hasattr(sys.stdout, 'log'):
            sys.stdout.log(content, level)
        else:
            # 降级方案：如果 stdout 没被重定向，则使用带前缀的 print
            print(f"[{level}] {content}")

    def run_cmd(self, cmd, timeout=10):
        """执行系统命令并返回输出，增加编码兼容性处理"""
        # 将命令中的 'adb' 替换为实际路径
        if cmd and cmd[0] == 'adb':
            cmd[0] = self.adb_path
            
        try:
            # 增加 creationflags=0x08000000 (CREATE_NO_WINDOW) 防止打包后执行命令时弹出 CMD 黑框
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                check=True,
                timeout=timeout,
                creationflags=0x08000000
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger(f"命令执行超时: {' '.join(cmd)}", "WARN")
            return ""
        except subprocess.CalledProcessError:
            return ""
        except Exception as e:
            self.logger(f"命令执行异常 ({' '.join(cmd)}): {e}", "ERROR")
            # 最后的退路：尝试系统默认编码
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout, creationflags=0x08000000)
                return result.stdout.strip()
            except Exception as e2:
                self.logger(f"备选执行方案也失败了: {e2}", "ERROR")
                return ""

    def get_devices(self):
        """获取所有已连接的设备 ID"""
        output = self.run_cmd(['adb', 'devices'])
        if not output: return []
        devices = re.findall(r'^(\S+)\tdevice$', output, re.MULTILINE)
        return devices

    def find_webview_sockets(self, device_id):
        """在设备中寻找 WebView 的调试套接字 (Socket)"""
        self.logger(f"正在扫描设备 {device_id} 的 WebView Sockets...", "DEBUG")
        
        # 策略 1: 使用 grep -a (处理可能存在的二进制流)
        cmd_grep_a = ['adb', '-s', device_id, 'shell', 'grep -a "webview_devtools_remote" /proc/net/unix']
        output = self.run_cmd(cmd_grep_a, timeout=4)
        
        if not output:
            # 策略 2: 使用标准 grep (部分设备不支持 -a)
            cmd_grep = ['adb', '-s', device_id, 'shell', 'grep "webview_devtools_remote" /proc/net/unix']
            output = self.run_cmd(cmd_grep, timeout=4)
            
        if not output:
            # 策略 3: 使用原始 cat 并由 Python 处理 (最后的手段)
            cmd_cat = ['adb', '-s', device_id, 'shell', 'cat /proc/net/unix']
            output = self.run_cmd(cmd_cat, timeout=6)
        
        # 匹配包含 webview_devtools_remote 的路径
        sockets = re.findall(r'webview_devtools_remote_\d+', output)
        return list(set(sockets))

    def restart_adb(self):
        """深度清理 ADB 服务"""
        self.logger("正在重启 ADB 服务...", "INFO")
        subprocess.run([self.adb_path, 'kill-server'], capture_output=True, creationflags=0x08000000)
        time.sleep(1)
        subprocess.run([self.adb_path, 'start-server'], capture_output=True, creationflags=0x08000000)
        time.sleep(2) # 等待服务稳定

    def check_device_responsiveness(self, device_id):
        """检查设备是否有响应 (通过 echo 命令)"""
        self.logger(f"正在检查设备 {device_id} 的响应能力...", "INFO")
        test_str = "response_check_ping"
        cmd = ['adb', '-s', device_id, 'shell', f'echo {test_str}']
        output = self.run_cmd(cmd, timeout=5)
        
        if output == test_str:
            self.logger(f"设备 {device_id} 响应正常", "INFO")
            return True
        else:
            self.logger(f"设备 {device_id} 无响应或返回错误: {output}", "WARN")
            return False

    def setup_forwarding(self, retry_on_timeout=False):
        """自动执行端口转发"""
        devices = self.get_devices()
        
        if not devices and retry_on_timeout:
            # 如果没发现设备，尝试重启服务再试一次
            self.restart_adb()
            devices = self.get_devices()

        if not devices:
            self.logger("未发现已连接的 ADB 设备", "DEBUG")
            return
        # 获取当前系统中已经存在的 adb forward 列表
        existing_forwards_raw = self.run_cmd(['adb', 'forward', '--list'])
        
        current_port = self.start_port
        new_active_forwards = {}

        for device in devices:
            sockets = self.find_webview_sockets(device)
            if not sockets:
                self.logger(f"设备 {device} 未发现可调试的 WebView", "DEBUG")
                continue
            
            for socket in sockets:
                local_port = current_port
                # 兼容不同版本的 adb forward --list 输出格式 (空格/制表符)
                # 只要 serial 和 localabstract 匹配即可
                found_existing = False
                for line in existing_forwards_raw.splitlines():
                    if device in line and f"tcp:{local_port}" in line and socket in line:
                        found_existing = True
                        break
                
                if not found_existing:
                    cmd = ['adb', '-s', device, 'forward', f'tcp:{local_port}', f'localabstract:{socket}']
                    self.run_cmd(cmd)
                    self.logger(f"建立新转发: 127.0.0.1:{local_port} -> {socket}", "INFO")
                else:
                    # self.logger(f"转发已存在: 127.0.0.1:{local_port} -> {socket}", "DEBUG")
                    pass
                
                new_active_forwards[socket] = {
                    "device": device,
                    "local_port": local_port,
                    "debug_url": f"http://127.0.0.1:{local_port}/json"
                }
                current_port += 1
        
        self.active_forwards = new_active_forwards

    def list_debug_targets(self):
        """获取所有可调试的页面信息 (需要安装 httpx)"""
        import httpx
        targets = []
        for socket, info in self.active_forwards.items():
            try:
                resp = httpx.get(info['debug_url'], timeout=0.5)
                if resp.status_code == 200:
                    pages = resp.json()
                    for page in pages:
                        # 补充一些元数据
                        page['local_port'] = info['local_port']
                        page['device'] = info['device']
                        targets.append(page)
            except Exception:
                continue
        return targets

if __name__ == "__main__":
    bridge = ADBDebuggerBridge()
    last_target_ids = set()
    
    print("\n" + "="*60)
    print("  WebDebugRS - 持续监测模式已启动")
    print("  正在后台自动同步 ADB 设备与 WebView 状态...")
    print("="*60 + "\n")

    # 首次启动执行一次深度清理
    bridge.run_cmd(['adb', 'forward', '--remove-all'])
    
    try:
        while True:
            # 执行扫描和转发
            bridge.setup_forwarding(retry_on_timeout=False)
            targets = bridge.list_debug_targets()
            
            # 获取当前所有目标的 ID 集合，用于判断是否发生变化
            current_target_ids = {t.get('id') for t in targets if t.get('id')}
            
            if current_target_ids != last_target_ids:
                if not targets:
                    print(f"[{time.strftime('%H:%M:%S')}] [-] 未发现活动目标。请确保 App 已打开且处于前台。")
                else:
                    print(f"\n[{time.strftime('%H:%M:%S')}] [!] 状态更新：发现 {len(targets)} 个可调试目标")
                    print("-" * 60)
                    for t in targets:
                        ws_url = t.get('webSocketDebuggerUrl')
                        if not ws_url: continue
                        
                        clean_ws = ws_url.replace("ws://", "")
                        local_debug_url = f"devtools://devtools/bundled/inspector.html?ws={clean_ws}"

                        print(f"【{t.get('title', '无标题')}】")
                        print(f"  PID: {t.get('description', '未知')}")
                        print(f"  调试地址: \033[92m{local_debug_url}\033[0m")
                        print("-" * 60)
                
                last_target_ids = current_target_ids
            
            # 这里的休眠时间决定了监测灵敏度
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n[退出] 监测已停止。")
    except Exception as e:
        print(f"\n[错误] 监测过程中发生异常: {e}")