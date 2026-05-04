import sys
import os
import urllib.parse
import socket

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QMessageBox, QPushButton, QFrame, QTreeWidget, 
                             QStackedWidget, QLabel, QTreeWidgetItem, QGraphicsOpacityEffect)
from PySide6.QtCore import QTimer, QUrl, Slot, Qt, Signal, QThread, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PySide6.QtGui import QKeySequence, QShortcut, QColor, QIcon

# 核心模块导入
from core.core_bridge import ADBDebuggerBridge
from core.proxy_server import WSProxyThread
from core.scan_worker import ScanWorker
from core.debug_view import DebugBrowserView
from core.utils import LogStream, get_resource_path

# 页面模块导入
from pages.debug_page import DebugPage
from pages.log_page import LogPage
from pages.settings_page import SettingsPage

class AnimatedStackedWidget(QStackedWidget):
    """支持淡入淡出和位移动画的堆栈窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 300
        self.setStyleSheet("background-color: #1e1e1e; border: none;")

    def setCurrentIndex(self, index):
        if index == self.currentIndex():
            return
        
        old_widget = self.currentWidget()
        new_widget = self.widget(index)
        
        # 1. 设置新组件的透明度动画
        eff = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(eff)
        
        self.anim = QPropertyAnimation(eff, b"opacity")
        self.anim.setDuration(self.duration)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # 2. 设置位移动画 (从下方微动上来)
        self.pos_anim = QPropertyAnimation(new_widget, b"pos")
        self.pos_anim.setDuration(self.duration)
        # 注意：这里的起始位置需要根据当前 widget 的大小动态计算
        # 简单起见，我们做一个向上的偏移
        self.pos_anim.setStartValue(QPoint(0, 15))
        self.pos_anim.setEndValue(QPoint(0, 0))
        self.pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.group = QParallelAnimationGroup()
        self.group.addAnimation(self.anim)
        self.group.addAnimation(self.pos_anim)
        
        super().setCurrentIndex(index)
        self.group.start()

class NavButton(QPushButton):
    """自定义导航按钮，支持扁平化风格和简单的 hover 效果"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(70, 55)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.active = False
        self.update_style()

    def set_active(self, active):
        self.active = active
        self.update_style()

    def update_style(self):
        if self.active:
            style = """
                QPushButton {
                    color: #007acc;
                    background-color: #252526;
                    border-left: 3px solid #007acc;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
        else:
            style = """
                QPushButton {
                    color: #969696;
                    background-color: transparent;
                    border: none;
                    font-weight: normal;
                    font-size: 13px;
                }
                QPushButton:hover {
                    color: white;
                    background-color: #37373d;
                }
            """
        self.setStyleSheet(style)

class CommandWorker(QThread):
    """通用命令执行 Worker，用于非阻塞执行 ADB 操作"""
    finished = Signal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            print(f"命令执行失败: {e}")
            self.finished.emit(None)

class AutoWebViewInspect(QMainWindow):
    log_received = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoWebViewInspect - 自动化离线调试终端")
        self.resize(1400, 900)
        
        # 1. 初始化数据与组件
        self.bridge = ADBDebuggerBridge()
        
        # 设置项目图标
        self.icon_path = get_resource_path(os.path.join("static", "App.png"))
        self.setWindowIcon(QIcon(self.icon_path))
        
        # 设置窗口背景色，防止初始白闪
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; }")
        self.current_page_id = None 
        self.current_ws_url = None 
        self.known_page_ids = set() 
        self.all_logs = []
        self.log_limits = {"DEBUG": 2000, "INFO": 1000, "WARN": 500, "ERROR": 500}
        self._active_workers = set()
        
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading_text)
        self.loading_dots = 0
        self.current_loading_msg = ""

        # 2. 资源与服务初始化
        self.devtools_dir = get_resource_path("chrome_devtools_frontend")
        self.static_dir = get_resource_path("static")
        self.empty_page_url = QUrl.fromLocalFile(os.path.join(self.static_dir, "empty_page.html"))
        
        self.proxy_thread = WSProxyThread(start_port=9223, target_port=9222)
        self.proxy_thread.start()
        self.proxy_thread._bind_success.wait(timeout=2)
        self.proxy_port = self.proxy_thread.listen_port
        
        self.entry_file_path = self._find_entry_file()
        self.entry_url_base = QUrl.fromLocalFile(self.entry_file_path).toString()

        # 3. 创建页面组件
        self.browser = DebugBrowserView()
        self.browser.load(self.empty_page_url)
        
        self.debug_page = DebugPage()
        self.log_page = LogPage()
        self.settings_page = SettingsPage()
        
        self.setup_ui()
        self.bind_events()
        
        # 4. 日志系统对接
        self.stdout_logger = LogStream(self.log_received, default_level="INFO")
        self.stderr_logger = LogStream(self.log_received, default_level="ERROR")
        sys.stdout = self.stdout_logger
        sys.stderr = self.stderr_logger
        
        self._init_late()

    def bind_events(self):
        self.log_received.connect(self.update_log_view)
        
        # Debug 页面事件
        self.debug_page.check_devices_clicked.connect(self.quick_check_devices)
        self.debug_page.restart_adb_clicked.connect(self.quick_restart_adb)
        self.debug_page.clear_forward_clicked.connect(self.quick_clear_forward)
        self.debug_page.release_adb_clicked.connect(self.toggle_adb_monitoring)
        self.debug_page.check_responsive_clicked.connect(self.quick_check_responsiveness)
        
        # Settings 页面事件
        self.settings_page.adb_mode_changed.connect(self.on_adb_mode_changed)
        
        # Log 页面事件
        self.log_page.btn_clear_logs.clicked.connect(self.clear_logs)
        self.log_page.filter_changed.connect(self.on_log_filter_changed)

    def on_log_filter_changed(self, level):
        # 仅刷新显示，不删除 all_logs 中的日志
        self.refresh_log_display()

    def toggle_adb_monitoring(self, is_released):
        """处理 ADB 监控的停止与恢复"""
        if is_released:
            self.logger("正在停止监控并释放 ADB 资源...", "INFO")
            if hasattr(self, 'scan_worker') and self.scan_worker.isRunning():
                self.scan_worker.stop()
            # 执行一次清理转发，确保其他工具可以接管端口
            self.bridge.run_cmd(['adb', 'forward', '--remove-all'])
            self.logger("ADB 监控已停止，资源已释放", "INFO")
        else:
            self.logger("正在恢复 ADB 监控...", "INFO")
            # 重新创建并启动扫描线程
            if not hasattr(self, 'scan_worker') or not self.scan_worker.isRunning():
                self.scan_worker = ScanWorker(self.bridge)
                self.scan_worker.targets_found.connect(self.on_targets_found)
                self.scan_worker.start()
            self.logger("ADB 监控已恢复", "INFO")

    def _init_late(self):
        QShortcut(QKeySequence("F5"), self).activated.connect(self.browser.reload)
        QShortcut(QKeySequence("F12"), self).activated.connect(self.browser.open_internal_devtools)

        self.scan_worker = ScanWorker(self.bridge)
        self.scan_worker.targets_found.connect(self.on_targets_found)
        self.scan_worker.start()

        QTimer.singleShot(1000, self.check_proxy_health)
        self.logger("系统初始化完成", "INFO")

    def logger(self, content, level="INFO"):
        if level == "ERROR":
            self.stderr_logger.log(content, level)
        else:
            self.stdout_logger.log(content, level)

    def _find_entry_file(self):
        for name in ["inspector.html", "devtools_app.html"]:
            path = os.path.join(self.devtools_dir, name)
            if os.path.exists(path): return path
        QMessageBox.critical(self, "错误", "未找到 DevTools 入口文件！")
        sys.exit(1)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(70)
        self.sidebar.setStyleSheet("background-color: #333333; border: none;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        self.btn_pages = NavButton("页面")
        self.btn_debug = NavButton("调试")
        self.btn_logs = NavButton("日志")
        self.btn_settings = NavButton("设置")
        
        self.nav_buttons = [self.btn_pages, self.btn_debug, self.btn_logs, self.btn_settings]
        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # 二级侧边栏 (目标列表)
        self.sub_sidebar = QFrame()
        self.sub_sidebar.setFixedWidth(280)
        self.sub_sidebar.setStyleSheet("background-color: #252526; border-right: 1px solid #3c3c3c;")
        sub_layout = QVBoxLayout(self.sub_sidebar)
        title_label = QLabel("调试目标列表")
        title_label.setStyleSheet("color: #cccccc; padding: 15px; font-weight: bold; font-size: 14px; border-bottom: 1px solid #3c3c3c;")
        sub_layout.addWidget(title_label)

        self.target_tree = QTreeWidget()
        self.target_tree.setHeaderHidden(True)
        self.target_tree.setIndentation(20)
        self.target_tree.setStyleSheet("""
            QTreeWidget { 
                background-color: transparent; 
                border: none; 
                color: #cccccc; 
                font-size: 13px;
                outline: none;
            }
            QTreeWidget::item { 
                padding: 12px 5px; 
                border-bottom: 1px solid #2d2d2d;
                transition: background-color 0.2s;
            }
            QTreeWidget::item:hover { 
                background-color: #2a2d2e; 
            }
            QTreeWidget::item:selected { 
                background-color: #37373d; 
                color: #007acc;
                border-left: 3px solid #007acc;
            }
        """)
        self.target_tree.itemClicked.connect(self.on_tree_item_clicked)
        sub_layout.addWidget(self.target_tree)
        main_layout.addWidget(self.sub_sidebar)

        # 内容堆栈
        self.content_stack = AnimatedStackedWidget()
        self.content_stack.addWidget(self.browser)
        self.content_stack.addWidget(self.debug_page)
        self.content_stack.addWidget(self.log_page)
        self.content_stack.addWidget(self.settings_page)
        main_layout.addWidget(self.content_stack)

        self.btn_pages.clicked.connect(lambda: self.switch_module(0))
        self.btn_debug.clicked.connect(lambda: self.switch_module(1))
        self.btn_logs.clicked.connect(lambda: self.switch_module(2))
        self.btn_settings.clicked.connect(lambda: self.switch_module(3))
        self.switch_module(0)

    def switch_module(self, index):
        if self.content_stack.currentIndex() == index:
            return
            
        self.content_stack.setCurrentIndex(index)
        self.sub_sidebar.setVisible(index == 0)
        
        # 更新按钮激活状态
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)

    def on_adb_mode_changed(self, use_builtin):
        version = self.bridge.set_adb_mode(use_builtin)
        mode_str = "内置" if use_builtin else "系统"
        self.settings_page.set_status(f"✓ 已切换至{mode_str} ADB (版本: {version})")
        QTimer.singleShot(3000, lambda: self.settings_page.set_status(""))

    @Slot(object)
    def update_log_view(self, log_obj):
        self.all_logs.append(log_obj)
        level = log_obj['level']
        limit = self.log_limits.get(level, 1000)
        level_logs = [i for i, log in enumerate(self.all_logs) if log['level'] == level]
        if len(level_logs) > limit:
            self.all_logs.pop(level_logs[0])
            if len(self.all_logs) % 100 == 0: self.refresh_log_display()
        self.log_page.append_log(log_obj)

    def refresh_log_display(self):
        self.log_page.clear()
        for log in self.all_logs:
            self.log_page.append_log(log)

    def clear_logs(self):
        level_to_clear = self.log_page.current_filter_level
        self.all_logs = [log for log in self.all_logs if self.log_page.log_level_map.get(log['level'], 0) > level_to_clear]
        self.refresh_log_display()

    def on_tree_item_clicked(self, item, column):
        target = item.data(0, Qt.UserRole)
        if target: self.load_target(target)

    def get_unique_id(self, target):
        return f"{target.get('device', 'unknown')}_{target.get('id', 'no-id')}"

    def load_target(self, target, force=False):
        page_id = self.get_unique_id(target)
        ws_url_raw = target.get('webSocketDebuggerUrl')
        if not ws_url_raw or (not force and page_id == self.current_page_id and ws_url_raw == self.current_ws_url):
            return

        ws_endpoint = ws_url_raw.replace("ws://", "").replace("localhost", "127.0.0.1").replace(":9222", f":{self.proxy_port}")
        params = {"ws": ws_endpoint, "remoteFrontend": "true", "dockSide": "undocked"}
        final_url = f"{self.entry_url_base}?{urllib.parse.urlencode(params)}"
        self.browser.load(QUrl(final_url))
        self.current_page_id, self.current_ws_url = page_id, ws_url_raw
        self.setWindowTitle(f"调试: {target.get('title')} - AutoWebViewInspect")

    @Slot(list)
    def on_targets_found(self, targets):
        current_ids = {self.get_unique_id(t) for t in targets if t.get('id')}
        new_ids = current_ids - self.known_page_ids
        device_groups = {}
        active_target_updated = False 
        newly_added_target = None 

        for t in targets:
            tid, did = self.get_unique_id(t), t.get('device', '未知设备')
            if did not in device_groups: device_groups[did] = []
            device_groups[did].append(t)
            if self.current_page_id and tid == self.current_page_id:
                if t.get('webSocketDebuggerUrl') != self.current_ws_url: self.load_target(t, force=True)
                active_target_updated = True
            if tid in new_ids and newly_added_target is None and t.get('webSocketDebuggerUrl'):
                newly_added_target = t

        if newly_added_target: self.load_target(newly_added_target, force=True)
        elif not active_target_updated and self.current_page_id:
            self.current_page_id = self.current_ws_url = None
            debuggable = [t for t in targets if t.get('webSocketDebuggerUrl')]
            if debuggable: self.load_target(debuggable[0])
            else: self.browser.load(self.empty_page_url)
        elif self.current_page_id is None and targets:
            debuggable = [t for t in targets if t.get('webSocketDebuggerUrl')]
            if debuggable: self.load_target(debuggable[0])

        if self.debug_page.btn_check_devices.isEnabled():
            # 获取当前下拉菜单中的所有设备
            existing_devices = [self.debug_page.device_selector.itemText(i) for i in range(self.debug_page.device_selector.count())]
            # 获取当前发现的目标所属的所有设备
            target_devices = list(set(t.get('device') for t in targets if t.get('device')))
            
            # 合并设备列表（并集）
            all_devices = sorted(list(set(existing_devices + target_devices)))
            
            if all_devices and set(all_devices) != set(existing_devices):
                # 只有当设备列表发生变化时才更新，且不主动清空已有设备
                self.debug_page.update_devices(all_devices)

        if targets: self.known_page_ids.update(current_ids)
        self.update_tree_ui(device_groups)

    def update_tree_ui(self, device_groups):
        self.target_tree.blockSignals(True)
        self.target_tree.clear()
        
        # 定义设备项的字体样式 (加粗)
        device_font = self.target_tree.font()
        device_font.setBold(True)
        device_font.setPointSize(10)

        for did, d_targets in device_groups.items():
            device_item = QTreeWidgetItem(self.target_tree)
            device_item.setText(0, f"📱 {did}")
            device_item.setFont(0, device_font)
            device_item.setExpanded(True)
            device_item.setFlags(device_item.flags() & ~Qt.ItemIsSelectable) # 设备行不可选中
            
            for t in d_targets:
                page_item = QTreeWidgetItem(device_item)
                title = t.get('title', '无标题')
                # 限制标题长度，防止过长
                if len(title) > 25:
                    title = title[:22] + "..."
                
                page_item.setText(0, f"  📄 {title}")
                page_item.setData(0, Qt.UserRole, t)
                
                if self.get_unique_id(t) == self.current_page_id:
                    self.target_tree.setCurrentItem(page_item)
                    page_item.setSelected(True)
        self.target_tree.blockSignals(False)

    def update_loading_text(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        self.debug_page.set_status(f"{self.current_loading_msg}{'.' * self.loading_dots}")

    def start_loading(self, msg):
        self.current_loading_msg = msg
        self.loading_timer.start(500)

    def stop_loading(self, final_msg):
        self.loading_timer.stop()
        self.debug_page.set_status(final_msg)

    def quick_check_devices(self):
        self.start_loading("正在执行检测")
        self.debug_page.set_buttons_enabled(False)
        worker = CommandWorker(self.bridge.get_devices)
        self._active_workers.add(worker)
        def on_finished(devices):
            self.debug_page.set_buttons_enabled(True)
            self.stop_loading(f"连接设备: {', '.join(devices)}" if devices else "未发现设备")
            if devices: self.debug_page.update_devices(devices)
            self._active_workers.discard(worker)
        worker.finished.connect(on_finished)
        worker.start()

    def quick_restart_adb(self):
        self.start_loading("正在重启 ADB 服务")
        self.debug_page.set_buttons_enabled(False)
        worker = CommandWorker(self.bridge.restart_adb)
        self._active_workers.add(worker)
        def on_finished(_):
            self.debug_page.set_buttons_enabled(True)
            self.stop_loading("ADB 服务已重启")
            self._active_workers.discard(worker)
        worker.finished.connect(on_finished)
        worker.start()

    def quick_clear_forward(self):
        self.start_loading("正在清理转发")
        self.debug_page.set_buttons_enabled(False)
        worker = CommandWorker(self.bridge.run_cmd, ['adb', 'forward', '--remove-all'])
        self._active_workers.add(worker)
        def on_finished(_):
            self.debug_page.set_buttons_enabled(True)
            self.stop_loading("已清理转发")
            self._active_workers.discard(worker)
        worker.finished.connect(on_finished)
        worker.start()

    def quick_check_responsiveness(self, target_device):
        if not target_device: return
        self.start_loading(f"检查 {target_device} 响应")
        self.debug_page.set_buttons_enabled(False)
        worker = CommandWorker(self.bridge.check_device_responsiveness, target_device)
        self._active_workers.add(worker)
        def on_finished(is_responsive):
            self.debug_page.set_buttons_enabled(True)
            self.stop_loading(f"设备 {target_device} " + ("响应正常" if is_responsive else "无响应"))
            self._active_workers.discard(worker)
        worker.finished.connect(on_finished)
        worker.start()

    def check_proxy_health(self):
        try:
            with socket.create_connection(("127.0.0.1", self.proxy_port), timeout=1): pass
        except Exception: self.logger("代理端口测试失败", "WARN")

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-web-security --allow-file-access-from-files --remote-allow-origins=* --ignore-certificate-errors --no-sandbox"
    app = QApplication(sys.argv)
    window = AutoWebViewInspect()
    window.show()
    sys.exit(app.exec())
