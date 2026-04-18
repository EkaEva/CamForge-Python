"""CamForge 静态图表绘制"""

import numpy as np

from i18n import t

from .constants import THEME, MAX_PRESSURE_ANGLE
from .drawing import draw_fixed_support


def draw_motion_curves(ax, data, lang, show_law_names=False):
    """
    在给定 ax 上绘制三 Y 轴推杆运动线图
    左侧 Y 轴：位移 s（红色实线）
    右侧 Y 轴 1：速度 v（蓝色虚线）
    右侧 Y 轴 2：加速度 a（绿色点划线）
    """
    delta_deg = data['delta_deg']
    s = data['s']
    v = data['v']
    a = data['a']
    pb = data['phase_bounds']
    h = data['h']

    # 清除主轴
    ax.clear()

    # 位移曲线（左侧 Y 轴，红色实线）
    color_s = 'tab:red'
    ax.plot(delta_deg, s, color=color_s, linestyle='-', linewidth=1.5, label=t("plot.legend.displacement", lang))
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$s$ (mm)', color=color_s)
    ax.tick_params(axis='y', labelcolor=color_s)
    ax.set_xlim(0, 360)
    ax.set_ylim(0, h * 1.15)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True, linestyle=':', alpha=0.6)

    # 相位分界线
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)

    # 速度曲线（右侧 Y 轴 1，蓝色虚线）
    ax_v = ax.twinx()
    color_v = 'tab:blue'
    v_max = np.max(np.abs(v)) * 1.15 if np.max(np.abs(v)) > 0 else 1
    ax_v.plot(delta_deg, v, color=color_v, linestyle='--', linewidth=1.5, label=t("plot.legend.velocity", lang))
    ax_v.set_ylabel(r'$v$ (mm/s)', color=color_v)
    ax_v.tick_params(axis='y', labelcolor=color_v)
    ax_v.set_ylim(-v_max, v_max)

    # 加速度曲线（右侧 Y 轴 2，绿色点划线）
    ax_a = ax.twinx()
    color_a = 'tab:green'
    a_max = np.max(np.abs(a)) * 1.15 if np.max(np.abs(a)) > 0 else 1
    ax_a.plot(delta_deg, a, color=color_a, linestyle='-.', linewidth=1.5, label=t("plot.legend.acceleration", lang))
    ax_a.set_ylabel(r'$a$ (mm/s$^2$)', color=color_a)
    ax_a.tick_params(axis='y', labelcolor=color_a)
    ax_a.set_ylim(-a_max, a_max)

    # 调整右侧 Y 轴位置，避免重叠
    ax_a.spines['right'].set_position(('outward', 60))

    # 标题
    if show_law_names:
        tc_name = t(f"law.{data.get('tc_law', 1)}", lang)
        hc_name = t(f"law.{data.get('hc_law', 1)}", lang)
        title = rf'{t("plot.title.motion", lang)} {t("plot.title.law_format", lang, rise=t("plot.subtitle.rise", lang), tc=tc_name, ret=t("plot.subtitle.return", lang), hc=hc_name)}'
        ax.set_title(title, fontsize=10)
    else:
        ax.set_title(t("plot.title.motion", lang), fontsize=11)

    # 图例（合并三个轴的线条）
    lines_s, labels_s = ax.get_legend_handles_labels()
    lines_v, labels_v = ax_v.get_legend_handles_labels()
    lines_a, labels_a = ax_a.get_legend_handles_labels()
    ax.legend(lines_s + lines_v + lines_a, labels_s + labels_v + labels_a,
              loc='upper right', fontsize=8)

    return ax_v, ax_a


