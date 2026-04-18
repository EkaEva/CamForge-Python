import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 设置图形大小
fig, ax = plt.subplots(figsize=(6, 8))

# 定义颜色和线宽
line_color = 'black'
bg_color = 'white'
linewidth = 2

# 1. 绘制导轨 (Guide Blocks)
# 两个矩形，左侧和右侧，带有斜线剖面填充
guide_height = 1.2
guide_width_total = 1.8
central_gap = 0.4
guide_block_width = (guide_width_total - central_gap) / 2.0

# 建立一个垂直偏移量，将整个装置居中
vertical_offset = 3.0

# 左侧导轨
left_guide = patches.Rectangle(
    ( - guide_width_total/2, vertical_offset ), # (x, y) 底部左角
    guide_block_width,               # 宽度
    guide_height,                    # 高度
    edgecolor=line_color,
    facecolor=bg_color,
    hatch='///',                     # 剖面线填充
    linewidth=linewidth
)
ax.add_patch(left_guide)

# 右侧导轨
right_guide = patches.Rectangle(
    ( central_gap/2, vertical_offset ), # (x, y) 底部左角
    guide_block_width,      # 宽度
    guide_height,           # 高度
    edgecolor=line_color,
    facecolor=bg_color,
    hatch='///',            # 剖面线填充
    linewidth=linewidth
)
ax.add_patch(right_guide)


# 2. 绘制导轨中间穿过区域的覆盖层 (确保导轨剖面线不在中间区域显示)
gap_rect = patches.Rectangle(
    (-central_gap/2, vertical_offset),
    central_gap,
    guide_height,
    edgecolor='none', # 无边框
    facecolor=bg_color,
    zorder=0 # 确保它在导轨和推杆后面
)
ax.add_patch(gap_rect)


# 3. 绘制推杆 (Push Rod) - 带有底部半圆
rod_width = central_gap * 0.9 # 比间隙略小
rod_length = 3.8
rod_bottom_y = vertical_offset + guide_height - rod_length

# 推杆上半部分主体 (矩形)
rod_rect = patches.Rectangle(
    (-rod_width/2, rod_bottom_y), # 从导轨顶部开始向下
    rod_width,
    rod_length,
    edgecolor=line_color,
    facecolor=bg_color,
    linewidth=linewidth,
    zorder=2 
)
ax.add_patch(rod_rect)

# 推杆底部半圆包覆 (使用一个圆形)
rod_end_circle = patches.Circle(
    (0, rod_bottom_y), 
    rod_width/2, # 半径为推杆宽度的一半
    edgecolor=line_color,
    facecolor=bg_color,
    linewidth=linewidth,
    zorder=2 
)
ax.add_patch(rod_end_circle)

# 消除矩形和底端半圆交界处的黑色横线 (用一根白线盖住)
# 左右各向内收缩一点点(0.02)，防止破坏外边框
mask_line = plt.Line2D(
    [-rod_width/2 + 0.02, rod_width/2 - 0.02], 
    [rod_bottom_y, rod_bottom_y], 
    color=bg_color, 
    linewidth=linewidth + 1, 
    zorder=2.1 # 必须在矩形和圆的上一层
)
ax.add_line(mask_line)


# 4. 绘制滚子 (Roller)
roller_radius = 0.6
roller_circle = patches.Circle(
    (0, vertical_offset + guide_height - rod_length), # 位于推杆底部
    roller_radius,
    edgecolor=line_color,
    facecolor=bg_color,
    linewidth=linewidth,
    zorder=1 # 在推杆后面，使推杆看起来插入其中
)
ax.add_patch(roller_circle)


# 5. 按照要求，在连接处用圆圈表示
# 在推杆底部和滚子中心的连接点绘制一个简单的圆圈
connection_radius = 0.12
connection_circle = patches.Circle(
    (0, vertical_offset + guide_height - rod_length),
    connection_radius,
    edgecolor=line_color,
    facecolor=bg_color,
    linewidth=1.5,
    zorder=3 # 覆盖推杆和滚子
)
ax.add_patch(connection_circle)


# 6. 设置图形布局
# 设置轴范围，包含所有形状
ax.set_xlim(-guide_width_total/2 - 0.2, guide_width_total/2 + 0.2)
ax.set_ylim(vertical_offset + guide_height - rod_length - roller_radius - 0.2, vertical_offset + guide_height + 0.2)

# 确保形状不扭曲
ax.set_aspect('equal') 
# 隐藏坐标轴
ax.axis('off')

# 显示图形
plt.tight_layout()
plt.show()