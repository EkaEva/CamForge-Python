"""ui 模块单元测试"""

import numpy as np
import pytest

from ui.constants import (
    TIP_WIDTH_RATIO, TIP_HEIGHT_RATIO, ROD_LENGTH_RATIO,
    LIMIT_LINE_RATIO, ARC_RADIUS_RATIO, SUPPORT_SIZE_RATIO,
    MAX_PRESSURE_ANGLE, ANIM_FRAME_SKIP, ANIM_MIN_DELAY_MS,
    ANIM_BASE_DELAY_MS, GIF_DURATION_MS, GIF_DPI, STATIC_DPI,
    THEME, THEME_DARK, DEFAULT_PARAMS,
)
from ui.drawing import draw_fixed_support
from ui.params import ParameterModel, generate_random_params
from ui.plots import (
    draw_displacement_curve, draw_velocity_curve,
    draw_acceleration_curve, draw_profile_plot,
    draw_pressure_angle_curve, draw_curvature_radius_curve,
)


# ============================================================================
# constants 测试
# ============================================================================

class TestConstants:
    """渲染常量合理性测试"""

    def test_ratios_positive(self):
        for name, val in [
            ('TIP_WIDTH_RATIO', TIP_WIDTH_RATIO),
            ('TIP_HEIGHT_RATIO', TIP_HEIGHT_RATIO),
            ('ROD_LENGTH_RATIO', ROD_LENGTH_RATIO),
            ('LIMIT_LINE_RATIO', LIMIT_LINE_RATIO),
            ('ARC_RADIUS_RATIO', ARC_RADIUS_RATIO),
            ('SUPPORT_SIZE_RATIO', SUPPORT_SIZE_RATIO),
        ]:
            assert val > 0, f"{name} should be positive"

    def test_max_pressure_angle(self):
        assert 0 < MAX_PRESSURE_ANGLE < 90

    def test_anim_delays(self):
        assert ANIM_MIN_DELAY_MS > 0
        assert ANIM_BASE_DELAY_MS > ANIM_MIN_DELAY_MS

    def test_dpi_values(self):
        assert GIF_DPI > 0
        assert STATIC_DPI > GIF_DPI

    def test_theme_has_required_keys(self):
        required = ['sidebar_bg', 'toolbar_bg', 'btn_start', 'btn_fg', 'info_text']
        for key in required:
            assert key in THEME, f"THEME missing key: {key}"

    def test_theme_dark_has_required_keys(self):
        required = ['sidebar_bg', 'toolbar_bg', 'btn_start', 'btn_fg', 'info_text']
        for key in required:
            assert key in THEME_DARK, f"THEME_DARK missing key: {key}"

    def test_default_params_complete(self):
        required = ['delta_0', 'delta_01', 'delta_ret', 'delta_02',
                     'h', 'omega', 'r_0', 'e', 'r_r', 'n_points', 'alpha_threshold']
        for key in required:
            assert key in DEFAULT_PARAMS, f"DEFAULT_PARAMS missing key: {key}"


# ============================================================================
# params 测试
# ============================================================================

class TestParameterModel:
    """参数数据模型测试"""

    def test_default_values(self):
        m = ParameterModel()
        assert m.delta_0 == 90
        assert m.h == 10
        assert m.r_0 == 40

    def test_custom_values(self):
        m = ParameterModel(delta_0=120, h=20, r_0=50)
        assert m.delta_0 == 120
        assert m.h == 20
        assert m.r_0 == 50

    def test_to_dict(self):
        m = ParameterModel()
        d = m.to_dict()
        assert isinstance(d, dict)
        assert d['delta_0'] == 90
        assert d['h'] == 10
        assert 'tc_law' in d
        assert 'hc_law' in d


class TestGenerateRandomParams:
    """随机参数生成测试"""

    def test_returns_dict(self):
        p = generate_random_params()
        assert isinstance(p, dict)

    def test_angles_sum_to_360(self):
        p = generate_random_params()
        assert p['delta_0'] + p['delta_01'] + p['delta_ret'] + p['delta_02'] == 360

    def test_angles_at_least_40(self):
        p = generate_random_params()
        assert p['delta_0'] >= 40
        assert p['delta_01'] >= 40
        assert p['delta_ret'] >= 40
        assert p['delta_02'] >= 40

    def test_valid_ranges(self):
        p = generate_random_params()
        assert p['h'] >= 1
        assert p['r_0'] >= 10
        assert p['e'] >= 0
        assert p['e'] < p['r_0']
        assert p['omega'] >= 1
        assert p['tc_law'] in (1, 2, 3, 4, 5)
        assert p['hc_law'] in (1, 2, 3, 4, 5)
        assert p['sn'] in (1, -1)
        assert p['pz'] in (1, -1)


# ============================================================================
# drawing 测试
# ============================================================================

class TestDrawFixedSupport:
    """固定铰支座绘制测试"""

    def test_draws_without_error(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_fixed_support(ax, r_0=40)
        plt.close(fig)

    def test_adds_patches(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        n_before = len(ax.patches)
        draw_fixed_support(ax, r_0=40)
        assert len(ax.patches) > n_before
        plt.close(fig)


# ============================================================================
# plots 测试
# ============================================================================

class TestPlots:
    """静态图表绘制测试"""

    @pytest.fixture
    def sample_data(self):
        """生成测试用仿真数据"""
        from cam_mechanics import (
            compute_full_motion, compute_cam_profile,
            compute_pressure_angle, compute_curvature_radius,
        )
        delta_deg, s, v, a, ds_ddelta, pb = compute_full_motion(
            90, 60, 120, 90, 10, 40, 5, 1, 1, 1
        )
        x, y, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        rho = compute_curvature_radius(x, y)

        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = 40 * np.cos(delta_full)
        y_base = 40 * np.sin(delta_full)
        x_offset = x_base / 40 * 5
        y_offset = y_base / 40 * 5
        R = np.hypot(x, y)
        Rmax = np.max(R)

        return {
            'delta_deg': delta_deg, 's': s, 'v': v, 'a': a,
            'ds_ddelta': ds_ddelta, 'phase_bounds': pb,
            'x': x, 'y': y, 's_0': s_0,
            'r_0': 40, 'e': 5, 'h': 10,
            'x_base': x_base, 'y_base': y_base,
            'x_offset': x_offset, 'y_offset': y_offset,
            'Rmax': Rmax, 'alpha_all': alpha_all,
            'rho': rho, 'rho_min': np.min(rho[np.isfinite(rho)]),
            'rho_min_idx': int(np.argmin(np.abs(rho - np.min(rho[np.isfinite(rho)])))),
            'tc_law': 1, 'hc_law': 1,
        }

    def test_draw_displacement(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_displacement_curve(ax, sample_data, 'zh')
        plt.close(fig)

    def test_draw_displacement_en(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_displacement_curve(ax, sample_data, 'en')
        plt.close(fig)

    def test_draw_velocity(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_velocity_curve(ax, sample_data, 'zh')
        plt.close(fig)

    def test_draw_acceleration(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_acceleration_curve(ax, sample_data, 'zh')
        plt.close(fig)

    def test_draw_profile(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_profile_plot(ax, sample_data, 'zh')
        plt.close(fig)

    def test_draw_pressure_angle_curve(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_pressure_angle_curve(ax, sample_data, 'zh')
        plt.close(fig)

    def test_draw_curvature_radius_curve(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_curvature_radius_curve(ax, sample_data, 'zh')
        plt.close(fig)

    def test_displacement_with_law_names(self, sample_data):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        draw_displacement_curve(ax, sample_data, 'zh', show_law_names=True)
        plt.close(fig)
