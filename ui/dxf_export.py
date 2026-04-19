"""
DXF 导出模块 - 导出凸轮廓形为 DXF 格式
支持 AutoCAD 等 CAD 软件导入
"""

import math
from typing import TextIO


def export_cam_profile_to_dxf(
    x: list[float],
    y: list[float],
    filepath: str,
    layer_name: str = "CAM_PROFILE",
) -> None:
    """导出凸轮廓形到 DXF 文件

    Args:
        x: X 坐标数组
        y: Y 坐标数组
        filepath: 输出文件路径
        layer_name: DXF 图层名称
    """
    with open(filepath, 'w', encoding='ascii') as f:
        _write_dxf_header(f)
        _write_dxf_tables(f, layer_name)
        _write_dxf_entities(f, x, y, layer_name)
        _write_dxf_footer(f)


def _write_dxf_header(f: TextIO) -> None:
    """写入 DXF 文件头"""
    f.write("0\nSECTION\n")
    f.write("2\nHEADER\n")
    f.write("9\n$INSUNITS\n")
    f.write("70\n4\n")  # 4 = millimeters
    f.write("0\nENDSEC\n")


def _write_dxf_tables(f: TextIO, layer_name: str) -> None:
    """写入 DXF 表定义"""
    f.write("0\nSECTION\n")
    f.write("2\nTABLES\n")

    # LTYPE 表
    f.write("0\nTABLE\n")
    f.write("2\nLTYPE\n")
    f.write("70\n1\n")
    f.write("0\nLTYPE\n")
    f.write("2\nCONTINUOUS\n")
    f.write("70\n0\n")
    f.write("3\nSolid line\n")
    f.write("72\n65\n")
    f.write("73\n0\n")
    f.write("40\n0.0\n")
    f.write("0\nENDTAB\n")

    # LAYER 表
    f.write("0\nTABLE\n")
    f.write("2\nLAYER\n")
    f.write("70\n1\n")
    f.write("0\nLAYER\n")
    f.write("2\n")
    f.write(f"{layer_name}\n")
    f.write("70\n0\n")
    f.write("62\n7\n")  # 颜色：白色
    f.write("6\nCONTINUOUS\n")
    f.write("0\nENDTAB\n")

    f.write("0\nENDSEC\n")


def _write_dxf_entities(f: TextIO, x: list[float], y: list[float], layer_name: str) -> None:
    """写入 DXF 实体（多段线）"""
    f.write("0\nSECTION\n")
    f.write("2\nENTITIES\n")

    n = len(x)
    if n < 2:
        f.write("0\nENDSEC\n")
        return

    # 使用 LWPOLYLINE（轻量多段线）
    f.write("0\nLWPOLYLINE\n")
    f.write("8\n")  # 图层名
    f.write(f"{layer_name}\n")
    f.write("90\n")  # 顶点数
    f.write(f"{n}\n")
    f.write("70\n")  # 标志：1 = 闭合
    f.write("1\n")
    f.write("43\n")  # 固定线宽
    f.write("0.0\n")

    # 写入顶点
    for i in range(n):
        f.write("10\n")  # X 坐标
        f.write(f"{x[i]:.6f}\n")
        f.write("20\n")  # Y 坐标
        f.write(f"{y[i]:.6f}\n")
        # 凸度（0 表示直线段）
        f.write("42\n")
        f.write("0.0\n")

    f.write("0\nENDSEC\n")


def _write_dxf_footer(f: TextIO) -> None:
    """写入 DXF 文件尾"""
    f.write("0\nEOF\n")


def export_roller_profile_to_dxf(
    x_actual: list[float],
    y_actual: list[float],
    filepath: str,
    layer_name: str = "ROLLER_PROFILE",
) -> None:
    """导出滚子实际廓形到 DXF 文件

    Args:
        x_actual: 实际廓形 X 坐标数组
        y_actual: 实际廓形 Y 坐标数组
        filepath: 输出文件路径
        layer_name: DXF 图层名称
    """
    export_cam_profile_to_dxf(x_actual, y_actual, filepath, layer_name)


def export_both_profiles_to_dxf(
    x: list[float],
    y: list[float],
    x_actual: list[float] | None,
    y_actual: list[float] | None,
    filepath: str,
) -> None:
    """同时导出理论廓形和实际廓形到 DXF 文件

    Args:
        x: 理论廓形 X 坐标数组
        y: 理论廓形 Y 坐标数组
        x_actual: 实际廓形 X 坐标数组（可选）
        y_actual: 实际廓形 Y 坐标数组（可选）
        filepath: 输出文件路径
    """
    with open(filepath, 'w', encoding='ascii') as f:
        _write_dxf_header(f)
        _write_dxf_tables(f, "CAM_THEORY")
        _write_dxf_tables_for_both(f)
        _write_dxf_entities(f, x, y, "CAM_THEORY")
        if x_actual is not None and y_actual is not None:
            _write_dxf_entities(f, x_actual, y_actual, "CAM_ACTUAL")
        _write_dxf_footer(f)


def _write_dxf_tables_for_both(f: TextIO) -> None:
    """为双廓形写入图层表"""
    # LAYER 表（两个图层）
    f.write("0\nTABLE\n")
    f.write("2\nLAYER\n")
    f.write("70\n2\n")

    # 理论廓形图层
    f.write("0\nLAYER\n")
    f.write("2\nCAM_THEORY\n")
    f.write("70\n0\n")
    f.write("62\n5\n")  # 蓝色
    f.write("6\nCONTINUOUS\n")

    # 实际廓形图层
    f.write("0\nLAYER\n")
    f.write("2\nCAM_ACTUAL\n")
    f.write("70\n0\n")
    f.write("62\n1\n")  # 红色
    f.write("6\nCONTINUOUS\n")

    f.write("0\nENDTAB\n")
    f.write("0\nENDSEC\n")
