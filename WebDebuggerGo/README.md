# WebDebuggerGo

> **为 Android/HBuilderX 开发者而生的全自动离线 WebView 调试利器。**

**WebDebuggerGo** 是一款专为 HBuilderX 生态打造的自动化调试终端。它彻底终结了在 `chrome://inspect` 页面中反复查找、频繁重连的痛苦，让移动端 Web 调试回归本应有的流畅体验。

---

## 💡 为什么选择 WebDebuggerGo?

|     |     |     |
| --- | --- | --- |
| **特性** | **传统 chrome://inspect** | **WebDebuggerGo** |
| **连接体验** | 手动寻找目标，点击 inspect | **即插即用，自动捕获并弹出窗口** |
| **网络要求** | 强依赖 Google 域名（易白屏） | **全离线支持，本地毫秒级加载** |
| **连接稳定性** | 刷新页面易断开，需重新开启 | **断线自动重连，状态实时保持** |
| **安全性限制** | 经常遭遇 `403 Forbidden` | **内置代理欺骗，物理绕过 Origin 校验** |
| **操作效率** | 窗口管理混乱，多设备切换繁琐 | **多设备分层管理，日志实时过滤** |

---

## ✨ 核心能力

- **⚡ 自动化捕获**：实时轮询 ADB Unix 域套接字，发现 WebView 瞬间自动完成端口转发并唤起调试界面。
- **🌐 离线 DevTools 引擎**：内置完整 Chromium 调试器资源，彻底告别“由于无法连接 Google 服务器导致调试界面白屏”的尴尬。
- **🛡️ WebSocket 代理**：底层拦截 HTTP 升级请求，动态剔除限制性 Header，完美解决 Android 系统对调试来源的 Origin 限制。
- **📊 日志系统**：
  - **分级过滤**：支持 DEBUG/INFO/WARN/ERROR 实时筛选。
- **🛠️ ADB 工具箱**：集成一键重启 ADB 服务、清理转发、设备状态探测等运维功能。  
  

---

## 🛠️ 快速开始

### 1\. 环境准备

确保您的 Python 环境版本 3.10，并安装必要依赖：

```bash
pip install -r dependence.txt
```

### 2\. 运行调试

```bash
python main_app.py
```

_连接手机并开启 USB 调试，App 内的 WebView 页面将自动同步至程序列表。_

---

## 📜 鸣谢与说明

- **灵感来源**：向 WebDebugX 致敬，感谢其在 Web 调试领域的启发。
- **免责声明**：本工具仅供开发者学习与交流使用，请勿用于非法用途。

License: This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.