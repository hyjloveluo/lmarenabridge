# update_script.py
import os
import shutil
import time
import subprocess
import sys
import json
import re

def load_jsonc_values(path):
    """从一个 .jsonc 文件中加载数据，忽略注释，只返回键值对。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'//.*', '', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"加载或解析 {path} 的值时出错: {e}")
        return None

def get_all_relative_paths(directory):
    """获取一个目录下所有文件和空文件夹的相对路径集合。"""
    paths = set()
    for root, dirs, files in os.walk(directory):
        # 添加文件
        for name in files:
            path = os.path.join(root, name)
            paths.add(os.path.relpath(path, directory))
        # 添加空文件夹
        for name in dirs:
            dir_path = os.path.join(root, name)
            if not os.listdir(dir_path):
                paths.add(os.path.relpath(dir_path, directory) + os.sep)
    return paths

def main():
    print("--- 更新脚本已启动 ---")
    
    # 1. 等待主程序退出
    print("等待主程序关闭 (3秒)...")
    time.sleep(3)
    
    # 2. 定义路径
    destination_dir = os.getcwd()
    update_dir = "update_temp"
    source_dir_inner = os.path.join(update_dir, "LMArenaBridge-main")
    config_filename = 'config.jsonc'
    models_filename = 'models.json'
    model_endpoint_map_filename = 'model_endpoint_map.json'
    
    if not os.path.exists(source_dir_inner):
        print(f"错误：找不到源目录 {source_dir_inner}。更新失败。")
        return
        
    print(f"源目录: {os.path.abspath(source_dir_inner)}")
    print(f"目标目录: {os.path.abspath(destination_dir)}")

    # 3. 备份关键文件
    print("正在备份当前配置和模型文件...")
    old_config_path = os.path.join(destination_dir, config_filename)
    old_models_path = os.path.join(destination_dir, models_filename)
    old_config_values = load_jsonc_values(old_config_path)
    
    # 4. 确定要保留的文件和文件夹
    # 保留 update_temp 自身, .git 目录, 和任何用户可能添加的隐藏文件/文件夹
    preserved_items = {update_dir, ".git", ".github"}

    # 5. 获取新旧文件列表
    new_files = get_all_relative_paths(source_dir_inner)
    # 排除 .git 和 .github 目录，因为它们不应该被部署
    new_files = {f for f in new_files if not (f.startswith('.git') or f.startswith('.github'))}

    current_files = get_all_relative_paths(destination_dir)

    print("\n--- 文件变更分析 ---")
    print("[*] 文件删除功能已禁用，以保护用户数据。仅执行文件复制和配置更新。")

    # 7. 复制新文件（除配置文件外）
    print("\n[+] 正在复制新文件...")
    try:
        new_config_template_path = os.path.join(source_dir_inner, config_filename)
        
        for item in os.listdir(source_dir_inner):
            s = os.path.join(source_dir_inner, item)
            d = os.path.join(destination_dir, item)
            
            # 跳过 .git 和 .github 目录
            if item in {".git", ".github"}:
                continue
            
            if os.path.basename(s) == config_filename:
                continue # 跳过主配置文件，稍后处理
            
            if os.path.basename(s) == model_endpoint_map_filename:
                continue # 跳过模型端点映射文件，保留用户本地版本

            if os.path.basename(s) == models_filename:
                continue # 跳过 models.json 文件，保留用户本地版本

            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("文件复制成功。")

    except Exception as e:
        print(f"文件复制过程中发生错误: {e}")
        return

    # 8. 智能合并配置
    if old_config_values and os.path.exists(new_config_template_path):
        print("\n[*] 正在智能合并配置（保留注释）...")
        try:
            with open(new_config_template_path, 'r', encoding='utf-8') as f:
                new_config_content = f.read()

            new_version_values = load_jsonc_values(new_config_template_path)
            new_version = new_version_values.get("version", "unknown")
            old_config_values["version"] = new_version

            for key, value in old_config_values.items():
                if isinstance(value, str):
                    replacement_value = f'"{value}"'
                elif isinstance(value, bool):
                    replacement_value = str(value).lower()
                else:
                    replacement_value = str(value)
                
                pattern = re.compile(f'("{key}"\s*:\s*)(?:".*?"|true|false|[\d\.]+)')
                if pattern.search(new_config_content):
                    new_config_content = pattern.sub(f'\\g<1>{replacement_value}', new_config_content)

            with open(old_config_path, 'w', encoding='utf-8') as f:
                f.write(new_config_content)
            print("配置合并成功。")

        except Exception as e:
            print(f"配置合并过程中发生严重错误: {e}")
    else:
        print("无法进行智能合并，将直接使用新版配置文件。")
        if os.path.exists(new_config_template_path):
            shutil.copy2(new_config_template_path, old_config_path)

    # 9. 清理临时文件夹
    print("\n[*] 正在清理临时文件...")
    try:
        shutil.rmtree(update_dir)
        print("清理完毕。")
    except Exception as e:
        print(f"清理临时文件时发生错误: {e}")

    # 10. 重启主程序
    print("\n[*] 正在重启主程序...")
    try:
        main_script_path = os.path.join(destination_dir, "api_server.py")
        if not os.path.exists(main_script_path):
             print(f"错误: 找不到主程序脚本 {main_script_path}。")
             return
        
        subprocess.Popen([sys.executable, main_script_path])
        print("主程序已在后台重新启动。")
    except Exception as e:
        print(f"重启主程序失败: {e}")
        print(f"请手动运行 {main_script_path}")

    print("--- 更新完成 ---")

if __name__ == "__main__":
    main()