def draw_geometry_constraints(ax, data, lang):
    """
    在给定 ax 上绘制双 Y 轴几何约束指标图
    左侧 Y 轴：压力角 α（红色实线）
    右侧 Y 轴：曲率半径 ρ（蓝色虚线）
    """
    delta_deg = data['delta_deg']
    alpha = data['alpha_all']
    rho = data['rho']
    pb = data['phase_bounds']
    threshold = data.get('alpha_threshold', MAX_PRESSURE_ANGLE)
    r_r = data.get('r_r', 0)

    # 清除主轴
    ax.clear()

    # 压力角曲线（左侧 Y 轴，红色实线）
    color_alpha = 'tab:red'
    ax.plot(delta_deg, alpha, color=color_alpha, linestyle='-', linewidth=1.5, label=t("plot.legend.pressure_angle", lang))
    # 压力角阈值线
    ax.axhline(y=threshold, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(y=-threshold, color='orange', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$\alpha$ (°)', color=color_alpha)
    ax.tick_params(axis='y', labelcolor=color_alpha)
    ax.set_xlim(0, 360)
    alpha_max = np.max(np.abs(alpha)) * 1.15 if np.max(np.abs(alpha)) > 0 else 30
    ax.set_ylim(-alpha_max, alpha_max)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True, linestyle=':', alpha=0.6)

    # 相位分界线
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)

    # 曲率半径曲线（右侧 Y 轴，蓝色虚线）
    ax_rho = ax.twinx()
    color_rho = 'tab:blue'
    ax_rho.plot(delta_deg, rho, color=color_rho, linestyle='--', linewidth=1.5, label=t("plot.legend.curvature", lang))
    # 滚子半径阈值线
    if r_r > 0:
        ax_rho.axhline(y=r_r, color='cyan', linestyle='--', linewidth=1, alpha=0.7)

    ax_rho.set_ylabel(r'$\rho$ (mm)', color=color_rho)
    ax_rho.tick_params(axis='y', labelcolor=color_rho)

    # 限制曲率半径 y 轴范围
    rho_finite = rho[np.isfinite(rho)]
    if len(rho_finite) > 0:
        rho_min = np.min(rho_finite)
        rho_max = np.max(rho_finite)
        if rho_max - rho_min > 10 * (np.percentile(rho_finite, 90) - np.percentile(rho_finite, 10) + 1):
            lo = np.percentile(rho_finite, 5)
            hi = np.percentile(rho_finite, 95)
            ax_rho.set_ylim(lo - (hi - lo) * 0.1, hi + (hi - lo) * 0.1)
        else:
            ax_rho.set_ylim(rho_min * 0.9 if rho_min > 0 else rho_min - 1,
                            rho_max * 1.1 if rho_max > 0 else rho_max + 1)

    # 标题
    ax.set_title(t("plot.title.geometry_constraints", lang), fontsize=11)

    # 图例（合并两个轴的线条）
    lines_alpha, labels_alpha = ax.get_legend_handles_labels()
    lines_rho, labels_rho = ax_rho.get_legend_handles_labels()
    ax.legend(lines_alpha + lines_rho, labels_alpha + labels_rho,
              loc='upper right', fontsize=8)

    return ax_rho


def draw_displacement_curve(ax, data, lang, show_law_names=False):
    """在给定 ax 上绘制位移曲线"""
    delta_deg = data['delta_deg']
    s = data['s']
    pb = data['phase_bounds']
    h = data['h']
    ax.plot(delta_deg, s, 'r-', linewidth=1.5)
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
    if show_law_names:
        tc_name = t(f"law.{data.get('tc_law', 1)}", lang)
        hc_name = t(f"law.{data.get('hc_law', 1)}", lang)
        title = rf'{t("plot.title.displacement", lang)} {t("plot.title.law_format", lang, rise=t("plot.subtitle.rise", lang), tc=tc_name, ret=t("plot.subtitle.return", lang), hc=hc_name)}'
        ax.set_title(title, fontsize=10)
    else:
        ax.set_title(t("plot.title.displacement", lang), fontsize=11)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$s$ (mm)')
    ax.set_xlim(0, 360)
    ax.set_ylim(0, h * 1.15)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True)


def draw_velocity_curve(ax, data, lang):
    """在给定 ax 上绘制速度曲线"""
    delta_deg = data['delta_deg']
    v = data['v']
    pb = data['phase_bounds']
    ax.plot(delta_deg, v, 'r-', linewidth=1.5)
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
    ax.set_title(t("plot.title.velocity", lang), fontsize=11)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$v$ (mm/s)')
    ax.set_xlim(0, 360)
    v_max = np.max(np.abs(v)) * 1.15
    if v_max > 0:
        ax.set_ylim(-v_max, v_max)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True)


def draw_acceleration_curve(ax, data, lang):
    """在给定 ax 上绘制加速度曲线"""
    delta_deg = data['delta_deg']
    a = data['a']
    pb = data['phase_bounds']
    ax.plot(delta_deg, a, 'r-', linewidth=1.5)
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
    ax.set_title(t("plot.title.acceleration", lang), fontsize=11)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$a$ (mm/s$^2$)')
    ax.set_xlim(0, 360)
    a_max = np.max(np.abs(a)) * 1.15
    if a_max > 0:
        ax.set_ylim(-a_max, a_max)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True)


