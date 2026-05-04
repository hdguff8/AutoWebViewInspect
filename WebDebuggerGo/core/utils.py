import sys
import os
from datetime import datetime

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境下的项目根目录
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)

class LogStream:
    """
    将 stdout/stderr 重定向到信号的辅助类。
    支持显式等级调用，同时也兼容标准的 print。
    """
    def __init__(self, signal, default_level="INFO"):
        self.signal = signal
        self.default_level = default_level

    def write(self, text):
        """兼容标准 sys.stdout.write (如 print)"""
        if not text or text == '\n': return
        self.log(text.strip(), self.default_level)

    def log(self, content, level="INFO"):
        """显式记录日志的方法"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_data = {
            "time": timestamp,
            "level": level,
            "content": content
        }
        self.signal.emit(log_data)

    def flush(self):
        pass
