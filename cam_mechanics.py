"""
CamForge - 凸轮机构运动学计算模块
实现五种推杆运动规律、凸轮廓形计算、压力角计算及动画辅助函数
"""

from __future__ import annotations

__version__: str = "0.6.0"

import numpy as np
from numpy.typing import NDArray

N_POINTS: int = 360  # 一圈离散点数（1度步长）
DEG2RAD: float = np.pi / 180


# ---------------------------------------------------------------------------
# 运动规律：推程
# ---------------------------------------------------------------------------

def compute_rise(
    delta_arr: NDArray[np.floating],
    delta_0: float,
    h: float,
    omega: float,
    law: int,
) -> tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating]]:
    """
    计算推程阶段的位移、速度、加速度

    Parameters
    ----------
    delta_arr : ndarray - 推程转角数组 (rad)，从0开始
    delta_0 : float - 推程运动角 (rad)
    h : float - 推杆最大位移
    omega : float - 凸轮角速度
    law : int - 运动规律编号 (1-5)

    Returns
    -------
    s, v, a : ndarray
    """
    if delta_0 <= 0:
        raise ValueError(f"delta_0 must be > 0, got {delta_0}")
    if h < 0:
        raise ValueError(f"h must be >= 0, got {h}")
    if omega <= 0:
        raise ValueError(f"omega must be > 0, got {omega}")
    if law not in (1, 2, 3, 4, 5, 6):
        raise ValueError(f"law must be 1-6, got {law}")
    if law == 1:  # 等速运动
        s = h * delta_arr / delta_0
        v = h * omega / delta_0 * np.ones_like(delta_arr)
        a = np.zeros_like(delta_arr)

    elif law == 2:  # 等加速等减速（按角度中点分割）
        mask1 = delta_arr <= delta_0 / 2
        mask2 = ~mask1
        delta_1 = delta_arr[mask1]
        delta_2 = delta_arr[mask2]

        s = np.empty_like(delta_arr)
        v = np.empty_like(delta_arr)
        a = np.empty_like(delta_arr)

        # 等加速段
        s[mask1] = 2 * h * delta_1 ** 2 / delta_0 ** 2
        v[mask1] = 4 * h * omega * delta_1 / delta_0 ** 2
        a[mask1] = 4 * h * omega ** 2 / delta_0 ** 2

        # 等减速段
        s[mask2] = h - 2 * h * (delta_0 - delta_2) ** 2 / delta_0 ** 2
        v[mask2] = 4 * h * omega * (delta_0 - delta_2) / delta_0 ** 2
        a[mask2] = -4 * h * omega ** 2 / delta_0 ** 2

    elif law == 3:  # 简谐运动
        ratio = np.pi * delta_arr / delta_0
        s = h * (1 - np.cos(ratio)) / 2
        v = np.pi * h * omega * np.sin(ratio) / (2 * delta_0)
        a = np.pi ** 2 * h * omega ** 2 * np.cos(ratio) / (2 * delta_0 ** 2)

    elif law == 4:  # 摆线运动
        ratio = 2 * np.pi * delta_arr / delta_0
        s = h * (delta_arr / delta_0 - np.sin(ratio) / (2 * np.pi))
        v = h * omega * (1 - np.cos(ratio)) / delta_0
        a = 2 * np.pi * h * omega ** 2 * np.sin(ratio) / delta_0 ** 2

    elif law == 5:  # 五次多项式 (3-4-5)
        t = delta_arr / delta_0
        s = h * (10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5)
        v = h * omega / delta_0 * (30 * t ** 2 - 60 * t ** 3 + 30 * t ** 4)
        a = h * omega ** 2 / delta_0 ** 2 * (60 * t - 180 * t ** 2 + 120 * t ** 3)

    elif law == 6:  # 七次多项式 (4-5-6-7)
        t = delta_arr / delta_0
        s = h * (35 * t ** 4 - 84 * t ** 5 + 70 * t ** 6 - 20 * t ** 7)
        v = h * omega / delta_0 * (140 * t ** 3 - 420 * t ** 4 + 420 * t ** 5 - 140 * t ** 6)
        a = h * omega ** 2 / delta_0 ** 2 * (420 * t ** 2 - 1680 * t ** 3 + 2100 * t ** 4 - 840 * t ** 5)

    else:
        raise ValueError(f"law must be 1-6, got {law}")

    return s, v, a


