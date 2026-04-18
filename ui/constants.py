"""CamForge 渲染常量与主题颜色"""

# ---------------------------------------------------------------------------
# 渲染常量
# ---------------------------------------------------------------------------
TIP_WIDTH_RATIO = 0.04       # 推杆尖顶半宽与基圆半径之比
TIP_HEIGHT_RATIO = 0.08      # 推杆尖顶高度与基圆半径之比
ROD_LENGTH_RATIO = 4.0       # 推杆杆身长度与基圆半径之比
LIMIT_LINE_RATIO = 3.0       # 推杆上下限线半宽与基圆半径之比
ARC_RADIUS_RATIO = 0.3       # 压力角弧线半径与基圆半径之比
SUPPORT_SIZE_RATIO = 0.12     # 固定铰支座尺寸与基圆半径之比
MAX_PRESSURE_ANGLE = 30.0    # 压力角推荐阈值（度）
ANIM_FRAME_SKIP = 2          # 动画每N帧刷新一次画布
ANIM_MIN_DELAY_MS = 20       # 动画最小帧间隔（毫秒）
ANIM_BASE_DELAY_MS = 200     # 动画基准帧间隔（毫秒，速度=1时）
GIF_DURATION_MS = 30         # GIF 每帧时长（毫秒）
GIF_DPI = 150                # GIF 导出 DPI
STATIC_DPI = 600             # 静态图导出 DPI

# ---------------------------------------------------------------------------
# 主题颜色
# ---------------------------------------------------------------------------
THEME = {
    'sidebar_bg':       '#f8fafc',
    'sidebar_border':   '#e2e8f0',
    'toolbar_bg':       '#ffffff',
    'status_bg':        '#ffffff',
    'status_fg':        '#ef4444',
    'info_text':        '#222',
    'support_fill':     '#555555',
    'group_fg':         '#64748b',
    'separator':        '#e2e8f0',
    'btn_start':        '#10b981',
    'btn_start_active': '#059669',
    'btn_pause':        '#f59e0b',
    'btn_pause_active': '#d97706',
    'btn_clear':        '#64748b',
    'btn_clear_active': '#475569',
    'btn_clear2':       '#94a3b8',
    'btn_clear2_active':'#64748b',
    'btn_random':       '#8b5cf6',
    'btn_random_active':'#7c3aed',
    'btn_download':     '#2563eb',
    'btn_download_active':'#1d4ed8',
    'btn_fg':           'white',
    'logo_fg':          '#2563eb',
}

THEME_DARK = {
    'sidebar_bg':       '#2d3748',
    'sidebar_border':   '#4a5568',
    'toolbar_bg':       '#2d3748',
    'status_bg':        '#2d3748',
    'status_fg':        '#fc8181',
    'info_text':        '#e2e8f0',
    'support_fill':     '#94a3b8',
    'group_fg':         '#a0aec0',
    'separator':        '#4a5568',
    'btn_start':        '#10b981',
    'btn_start_active': '#059669',
    'btn_pause':        '#f59e0b',
    'btn_pause_active': '#d97706',
    'btn_clear':        '#718096',
    'btn_clear_active': '#4a5569',
    'btn_clear2':       '#a0aec0',
    'btn_clear2_active':'#718096',
    'btn_random':       '#8b5cf6',
    'btn_random_active':'#7c3aed',
    'btn_download':     '#3b82f6',
    'btn_download_active':'#2563eb',
    'btn_fg':           'white',
    'logo_fg':          '#63b3ed',
}

# ---------------------------------------------------------------------------
# 参数类型常量
# ---------------------------------------------------------------------------
ANGLE_PARAMS = {'delta_0', 'delta_01', 'delta_ret', 'delta_02'}
FLOAT_PARAMS = {'h', 'r_0', 'e', 'omega', 'r_r', 'alpha_threshold'}
INT_PARAMS = {'n_points'}
COMBO_PARAMS = {'tc_law', 'hc_law', 'sn', 'pz'}
CHECK_PARAMS = {'show_base', 'show_offset', 'show_tangent', 'show_normal',
                'show_limits', 'show_boundaries', 'show_arc'}

# ---------------------------------------------------------------------------
# 默认参数值
# ---------------------------------------------------------------------------
DEFAULT_PARAMS = {
    'delta_0': 90, 'delta_01': 60,
    'delta_ret': 120, 'delta_02': 90,
    'h': 10, 'omega': 1,
    'r_0': 40, 'e': 5,
    'r_r': 0, 'n_points': 360,
    'alpha_threshold': 30,
}
