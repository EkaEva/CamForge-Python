"""
CamForge - 尖顶凸轮仿真
使用 tkinter + matplotlib 实现凸轮机构运动学仿真
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import random as _random
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

from cam_mechanics import (
    compute_full_motion, compute_cam_profile, compute_pressure_angle,
    compute_rotated_cam, compute_anim_frame_data,
    compute_pressure_angle_arc, validate_params,
    DEG2RAD,
)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def generate_random_params():
    """生成随机凸轮参数（返回实际符号值 sn=±1, pz=±1）"""
    while True:
        af = _random.randint(1, 33) * 10
        bf = _random.randint(1, 34 - af // 10) * 10
        cf = _random.randint(1, 35 - af // 10 - bf // 10) * 10
        df = 360 - af - bf - cf
        if af >= 40 and bf >= 40 and cf >= 40 and df >= 40:
            break

    ff = _random.randint(10, 100)   # 基圆半径（最小10，避免极端值）
    gf = _random.randint(0, ff - 1)  # 偏距（允许0=对心）
    ef = _random.randint(1, ff)   # 推杆最大位移
    hf = _random.randint(1, 100)   # 角速度
    tc_law = _random.randint(1, 5)
    hc_law = _random.randint(1, 5)
    sn = 1 if _random.randint(1, 2) == 1 else -1
    pz = 1 if _random.randint(1, 2) == 1 else -1

    return {
        'delta_0': af, 'delta_01': bf,
        'delta_ret': cf, 'delta_02': df,
        'h': ef, 'r_0': ff, 'e': gf, 'omega': hf,
        'tc_law': tc_law, 'hc_law': hc_law,
        'sn': sn, 'pz': pz,
    }


class CamSimulator:
    """凸轮机构仿真主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CamForge - 凸轮仿真")
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.geometry("1400x800")

        # 动画控制
        self.animating = False
        self.paused = False
        self.anim_id = None
        self.current_frame = 0

        # 预计算缓存
        self.sim_data = None
        self._anim_artists = None

        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_gui()

        # 延迟刷新侧边栏，确保初始内容正确显示
        self.root.after(50, self._refresh_sidebar)

    # ===================================================================
    # GUI 构建
    # ===================================================================

    def _build_gui(self):
        # ---- 整体布局：左侧边栏（可滚动） + 右侧主区域 ----
        sidebar_outer = tk.Frame(self.root, width=280, bg='#f8fafc',
                                 highlightbackground='#e2e8f0', highlightthickness=1)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_outer.pack_propagate(False)

        # 可滚动侧边栏：Canvas + Scrollbar + 内部Frame
        self._sb_canvas = tk.Canvas(sidebar_outer, bg='#f8fafc', highlightthickness=0, width=260)
        sb_scrollbar = tk.Scrollbar(sidebar_outer, orient=tk.VERTICAL, command=self._sb_canvas.yview)
        sb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._sb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(self._sb_canvas, bg='#f8fafc')
        self._sb_win = self._sb_canvas.create_window(0, 0, window=sidebar, anchor='nw')

        sidebar.bind('<Configure>', self._on_sidebar_configure)
        self._sb_canvas.configure(yscrollcommand=sb_scrollbar.set)

        # 鼠标滚轮绑定（仅悬停时）
        self._sb_canvas.bind('<Enter>', lambda e: self._sb_canvas.bind_all('<MouseWheel>', self._on_mousewheel))
        self._sb_canvas.bind('<Leave>', lambda e: self._sb_canvas.unbind_all('<MouseWheel>'))

        main_area = tk.Frame(self.root)
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- 侧边栏 ----
        lbl_font = ('Microsoft YaHei', 10)
        ent_font = ('Microsoft YaHei', 10)
        lbl_kw = {'font': lbl_font, 'bg': '#f8fafc', 'anchor': 'w'}
        ent_kw = {'font': ent_font, 'width': 14}

        # Logo
        tk.Label(sidebar, text="CamForge", font=('Microsoft YaHei', 16, 'bold'),
                 fg='#2563eb', bg='#f8fafc', anchor='w').pack(fill=tk.X, padx=16, pady=(16, 20))

        # ---- 运动参数组 ----
        self._sidebar_group(sidebar, "运动参数")

        self._sidebar_item(sidebar, "推程运动角 (°)", lbl_kw)
        self.entry_delta_0 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_0.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "远休止角 (°)", lbl_kw)
        self.entry_delta_01 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_01.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "回程运动角 (°)", lbl_kw)
        self.entry_delta_ret = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_ret.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "近休止角 (°)", lbl_kw)
        self.entry_delta_02 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_02.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "推杆最大位移 (mm)", lbl_kw)
        self.entry_h = tk.Entry(sidebar, **ent_kw)
        self.entry_h.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "凸轮角速度 (rad/s)", lbl_kw)
        self.entry_omega = tk.Entry(sidebar, **ent_kw)
        self.entry_omega.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 几何参数组 ----
        self._sidebar_group(sidebar, "几何参数")

        self._sidebar_item(sidebar, "基圆半径 (mm)", lbl_kw)
        self.entry_r0 = tk.Entry(sidebar, **ent_kw)
        self.entry_r0.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "偏距 (mm)", lbl_kw)
        self.entry_e = tk.Entry(sidebar, **ent_kw)
        self.entry_e.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 运动规律组 ----
        self._sidebar_group(sidebar, "运动规律")

        motion_laws = ['等速运动', '等加速等减速', '简谐运动规律',
                       '摆线运动规律', '五次多项式运动规律']
        combo_kw = {'state': 'readonly', 'width': 14}

        self._sidebar_item(sidebar, "推程规律", lbl_kw)
        self.popup_tc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_tc.current(0)
        self.popup_tc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "回程规律", lbl_kw)
        self.popup_hc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_hc.current(0)
        self.popup_hc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "旋向", lbl_kw)
        self.popup_sn = ttk.Combobox(sidebar, values=['顺时针', '逆时针'], **combo_kw)
        self.popup_sn.current(0)
        self.popup_sn.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, "偏距方向", lbl_kw)
        self.popup_pz = ttk.Combobox(sidebar, values=['正偏距', '负偏距'], **combo_kw)
        self.popup_pz.current(0)
        self.popup_pz.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 动态显示组 ----
        self._sidebar_group(sidebar, "动态显示")

        cb_kw = {'font': ('Microsoft YaHei', 10), 'anchor': 'w', 'bg': '#f8fafc'}

        self.show_tangent = tk.BooleanVar(value=False)
        tk.Checkbutton(sidebar, text="切线", variable=self.show_tangent,
                       **cb_kw).pack(fill=tk.X, padx=16, pady=1)

        self.show_normal = tk.BooleanVar(value=False)
        tk.Checkbutton(sidebar, text="法线", variable=self.show_normal,
                       **cb_kw).pack(fill=tk.X, padx=16, pady=1)

        self.show_arc = tk.BooleanVar(value=False)
        tk.Checkbutton(sidebar, text="压力角弧线", variable=self.show_arc,
                       command=self._on_arc_toggle, **cb_kw).pack(fill=tk.X, padx=16, pady=1)

        self.show_boundaries = tk.BooleanVar(value=False)
        tk.Checkbutton(sidebar, text="角度分界线", variable=self.show_boundaries,
                       **cb_kw).pack(fill=tk.X, padx=16, pady=1)

        self.show_grid = tk.BooleanVar(value=False)
        tk.Checkbutton(sidebar, text="网格线", variable=self.show_grid,
                       command=self._on_grid_toggle, **cb_kw).pack(fill=tk.X, padx=16, pady=1)

        # ---- 右侧主区域：按钮 + 图表 ----
        # 按钮栏
        toolbar = tk.Frame(main_area, bg='#ffffff', pady=6)
        toolbar.pack(fill=tk.X, padx=12, pady=(8, 0))

        btn_kw = {'font': ('Microsoft YaHei', 10), 'width': 10, 'height': 1,
                  'relief': tk.FLAT, 'cursor': 'hand2', 'bd': 0}

        self.btn_start = tk.Button(toolbar, text="开始仿真", command=self._on_start,
                                   bg='#10b981', fg='white', activebackground='#059669',
                                   **btn_kw)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_pause = tk.Button(toolbar, text="暂停", command=self._on_pause,
                                   bg='#f59e0b', fg='white', activebackground='#d97706',
                                   **btn_kw)
        self.btn_pause.pack(side=tk.LEFT, padx=6)

        self.btn_clear_params = tk.Button(toolbar, text="清除参数",
                                          command=self._on_clear_params,
                                          bg='#ffffff', fg='#475569',
                                          activebackground='#f1f5f9',
                                          relief=tk.FLAT, bd=1,
                                          font=('Microsoft YaHei', 10), width=10, height=1)
        self.btn_clear_params.pack(side=tk.LEFT, padx=6)

        self.btn_clear_plots = tk.Button(toolbar, text="清除图像",
                                         command=self._on_clear_plots,
                                         bg='#ffffff', fg='#475569',
                                         activebackground='#f1f5f9',
                                         relief=tk.FLAT, bd=1,
                                         font=('Microsoft YaHei', 10), width=10, height=1)
        self.btn_clear_plots.pack(side=tk.LEFT, padx=6)

        self.btn_random = tk.Button(toolbar, text="随机凸轮",
                                    command=self._on_random,
                                    bg='#ffffff', fg='#475569',
                                    activebackground='#f1f5f9',
                                    relief=tk.FLAT, bd=1,
                                    font=('Microsoft YaHei', 10), width=10, height=1)
        self.btn_random.pack(side=tk.LEFT, padx=6)

        self.btn_download = tk.Button(toolbar, text="下载图片",
                                      command=self._on_download,
                                      bg='#2563eb', fg='white',
                                      activebackground='#1d4ed8',
                                      relief=tk.FLAT, bd=0,
                                      font=('Microsoft YaHei', 10), width=10, height=1,
                                      cursor='hand2')
        self.btn_download.pack(side=tk.LEFT, padx=6)

        # 下载勾选项
        dl_cb_kw = {'font': ('Microsoft YaHei', 9), 'bg': '#ffffff', 'anchor': 'w'}
        self.dl_s = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="位移", variable=self.dl_s, **dl_cb_kw).pack(side=tk.LEFT, padx=2)
        self.dl_v = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="速度", variable=self.dl_v, **dl_cb_kw).pack(side=tk.LEFT, padx=2)
        self.dl_a = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="加速度", variable=self.dl_a, **dl_cb_kw).pack(side=tk.LEFT, padx=2)
        self.dl_profile = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="廓形", variable=self.dl_profile, **dl_cb_kw).pack(side=tk.LEFT, padx=2)
        self.dl_anim = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="动态图", variable=self.dl_anim, **dl_cb_kw).pack(side=tk.LEFT, padx=2)

        # 速度滑块（靠右，标签在左滑块在右）
        speed_frame = tk.Frame(toolbar, bg='#ffffff')
        speed_frame.pack(side=tk.RIGHT, padx=(0, 8))
        tk.Label(speed_frame, text="仿真速度:", font=('Microsoft YaHei', 10),
                 bg='#ffffff').pack(side=tk.LEFT, padx=(0, 4))
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                    variable=self.speed_var, length=120,
                                    font=('Microsoft YaHei', 9), bg='#ffffff',
                                    highlightthickness=0)
        self.speed_scale.pack(side=tk.LEFT)

        # 状态/警告行
        status_bar = tk.Frame(main_area, bg='#ffffff')
        status_bar.pack(fill=tk.X, padx=12, pady=(2, 0))

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(status_bar, textvariable=self.status_var, fg='#ef4444',
                                     font=('Microsoft YaHei', 10), anchor='w', bg='#ffffff')
        self.status_label.pack(side=tk.LEFT)

        self.alpha_var = tk.StringVar()
        self.alpha_label = tk.Label(status_bar, textvariable=self.alpha_var,
                                    font=('Microsoft YaHei', 11, 'bold'), anchor='w', bg='#ffffff')
        self.alpha_label.pack(side=tk.LEFT, padx=16)

        # ---- 图表区 ----
        self.fig = Figure(figsize=(14, 7), dpi=100)

        gs = GridSpec(2, 3, figure=self.fig,
                      left=0.05, right=0.82, top=0.95, bottom=0.08,
                      wspace=0.30, hspace=0.35,
                      width_ratios=[1, 1, 1.6])

        self.ax_s = self.fig.add_subplot(gs[0, 0])
        self.ax_v = self.fig.add_subplot(gs[0, 1])
        self.ax_a = self.fig.add_subplot(gs[1, 0])
        self.ax_profile = self.fig.add_subplot(gs[1, 1])
        self.ax_anim = self.fig.add_subplot(gs[:, 2])

        # 信息面板：紧贴动态图右侧，上下对齐
        self.ax_info = self.fig.add_axes([0.83, 0.08, 0.14, 0.87])
        self.ax_info.set_xticks([])
        self.ax_info.set_yticks([])
        self.ax_info.set_frame_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def _on_sidebar_configure(self, event):
        """侧边栏内容变化时更新滚动区域"""
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _on_mousewheel(self, event):
        """鼠标滚轮滚动侧边栏"""
        self._sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _refresh_sidebar(self):
        """强制刷新侧边栏显示"""
        self._sb_canvas.update_idletasks()
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _sidebar_group(self, parent, title):
        """侧边栏分组标题"""
        frame = tk.Frame(parent, bg='#f8fafc')
        frame.pack(fill=tk.X, padx=16, pady=(12, 4))
        tk.Label(frame, text=title, font=('Microsoft YaHei', 9),
                 fg='#64748b', bg='#f8fafc', anchor='w').pack(fill=tk.X)
        tk.Frame(frame, height=1, bg='#e2e8f0').pack(fill=tk.X, pady=(2, 0))

    def _sidebar_item(self, parent, text, lbl_kw):
        """侧边栏参数标签"""
        tk.Label(parent, text=text, **lbl_kw).pack(fill=tk.X, padx=16, pady=(4, 0))

    # ===================================================================
    # 参数读取与校验
    # ===================================================================

    def _read_params(self):
        """读取并校验参数，返回 dict 或 None"""
        try:
            vals = {
                'delta_0': float(self.entry_delta_0.get()),
                'delta_01': float(self.entry_delta_01.get()),
                'delta_ret': float(self.entry_delta_ret.get()),
                'delta_02': float(self.entry_delta_02.get()),
                'h': float(self.entry_h.get()),
                'r_0': float(self.entry_r0.get()),
                'e': float(self.entry_e.get()),
                'omega': float(self.entry_omega.get()),
            }
        except ValueError:
            self.status_var.set("请输入完整的参数数据")
            return None

        ok, err = validate_params(
            vals['delta_0'], vals['delta_01'], vals['delta_ret'], vals['delta_02'],
            vals['h'], vals['r_0'], vals['e'], vals['omega']
        )
        if not ok:
            self.status_var.set(err)
            return None

        # 读取下拉菜单
        vals['tc_law'] = self.popup_tc.current() + 1
        vals['hc_law'] = self.popup_hc.current() + 1
        vals['sn'] = 1 if self.popup_sn.current() == 0 else -1
        vals['pz'] = 1 if self.popup_pz.current() == 0 else -1
        vals['e'] = abs(vals['e'])  # 偏距取正值，方向由 pz 控制

        self.status_var.set("")
        self.alpha_var.set("")
        return vals

    # ===================================================================
    # 计算与启动
    # ===================================================================

    def _on_start(self):
        """开始仿真"""
        self._stop_animation()

        params = self._read_params()
        if params is None:
            return

        # 计算运动
        delta_deg, s, v, a, ds_ddelta, phase_bounds = compute_full_motion(
            params['delta_0'], params['delta_01'],
            params['delta_ret'], params['delta_02'],
            params['h'], params['r_0'], params['e'],
            params['omega'], params['tc_law'], params['hc_law']
        )

        # 计算凸轮廓形
        x, y, s_0 = compute_cam_profile(
            s, params['r_0'], params['e'], params['sn'], params['pz']
        )

        # 预计算基圆/偏距圆坐标
        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = params['r_0'] * np.cos(delta_full)
        y_base = params['r_0'] * np.sin(delta_full)
        x_offset = x_base / params['r_0'] * params['e']
        y_offset = y_base / params['r_0'] * params['e']

        # 预计算 Rmax
        R = np.hypot(x, y)
        Rmax = np.max(R)

        # 解析压力角
        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, params['e'], params['pz'])
        max_alpha = np.max(np.abs(alpha_all))

        # 压力角超限警告
        if max_alpha > 30:
            self.status_var.set(f"警告：最大压力角 {max_alpha:.1f}° 超过推荐值 30°")

        # 行程过大警告（h > r_0 时凸轮形状可能不合理）
        if params['h'] > params['r_0']:
            self.status_var.set(
                f"警告：推杆行程({params['h']:.1f})大于基圆半径({params['r_0']:.1f})，凸轮形状可能不合理")

        # 保存计算结果
        self.sim_data = {
            'delta_deg': delta_deg, 's': s, 'v': v, 'a': a,
            'ds_ddelta': ds_ddelta, 'phase_bounds': phase_bounds,
            'x': x, 'y': y, 's_0': s_0,
            'r_0': params['r_0'], 'e': params['e'], 'h': params['h'],
            'omega': params['omega'], 'sn': params['sn'], 'pz': params['pz'],
            'x_base': x_base, 'y_base': y_base,
            'x_offset': x_offset, 'y_offset': y_offset,
            'Rmax': Rmax, 'max_alpha': max_alpha,
            'alpha_all': alpha_all,
        }

        # 绘制静态图
        self._plot_static()

        # 开始动画
        self._start_animation()

    # ===================================================================
    # 静态图表
    # ===================================================================

    def _plot_static(self):
        """绘制静态图表"""
        data = self.sim_data
        delta_deg = data['delta_deg']
        s, v, a = data['s'], data['v'], data['a']
        pb = data['phase_bounds']
        x, y = data['x'], data['y']
        r_0, e, s_0, h = data['r_0'], data['e'], data['s_0'], data['h']
        Rmax = data['Rmax']

        for ax in [self.ax_s, self.ax_v, self.ax_a, self.ax_profile]:
            ax.clear()

        # ---- 位移图 ----
        self.ax_s.plot(delta_deg, s, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_s.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_s.set_title(r'推杆位移 $s$', fontsize=11)
        self.ax_s.set_xlabel(r'$\theta$ (°)')
        self.ax_s.set_ylabel(r'$s$ (mm)')
        self.ax_s.set_xlim(0, 360)
        self.ax_s.set_ylim(0, h * 1.15)
        self.ax_s.set_xticks(range(0, 361, 60))
        self.ax_s.grid(True)

        # ---- 速度图 ----
        self.ax_v.plot(delta_deg, v, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_v.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_v.set_title(r'推杆速度 $v$', fontsize=11)
        self.ax_v.set_xlabel(r'$\theta$ (°)')
        self.ax_v.set_ylabel(r'$v$ (mm/s)')
        self.ax_v.set_xlim(0, 360)
        v_max = np.max(np.abs(v)) * 1.15
        if v_max > 0:
            self.ax_v.set_ylim(-v_max, v_max)
        self.ax_v.set_xticks(range(0, 361, 60))
        self.ax_v.grid(True)

        # ---- 加速度图 ----
        self.ax_a.plot(delta_deg, a, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_a.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_a.set_title(r'推杆加速度 $a$', fontsize=11)
        self.ax_a.set_xlabel(r'$\theta$ (°)')
        self.ax_a.set_ylabel(r'$a$ (mm/s$^2$)')
        self.ax_a.set_xlim(0, 360)
        a_max = np.max(np.abs(a)) * 1.15
        if a_max > 0:
            self.ax_a.set_ylim(-a_max, a_max)
        self.ax_a.set_xticks(range(0, 361, 60))
        self.ax_a.grid(True)

        # ---- 凸轮廓形图 ----
        self.ax_profile.plot(x, y, 'r-', linewidth=2, label='廓形')
        self.ax_profile.plot(data['x_base'], data['y_base'],
                             'm-', linewidth=1, label='基圆')
        self.ax_profile.plot(data['x_offset'], data['y_offset'],
                             'c-', linewidth=1, label='偏距圆')

        n = len(x)
        for b_deg in pb[1:-1]:
            idx = int(b_deg)
            if idx < n:
                self.ax_profile.plot([0, x[idx]], [0, y[idx]],
                                     'k-', linewidth=0.8)

        self.ax_profile.set_title(r'凸轮廓形', fontsize=11)
        self.ax_profile.set_xlabel(r'$x$ (mm)')
        self.ax_profile.set_ylabel(r'$y$ (mm)')
        self.ax_profile.grid(True)
        margin = r_0 / 2
        self.ax_profile.set_xlim(-Rmax - margin, Rmax + margin)
        self.ax_profile.set_ylim(-Rmax - r_0, Rmax + r_0)
        self.ax_profile.set_aspect('equal')
        self.ax_profile.legend(fontsize=8, loc='upper right')

        self.canvas.draw()

    # ===================================================================
    # 动画
    # ===================================================================

    def _init_anim_artists(self):
        """初始化动画图形对象（只创建一次，后续用 set_data 更新）"""
        ax = self.ax_anim
        ax.clear()

        data = self.sim_data
        r_0 = data['r_0']
        h = data['h']
        Rmax = data['Rmax']

        # 凸轮廓形
        line_cam, = ax.plot([], [], 'r-', linewidth=2)
        # 基圆
        line_base, = ax.plot(data['x_base'], data['y_base'], 'm-', linewidth=1)
        # 偏距圆
        line_offset, = ax.plot(data['x_offset'], data['y_offset'], 'c-', linewidth=1)
        # 切线
        line_tangent, = ax.plot([], [], 'm-', linewidth=1)
        # 法线
        line_normal, = ax.plot([], [], 'm-', linewidth=1)
        # 推杆杆身
        line_rod, = ax.plot([], [], 'k-', linewidth=3, solid_capstyle='butt')
        # 推杆尖顶（小三角）
        line_tip, = ax.plot([], [], 'k-', linewidth=2)
        # 推杆中心虚线（压力角弧线参考线）
        line_center, = ax.plot([], [], 'k--', linewidth=0.8)
        # 推杆下限
        line_lower, = ax.plot([], [], 'c-.', linewidth=1)
        # 推杆上限
        line_upper, = ax.plot([], [], 'm--', linewidth=1)
        # 角度分界线（最多4条）
        lines_boundary = []
        for _ in range(4):
            lb, = ax.plot([], [], 'k-', linewidth=0.8)
            lines_boundary.append(lb)
        # 压力角弧线
        line_arc, = ax.plot([], [], 'k-', linewidth=1)

        ax.set_xlim(-Rmax - h, Rmax + h)
        ax.set_ylim(-Rmax - r_0, Rmax + r_0)
        ax.set_aspect('equal')
        ax.grid(self.show_grid.get())
        ax.set_title('凸轮动态仿真', fontsize=12)
        ax.set_xlabel(r'$x$ (mm)')
        ax.set_ylabel(r'$y$ (mm)')

        # 信息面板：紧贴动态图右侧，上下对齐
        anim_pos = ax.get_position()
        info_x0 = anim_pos.x1 + 0.01
        info_w = 0.14
        self.ax_info.set_position([info_x0, anim_pos.y0, info_w, anim_pos.y1 - anim_pos.y0])
        self._init_info_panel()

        self._anim_artists = {
            'cam': line_cam,
            'tangent': line_tangent,
            'normal': line_normal,
            'rod': line_rod,
            'tip': line_tip,
            'center': line_center,
            'lower': line_lower,
            'upper': line_upper,
            'boundaries': lines_boundary,
            'arc': line_arc,
        }

    def _init_info_panel(self):
        """初始化信息面板（独立的 ax_info，与动态图完全不重叠）"""
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

        info_items = [
            ('delta', r'转角 $\theta$'),
            ('alpha', r'压力角 $\alpha$'),
            ('s', r'位移 $s$'),
            ('h', r'行程 $h$'),
            ('s0', r'初始位移 $s_{0}$'),
        ]
        self._info_labels = {}
        for idx, (key, name) in enumerate(info_items):
            y_pos = 0.95 - idx * 0.10
            lbl = ax.text(0.05, y_pos, f'{name}: --', transform=ax.transAxes,
                          fontsize=10, ha='left', va='top', color='#222')
            self._info_labels[key] = lbl

    def _start_animation(self):
        """开始凸轮旋转动画"""
        self.animating = True
        self.paused = False
        self.current_frame = 0
        self.btn_pause.config(text="暂停")
        self._init_anim_artists()
        self._animate_frame()

    def _stop_animation(self):
        """停止动画"""
        self.animating = False
        self.paused = False
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self._anim_artists = None

    def _on_pause(self):
        """暂停/继续"""
        if not self.animating:
            return
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="继续")
        else:
            self.btn_pause.config(text="暂停")
            self._animate_frame()

    def _animate_frame(self):
        """绘制一帧动画（解析计算推杆位置，set_data 更新）"""
        if not self.animating or self.paused:
            return

        data = self.sim_data
        artists = self._anim_artists
        if artists is None:
            return

        r_0 = data['r_0']
        h = data['h']
        sn = data['sn']
        pb = data['phase_bounds']
        s = data['s']
        s_0 = data['s_0']
        e = data['e']
        pz = data['pz']
        alpha_all = data['alpha_all']

        N = len(s)
        i = self.current_frame

        if i >= N:
            self.animating = False
            self.alpha_var.set(f"最大压力角={data['max_alpha']:.2f}°")
            self._info_labels['delta'].set_text(r'转角 $\theta$: 360°/360°')
            self._info_labels['alpha'].set_text(rf'压力角 $\alpha$: {data["max_alpha"]:.2f}°')
            self._info_labels['s'].set_text(rf'位移 $s$: 0.00 mm')
            self._info_labels['h'].set_text(rf'行程 $h$: {h:.1f} mm')
            self._info_labels['s0'].set_text(rf'初始位移 $s_{{0}}$: {s_0:.2f} mm')
            self.canvas.draw_idle()
            return

        # ---- 凸轮旋转 ----
        angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
        x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)
        artists['cam'].set_data(x_rot, y_rot)

        # ---- 解析计算帧数据 ----
        frame = compute_anim_frame_data(
            s, data['ds_ddelta'], s_0, e, r_0, sn, pz, i, alpha_all)
        follower_x = frame['follower_x']
        cy = frame['contact_y']
        cx = follower_x
        nx, ny = frame['nx'], frame['ny']
        tx, ty = frame['tx'], frame['ty']
        alpha_i = frame['alpha_i']

        # ---- 切线 ----
        if self.show_tangent.get():
            artists['tangent'].set_data(
                [cx - r_0 * tx, cx + r_0 * tx],
                [cy - r_0 * ty, cy + r_0 * ty]
            )
        else:
            artists['tangent'].set_data([], [])

        # ---- 法线 ----
        if self.show_normal.get():
            artists['normal'].set_data(
                [cx + r_0 * nx, cx - r_0 * nx],
                [cy + r_0 * ny, cy - r_0 * ny]
            )
        else:
            artists['normal'].set_data([], [])

        # ---- 推杆（杆身 + 尖顶） ----
        tip_w = r_0 * 0.04   # 尖顶半宽
        tip_h = r_0 * 0.08   # 尖顶高度
        rod_top = cy + r_0 * 4
        # 杆身（尖顶上方到顶部）
        artists['rod'].set_data(
            [follower_x, follower_x], [cy + tip_h, rod_top])
        # 尖顶（小三角）
        artists['tip'].set_data(
            [follower_x - tip_w, follower_x, follower_x + tip_w, follower_x - tip_w],
            [cy + tip_h, cy, cy + tip_h, cy + tip_h])

        # ---- 推杆上下限水平线 ----
        artists['lower'].set_data([-r_0 * 3, r_0 * 3], [s_0, s_0])
        artists['upper'].set_data([-r_0 * 3, r_0 * 3], [s_0 + h, s_0 + h])

        # ---- 角度分界线 ----
        if self.show_boundaries.get():
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

        # ---- 压力角弧线 + 中心虚线 ----
        if self.show_arc.get():
            arc_r = r_0 * 0.3
            x_arc, y_arc = compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r)
            artists['arc'].set_data(x_arc, y_arc)
            # 中心虚线（推杆中心延伸线，作为压力角参考）
            artists['center'].set_data(
                [follower_x, follower_x], [cy - r_0 * 2, cy + r_0 * 5])
        else:
            artists['arc'].set_data([], [])
            artists['center'].set_data([], [])

        # ---- 信息面板（图框外 tkinter 标签）----
        self._info_labels['delta'].set_text(rf'转角 $\theta$: {i:3d}°/360°')
        self._info_labels['alpha'].set_text(rf'压力角 $\alpha$: {alpha_i:.1f}°')
        self._info_labels['s'].set_text(rf'位移 $s$: {frame["s_i"]:.2f} mm')
        self._info_labels['h'].set_text(rf'行程 $h$: {h:.1f} mm')
        self._info_labels['s0'].set_text(rf'初始位移 $s_{{0}}$: {s_0:.2f} mm')

        # 仅每2帧刷新一次画布，减少卡顿
        if i % 2 == 0:
            self.canvas.draw_idle()

        self.current_frame += 1
        # 帧间隔：速度1=200ms, 5=40ms, 10=5ms（指数映射），最小20ms防止卡顿
        delay = max(20, int(200 / (self.speed_var.get() ** 1.5)))
        self.anim_id = self.root.after(delay, self._animate_frame)

    # ===================================================================
    # 按钮回调
    # ===================================================================

    def _on_arc_toggle(self):
        """勾选压力角弧线时自动开启法线，关闭时同时关闭法线并清除残留"""
        if self.show_arc.get():
            self.show_normal.set(True)
        else:
            self.show_normal.set(False)
            # 立即清除弧线、法线和中心虚线，避免残留
            if self._anim_artists:
                self._anim_artists['arc'].set_data([], [])
                self._anim_artists['normal'].set_data([], [])
                self._anim_artists['center'].set_data([], [])
                self.canvas.draw_idle()

    def _on_grid_toggle(self):
        """切换动态图网格线"""
        self.ax_anim.grid(self.show_grid.get())
        self.canvas.draw_idle()

    def _on_download(self):
        """下载勾选的图片（静态图为PNG，动态图为GIF）"""
        from tkinter import filedialog
        import os
        from io import BytesIO

        # 检查是否有勾选
        if not any([self.dl_s.get(), self.dl_v.get(), self.dl_a.get(),
                     self.dl_profile.get(), self.dl_anim.get()]):
            self.status_var.set("请至少勾选一项要下载的图片")
            return

        if self.sim_data is None:
            self.status_var.set("请先运行仿真再下载")
            return

        folder = filedialog.askdirectory(title="选择保存文件夹")
        if not folder:
            return

        dpi = 150
        saved = []

        # 保存单张静态图的辅助函数
        def save_static(ax, name, square=False):
            import matplotlib.transforms as mtransforms
            size = (6, 6) if square else (6, 4)
            fig_single = Figure(figsize=size, dpi=dpi)
            ax_new = fig_single.add_subplot(111)
            # 复制所有 Line2D（包括 plot 和 axvline）
            for line in ax.get_lines():
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                # axvline 使用 BlendedGenericTransform（x数据坐标，y轴坐标0-1）
                # 需要将 y 从轴坐标转换为数据坐标
                if isinstance(line.get_transform(), mtransforms.BlendedGenericTransform):
                    ylim = ax.get_ylim()
                    ydata = [ylim[0] + y * (ylim[1] - ylim[0]) for y in ydata]
                ax_new.plot(xdata, ydata,
                            color=line.get_color(), linewidth=line.get_linewidth(),
                            linestyle=line.get_linestyle(), label=line.get_label())
            ax_new.set_title(ax.get_title(), fontsize=11)
            ax_new.set_xlabel(ax.get_xlabel())
            ax_new.set_ylabel(ax.get_ylabel())
            ax_new.set_xlim(ax.get_xlim())
            ax_new.set_ylim(ax.get_ylim())
            ax_new.grid(True)
            if square:
                ax_new.set_aspect('equal')
            if ax.get_legend():
                ax_new.legend(fontsize=8)
            filepath = os.path.join(folder, f'{name}.png')
            fig_single.savefig(filepath, dpi=dpi, bbox_inches='tight')
            plt.close(fig_single)
            saved.append(name)

        # 四张静态图
        if self.dl_s.get():
            save_static(self.ax_s, '位移曲线')
        if self.dl_v.get():
            save_static(self.ax_v, '速度曲线')
        if self.dl_a.get():
            save_static(self.ax_a, '加速度曲线')
        if self.dl_profile.get():
            save_static(self.ax_profile, '凸轮廓形', square=True)

        # 动态图：保存完整360帧为GIF（逐帧写入，避免内存爆炸）
        if self.dl_anim.get():
            from PIL import Image as PILImage

            data = self.sim_data
            s = data['s']
            ds_ddelta = data['ds_ddelta']
            s_0 = data['s_0']
            e = data['e']
            r_0 = data['r_0']
            h = data['h']
            sn = data['sn']
            pz = data['pz']
            alpha_all = data['alpha_all']
            N = len(s)

            self.status_var.set("正在生成动态图GIF，请稍候...")
            self.root.update_idletasks()

            xlim = self.ax_anim.get_xlim()
            ylim = self.ax_anim.get_ylim()

            fig_gif = Figure(figsize=(8, 6), dpi=80)
            ax_gif = fig_gif.add_axes([0.05, 0.08, 0.65, 0.87])
            ax_info_gif = fig_gif.add_axes([0.73, 0.08, 0.25, 0.87])
            ax_info_gif.set_xticks([])
            ax_info_gif.set_yticks([])
            ax_info_gif.set_frame_on(False)

            filepath = os.path.join(folder, '凸轮动态仿真.gif')
            first_frame = None
            append_frames = []

            for i in range(N):
                angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
                x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)

                ax_gif.clear()
                ax_gif.plot(x_rot, y_rot, 'r-', linewidth=2)
                ax_gif.plot(data['x_base'], data['y_base'], 'm-', linewidth=1)
                ax_gif.plot(data['x_offset'], data['y_offset'], 'c-', linewidth=1)

                frame_data = compute_anim_frame_data(
                    s, ds_ddelta, s_0, e, r_0, sn, pz, i, alpha_all)
                fx = frame_data['follower_x']
                cy = frame_data['contact_y']
                alpha_i = frame_data['alpha_i']
                # 推杆杆身 + 尖顶（与动画一致）
                tip_w = r_0 * 0.04
                tip_h = r_0 * 0.08
                ax_gif.plot([fx, fx], [cy + tip_h, cy + r_0 * 4], 'k-', linewidth=3)
                ax_gif.plot([fx - tip_w, fx, fx + tip_w, fx - tip_w],
                            [cy + tip_h, cy, cy + tip_h, cy + tip_h], 'k-', linewidth=2)
                # 推杆上下限
                ax_gif.plot([-r_0 * 3, r_0 * 3], [s_0, s_0], 'c-.', linewidth=1)
                ax_gif.plot([-r_0 * 3, r_0 * 3], [s_0 + h, s_0 + h], 'm--', linewidth=1)
                ax_gif.set_xlim(xlim)
                ax_gif.set_ylim(ylim)
                ax_gif.set_aspect('equal')
                ax_gif.set_title(f'凸轮动态仿真  {i:3d}°/360°', fontsize=11)

                # 信息面板
                ax_info_gif.clear()
                ax_info_gif.set_xticks([])
                ax_info_gif.set_yticks([])
                ax_info_gif.set_frame_on(False)
                info_items = [
                    (0.95, r'转角 $\theta$: ' + f'{i:3d}' + r'°/360°'),
                    (0.85, r'压力角 $\alpha$: ' + f'{alpha_i:.1f}°'),
                    (0.75, r'位移 $s$: ' + f'{frame_data["s_i"]:.2f} mm'),
                    (0.65, r'行程 $h$: ' + f'{h:.1f} mm'),
                    (0.55, rf'初始位移 $s_{{0}}$: {s_0:.2f} mm'),
                ]
                for y_pos, text in info_items:
                    ax_info_gif.text(0.05, y_pos, text, transform=ax_info_gif.transAxes,
                                     fontsize=10, ha='left', va='top', color='#222')

                buf = BytesIO()
                fig_gif.savefig(buf, format='png', dpi=80)
                buf.seek(0)
                img = PILImage.open(buf).copy()
                buf.close()

                if first_frame is None:
                    first_frame = img
                else:
                    append_frames.append(img)

            plt.close(fig_gif)
            if first_frame is not None:
                first_frame.save(filepath, save_all=True, append_images=append_frames,
                                 duration=30, loop=0)
            saved.append('动态图(GIF)')

        self.status_var.set(f"已保存: {', '.join(saved)} → {folder}")

    def _on_clear_params(self):
        """清除参数"""
        for entry in [self.entry_delta_0, self.entry_delta_01,
                      self.entry_delta_ret, self.entry_delta_02,
                      self.entry_h, self.entry_r0, self.entry_e,
                      self.entry_omega]:
            entry.delete(0, tk.END)
        self.status_var.set("")
        self.alpha_var.set("")

    def _on_clear_plots(self):
        """清除图像"""
        self._stop_animation()
        for ax in [self.ax_s, self.ax_v, self.ax_a,
                   self.ax_profile, self.ax_anim, self.ax_info]:
            ax.clear()
        self.canvas.draw()

    def _on_random(self):
        """随机凸轮参数"""
        params = generate_random_params()
        self._on_clear_params()

        self.entry_delta_0.insert(0, str(params['delta_0']))
        self.entry_delta_01.insert(0, str(params['delta_01']))
        self.entry_delta_ret.insert(0, str(params['delta_ret']))
        self.entry_delta_02.insert(0, str(params['delta_02']))
        self.entry_h.insert(0, str(params['h']))
        self.entry_r0.insert(0, str(params['r_0']))
        self.entry_e.insert(0, str(params['e']))
        self.entry_omega.insert(0, str(params['omega']))

        self.popup_tc.current(params['tc_law'] - 1)
        self.popup_hc.current(params['hc_law'] - 1)
        self.popup_sn.current(0 if params['sn'] == 1 else 1)
        self.popup_pz.current(0 if params['pz'] == 1 else 1)

    def _on_close(self):
        """窗口关闭处理"""
        self._stop_animation()
        self.root.destroy()

    def run(self):
        """运行主窗口"""
        self.root.mainloop()


if __name__ == '__main__':
    app = CamSimulator()
    app.run()
