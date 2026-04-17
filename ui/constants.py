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
    'sidebar_bg':       '#1e293b',
    'sidebar_border':   '#334155',
    'toolbar_bg':       '#0f172a',
    'status_bg':        '#0f172a',
    'status_fg':        '#f87171',
    'info_text':        '#e2e8f0',
    'support_fill':     '#94a3b8',
    'group_fg':         '#94a3b8',
    'separator':        '#334155',
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
    'btn_download':     '#3b82f6',
    'btn_download_active':'#2563eb',
    'btn_fg':           'white',
    'logo_fg':          '#60a5fa',
}

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
