![Banner](https://github.com/hdguff8/WebDebuggerGo/blob/main/static/WebDebuggerGoBanner.png?raw=true)

> **为 Android/HBuilderX 开发者而生的全自动离线 WebView 调试利器。**

**WebDebuggerGo** 是一款专为 HBuilderX 生态打造的自动化调试终端。它彻底终结了在 `chrome://inspect` 页面中反复查找、频繁重连的痛苦，让移动端 Web 调试回归本应有的流畅体验。

---

## 💡 为什么选择 WebDebuggerGo?

|     |     |     |
| --- | --- | --- |
| **特性** | **传统 chrome://inspect** | **WebDebuggerGo** |
| **连接体验** | 手动寻找目标，点击 inspect | **即插即用，自动捕获并弹出窗口** |
| **网络要求** | 容易加载不出来google相关资源 | **全离线支持，本地毫秒级加载** |
| **连接稳定性** | 刷新页面易断开，需重新开启 | **断线自动重连，状态实时保持** |

---

## ✨ 核心能力

- **⚡ 自动化捕获**：实时轮询 ADB Unix 域套接字，发现 WebView 瞬间自动完成端口转发并唤起调试界面。
- **🌐 离线 DevTools 引擎**：内置完整 Chromium 调试器资源，彻底告别“由于无法连接 Google 服务器导致调试界面白屏”的尴尬。
- **🛡️ WebSocket 代理**：底层拦截 HTTP 升级请求，动态剔除限制性 Header，完美解决 Android 系统对调试来源的 Origin 限制。
- **📊 日志系统**：
  - **分级过滤**：支持 DEBUG/INFO/WARN/ERROR 实时筛选。
- **🛠️ ADB 工具箱**：集成一键重启 ADB 服务、清理转发、设备状态探测等运维功能。  
  

---

## 快速开始

#### 📦开箱即用（推荐）

 无需配置 Python 环境和 ADB 路径，下载即用。

1. 前往项目的 [**Releases 页面**](https://github.com/hdguff8/WebDebuggerGo/releases) 下载最新的绿色免安装包（rar）。 
2. 将压缩包解压至任意目录。 
3. 双击运行 `WebDebuggerGo.exe`。
4.  连接手机并确保开启 **USB 调试**，在 App 内打开 Web 页面，即可自动弹出调试窗口。

### 💻源码运行

 如果你想查看底层逻辑或进行二次开发，请按照以下步骤配置环境。

#### 1. 环境准备

确保您的系统已安装 **Python 3.10**。建议在虚拟环境中安装依赖，以保持环境纯净：

```bash
# 克隆仓库后进入目录
pip install -r dependence.txt
```

#### 2. 资源配置

为了实现离线调试与 ADB 通信，请按以下目录结构放置资源：

- **Chrome DevTools 资源**：从 [Resources 分支](https://github.com/hdguff8/WebDebuggerGo/blob/Resources/chrome_devtools_frontend.rar) 下载 `chrome_devtools_frontend.rar`，解压至项目根目录的 `chrome_devtools_frontend/` 文件夹下。
- **ADB 工具**：将 `adb.exe`（及相关 dll）放入 `adb/` 目录。您可以直接使用 Resources 分支提供的版本，或指向本地现有的 ADB 路径。

**📂 预期目录结构：**

```
WebDebuggerGo/
├── adb/
│   └── adb.exe
├── chrome_devtools_frontend/
│   ├── devtools_app.html
│   └── ... (其他静态资源)
├── main_app.py
└── ...
```

#### 3. 运行与调试

一切就绪后，启动主程序：

```bash
python main_app.py
```

**连接步骤：**

1. 使用数据线连接 Android 手机。
2. 确保手机已开启 **USB 调试** 权限。
3. 打开 App 中的 WebView 页面，**WebDebuggerGo** 将自动捕捉目标并弹出调试窗口。

---

## 📜 鸣谢与说明

- **灵感来源**：向 WebDebugX 致敬，感谢其在 Web 调试领域的启发。
- **免责声明**：本工具仅供开发者学习与交流使用，请勿用于非法用途。

License: This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.