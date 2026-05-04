import os
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PySide6.QtGui import QColor

class DebugBrowserView(QWebEngineView):
    """负责显示 Chrome DevTools 的浏览器组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置默认背景颜色，防止加载前的白闪
        self.page().setBackgroundColor(QColor("#1e1e1e"))
        self.setup_security()
        self.page().javaScriptConsoleMessage = self.on_console_message

    def setup_security(self):
        """开启 Chromium 的安全豁免，允许 file:// 访问 WebSocket"""
        settings = self.settings()
        # 核心设置：允许本地加载的资源访问远程或本地端口 (WebSocket)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        # 允许运行不安全内容
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        # 允许本地文件访问其他本地文件 (加载 static 里的 JS/CSS)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        # 允许跨域资源共享
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        # 必须对全局 Profile 也进行同样的设置，否则 DevTools 内部子页面会拦截请求
        p_settings = profile.settings()
        p_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        p_settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        p_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        p_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    def on_console_message(self, level, message, line, source):
        """将 JS 日志打印到终端"""
        if "Autofill" in message: return
        level_name = "LOG"
        try:
            level_name = level.name
        except AttributeError:
            level_name = str(level)
        print(f"    [JS {level_name}] {message} (行:{line}, 来源:{os.path.basename(source)})")

    def open_internal_devtools(self):
        """打开递归调试窗口 (调试调试器本身)"""
        print("[系统] 正在打开递归调试窗口...")
        self.dev_view = QWebEngineView()
        self.page().setDevToolsPage(self.dev_view.page())
        self.dev_view.setWindowTitle("Internal DevTools")
        self.dev_view.resize(1000, 700)
        self.dev_view.show()
