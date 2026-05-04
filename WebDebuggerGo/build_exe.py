import os
import subprocess
import sys

def build_exe():
    """使用 PyInstaller 打包程序"""
    print("开始打包程序...")
    
    # 确保在项目根目录运行
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # 确保图标路径正确
    icon_file = 'WebDebuggerGo.ico' if os.path.exists(os.path.join(project_root, 'static/WebDebuggerGo.ico')) else 'WebDebuggerGo.png'
    icon_path = os.path.join(project_root, 'static', icon_file)
    
    # 打包参数
    params = [
        sys.executable, '-m', 'PyInstaller',
        '--name=WebDebuggerGo',
        # '--onefile',             # 打包成单个 exe 文件
        '--onedir',              # 打包成文件夹模式 (多文件)
        '--noconsole',           # 运行时不显示控制台窗口
        '--clean',               # 清理临时文件
        f'--icon={icon_path}',   # 设置程序图标 (使用绝对路径)
        # 包含静态资源目录
        '--add-data=adb;adb',
        '--add-data=chrome_devtools_frontend;chrome_devtools_frontend',
        '--add-data=static;static',
        '--add-data=pages;pages', # 确保包含 pages 模块
        # 指定入口文件
        'main_app.py'
    ]
    
    # 执行打包命令
    try:
        subprocess.run(params, check=True)
        print("\n" + "="*50)
        print("打包成功！")
        print(f"生成的程序目录位于: {os.path.join(project_root, 'dist', 'WebDebuggerGo')}")
        print(f"请运行其中的 WebDebuggerGo.exe")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
    except Exception as e:
        print(f"发生异常: {e}")

if __name__ == "__main__":
    build_exe()
