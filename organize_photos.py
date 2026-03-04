import os
import shutil
import logging
from pathlib import Path
import sys

def setup_logging(log_file):
    """配置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def verify_file_integrity(src_path, dst_path):
    """简单的文件完整性检查（基于文件大小）"""
    try:
        return os.path.getsize(src_path) == os.path.getsize(dst_path)
    except OSError:
        return False

def organize_photos(source_dir_path):
    source_path = Path(source_dir_path)
    
    if not source_path.exists():
        print(f"错误: 源文件夹 '{source_dir_path}' 不存在。")
        return

    # 创建目标文件夹名称: "源文件夹名称_完成整理"
    dest_dir_name = f"{source_path.name}_完成整理"
    dest_path = source_path.parent / dest_dir_name
    
    # 设置日志
    # 日志放置在源文件夹下
    log_file = source_path / f"{dest_dir_name}_log.txt"
    
    setup_logging(log_file)
    logging.info(f"开始整理文件夹: {source_path}")
    logging.info(f"目标文件夹: {dest_path}")

    # 创建目标文件夹
    try:
        dest_path.mkdir(exist_ok=True)
        logging.info("目标文件夹已准备就绪。")
    except Exception as e:
        logging.error(f"无法创建目标文件夹: {e}")
        return

    # 扫描所有文件
    files = [f for f in source_path.iterdir() if f.is_file()]
    # 使用字典存储，key为文件名(不含后缀)，value为完整路径对象
    jpg_files = {f.stem: f for f in files if f.suffix.lower() == '.jpg'}
    nef_files = {f.stem: f for f in files if f.suffix.lower() == '.nef'}

    # 找出同时存在 JPG 和 NEF 的文件名
    common_stems = set(jpg_files.keys()) & set(nef_files.keys())
    sorted_stems = sorted(list(common_stems))
    total_groups = len(sorted_stems)

    logging.info(f"扫描完成: 发现 {len(jpg_files)} 个 JPG 文件, {len(nef_files)} 个 NEF 文件。")
    logging.info(f"符合条件（同时存在JPG和NEF）的文件组数量: {total_groups}")

    if total_groups == 0:
        logging.info("没有发现需要复制的文件组。")
        print("\n未发现同时包含JPG和NEF的文件组，无需整理。")
        return

    logging.info("--- 开始复制成对的 JPG 和 NEF 文件 ---")
    
    for index, stem in enumerate(sorted_stems, 1):
        # 处理 JPG
        jpg_file = jpg_files[stem]
        try:
            dest_file = dest_path / jpg_file.name
            
            if dest_file.exists():
                logging.warning(f"[{index}/{total_groups}] JPG 文件已存在，跳过: {jpg_file.name}")
            else:
                shutil.copy2(jpg_file, dest_file)
                if verify_file_integrity(jpg_file, dest_file):
                    logging.info(f"[{index}/{total_groups}] 成功复制 JPG: {jpg_file.name}")
                else:
                    logging.error(f"[{index}/{total_groups}] JPG 复制验证失败: {jpg_file.name}")
                    try: os.remove(dest_file)
                    except: pass
        except Exception as e:
            logging.error(f"[{index}/{total_groups}] 复制 JPG {jpg_file.name} 时出错: {e}")

        # 处理 NEF
        nef_file = nef_files[stem]
        try:
            dest_file = dest_path / nef_file.name
            
            if dest_file.exists():
                logging.warning(f"[{index}/{total_groups}] NEF 文件已存在，跳过: {nef_file.name}")
            else:
                shutil.copy2(nef_file, dest_file)
                if verify_file_integrity(nef_file, dest_file):
                    logging.info(f"[{index}/{total_groups}] 成功复制 NEF: {nef_file.name}")
                else:
                    logging.error(f"[{index}/{total_groups}] NEF 复制验证失败: {nef_file.name}")
                    try: os.remove(dest_file)
                    except: pass
        except Exception as e:
            logging.error(f"[{index}/{total_groups}] 复制 NEF {nef_file.name} 时出错: {e}")

    logging.info("--- 整理完成 ---")
    print(f"\n整理完成! 共处理 {total_groups} 组文件。")
    print(f"日志文件已保存至: {log_file}")

if __name__ == "__main__":
    print("=== 自动化照片整理脚本 ===")
    print("功能说明：")
    print("1. 扫描源文件夹中的 JPG 和 NEF 文件")
    print("2. 创建以 '_完成整理' 结尾的新文件夹")
    print("3. 仅复制同时存在 JPG 和 NEF 的文件对")
    print("4. 日志文件将保存在源文件夹内")
    print("==========================")

    # 默认测试路径
    default_path = r"c:\Users\joyjo\Desktop\Done\PicturesEdit\day1（迪拜）"
    
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        try:
            # 如果没有命令行参数，询问用户输入
            print(f"\n提示：直接按回车可使用默认测试路径")
            print(f"默认路径: {default_path}")
            user_input = input("请输入源文件夹路径: ").strip()
            source_dir = user_input if user_input else default_path
        except EOFError:
            # 处理非交互式环境（如某些自动化测试）
            source_dir = default_path
    
    # 移除引号（如果用户直接拖入文件夹可能会带引号）
    source_dir = source_dir.strip('"').strip("'")
    
    if source_dir:
        print(f"\n正在处理文件夹: {source_dir}")
        organize_photos(source_dir)
        # 等待用户按键退出，防止窗口直接关闭
        input("\n按回车键退出程序...")
    else:
        print("未输入有效路径，程序退出。")
