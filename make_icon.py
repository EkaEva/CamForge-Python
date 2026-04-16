"""
CamForge 图标生成脚本
用 Pillow 绘制凸轮轮廓形状的应用图标，保存为多分辨率 .ico 文件
"""

import numpy as np
from PIL import Image, ImageDraw

def draw_cam_shape(draw, cx, cy, r, color):
    """在 draw 对象上绘制凸轮轮廓形状"""
    # 基圆
    r_base = r * 0.55
    # 推程段（上半部分凸出）
    n = 120
    points = []
    for i in range(n):
        angle = 2 * np.pi * i / n
        # 简单凸轮形状：基圆 + 推程凸起
        if 0 < angle < np.pi * 0.5:  # 推程段
            s = r * 0.35 * (1 - np.cos(2 * np.pi * angle / (np.pi * 0.5))) / 2
        elif np.pi * 0.5 <= angle < np.pi * 0.75:  # 远休止
            s = r * 0.35
        elif np.pi * 0.75 <= angle < np.pi * 1.25:  # 回程段
            t = (angle - np.pi * 0.75) / (np.pi * 0.5)
            s = r * 0.35 * (1 + np.cos(np.pi * t)) / 2
        else:  # 近休止
            s = 0
        rr = r_base + s
        x = cx + rr * np.cos(angle)
        y = cy - rr * np.sin(angle)
        points.append((x, y))

    # 填充凸轮
    draw.polygon(points, fill=color)

    # 画推杆（顶部竖线）
    follower_x = cx
    follower_top = cy - r_base - r * 0.35 - r * 0.15
    follower_bottom = cy - r_base - r * 0.35
    draw.rectangle([follower_x - r * 0.04, follower_top,
                     follower_x + r * 0.04, follower_bottom], fill='#475569')

    # 推杆尖顶（小三角）
    tip_y = follower_bottom
    draw.polygon([
        (follower_x, tip_y),
        (follower_x - r * 0.06, tip_y + r * 0.08),
        (follower_x + r * 0.06, tip_y + r * 0.08),
    ], fill='#475569')

    # 中心点
    draw.ellipse([cx - r * 0.04, cy - r * 0.04, cx + r * 0.04, cy + r * 0.04], fill='#1e293b')


def create_icon(size=256):
    """创建指定尺寸的图标图像"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 背景圆
    margin = size * 0.05
    draw.ellipse([margin, margin, size - margin, size - margin], fill='#f8fafc')

    # 绘制凸轮
    cx, cy = size / 2, size / 2 + size * 0.02
    r = size * 0.38
    draw_cam_shape(draw, cx, cy, r, '#2563eb')

    return img


def main():
    sizes = [16, 32, 48, 256]
    images = []
    for s in sizes:
        img = create_icon(s)
        images.append(img)

    # 保存为 .ico（Pillow 原生支持多分辨率 ICO）
    images[0].save('camforge.ico', format='ICO', sizes=[(s, s) for s in sizes],
                    append_images=images[1:])
    print('camforge.ico 已生成（分辨率: 16x16, 32x32, 48x48, 256x256）')


if __name__ == '__main__':
    main()
