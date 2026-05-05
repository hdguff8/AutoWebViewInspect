![Banner](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/AutoWebViewInspectBanner.png?raw=true)

> **为 Android 开发者而生的全自动离线 WebView 调试利器。**

**AutoWebViewInspect** 是一款专为移动端 Web 开发者打造的自动化调试工具，旨在成为 `chrome://inspect` 更好用、更高效的替代方案。它彻底终结了在传统调试页面中加载缓慢、频繁重连的痛苦，让移动端调试回归流畅。

---

## 🚀 核心亮点

- **🌐 不挑网络环境**：内置完整 Chromium 调试资源，彻底告别“因无法连接 Google 服务器导致调试页白屏”的尴尬，内网、离线环境均可毫秒级加载。
- **💎 与 Chrome 一致的体验**：集成 Chrome DevTools 引擎，熟悉的 Console、Elements、Network、Application 等功能应有尽有。
- **⚡ 全自动 WebView 探测**：无需手动寻找目标。即插即用，系统自动轮询并完成端口转发，瞬间唤起调试窗口；App 关闭时自动回收资源。
- **📱 透明的 ADB 设备管理**：可视化管理多设备连接，支持一键重启 ADB 服务、清理转发异常，让连接状态一目了然。
- **📦 零配置上手**：无需安装 Python 或配置复杂的环境变量。下载 RAR 免安装包，自带运行环境，双击即可开始开发。

---

## ✨ 软件功能

### 1. 极致的调试面板
Chrome 原生调试体验，支持完整的断点调试、性能分析及网络抓包。
![调试面板](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-index-0.png?raw=true)
![调试交互](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-index-1.png?raw=true)

### 2. 自动化目标捕获
实时监控手机端的 WebView 状态，自动捕获调试目标，让您专注于代码本身。
![目标列表](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-index-2.png?raw=true)

### 3. 可视化 ADB 控制台
集成 ADB 核心运维功能，通过 UI 界面快速排查设备连接问题，不再需要记忆复杂的命令行。
![ADB管理](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-adb.png?raw=true)

### 4. 实时日志系统
支持 DEBUG/INFO/WARN/ERROR 分级过滤，帮助您精准捕捉移动端的各种报错信息。
![日志系统](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-log.png?raw=true)

### 5. 个性化系统设置
轻松切换内置 ADB 与系统 ADB，灵活适配不同的开发环境需求。
![系统设置](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/img/page-setting.png?raw=true)

---

## 快速开始

#### 📦 开箱即用（推荐）
**无需安装任何运行环境，解压即用。**

1. 前往项目的 [**Releases 页面**](https://github.com/hdguff8/AutoWebViewInspect/releases) 下载最新的绿色免安装包（rar）。 
2. 将压缩包解压至任意目录。 
3. 双击运行 `AutoWebViewInspect.exe`。
4. 连接手机（开启 **USB 调试**），在 App 内打开 WebView，调试窗口将自动弹出。

### 💻 源码运行
如果您希望进行二次开发，请按以下步骤配置：

#### 1. 环境准备
确保系统安装了 **Python 3.10+**。
```bash
pip install -r dependence.txt
```

#### 2. 资源配置
- **DevTools 资源**：从 [Resources 分支](https://github.com/hdguff8/AutoWebViewInspect/blob/Resources/chrome_devtools_frontend.rar) 下载 `chrome_devtools_frontend.rar`，解压至 `chrome_devtools_frontend/`。
- **ADB 工具**：将 `adb.exe` 及其相关 DLL 放入 `adb/` 目录。

#### 3. 启动程序
```bash
python main_app.py
```

---

## 📜 鸣谢与说明

- **灵感来源**：向 WebDebugX 致敬，感谢其在 Web 调试领域的启发。
- **License**：本项目采用 [Apache 2.0 License](LICENSE) 开源。
- **免责声明**：本工具仅供开发者学习与交流使用。