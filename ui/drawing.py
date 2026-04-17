"""CamForge 共享绘图函数"""

import matplotlib.pyplot as plt

from .constants import SUPPORT_SIZE_RATIO, THEME


def draw_fixed_support(ax, r_0):
    """在凸轮旋转中心 (0,0) 绘制固定铰支座符号（小圆圈 + 三角形 + 底座 + 斜线）"""
    sz = r_0 * SUPPORT_SIZE_RATIO
    # 三角形顶点：顶点在原点下方，底边在更下方
    tri_top_y = -sz * 0.15
    tri_bot_y = -sz * 1.35
    tri_x = [0, -sz, sz, 0]
    tri_y = [tri_top_y, tri_bot_y, tri_bot_y, tri_top_y]
    ax.fill(tri_x, tri_y, color=THEME['support_fill'], zorder=5)
    ax.plot(tri_x, tri_y, 'k-', linewidth=1, zorder=5)
    # 铰链小圆圈
    circle_r = sz * 0.2
    circle = plt.Circle((0, 0), circle_r, fill=False, edgecolor='k',
                         linewidth=1, zorder=6)
    ax.add_patch(circle)
    # 底座横线
    base_y = tri_bot_y
    hw = sz * 1.3
    ax.plot([-hw, hw], [base_y, base_y], 'k-', linewidth=1.5, zorder=5)
    # 斜线阴影（5条）
    n_hatch = 5
    hatch_len = sz * 0.5
    for j in range(n_hatch):
        x0 = -hw + (2 * hw) * (j + 0.5) / n_hatch
        ax.plot([x0, x0 - hatch_len * 0.6], [base_y, base_y - hatch_len],
                'k-', linewidth=0.8, zorder=5)
