import customtkinter as ctk
import tkinter as tk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ============================================================================
# 第一部分：全局配置与样式
# ============================================================================

# 初始化 CustomTkinter 的全局风格设置
ctk.set_appearance_mode("System")  # 跟随系统深浅色
ctk.set_default_color_theme("blue")  # 使用 Apple System Blue 作为主色调

UI_PADDING = 15
CORNER_RADIUS = 10

# 优化 Matplotlib 全局样式使其更现代 (极简无边框)
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'Segoe UI', 'sans-serif'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--'
})

# ============================================================================
# 第二部分：现代化侧边栏构建器
# ============================================================================

class ModernSidebar:
    def __init__(self, parent_frame):
        self.frame = parent_frame
        self.entries = {}
        self.switches = {}
        self.combos = {}

    def build(self, app_instance):
        # Logo
        title_lbl = ctk.CTkLabel(
            self.frame, text="CamForge", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=["#1d1d1f", "#f5f5f7"] # [浅色模式, 深色模式]
        )
        title_lbl.pack(fill="x", padx=UI_PADDING, pady=(20, 20), anchor="w")

        # --- 卡片 1：通用设置 ---
        group_general = self._create_card_group(self.frame, "General Settings")
        
        self.combos['theme'] = ctk.CTkOptionMenu(
            group_general, 
            values=['System', 'Light', 'Dark'], 
            command=self._on_theme_switch,
            corner_radius=CORNER_RADIUS,
            dynamic_resizing=False
        )
        self.combos['theme'].set("System")
        self.combos['theme'].pack(fill="x", padx=10, pady=(10, 10))

        # --- 卡片 2：运动参数 ---
        group_motion = self._create_card_group(self.frame, "Motion Parameters")
        self._add_entry(group_motion, 'delta_0', "Rise Angle (°)", "90")
        self._add_entry(group_motion, 'delta_ret', "Return Angle (°)", "120")
        self._add_entry(group_motion, 'h', "Stroke (mm)", "10")
        self._add_entry(group_motion, 'omega', "Angular Vel (rad/s)", "1")

        # --- 卡片 3：显示控制 (Apple风格开关) ---
        group_display = self._create_card_group(self.frame, "Display Options")
        self._add_switch(group_display, 'show_tangent', "Show Tangent")
        self._add_switch(group_display, 'show_arc', "Pressure Arc")
        self._add_switch(group_display, 'show_grid', "Grid Lines", command=app_instance._toggle_grid)

    def _create_card_group(self, parent, title):
        """创建 iOS 设置样式的圆角卡片"""
        lbl = ctk.CTkLabel(parent, text=title.upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        lbl.pack(fill="x", padx=UI_PADDING, pady=(10, 2), anchor="w")
        
        card = ctk.CTkFrame(parent, corner_radius=CORNER_RADIUS, fg_color=["#ffffff", "#2c2c2e"])
        card.pack(fill="x", padx=UI_PADDING, pady=(0, 10))
        return card

    def _add_entry(self, parent, name, label_text, default_val):
        """左右布局的输入行"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=6)
        
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=13))
        lbl.pack(side="left")
        
        entry = ctk.CTkEntry(row, width=70, height=28, justify="right", corner_radius=6)
        entry.insert(0, default_val)
        entry.pack(side="right")
        self.entries[name] = entry

    def _add_switch(self, parent, name, label_text, command=None):
        """Apple 风格拨动开关"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=8)
        
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=13))
        lbl.pack(side="left")
        
        var = tk.BooleanVar(value=True)
        switch = ctk.CTkSwitch(row, text="", variable=var, command=command, switch_width=36, switch_height=20)
        switch.pack(side="right")
        self.switches[name] = var

    def _on_theme_switch(self, choice):
        if choice == "System": ctk.set_appearance_mode("System")
        elif choice == "Light": ctk.set_appearance_mode("Light")
        else: ctk.set_appearance_mode("Dark")


# ============================================================================
# 第三部分：主程序与 Matplotlib 整合
# ============================================================================

class ModernCamSimulatorUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CamForge - Modern Apple Style")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # 整体布局：左侧控制栏(Sidebar)，右侧主内容区(Main)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- 1. 左侧侧边栏 ---
        self.sidebar_frame = ctk.CTkScrollableFrame(
            self, width=280, corner_radius=0, 
            fg_color=["#f2f2f7", "#1c1c1e"] # Apple iOS/macOS 典型的基础背景色
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar = ModernSidebar(self.sidebar_frame)
        self.sidebar.build(self)

        # --- 2. 右侧主区域 ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=["#ffffff", "#000000"])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_canvas()

    def _build_toolbar(self):
        """顶部工具栏，使用圆角按钮"""
        toolbar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))

        # 开始按钮 (绿色填充)
        self.btn_start = ctk.CTkButton(
            toolbar, text="Start Simulation", 
            fg_color="#34c759", hover_color="#32b353", # Apple System Green
            font=ctk.CTkFont(weight="bold"), corner_radius=CORNER_RADIUS, width=140
        )
        self.btn_start.pack(side="left", padx=(0, 10))

        # 随机按钮 (蓝色轮廓)
        self.btn_random = ctk.CTkButton(
            toolbar, text="Random Parameters", 
            fg_color="transparent", border_width=2, text_color=["#007aff", "#0a84ff"],
            hover_color=["#e5f1ff", "#1a2c42"],
            corner_radius=CORNER_RADIUS
        )
        self.btn_random.pack(side="left", padx=10)

        # 进度条模拟 (右侧)
        self.progress_slider = ctk.CTkSlider(toolbar, from_=0, to=360, number_of_steps=360, width=200)
        self.progress_slider.set(0)
        self.progress_slider.pack(side="right", padx=(10, 0))
        
        ctk.CTkLabel(toolbar, text="Timeline:").pack(side="right")

    def _build_canvas(self):
        """Matplotlib 图表区域"""
        # 图表背景色动态适配深色/浅色模式
        bg_color = '#ffffff' if ctk.get_appearance_mode() == 'Light' else '#000000'
        text_color = '#000000' if ctk.get_appearance_mode() == 'Light' else '#ffffff'
        
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor=bg_color)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(bg_color)
        self.ax.tick_params(colors=text_color)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('gray')
            spine.set_alpha(0.3)

        # 绘制一点模拟数据让图表不为空白
        x = np.linspace(0, 360, 360)
        y = np.sin(np.radians(x)) * 10
        self.ax.plot(x, y, color="#ff3b30", linewidth=2, label="Displacement") # Apple System Red
        self.ax.set_title("Cam Follower Motion Profile", color=text_color, pad=15)
        self.ax.legend(frameon=False, labelcolor=text_color)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.fig.tight_layout()

    def _toggle_grid(self):
        """由 Switch 触发的网格切换"""
        show = self.sidebar.switches['show_grid'].get()
        self.ax.grid(show)
        self.canvas.draw_idle()


if __name__ == "__main__":
    app = ModernCamSimulatorUI()
    app.mainloop()