# ---------------------------------------------------------------------------
# 运动规律：回程
# ---------------------------------------------------------------------------

def compute_return(
    delta_arr: NDArray[np.floating],
    delta_ret: float,
    h: float,
    omega: float,
    law: int,
) -> tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating]]:
    """
    计算回程阶段的位移、速度、加速度

    Parameters
    ----------
    delta_arr : ndarray - 回程转角数组 (rad)，从0开始（局部坐标）
    delta_ret : float - 回程运动角 (rad)
    h : float - 推杆最大位移
    omega : float - 凸轮角速度
    law : int - 运动规律编号 (1-5)

    Returns
    -------
    s, v, a : ndarray
    """
    if delta_ret <= 0:
        raise ValueError(f"delta_ret must be > 0, got {delta_ret}")
    if h < 0:
        raise ValueError(f"h must be >= 0, got {h}")
    if omega <= 0:
        raise ValueError(f"omega must be > 0, got {omega}")
    if law not in (1, 2, 3, 4, 5, 6):
        raise ValueError(f"law must be 1-6, got {law}")
    if law == 1:  # 等速运动
        s = h * (1 - delta_arr / delta_ret)
        v = -h * omega / delta_ret * np.ones_like(delta_arr)
        a = np.zeros_like(delta_arr)

    elif law == 2:  # 等加速等减速（按角度中点分割）
        mask1 = delta_arr <= delta_ret / 2
        mask2 = ~mask1
        delta_1 = delta_arr[mask1]
        delta_2 = delta_arr[mask2]

        s = np.empty_like(delta_arr)
        v = np.empty_like(delta_arr)
        a = np.empty_like(delta_arr)

        # 等加速段（速度减小）
        s[mask1] = h - 2 * h * delta_1 ** 2 / delta_ret ** 2
        v[mask1] = -4 * h * omega * delta_1 / delta_ret ** 2
        a[mask1] = -4 * h * omega ** 2 / delta_ret ** 2

        # 等减速段
        s[mask2] = 2 * h * (delta_ret - delta_2) ** 2 / delta_ret ** 2
        v[mask2] = -4 * h * omega * (delta_ret - delta_2) / delta_ret ** 2
        a[mask2] = 4 * h * omega ** 2 / delta_ret ** 2

    elif law == 3:  # 简谐运动
        ratio = np.pi * delta_arr / delta_ret
        s = h * (1 + np.cos(ratio)) / 2
        v = -np.pi * h * omega * np.sin(ratio) / (2 * delta_ret)
        a = -np.pi ** 2 * h * omega ** 2 * np.cos(ratio) / (2 * delta_ret ** 2)

    elif law == 4:  # 摆线运动
        ratio = 2 * np.pi * delta_arr / delta_ret
        s = h - h * (delta_arr / delta_ret - np.sin(ratio) / (2 * np.pi))
        v = -h * omega * (1 - np.cos(ratio)) / delta_ret
        a = -2 * np.pi * h * omega ** 2 * np.sin(ratio) / delta_ret ** 2

    elif law == 5:  # 五次多项式 (3-4-5)
        t = delta_arr / delta_ret
        s = h * (1 - (10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5))
        v = -h * omega / delta_ret * (30 * t ** 2 - 60 * t ** 3 + 30 * t ** 4)
        a = -h * omega ** 2 / delta_ret ** 2 * (60 * t - 180 * t ** 2 + 120 * t ** 3)

    elif law == 6:  # 七次多项式 (4-5-6-7)
        t = delta_arr / delta_ret
        s = h * (1 - (35 * t ** 4 - 84 * t ** 5 + 70 * t ** 6 - 20 * t ** 7))
        v = -h * omega / delta_ret * (140 * t ** 3 - 420 * t ** 4 + 420 * t ** 5 - 140 * t ** 6)
        a = -h * omega ** 2 / delta_ret ** 2 * (420 * t ** 2 - 1680 * t ** 3 + 2100 * t ** 4 - 840 * t ** 5)

    else:
        raise ValueError(f"law must be 1-6, got {law}")

    return s, v, a


