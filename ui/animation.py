"""CamForge 动画帧渲染逻辑

提取自 main.py 中 _animate_frame 和 _draw_single_frame 的共享渲染代码，
以及 GIF 导出的帧生成逻辑。
"""

import numpy as np
import os
from scipy.interpolate import splprep, splev

from cam_mechanics import (
    compute_rotated_cam, compute_anim_frame_data,
    compute_pressure_angle_arc, DEG2RAD,
)
from ui.constants import (
    TIP_WIDTH_RATIO, TIP_HEIGHT_RATIO, ROD_LENGTH_RATIO,
    LIMIT_LINE_RATIO, ARC_RADIUS_RATIO, ANIM_FRAME_SKIP,
    GIF_DPI, GIF_DURATION_MS,
)
from ui.drawing import draw_fixed_support
from i18n import t


def smooth_closed_curve(x, y, n_points=360):
    """
    使用周期样条插值平滑闭合曲线。

    Parameters
    ----------
    x, y : ndarray
        原始曲线坐标。
    n_points : int
        插值后的点数。

    Returns
    -------
    x_smooth, y_smooth : ndarray
        平滑后的曲线坐标。
    """
    if len(x) < 4:
        return x, y
    try:
        # 周期样条插值（per=1 表示闭合曲线）
        tck, u = splprep([x, y], s=0, per=True)
        u_new = np.linspace(0, 1, n_points, endpoint=False)
        x_smooth, y_smooth = splev(u_new, tck)
        return np.array(x_smooth), np.array(y_smooth)
    except Exception:
        return x, y


