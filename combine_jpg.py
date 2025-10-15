#!/usr/bin/env python3
"""
交互式合并 JPG 图片脚本（支持多副图）。

运行后，用户依次输入：
1) 主图片路径
2) 多个副图片路径（逐个输入，直接按 Enter 结束）
3) 缩放维度编号（1：左，2：右，3：上，4：下）

脚本会将所有副图按所选方向的接缝维度进行等比缩放，
并与主图按顺序贴合合并：
- 右侧：副图片1在主图右侧，副图片2在副图片1右侧，依次类推；
- 左侧：副图片1在主图左侧，副图片2在副图片1左侧，依次类推；
- 上方：副图片1在主图上方，副图片2在副图片1上方，依次类推；
- 下方：副图片1在主图下方，副图片2在副图片1下方，依次类推。

生成文件到主图片所在目录，文件名为：主图片文件名_combined.jpg。
脚本不会结束，除非用户输入 Exit（不区分大小写）。
"""

import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    print("[错误] 未安装 Pillow 库。请先运行：pip install pillow")
    sys.exit(1)


def load_image(path: str) -> Image.Image:
    """加载图片，应用 EXIF 方向，并转换为 RGB。"""
    img = Image.open(path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def get_resample_method():
    """兼容不同 Pillow 版本的高质量缩放算法。"""
    try:
        return Image.Resampling.LANCZOS  # Pillow >= 9.1
    except AttributeError:
        return getattr(Image, "LANCZOS", Image.ANTIALIAS)  # 旧版本兼容


def resize_secondary_to_fit(main_img: Image.Image, secondary_img: Image.Image, position: str) -> Image.Image:
    """根据合并位置，缩放副图使其在接缝维度完全贴合主图。"""
    resample = get_resample_method()
    if position in ("top", "bottom"):
        target_w = main_img.width
        new_h = round(secondary_img.height * (target_w / secondary_img.width))
        return secondary_img.resize((target_w, new_h), resample)
    else:  # left/right
        target_h = main_img.height
        new_w = round(secondary_img.width * (target_h / secondary_img.height))
        return secondary_img.resize((new_w, target_h), resample)


def combine_images_multi(main_img: Image.Image, secondary_list: list[Image.Image], position: str) -> Image.Image:
    """按指定位置合并多张图片，返回新图。

    排列规则（从左上到右下的可视顺序）：
    - top: 依次在主图上方，显示顺序为 [副图N, ..., 副图2, 副图1, 主图]
    - bottom: 依次在主图下方，显示顺序为 [主图, 副图1, 副图2, ..., 副图N]
    - left: 依次在主图左侧，显示顺序为 [副图N, ..., 副图2, 副图1, 主图]
    - right: 依次在主图右侧，显示顺序为 [主图, 副图1, 副图2, ..., 副图N]
    """
    if position == "top":
        new_w = main_img.width
        total_h = main_img.height + sum(img.height for img in secondary_list)
        canvas = Image.new("RGB", (new_w, total_h), (255, 255, 255))
        y = 0
        for img in reversed(secondary_list):
            canvas.paste(img, (0, y))
            y += img.height
        canvas.paste(main_img, (0, y))
        return canvas
    elif position == "bottom":
        new_w = main_img.width
        total_h = main_img.height + sum(img.height for img in secondary_list)
        canvas = Image.new("RGB", (new_w, total_h), (255, 255, 255))
        y = 0
        canvas.paste(main_img, (0, y))
        y += main_img.height
        for img in secondary_list:
            canvas.paste(img, (0, y))
            y += img.height
        return canvas
    elif position == "left":
        total_w = main_img.width + sum(img.width for img in secondary_list)
        new_h = main_img.height
        canvas = Image.new("RGB", (total_w, new_h), (255, 255, 255))
        x = 0
        for img in reversed(secondary_list):
            canvas.paste(img, (x, 0))
            x += img.width
        canvas.paste(main_img, (x, 0))
        return canvas
    elif position == "right":
        total_w = main_img.width + sum(img.width for img in secondary_list)
        new_h = main_img.height
        canvas = Image.new("RGB", (total_w, new_h), (255, 255, 255))
        x = 0
        canvas.paste(main_img, (x, 0))
        x += main_img.width
        for img in secondary_list:
            canvas.paste(img, (x, 0))
            x += img.width
        return canvas
    else:
        raise ValueError("未知的合并位置")


def build_output_path(main_path: str) -> str:
    """生成输出路径：同目录下，主文件名 + _combined.jpg"""
    d = os.path.dirname(main_path)
    base = os.path.splitext(os.path.basename(main_path))[0]
    return os.path.join(d or ".", f"{base}_combined.jpg")


def code_to_position(code: str) -> str:
    """将编号 1/2/3/4 转换为位置 left/right/top/bottom。"""
    code = (code or "").strip()
    mapping = {
        "1": "left",
        "2": "right",
        "3": "top",
        "4": "bottom",
    }
    return mapping.get(code)


def is_exit(text: str) -> bool:
    return (text or "").strip().lower() == "exit"


def interactive_loop():
    print("—— 合并 JPG 图片（支持多副图）——")
    print("输入 Exit 可随时退出。")
    print("缩放维度编号：1=左, 2=右, 3=上, 4=下")

    while True:
        main_path = input("请输入主图片路径（或输入 Exit 退出）：").strip()
        if is_exit(main_path):
            print("已退出。")
            break
        if not os.path.isfile(main_path):
            print("[错误] 主图片路径不存在，请重试。")
            continue

        # 多副图采集
        secondary_paths = []
        idx = 1
        while True:
            prompt = f"请输入副图片路径{idx}（直接按 Enter 结束，或输入 Exit 退出）："
            sp = input(prompt).strip()
            if is_exit(sp):
                print("已退出。")
                return
            if sp == "":
                if not secondary_paths:
                    print("[错误] 未输入任何副图片路径，请重试。")
                    # 回到主路径重新开始
                    break
                else:
                    # 结束副图采集
                    print(f"已添加 {len(secondary_paths)} 张副图片：" + ", ".join([f"副图片{i}" for i in range(1, len(secondary_paths)+1)]))
                    break
            if not os.path.isfile(sp):
                print("[错误] 该副图片路径不存在，请重试。")
                continue
            secondary_paths.append(sp)
            idx += 1

        if not secondary_paths:
            # 未输入副图，重新开始一次循环
            continue

        code = input("请输入缩放维度编号（1：左，2：右，3：上，4：下；直接按 Enter 默认选择右）：").strip()
        if is_exit(code):
            print("已退出。")
            break
        if code == "":
            position = "right"
            print("[提示] 未输入编号，已默认选择：右（2）。")
        else:
            position = code_to_position(code)
        if position is None:
            print("[错误] 编号不合法，请输入 1/2/3/4。")
            continue

        # 处理与保存
        try:
            main_img = load_image(main_path)
            # 加载并缩放所有副图
            secondary_imgs = []
            for spath in secondary_paths:
                img = load_image(spath)
                img_resized = resize_secondary_to_fit(main_img, img, position)
                secondary_imgs.append(img_resized)

            combined = combine_images_multi(main_img, secondary_imgs, position)
            out_path = build_output_path(main_path)
            combined.save(out_path, format="JPEG", quality=95, optimize=True)
            print(f"[成功] 已生成：{out_path}")
        except Exception as e:
            print(f"[错误] 处理失败：{e}")
            continue


if __name__ == "__main__":
    interactive_loop()