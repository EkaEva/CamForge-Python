"""CamForge CustomTkinter 样式常量

定义现代化的 UI 样式常量，包括颜色、间距、圆角等。
采用 Apple/iOS 设计风格。
"""

import customtkinter as ctk

# ============================================================================
# 全局配置
# ============================================================================

# 初始化 CustomTkinter 全局设置
ctk.set_appearance_mode("System")  # 跟随系统深浅色
ctk.set_default_color_theme("blue")  # Apple System Blue 主色调

# ============================================================================
# 布局常量
# ============================================================================

UI_PADDING = 15          # 外边距
CARD_PADDING = 10        # 卡片内边距
CORNER_RADIUS = 10       # 圆角半径
SMALL_CORNER_RADIUS = 6  # 小圆角半径（输入框等）

# 侧边栏宽度
SIDEBAR_WIDTH = 280

# 控件尺寸
BUTTON_HEIGHT = 36
ENTRY_HEIGHT = 28
SWITCH_WIDTH = 36
SWITCH_HEIGHT = 20

# ============================================================================
# 颜色方案 (Apple/iOS 风格)
# ============================================================================

# 浅色模式颜色
COLORS_LIGHT = {
    # 背景色
    'sidebar_bg': '#f2f2f7',      # iOS 设置页背景
    'card_bg': '#ffffff',          # 卡片背景
    'main_bg': '#ffffff',          # 主区域背景
    'toolbar_bg': '#ffffff',       # 工具栏背景

    # 文字色
    'text_primary': '#1d1d1f',     # 主要文字
    'text_secondary': '#8e8e93',   # 次要文字
    'text_tertiary': '#c7c7cc',    # 第三级文字

    # 主题色
    'accent': '#007aff',           # Apple Blue
    'accent_hover': '#0066d6',     # 悬停色

    # 功能色
    'success': '#34c759',          # Apple Green
    'success_hover': '#32b353',
    'warning': '#ff9500',          # Apple Orange
    'warning_hover': '#e68600',
    'danger': '#ff3b30',           # Apple Red
    'danger_hover': '#e6352b',

    # 边框和分隔线
    'separator': '#c6c6c8',
    'border': '#e5e5e7',
}

# 深色模式颜色
COLORS_DARK = {
    # 背景色
    'sidebar_bg': '#1c1c1e',       # iOS 深色背景
    'card_bg': '#2c2c2e',          # 卡片背景
    'main_bg': '#000000',          # 主区域背景
    'toolbar_bg': '#1c1c1e',       # 工具栏背景

    # 文字色
    'text_primary': '#f5f5f7',     # 主要文字
    'text_secondary': '#8e8e93',   # 次要文字
    'text_tertiary': '#48484a',    # 第三级文字

    # 主题色
    'accent': '#0a84ff',           # Apple Blue (深色)
    'accent_hover': '#4090ff',

    # 功能色
    'success': '#30d158',          # Apple Green (深色)
    'success_hover': '#28b74c',
    'warning': '#ff9f0a',          # Apple Orange (深色)
    'warning_hover': '#e68a00',
    'danger': '#ff453a',           # Apple Red (深色)
    'danger_hover': '#e63e34',

    # 边框和分隔线
    'separator': '#38383a',
    'border': '#3a3a3c',
}

# ============================================================================
# 字体配置
# ============================================================================

# 字体族
FONT_FAMILY = "Microsoft YaHei"  # 中文字体
FONT_FAMILY_EN = "Segoe UI"       # 英文字体

# 字体大小
FONT_SIZE_TITLE = 24      # 标题
FONT_SIZE_SECTION = 11    # 分组标题
FONT_SIZE_LABEL = 13      # 标签
FONT_SIZE_BUTTON = 13     # 按钮
FONT_SIZE_ENTRY = 13      # 输入框

# ============================================================================
# 按钮样式
# ============================================================================

# 主要按钮样式（填充）
BUTTON_PRIMARY = {
    'fg_color': COLORS_LIGHT['accent'],
    'hover_color': COLORS_LIGHT['accent_hover'],
    'text_color': 'white',
    'corner_radius': CORNER_RADIUS,
    'height': BUTTON_HEIGHT,
}