def render_frame_artists(artists, data, i, *,
                         show_base, show_offset, show_tangent,
                         show_normal, show_limits, show_boundaries,
                         show_arc):
    """
    更新动画 artists 用于帧索引 i。

    这是实时动画和帧跳转共享的渲染逻辑。

    Parameters
    ----------
    artists : dict
        Matplotlib line artists，包含键: cam, theory, base, offset,
        tangent, normal, rod, tip, roller, center, lower, upper, boundaries, arc。
    data : dict
        CamSimulator.sim_data 仿真数据字典。
    i : int
        帧索引 (0 到 N-1)。
    show_base, show_offset, ... : bool
        显示开关。

    Returns
    -------
    dict
        帧几何数据: follower_x, contact_y, alpha_i, s_i, nx, ny, tx, ty, x_rot, y_rot
    """
    r_0 = data['r_0']
    h = data['h']
    sn = data['sn']
    pb = data['phase_bounds']
    s = data['s']
    s_0 = data['s_0']
    e = data['e']
    pz = data['pz']
    alpha_all = data['alpha_all']
    r_r = data.get('r_r', 0)
    n_points = data.get('n_points', len(s))
    N = len(s)

    # 旋转凸轮（角度需要根据 n_points 缩放）
    angle_deg = i * 360.0 / n_points
    angle_rad = -angle_deg * DEG2RAD if sn == 1 else angle_deg * DEG2RAD
    x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)

    # 当离散点数较少时，对轮廓进行样条插值平滑
    smooth_display = n_points < 180
    if smooth_display:
        x_rot_smooth, y_rot_smooth = smooth_closed_curve(x_rot, y_rot)
    else:
        x_rot_smooth, y_rot_smooth = x_rot, y_rot

    # 根据滚子半径决定显示哪个廓形
    if r_r > 0:
        # 显示实际廓形（红色实线）
        x_actual_rot, y_actual_rot = compute_rotated_cam(data['x_actual'], data['y_actual'], angle_rad)
        if smooth_display:
            x_actual_smooth, y_actual_smooth = smooth_closed_curve(x_actual_rot, y_actual_rot)
            x_rot_smooth, y_rot_smooth = smooth_closed_curve(x_rot, y_rot)
        else:
            x_actual_smooth, y_actual_smooth = x_actual_rot, y_actual_rot
            x_rot_smooth, y_rot_smooth = x_rot, y_rot
        artists['cam'].set_data(x_actual_smooth, y_actual_smooth)
        # 显示理论廓形（蓝色双点划线）
        artists['theory'].set_data(x_rot_smooth, y_rot_smooth)
    else:
        # 显示理论廓形（红色实线）
        artists['cam'].set_data(x_rot_smooth, y_rot_smooth)
        artists['theory'].set_data([], [])

    # 基圆/偏距圆
    if show_base:
        artists['base'].set_data(data['x_base'], data['y_base'])
    else:
        artists['base'].set_data([], [])

    if show_offset:
        artists['offset'].set_data(data['x_offset'], data['y_offset'])
    else:
        artists['offset'].set_data([], [])

    # 帧数据
    frame = compute_anim_frame_data(s, data['ds_ddelta'], s_0, e, r_0, sn, pz, i, alpha_all, n_points)
    follower_x = frame['follower_x']
    cy = frame['contact_y']
    cx = follower_x
    nx, ny = frame['nx'], frame['ny']
    tx, ty = frame['tx'], frame['ty']
    alpha_i = frame['alpha_i']

    # 切线/法线
    if show_tangent:
        artists['tangent'].set_data([cx - r_0 * tx, cx + r_0 * tx], [cy - r_0 * ty, cy + r_0 * ty])
    else:
        artists['tangent'].set_data([], [])

    if show_normal:
        artists['normal'].set_data([cx + r_0 * nx, cx - r_0 * nx], [cy + r_0 * ny, cy - r_0 * ny])
    else:
        artists['normal'].set_data([], [])

    # 推杆杆身
    tip_w = r_0 * TIP_WIDTH_RATIO
    tip_h = r_0 * TIP_HEIGHT_RATIO
    rod_top = cy + r_0 * ROD_LENGTH_RATIO

    # 推杆尖端：根据滚子半径显示不同形状
    if r_r > 0:
        # 滚子圆形
        theta = np.linspace(0, 2 * np.pi, 36)
        roller_x = follower_x + r_r * np.cos(theta)
        roller_y = cy + r_r * np.sin(theta)
        artists['roller'].set_data(roller_x, roller_y)

        # 滚子圆心实心小圆
        artists['roller_center'].set_data([follower_x], [cy])

        # 从圆心向上的推杆线
        artists['rod'].set_data([follower_x, follower_x], [cy, rod_top])

        # 隐藏三角形尖端
        artists['tip'].set_data([], [])
    else:
        # 三角形尖端
        artists['tip'].set_data([follower_x - tip_w, follower_x, follower_x + tip_w, follower_x - tip_w],
                                [cy + tip_h, cy, cy + tip_h, cy + tip_h])
        # 推杆杆身
        artists['rod'].set_data([follower_x, follower_x], [cy + tip_h, rod_top])
        # 隐藏滚子圆形和圆心
        artists['roller'].set_data([], [])
        artists['roller_center'].set_data([], [])

    # 推杆上下限线
    if show_limits:
        artists['lower'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0])
        artists['upper'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h])
    else:
        artists['lower'].set_data([], [])
        artists['upper'].set_data([], [])

    # 角度分界线
    if show_boundaries:
        for j, lb in enumerate(artists['boundaries']):
            if j < len(pb) - 1:
                b_deg = pb[j + 1]
                idx = int(b_deg)
                if idx < N:
                    lb.set_data([0, x_rot[idx]], [0, y_rot[idx]])
                else:
                    lb.set_data([], [])
            else:
                lb.set_data([], [])
    else:
        for lb in artists['boundaries']:
            lb.set_data([], [])

    # 压力角弧线
    if show_arc:
        arc_r = r_0 * ARC_RADIUS_RATIO
        x_arc, y_arc = compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r)
        artists['arc'].set_data(x_arc, y_arc)
        artists['center'].set_data([follower_x, follower_x], [cy - r_0 * 2, cy + r_0 * 5])
    else:
        artists['arc'].set_data([], [])
        artists['center'].set_data([], [])

    return {
        'follower_x': follower_x, 'contact_y': cy,
        'alpha_i': alpha_i, 's_i': frame['s_i'],
        'nx': nx, 'ny': ny, 'tx': tx, 'ty': ty,
        'x_rot': x_rot, 'y_rot': y_rot,
    }


def update_info_panel(info_labels, i, alpha_i, s_i, h, s_0, lang):
    """更新信息面板文本标签。

    Parameters
    ----------
    info_labels : dict
        信息面板 matplotlib text 对象，键: delta, alpha, s。
    i : int
        帧索引。
    alpha_i : float
        当前压力角。
    s_i : float
        当前位移。
    h : float
        推杆最大位移（返回值，不显示）。
    s_0 : float
        初始位移（返回值，不显示）。
    lang : str
        当前语言代码。

    Returns
    -------
    tuple
        (h, s_0) 用于状态栏显示
    """
    label_delta = t("info.label.delta", lang)
    label_alpha = t("info.label.alpha", lang)
    label_s = t("info.label.s", lang)
    info_labels['delta'].set_text(rf'{label_delta}: {i:3d}°/360°')
    info_labels['alpha'].set_text(rf'{label_alpha}: {alpha_i:.1f}°')
    info_labels['s'].set_text(rf'{label_s}: {s_i:.2f} mm')
    return h, s_0


