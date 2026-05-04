import time
from PySide6.QtCore import QThread, Signal

class ScanWorker(QThread):
    """异步扫描 Worker：在后台扫描 ADB 设备和页面，不阻塞 UI"""
    targets_found = Signal(list)

    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.active = True

    def run(self):
        while self.active:
            try:
                self.bridge.setup_forwarding()
                targets = self.bridge.list_debug_targets()
                # 无论是否发现目标都发送信号，以便 UI 处理“无目标”状态
                self.targets_found.emit(targets if targets else [])
            except Exception as e:
                print(f"    [扫描异常] {e}")
            time.sleep(2.0)

    def stop(self):
        self.active = False
        self.wait()