# ---------------------------------------------------------------------------
# 全程运动计算
# ---------------------------------------------------------------------------

def compute_full_motion(
    delta_0_deg: float, delta_01_deg: float, delta_ret_deg: float, delta_02_deg: float,
    h: float, r_0: float, e: float, omega: float, tc_law: int, hc_law: int,
    n_points: int = 360,
) -> tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating],
           NDArray[np.floating], NDArray[np.floating], list[float]]:
    """
    计算凸轮一整圈运动的位移、速度、加速度

    Parameters
    ----------
    delta_0_deg : float - 推程运动角 (度)
    delta_01_deg : float - 远休止角 (度)
    delta_ret_deg : float - 回程运动角 (度)
    delta_02_deg : float - 近休止角 (度)
    h : float - 推杆最大位移
    r_0 : float - 基圆半径
    e : float - 偏距
    omega : float - 凸轮角速度
    tc_law : int - 推程运动规律 (1-5)
    hc_law : int - 回程运动规律 (1-5)
    n_points : int - 离散点数 (默认 360)

    Returns
    -------
    delta_deg : ndarray - 全程转角 (度)
    s, v, a : ndarray - 位移、速度、加速度
    ds_ddelta : ndarray - 位移对转角的解析导数 ds/dδ = v/ω
    phase_boundaries : list - 各阶段分界点 (度数)
    """
    if delta_0_deg <= 0 or delta_01_deg < 0 or delta_ret_deg <= 0 or delta_02_deg < 0:
        raise ValueError(f"All motion angles must be positive (dwell angles >= 0): "
                         f"delta_0={delta_0_deg}, delta_01={delta_01_deg}, "
                         f"delta_ret={delta_ret_deg}, delta_02={delta_02_deg}")
    if abs(delta_0_deg + delta_01_deg + delta_ret_deg + delta_02_deg - 360) > 0.01:
        raise ValueError(f"Four angles must sum to 360°, "
                         f"got {delta_0_deg + delta_01_deg + delta_ret_deg + delta_02_deg}")
    if h <= 0:
        raise ValueError(f"h must be > 0, got {h}")
    if r_0 <= 0:
        raise ValueError(f"r_0 must be > 0, got {r_0}")
    if e < 0:
        raise ValueError(f"e must be >= 0, got {e}")
    if e >= r_0:
        raise ValueError(f"e must be < r_0, got e={e}, r_0={r_0}")
    if omega <= 0:
        raise ValueError(f"omega must be > 0, got {omega}")
    if tc_law not in (1, 2, 3, 4, 5, 6):
        raise ValueError(f"tc_law must be 1-6, got {tc_law}")
    if hc_law not in (1, 2, 3, 4, 5, 6):
        raise ValueError(f"hc_law must be 1-6, got {hc_law}")
    if n_points < 36:
        raise ValueError(f"n_points must be >= 36, got {n_points}")
    n_total = n_points
    delta = np.linspace(0, 2 * np.pi, n_total, endpoint=False)
    delta_deg_arr = np.degrees(delta)

    s = np.empty(n_total)
    v = np.empty(n_total)
    a = np.empty(n_total)

    # 各阶段角度范围（弧度）
    delta_0 = np.radians(delta_0_deg)
    delta_ret = np.radians(delta_ret_deg)

    # 阶段分界索引（带边界保护）
    # 索引需要根据 n_points 缩放：角度/360° * n_points
    scale = n_points / 360.0
    i1 = int(round(delta_0_deg * scale))            # 推程结束
    i2 = i1 + int(round(delta_01_deg * scale))      # 远休止结束
    i3 = i2 + int(round(delta_ret_deg * scale))     # 回程结束
    # 确保索引不越界：i1 >= 1, i2 > i1, i3 <= n_total
    i1 = max(1, min(i1, n_total - 2))
    i2 = max(i1 + 1, min(i2, n_total - 1))
    i3 = max(i2 + 1, min(i3, n_total))

    # 推程：独立 linspace，endpoint=True 确保末端角度精确到达 delta_0
    delta_rise = np.linspace(0, delta_0, i1, endpoint=True)
    s[:i1], v[:i1], a[:i1] = compute_rise(delta_rise, delta_0, h, omega, tc_law)

    # 远休止
    s[i1:i2] = h
    v[i1:i2] = 0
    a[i1:i2] = 0

    # 回程：独立 linspace，endpoint=True 确保末端角度精确到达 delta_ret
    n_return = i3 - i2
    delta_return_local = np.linspace(0, delta_ret, n_return, endpoint=True)
    s[i2:i3], v[i2:i3], a[i2:i3] = compute_return(
        delta_return_local, delta_ret, h, omega, hc_law)

    # 近休止
    s[i3:] = 0
    v[i3:] = 0
    a[i3:] = 0

    # 位移对转角的解析导数 ds/dδ = v/ω（精确，非数值微分）
    ds_ddelta = v / omega

    # 阶段分界点 (度)
    phase_boundaries = [
        0,
        delta_0_deg,
        delta_0_deg + delta_01_deg,
        delta_0_deg + delta_01_deg + delta_ret_deg,
        360
    ]

    return delta_deg_arr, s, v, a, ds_ddelta, phase_boundaries