def draw_profile_plot(ax, data, lang):
    """在给定 ax 上绘制凸轮廓形图"""
    x, y = data['x'], data['y']
    r_0, Rmax = data['r_0'], data['Rmax']
    pb = data['phase_bounds']
    n = len(x)
    ax.plot(x, y, 'r-', linewidth=2, label=t("plot.legend.profile", lang))
    ax.plot(data['x_base'], data['y_base'],
            'm-', linewidth=1, label=t("plot.legend.base_circle", lang))
    ax.plot(data['x_offset'], data['y_offset'],
            'c-', linewidth=1, label=t("plot.legend.offset_circle", lang))
    # 滚子实际廓形
    if data.get('r_r', 0) > 0 and 'x_actual' in data:
        ax.plot(data['x_actual'], data['y_actual'],
                'b-', linewidth=1.5, label=t("plot.legend.roller_profile", lang))
    # 最小曲率半径标注
    if 'rho' in data and 'min_rho_idx' in data:
        idx = data['min_rho_idx']
        rho_min = data['rho'][idx]
        if np.isfinite(rho_min):
            ax.plot(x[idx], y[idx], 'go', markersize=8,
                    label=f'{t("plot.legend.min_curvature", lang)}: {rho_min:.2f} mm')
    for b_deg in pb[1:-1]:
        idx = int(b_deg)
        if idx < n:
            ax.plot([0, x[idx]], [0, y[idx]], 'k-', linewidth=0.8)
    ax.set_title(t("plot.title.profile", lang), fontsize=11)
    ax.set_xlabel(r'$x$ (mm)')
    ax.set_ylabel(r'$y$ (mm)')
    ax.grid(True)
    draw_fixed_support(ax, r_0)
    margin = r_0 / 2
    ax.set_xlim(-Rmax - margin, Rmax + margin)
    ax.set_ylim(-Rmax - r_0, Rmax + r_0)
    ax.set_aspect('equal')
    ax.legend(fontsize=8, loc='upper right')


def draw_pressure_angle_curve(ax, data, lang):
    """在给定 ax 上绘制压力角曲线"""
    delta_deg = data['delta_deg']
    alpha = data['alpha_all']
    pb = data['phase_bounds']
    threshold = data.get('alpha_threshold', MAX_PRESSURE_ANGLE)
    ax.plot(delta_deg, alpha, 'r-', linewidth=1.5)
    ax.axhline(y=threshold, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(y=-threshold, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
    ax.set_title(t("plot.title.pressure_angle", lang), fontsize=11)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$\alpha$ (°)')
    ax.set_xlim(0, 360)
    a_max = np.max(np.abs(alpha)) * 1.15
    if a_max > 0:
        ax.set_ylim(-a_max, a_max)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True)


def draw_curvature_radius_curve(ax, data, lang):
    """在给定 ax 上绘制曲率半径曲线"""
    delta_deg = data['delta_deg']
    rho = data['rho']
    pb = data['phase_bounds']
    r_r = data.get('r_r', 0)
    ax.plot(delta_deg, rho, 'r-', linewidth=1.5)
    if r_r > 0:
        ax.axhline(y=r_r, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    for b in pb[1:-1]:
        ax.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
    ax.set_title(t("plot.title.curvature", lang), fontsize=11)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel(r'$\rho$ (mm)')
    ax.set_xlim(0, 360)
    # 限制 y 轴范围，避免极端值导致图形不可读
    rho_finite = rho[np.isfinite(rho)]
    if len(rho_finite) > 0:
        rho_min = np.min(rho_finite)
        rho_max = np.max(rho_finite)
        # 如果范围太大，使用百分位裁剪
        if rho_max - rho_min > 10 * (np.percentile(rho_finite, 90) - np.percentile(rho_finite, 10) + 1):
            lo = np.percentile(rho_finite, 5)
            hi = np.percentile(rho_finite, 95)
            ax.set_ylim(lo - (hi - lo) * 0.1, hi + (hi - lo) * 0.1)
        else:
            ax.set_ylim(rho_min * 1.1 if rho_min > 0 else rho_min - 1,
                        rho_max * 1.1 if rho_max > 0 else rho_max + 1)
    ax.set_xticks(range(0, 361, 60))
    ax.grid(True)