# 成功按钮样式（绿色）
BUTTON_SUCCESS = {
    'fg_color': COLORS_LIGHT['success'],
    'hover_color': COLORS_LIGHT['success_hover'],
    'text_color': 'white',
    'corner_radius': CORNER_RADIUS,
    'height': BUTTON_HEIGHT,
}

# 警告按钮样式（橙色）
BUTTON_WARNING = {
    'fg_color': COLORS_LIGHT['warning'],
    'hover_color': COLORS_LIGHT['warning_hover'],
    'text_color': 'white',
    'corner_radius': CORNER_RADIUS,
    'height': BUTTON_HEIGHT,
}

# 轮廓按钮样式（透明背景+边框）
BUTTON_OUTLINE = {
    'fg_color': 'transparent',
    'border_width': 2,
    'text_color': COLORS_LIGHT['accent'],
    'hover_color': '#e5f1ff',
    'corner_radius': CORNER_RADIUS,
    'height': BUTTON_HEIGHT,
}

# 次要按钮样式（灰色）
BUTTON_SECONDARY = {
    'fg_color': '#64748b',
    'hover_color': '#475569',
    'text_color': 'white',
    'corner_radius': CORNER_RADIUS,
    'height': BUTTON_HEIGHT,
}

# ============================================================================
# 输入框样式
# ============================================================================

ENTRY_STYLE = {
    'height': ENTRY_HEIGHT,
    'corner_radius': SMALL_CORNER_RADIUS,
    'justify': 'right',
}

# ============================================================================
# 开关样式
# ============================================================================

SWITCH_STYLE = {
    'switch_width': SWITCH_WIDTH,
    'switch_height': SWITCH_HEIGHT,
}

# ============================================================================
# 下拉菜单样式
# ============================================================================

OPTION_MENU_STYLE = {
    'corner_radius': SMALL_CORNER_RADIUS,
    'dynamic_resizing': False,
    'width': 140,
    'height': ENTRY_HEIGHT,
}

# 下拉菜单按钮样式（未展开时）
OPTION_MENU_BUTTON_STYLE = {
    'fg_color': COLORS_LIGHT['card_bg'],
    'button_color': COLORS_LIGHT['accent'],
    'button_hover_color': COLORS_LIGHT['accent_hover'],
    'text_color': COLORS_LIGHT['text_primary'],
    'hover': True,
}

# 下拉菜单列表样式（展开时的选项列表）
OPTION_MENU_DROPDOWN_STYLE = {
    'fg_color': COLORS_LIGHT['card_bg'],
    'hover_color': '#e5f1ff',
    'text_color': COLORS_LIGHT['text_primary'],
}

# ============================================================================
# 卡片样式
# ============================================================================

CARD_STYLE = {
    'corner_radius': CORNER_RADIUS,
}

# ============================================================================
# 辅助函数
# ============================================================================

def get_colors(dark_mode: bool = False) -> dict:
    """获取当前主题的颜色方案"""
    return COLORS_DARK if dark_mode else COLORS_LIGHT


def get_button_style(style_name: str, dark_mode: bool = False) -> dict:
    """获取按钮样式"""
    styles = {
        'primary': BUTTON_PRIMARY.copy(),
        'success': BUTTON_SUCCESS.copy(),
        'warning': BUTTON_WARNING.copy(),
        'outline': BUTTON_OUTLINE.copy(),
        'secondary': BUTTON_SECONDARY.copy(),
    }

    style = styles.get(style_name, BUTTON_PRIMARY)

    # 深色模式调整
    if dark_mode and style_name == 'outline':
        style['text_color'] = COLORS_DARK['accent']
        style['hover_color'] = '#1a2c42'

    return style


def create_font(size: int = FONT_SIZE_LABEL, weight: str = "normal") -> tuple:
    """创建字体元组"""
    return (FONT_FAMILY, size, weight)


def create_ctk_font(size: int = FONT_SIZE_LABEL, weight: str = "normal"):
    """创建 CTkFont 对象"""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