# ---------------------------------------------------------------------------
# 凸轮廓形计算
# ---------------------------------------------------------------------------

def compute_cam_profile(
    s: NDArray[np.floating], r_0: float, e: float, sn: int, pz: int,
) -> tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating]]:
    """
    计算凸轮廓形坐标

    Parameters
    ----------
    s : ndarray - 位移数组
    r_0 : float - 基圆半径
    e : float - 偏距（正值）
    sn : int - 旋向符号 (+1顺时针, -1逆时针)
    pz : int - 偏距符号 (+1正偏距, -1负偏距)

    Returns
    -------
    x, y : ndarray - 凸轮廓形坐标
    s_0 : float - 初始位移 sqrt(r_0^2 - e^2)
    """
    if r_0 <= 0:
        raise ValueError(f"r_0 must be > 0, got {r_0}")
    if e < 0:
        raise ValueError(f"e must be >= 0, got {e}")
    if e >= r_0:
        raise ValueError(f"e must be < r_0, got e={e}, r_0={r_0}")
    if sn not in (1, -1):
        raise ValueError(f"sn must be +1 or -1, got {sn}")
    if pz not in (1, -1):
        raise ValueError(f"pz must be +1 or -1, got {pz}")
    s_0 = np.sqrt(r_0 ** 2 - e ** 2)
    n = len(s)
    delta = np.linspace(0, 2 * np.pi, n, endpoint=False)

    x = (s_0 + s) * np.sin(delta) + pz * e * np.cos(delta)
    y = (s_0 + s) * np.cos(delta) - pz * e * np.sin(delta)
    x = -sn * x

    return x, y, s_0


# ---------------------------------------------------------------------------
# 滚子从动件实际廓形计算
# ---------------------------------------------------------------------------

