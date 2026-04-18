"""CamForge 导出管理器

处理 TIFF、SVG、CSV、Excel、GIF 等格式的导出逻辑。
"""

import os
import csv as csv_mod
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

try:
    import openpyxl
except ImportError:
    openpyxl = None

from i18n import t
from ui.constants import STATIC_DPI, MAX_PRESSURE_ANGLE
from ui.animation import generate_gif_frames


class ExportManager:
    """处理图像/数据导出（TIFF, SVG, CSV, Excel, GIF）。"""

    def __init__(self, root, sim_data_lock):
        self.root = root
        self._sim_data_lock = sim_data_lock

    def download(self, sim_data, toggles, draw_funcs, lang, tk_font_family,
                 axes_ref, status_var, folder):
        """下载勾选的图片。

        Parameters
        ----------
        sim_data : dict
            仿真数据。
        toggles : dict
            导出勾选项 BooleanVar 字典，键: motion, geom, profile, svg, csv。
        draw_funcs : dict
            绘图函数字典，键: motion_curves, geometry_constraints, profile。
        lang : str
            当前语言代码。
        tk_font_family : str
            tkinter 字体族名。
        axes_ref : dict
            动画坐标轴引用，键: ax_anim。
        status_var : tk.StringVar
            状态栏变量。
        folder : str
            导出目标文件夹路径。
        """
        if not any(toggles.values()):
            status_var.set(t("status.no_download_selection", lang))
            return

        if sim_data is None:
            status_var.set(t("status.run_first", lang))
            return

        dpi = STATIC_DPI
        saved = []
        data = sim_data
        errors = []

        # 运动线图导出
        if toggles.get('motion'):
            try:
                fig_motion = Figure(figsize=(8, 5), dpi=dpi)
                ax_motion = fig_motion.add_subplot(111)
                draw_funcs['motion_curves'](ax_motion, data, show_law_names=True)
                filename_motion = t("export.filename.motion", lang) + ".tiff"
                fig_motion.savefig(os.path.join(folder, filename_motion), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_motion)
                saved.append(filename_motion)
            except Exception as exc:
                errors.append(f"motion: {exc}")

        # 几何约束导出
        if toggles.get('geom'):
            try:
                fig_geom = Figure(figsize=(8, 5), dpi=dpi)
                ax_geom = fig_geom.add_subplot(111)
                draw_funcs['geometry_constraints'](ax_geom, data)
                filename_geom = t("export.filename.geometry", lang) + ".tiff"
                fig_geom.savefig(os.path.join(folder, filename_geom), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_geom)
                saved.append(filename_geom)
            except Exception as exc:
                errors.append(f"geometry: {exc}")

        # 廓形图导出
        if toggles.get('profile'):
            try:
                fig_p = Figure(figsize=(6, 6), dpi=dpi)
                ax_p = fig_p.add_subplot(111)
                draw_funcs['profile'](ax_p, data)
                filename_p = t("export.filename.profile", lang) + ".tiff"
                fig_p.savefig(os.path.join(folder, filename_p), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_p)
                saved.append(filename_p)
            except Exception as exc:
                errors.append(f"profile: {exc}")

        # SVG 矢量图导出
        if toggles.get('svg'):
            try:
                fig_svg = Figure(figsize=(14, 7), dpi=100)
                gs_svg = GridSpec(1, 2, figure=fig_svg, wspace=0.30)
                ax_motion_svg = fig_svg.add_subplot(gs_svg[0, 0])
                ax_geom_svg = fig_svg.add_subplot(gs_svg[0, 1])
                draw_funcs['motion_curves'](ax_motion_svg, data, show_law_names=True)
                draw_funcs['geometry_constraints'](ax_geom_svg, data)
                filename_svg = "camforge_all.svg"
                fig_svg.savefig(os.path.join(folder, filename_svg), format='svg', bbox_inches='tight')
                plt.close(fig_svg)
                saved.append(filename_svg)
            except Exception as exc:
                errors.append(f"svg: {exc}")

        # CSV 数据表导出
        if toggles.get('csv'):
            try:
                filename_csv = t("export.filename.csv", lang) + ".csv"
                filepath_csv = os.path.join(folder, filename_csv)
                delta_deg = data['delta_deg']
                s_arr = data['s']
                v_arr = data['v']
                a_arr = data['a']
                x_arr = data['x']
                y_arr = data['y']
                R_arr = np.hypot(x_arr, y_arr)
                alpha_arr = data['alpha_all']
                rho_arr = data.get('rho', np.full_like(alpha_arr, np.nan))
                with open(filepath_csv, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv_mod.writer(f)
                    # 使用 i18n 表头
                    header = [
                        t("excel.col.delta", lang),
                        t("excel.col.radius", lang),
                        t("excel.col.displacement", lang),
                        t("excel.col.velocity", lang),
                        t("excel.col.acceleration", lang),
                        t("excel.col.curvature", lang),
                        t("excel.col.pressure_angle", lang),
                    ]
                    writer.writerow(header)
                    for i in range(len(delta_deg)):
                        rho_val = round(rho_arr[i], 4) if np.isfinite(rho_arr[i]) else ''
                        writer.writerow([
                            round(delta_deg[i], 2),
                            round(R_arr[i], 4),
                            round(s_arr[i], 4),
                            round(v_arr[i], 4),
                            round(a_arr[i], 4),
                            rho_val,
                            round(alpha_arr[i], 4),
                        ])
                saved.append(filename_csv)
            except Exception as exc:
                errors.append(f"csv: {exc}")

        if toggles.get('excel'):
            self._export_excel(folder, saved, data, lang, errors)

        return saved, errors, folder

    def _export_excel(self, folder, saved_list, data, lang, errors):
        """导出凸轮数据为 Excel 表格。"""
        if openpyxl is None:
            errors.append("openpyxl_missing")
            return

        try:
            delta_deg = data['delta_deg']
            s = data['s']
            v = data['v']
            a = data['a']
            x = data['x']
            y = data['y']
            R = np.hypot(x, y)
            alpha = data['alpha_all']
            rho = data.get('rho', np.full_like(alpha, np.nan))

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = t("excel.sheet_name", lang)

            headers = [
                t("excel.col.delta", lang),
                t("excel.col.radius", lang),
                t("excel.col.displacement", lang),
                t("excel.col.velocity", lang),
                t("excel.col.acceleration", lang),
                t("excel.col.curvature", lang),
                t("excel.col.pressure_angle", lang),
            ]
            ws.append(headers)

            for i in range(len(delta_deg)):
                rho_val = round(rho[i], 4) if np.isfinite(rho[i]) else ''
                ws.append([
                    round(delta_deg[i], 1),
                    round(R[i], 4),
                    round(s[i], 4),
                    round(v[i], 4),
                    round(a[i], 4),
                    rho_val,
                    round(alpha[i], 4),
                ])

            for col in range(1, 8):
                max_len = len(str(ws.cell(row=1, column=col).value))
                for row in range(2, min(10, len(delta_deg) + 2)):
                    cell_len = len(str(ws.cell(row=row, column=col).value))
                    if cell_len > max_len:
                        max_len = cell_len
                ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max_len + 4

            filename = t("export.filename.excel", lang) + ".xlsx"
            filepath = os.path.join(folder, filename)
            wb.save(filepath)
            saved_list.append(filename)
        except Exception as exc:
            errors.append(f"excel: {exc}")