def generate_gif_frames(data, filepath, saved_list, folder,
                        *, show_base, show_offset, show_tangent,
                        show_normal, show_limits, show_boundaries,
                        show_arc, lang, xlim, ylim,
                        progress_callback=None):
    """
    生成所有 GIF 帧并保存为动画 GIF。

    Parameters
    ----------
    data : dict
        仿真数据（必须是线程安全的副本）。
    filepath : str
        输出 GIF 文件路径。
    saved_list : list
        已保存文件名列表（会追加新文件名）。
    folder : str
        保存目录。
    show_* : bool
        显示开关。
    lang : str
        语言代码。
    xlim, ylim : tuple
        动画坐标轴范围。
    progress_callback : callable or None
        进度回调，签名 callback(frame_index, total_frames, phase_text)。
        phase_text 为 None 表示正在渲染帧，非 None 表示正在合成 GIF。
    """
    from PIL import Image as PILImage
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    from io import BytesIO
    import matplotlib.pyplot as plt

    s = data['s']
    ds_ddelta = data['ds_ddelta']
    alpha_all = data['alpha_all']
    x_cam = data['x']
    y_cam = data['y']
    x_base = data['x_base']
    y_base = data['y_base']
    x_offset = data['x_offset']
    y_offset = data['y_offset']
    s_0 = data['s_0']
    e = data['e']
    r_0 = data['r_0']
    h = data['h']
    sn = data['sn']
    pz = data['pz']
    pb = data['phase_bounds']
    r_r = data.get('r_r', 0)
    x_actual = data.get('x_actual')
    y_actual = data.get('y_actual')
    n_points = data.get('n_points', len(s))
    N = len(s)

    fig_gif = Figure(figsize=(8, 6), dpi=GIF_DPI)
    ax_gif = fig_gif.add_axes([0.05, 0.08, 0.65, 0.87])
    ax_info_gif = fig_gif.add_axes([0.73, 0.08, 0.25, 0.87])

    label_delta_gif = t("info.label.delta", lang)
    label_alpha_gif = t("info.label.alpha", lang)
    label_s_gif = t("info.label.s", lang)
    label_h_gif = t("info.label.h", lang)
    label_s0_gif = t("info.label.s0", lang)
    title_anim_gif = t("plot.title.animation", lang)

    frame_images = []

    # 当离散点数较少时，对轮廓进行样条插值平滑
    smooth_display = n_points < 180

    for i in range(N):
        # 角度需要根据 n_points 缩放
        angle_deg = i * 360.0 / n_points
        angle_rad = -angle_deg * DEG2RAD if sn == 1 else angle_deg * DEG2RAD
        x_rot, y_rot = compute_rotated_cam(x_cam, y_cam, angle_rad)

        ax_gif.clear()

        # 根据滚子半径决定显示哪个廓形
        if r_r > 0 and x_actual is not None:
            # 显示实际廓形（红色实线）和理论廓形（蓝色点线）
            x_actual_rot, y_actual_rot = compute_rotated_cam(x_actual, y_actual, angle_rad)
            if smooth_display:
                x_rot_s, y_rot_s = smooth_closed_curve(x_rot, y_rot)
                x_actual_s, y_actual_s = smooth_closed_curve(x_actual_rot, y_actual_rot)
            else:
                x_rot_s, y_rot_s = x_rot, y_rot
                x_actual_s, y_actual_s = x_actual_rot, y_actual_rot
            ax_gif.plot(x_actual_s, y_actual_s, 'r-', linewidth=2)
            ax_gif.plot(x_rot_s, y_rot_s, 'b:', linewidth=1.5)
        else:
            if smooth_display:
                x_rot_s, y_rot_s = smooth_closed_curve(x_rot, y_rot)
            else:
                x_rot_s, y_rot_s = x_rot, y_rot
            ax_gif.plot(x_rot_s, y_rot_s, 'r-', linewidth=2)

        if show_base:
            ax_gif.plot(x_base, y_base, 'm-', linewidth=1)
        if show_offset:
            ax_gif.plot(x_offset, y_offset, 'c-', linewidth=1)

        frame_data = compute_anim_frame_data(s, ds_ddelta, s_0, e, r_0, sn, pz, i, alpha_all, n_points)
        fx = frame_data['follower_x']
        cy = frame_data['contact_y']
        alpha_i = frame_data['alpha_i']
        nx_i, ny_i = frame_data['nx'], frame_data['ny']
        tx_i, ty_i = frame_data['tx'], frame_data['ty']
        tip_w = r_0 * TIP_WIDTH_RATIO
        tip_h = r_0 * TIP_HEIGHT_RATIO
        rod_top = cy + r_0 * ROD_LENGTH_RATIO

        # 推杆尖端：根据滚子半径显示不同形状
        if r_r > 0:
            # 滚子圆形（与凸轮轮廓线宽一致）
            theta = np.linspace(0, 2 * np.pi, 36)
            roller_x = fx + r_r * np.cos(theta)
            roller_y = cy + r_r * np.sin(theta)
            ax_gif.plot(roller_x, roller_y, 'k-', linewidth=2)
            # 滚子圆心实心小圆
            ax_gif.plot(fx, cy, 'ko', markersize=2)
            # 从圆心向上的推杆线
            ax_gif.plot([fx, fx], [cy, rod_top], 'k-', linewidth=1.5)
        else:
            # 三角形尖端
            ax_gif.plot([fx - tip_w, fx, fx + tip_w, fx - tip_w], [cy + tip_h, cy, cy + tip_h, cy + tip_h], 'k-', linewidth=2)
            ax_gif.plot([fx, fx], [cy + tip_h, rod_top], 'k-', linewidth=2)

        if show_limits:
            ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0], 'c-.', linewidth=1)
            ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h], 'm--', linewidth=1)
        if show_tangent:
            ax_gif.plot([fx - r_0 * tx_i, fx + r_0 * tx_i], [cy - r_0 * ty_i, cy + r_0 * ty_i], 'm-', linewidth=1)
        if show_normal:
            ax_gif.plot([fx + r_0 * nx_i, fx - r_0 * nx_i], [cy + r_0 * ny_i, cy - r_0 * ny_i], 'm-', linewidth=1)
        if show_boundaries:
            for j_b in range(len(pb) - 1):
                idx_b = int(pb[j_b + 1])
                if idx_b < N:
                    ax_gif.plot([0, x_rot[idx_b]], [0, y_rot[idx_b]], 'k-', linewidth=0.8)
        if show_arc:
            arc_r = r_0 * ARC_RADIUS_RATIO
            x_arc, y_arc = compute_pressure_angle_arc(fx, cy, nx_i, ny_i, alpha_i, arc_r)
            ax_gif.plot(x_arc, y_arc, 'k-', linewidth=1)
            ax_gif.plot([fx, fx], [cy - r_0 * 2, cy + r_0 * 5], 'k--', linewidth=0.8)
        draw_fixed_support(ax_gif, r_0)
        ax_gif.set_xlim(xlim)
        ax_gif.set_ylim(ylim)
        ax_gif.set_aspect('equal', adjustable='box')
        ax_gif.set_title(f'{title_anim_gif}  {int(angle_deg):3d}°/360°', fontsize=11)

        ax_info_gif.clear()
        ax_info_gif.set_xticks([])
        ax_info_gif.set_yticks([])
        ax_info_gif.set_frame_on(False)
        info_items = [
            (0.95, rf'{label_delta_gif}: {int(angle_deg):3d}°/360°'),
            (0.85, rf'{label_alpha_gif}: {alpha_i:.1f}°'),
            (0.75, rf'{label_s_gif}: {frame_data["s_i"]:.2f} mm'),
            (0.65, rf'{label_h_gif}: {h:.1f} mm'),
            (0.55, rf'{label_s0_gif}: {s_0:.2f} mm'),
        ]
        for y_pos, text in info_items:
            ax_info_gif.text(0.05, y_pos, text, transform=ax_info_gif.transAxes,
                             fontsize=10, ha='left', va='top', color='#222')

        buf = BytesIO()
        fig_gif.savefig(buf, format='png', dpi=GIF_DPI)
        buf.seek(0)
        img = PILImage.open(buf).copy()
        buf.close()
        frame_images.append(img)

        if progress_callback is not None:
            progress_callback(i, N, None)

    plt.close(fig_gif)

    if progress_callback is not None:
        progress_callback(N - 1, N, "composing")

    if frame_images:
        frame_images[0].save(filepath, save_all=True, append_images=frame_images[1:],
                             duration=GIF_DURATION_MS, loop=0, optimize=True)
    saved_list.append(os.path.basename(filepath))