def compute_roller_profile(
    x_theory: NDArray[np.floating], y_theory: NDArray[np.floating],
    r_r: float, sn: int,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """
    计算滚子从动件的实际廓形（理论廓形的等距内包络线）

    实际廓形 = 理论廓形向内偏移滚子半径 r_r 的等距曲线。
    对每个理论廓形点，沿内法线方向偏移 r_r 得到实际廓形点。

    Parameters
    ----------
    x_theory, y_theory : ndarray - 理论廓形坐标
    r_r : float - 滚子半径（>0 时计算实际廓形，=0 时返回理论廓形）
    sn : int - 旋向符号 (+1顺时针, -1逆时针)

    Returns
    -------
    x_actual, y_actual : ndarray - 实际廓形坐标
    """
    if r_r < 0:
        raise ValueError(f"r_r must be >= 0, got {r_r}")
    if r_r == 0:
        return x_theory.copy(), y_theory.copy()

    # 中心差分求切线方向（向量化，周期边界 via np.roll）
    dx = np.roll(x_theory, -1) - np.roll(x_theory, 1)
    dy = np.roll(y_theory, -1) - np.roll(y_theory, 1)
    len_t = np.hypot(dx, dy)

    # 切线方向（单位向量），处理近零长度
    safe_len = np.where(len_t > 1e-12, len_t, 1.0)
    tx = dx / safe_len
    ty = dy / safe_len
    degenerate = len_t < 1e-12
    tx = np.where(degenerate, 0.0, tx)
    ty = np.where(degenerate, 0.0, ty)

    # 内法线方向（指向凸轮中心）
    # 对于 sn=1 (顺时针)，内法线 = 切线顺时针旋转90度
    # 对于 sn=-1 (逆时针)，内法线 = 切线逆时针旋转90度
    if sn == 1:
        nx = ty
        ny = -tx
    else:
        nx = -ty
        ny = tx

    # 选择指向凸轮中心(0,0)的法线方向
    dot = -x_theory * nx + -y_theory * ny
    flip = dot < 0
    nx = np.where(flip, -nx, nx)
    ny = np.where(flip, -ny, ny)

    # 退化点回退到理论廓形坐标
    x_actual = np.where(degenerate, x_theory, x_theory + r_r * nx)
    y_actual = np.where(degenerate, y_theory, y_theory + r_r * ny)

    return x_actual, y_actual


# ---------------------------------------------------------------------------
# 凸轮廓形曲率半径计算
# ---------------------------------------------------------------------------

def compute_curvature_radius(
    x: NDArray[np.floating], y: NDArray[np.floating],
) -> NDArray[np.floating]:
    """
    计算凸轮廓形各点的曲率半径

    使用参数曲线曲率公式：
    ρ = ((x'^2 + y'^2)^(3/2)) / |x'y'' - y'x''|

    Parameters
    ----------
    x, y : ndarray - 凸轮廓形坐标

    Returns
    -------
    rho : ndarray - 曲率半径数组（正值表示凸面，负值表示凹面/ undercutting）
    """
    n = len(x)
    if n < 3:
        raise ValueError(f"Need at least 3 points, got {n}")

    # 中心差分求一阶和二阶导数（向量化，周期边界 via np.roll）
    x_prev = np.roll(x, 1)
    x_next = np.roll(x, -1)
    y_prev = np.roll(y, 1)
    y_next = np.roll(y, -1)

    dx = (x_next - x_prev) / 2.0
    dy = (y_next - y_prev) / 2.0
    ddx = x_next - 2 * x + x_prev
    ddy = y_next - 2 * y + y_prev

    # 曲率 κ = (x'y'' - y'x'') / (x'^2 + y'^2)^(3/2)
    cross = dx * ddy - dy * ddx
    speed_cubed = (dx ** 2 + dy ** 2) ** 1.5

    # 避免除零
    rho = np.where(speed_cubed > 1e-12, speed_cubed / cross, np.inf)

    return rho


# ---------------------------------------------------------------------------
# 压力角计算
# ---------------------------------------------------------------------------

def compute_pressure_angle(
    s: NDArray[np.floating], ds_ddelta: NDArray[np.floating],
    s_0: float, e: float, pz: int,
) -> NDArray[np.floating]:
    """
    用解析公式计算压力角

    α = arctan2(ds/dδ - pz·e, s_0 + s)

    Parameters
    ----------
    s : ndarray - 位移数组
    ds_ddelta : ndarray - 位移对转角的解析导数
    s_0 : float - 初始位移
    e : float - 偏距（正值）
    pz : int - 偏距符号 (+1正偏距, -1负偏距)

    Returns
    -------
    alpha : ndarray - 压力角 (度)
    """
    if s_0 <= 0:
        raise ValueError(f"s_0 must be > 0, got {s_0}")
    if e < 0:
        raise ValueError(f"e must be >= 0, got {e}")
    if pz not in (1, -1):
        raise ValueError(f"pz must be +1 or -1, got {pz}")
    numerator = ds_ddelta - pz * e
    denominator = s_0 + s
    alpha = np.degrees(np.arctan2(numerator, denominator))
    return alpha


# ---------------------------------------------------------------------------
# 凸轮旋转（动画用）
# ---------------------------------------------------------------------------

def compute_rotated_cam(
    x_static: NDArray[np.floating], y_static: NDArray[np.floating], angle_rad: float,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """
    通过旋转矩阵旋转凸轮廓形坐标

    Parameters
    ----------
    x_static, y_static : ndarray - 静态凸轮廓形坐标
    angle_rad : float - 旋转角度 (rad)

    Returns
    -------
    x, y : ndarray - 旋转后的凸轮廓形坐标
    """
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    x = x_static * cos_a - y_static * sin_a
    y = x_static * sin_a + y_static * cos_a
    return x, y


# ---------------------------------------------------------------------------
# 动画帧数据计算
# ---------------------------------------------------------------------------

def compute_anim_frame_data(
    s: NDArray[np.floating], ds_ddelta: NDArray[np.floating],
    s_0: float, e: float, r_0: float, sn: int, pz: int,
    i: int, alpha_all: NDArray[np.floating],
    n_points: int = 360,
) -> dict[str, float]:
    """
    解析计算一帧动画所需的全部数据

    法线/切线方向由廓形解析导数计算，而非接触点到中心的几何连线。
    当偏距 e≠0 时，两者方向不同。

    Parameters
    ----------
    s : ndarray - 位移数组
    ds_ddelta : ndarray - 位移对转角的解析导数
    s_0 : float - 初始位移
    e : float - 偏距
    r_0 : float - 基圆半径
    sn : int - 旋向符号
    pz : int - 偏距符号
    i : int - 当前帧索引
    alpha_all : ndarray - 全程压力角数组
    n_points : int - 离散点数（默认 360）

    Returns
    -------
    dict : 包含 follower_x, contact_y, nx, ny, tx, ty, alpha_i, s_i
    """
    if i < 0 or i >= len(s):
        raise ValueError(f"Frame index i must be in [0, {len(s)-1}], got {i}")
    # 推杆固定在 x = -sn*pz*e（反转法中推杆的固定x坐标）
    follower_x = -sn * pz * e
    # 接触点 y = s_0 + s[i]（解析值，精确无跳动）
    contact_y = s_0 + s[i]

    # ---- 解析切线/法线方向 ----
    # 静态廓形（翻转前）对 δ 的导数在 delta_i 处：
    #   dx0/dδ = (s_0+s)*cos(δ) + (ds/dδ)*sin(δ) - pz*e*sin(δ)
    #   dy0/dδ = -(s_0+s)*sin(δ) + (ds/dδ)*cos(δ) - pz*e*cos(δ)
    # 翻转后：dx/dδ = -sn * dx0/dδ,  dy/dδ = dy0/dδ
    # 旋转 θ 后：切线 = R(θ) * (dx/dδ, dy/dδ)
    # 角度需要根据 n_points 缩放：角度 = i * 360 / n_points
    angle_deg = i * 360.0 / n_points
    delta_i = angle_deg * DEG2RAD
    theta = -sn * delta_i  # sn=1时顺时针(负角)，sn=-1时逆时针(正角)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    cos_d, sin_d = np.cos(delta_i), np.sin(delta_i)

    sp = s_0 + s[i]       # s_0 + s
    dsd = ds_ddelta[i]    # ds/dδ

    # 翻转前廓形导数
    dx0 = sp * cos_d + dsd * sin_d - pz * e * sin_d
    dy0 = -sp * sin_d + dsd * cos_d - pz * e * cos_d
    # 翻转后
    dx = -sn * dx0
    dy = dy0
    # 旋转后得到切线方向
    tx = dx * cos_t - dy * sin_t
    ty = dx * sin_t + dy * cos_t
    len_t = np.hypot(tx, ty)
    if len_t > 1e-10:
        tx /= len_t
        ty /= len_t
    else:
        tx, ty = 1.0, 0.0

    # 法线 = 切线旋转90度，取指向凸轮中心的方向
    nx1, ny1 = -ty, tx    # 逆时针旋转90度
    nx2, ny2 = ty, -tx    # 顺时针旋转90度
    # 接触点坐标
    cx = follower_x
    cy = contact_y
    # 选择指向凸轮中心(0,0)的法线
    dot1 = (0 - cx) * nx1 + (0 - cy) * ny1
    if dot1 > 0:
        nx, ny = nx1, ny1
    else:
        nx, ny = nx2, ny2

    alpha_i = abs(alpha_all[i])
    s_i = s[i]

    return {
        'follower_x': follower_x,
        'contact_y': contact_y,
        'nx': nx, 'ny': ny,
        'tx': tx, 'ty': ty,
        'alpha_i': alpha_i,
        's_i': s_i,
    }


# ---------------------------------------------------------------------------
# 压力角弧线计算
# ---------------------------------------------------------------------------

def compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r):
    """
    计算压力角弧线坐标（画在凸轮内部，接触点处）

    弧线从推杆中心线方向（-y）出发，扫 alpha_i 角度到达法线方向。
    自动判断扫掠方向，确保弧线角度等于压力角（非补角）。

    Parameters
    ----------
    cx, cy : float - 接触点坐标
    nx, ny : float - 法线方向分量（单位向量）
    alpha_i : float - 压力角绝对值 (度)
    arc_r : float - 弧线半径

    Returns
    -------
    x_arc, y_arc : ndarray - 弧线坐标（角度太小则返回空数组）
    """
    if arc_r <= 0:
        raise ValueError(f"arc_r must be > 0, got {arc_r}")
    if alpha_i < 0.5:
        return np.array([]), np.array([])

    alpha_rad = np.radians(alpha_i)

    # -y 方向角度
    theta_start = -np.pi / 2

    # 计算从 -y 到法线的有向角度差
    theta_n = np.arctan2(ny, nx)
    diff = (theta_n - theta_start + np.pi) % (2 * np.pi) - np.pi

    # 如果 |diff| 不接近 alpha_rad，说明法线方向需要取反
    # （法线有两个方向，当前方向使弧线为补角）
    if abs(abs(diff) - alpha_rad) > 0.1:
        theta_n = np.arctan2(-ny, -nx)
        diff = (theta_n - theta_start + np.pi) % (2 * np.pi) - np.pi

    theta_arr = np.linspace(theta_start, theta_start + diff, 30)

    x_arc = cx + arc_r * np.cos(theta_arr)
    y_arc = cy + arc_r * np.sin(theta_arr)

    return x_arc, y_arc


# ---------------------------------------------------------------------------
# 参数校验
# ---------------------------------------------------------------------------

def validate_params(
    delta_0: float, delta_01: float, delta_ret: float, delta_02: float,
    h: float, r_0: float, e: float, omega: float,
) -> tuple[bool, str]:
    """
    校验凸轮参数

    Returns
    -------
    ok : bool
    error : str or tuple or None
        str: error key (e.g. "error.angles_sum")
        tuple: (error_key, name_key) for parameterized errors
        None: no error
    """
    _ANGLE_NAME_KEYS = [
        ('sidebar.label.delta_0', delta_0),
        ('sidebar.label.delta_01', delta_01),
        ('sidebar.label.delta_ret', delta_ret),
        ('sidebar.label.delta_02', delta_02),
    ]

    if abs(delta_0 + delta_01 + delta_ret + delta_02 - 360) > 0.01:
        return False, "error.angles_sum"

    for name_key, val in _ANGLE_NAME_KEYS:
        if val != int(val):
            return False, ("error.angle_integer", name_key)
        if val <= 1:
            return False, ("error.angle_min", name_key)

    if h <= 0:
        return False, "error.h_positive"
    if r_0 <= 0:
        return False, "error.r0_positive"
    if omega <= 0:
        return False, "error.omega_positive"
    if e < 0:
        return False, "error.e_negative"
    if e >= r_0:
        return False, "error.e_lt_r0"

    return True, None
