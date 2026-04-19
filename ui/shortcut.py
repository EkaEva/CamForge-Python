"""
快捷键管理器 - 管理键盘快捷键
支持动画控制、参数操作等快捷键
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

try:
    import customtkinter as ctk
    CTkEntry = ctk.CTkEntry
except ImportError:
    CTkEntry = None


class ShortcutManager:
    """键盘快捷键管理器"""

    def __init__(self, root: tk.Tk):
        """初始化快捷键管理器

        Args:
            root: Tkinter 根窗口
        """
        self.root = root
        self._callbacks: dict[str, Callable] = {}
        self._bound_keys: list[str] = []

    def register(self, key: str, callback: Callable, description: str = '') -> None:
        """注册快捷键

        Args:
            key: 快捷键（如 '<space>', '<Left>', '<Right>'）
            callback: 回调函数
            description: 快捷键描述
        """
        self._callbacks[key] = callback

        def handler(event):
            # 当 Entry 或 Combobox 聚焦时，屏蔽单字母快捷键
            focus_widget = self.root.focus_get()
            if focus_widget is not None:
                # 检查是否是输入类控件
                is_entry = isinstance(focus_widget, tk.Entry)
                is_ctk_entry = CTkEntry is not None and isinstance(focus_widget, CTkEntry)
                is_combobox = isinstance(focus_widget, ttk.Combobox)

                if is_entry or is_ctk_entry or is_combobox:
                    if key in ('<space>', '<r>', '<R>', '<s>', '<S>', '<p>', '<P>'):
                        return
            callback()
            return 'break'  # 阻止事件继续传播

        self.root.bind(key, handler)
        if key not in self._bound_keys:
            self._bound_keys.append(key)

    def unregister(self, key: str) -> None:
        """取消注册快捷键"""
        if key in self._callbacks:
            del self._callbacks[key]
            self.root.unbind(key)
            if key in self._bound_keys:
                self._bound_keys.remove(key)

    def get_shortcuts(self) -> dict[str, str]:
        """获取所有快捷键及其描述"""
        return {
            '<Return>': '开始仿真',
            '<space>': '暂停/继续',
            '<r>': '随机参数',
            '<R>': '随机参数',
            '<Left>': '上一帧',
            '<Right>': '下一帧',
            '<Home>': '第一帧',
            '<End>': '最后一帧',
            '<Escape>': '停止动画',
        }


def setup_animation_shortcuts(
    root: tk.Tk,
    on_start: Callable,
    on_pause: Callable,
    on_random: Callable,
    on_prev_frame: Callable,
    on_next_frame: Callable,
    on_first_frame: Callable,
    on_last_frame: Callable,
    on_stop: Callable,
) -> ShortcutManager:
    """设置动画控制快捷键

    Args:
        root: Tkinter 根窗口
        on_start: 开始仿真回调
        on_pause: 暂停/继续回调
        on_random: 随机参数回调
        on_prev_frame: 上一帧回调
        on_next_frame: 下一帧回调
        on_first_frame: 第一帧回调
        on_last_frame: 最后一帧回调
        on_stop: 停止动画回调

    Returns:
        ShortcutManager 实例
    """
    mgr = ShortcutManager(root)

    # 基本控制
    mgr.register('<Return>', on_start, '开始仿真')
    mgr.register('<space>', on_pause, '暂停/继续')
    mgr.register('<r>', on_random, '随机参数')
    mgr.register('<R>', on_random, '随机参数')

    # 帧控制
    mgr.register('<Left>', on_prev_frame, '上一帧')
    mgr.register('<Right>', on_next_frame, '下一帧')
    mgr.register('<Home>', on_first_frame, '第一帧')
    mgr.register('<End>', on_last_frame, '最后一帧')

    # 停止
    mgr.register('<Escape>', on_stop, '停止动画')

    return mgr
