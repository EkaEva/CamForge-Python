"""cam_mechanics 模块单元测试"""

import numpy as np
import pytest

from cam_mechanics import (
    compute_rise, compute_return, compute_full_motion,
    compute_cam_profile, compute_pressure_angle,
    compute_rotated_cam, compute_anim_frame_data,
    compute_pressure_angle_arc, validate_params,
    N_POINTS, DEG2RAD,
)


# ============================================================================
# 运动规律测试
# ============================================================================

class TestComputeRise:
    """推程运动规律测试"""

    @pytest.fixture
    def common_params(self):
        delta_0 = np.radians(90)
        h = 10.0
        omega = 1.0
        delta_arr = np.linspace(0, delta_0, 100)
        return delta_arr, delta_0, h, omega

    @pytest.mark.parametrize("law", [1, 2, 3, 4, 5])
    def test_rise_boundary_values(self, common_params, law):
        """推程始末位移应为 0 和 h"""
        delta_arr, delta_0, h, omega = common_params
        s, v, a = compute_rise(delta_arr, delta_0, h, omega, law)
        assert abs(s[0]) < 1e-10, f"推程起始位移应为0，实际为{s[0]}"
        assert abs(s[-1] - h) < 1e-6, f"推程终止位移应为{h}，实际为{s[-1]}"

    @pytest.mark.parametrize("law", [1, 2, 3, 4, 5])
    def test_rise_monotonic(self, common_params, law):
        """推程位移应单调递增"""
        delta_arr, delta_0, h, omega = common_params
        s, _, _ = compute_rise(delta_arr, delta_0, h, omega, law)
        assert np.all(np.diff(s) >= -1e-10), f"推程规律{law}位移非单调递增"

    @pytest.mark.parametrize("law", [1, 2, 3, 4, 5])
    def test_rise_non_negative(self, common_params, law):
        """推程位移应非负"""
        delta_arr, delta_0, h, omega = common_params
        s, _, _ = compute_rise(delta_arr, delta_0, h, omega, law)
        assert np.all(s >= -1e-10), f"推程规律{law}存在负位移"

    def test_rise_constant_velocity(self, common_params):
        """等速运动速度恒定"""
        delta_arr, delta_0, h, omega = common_params
        s, v, a = compute_rise(delta_arr, delta_0, h, omega, 1)
        assert np.allclose(a, 0, atol=1e-10), "等速运动加速度应为0"
        expected_v = h * omega / delta_0
        assert np.allclose(v, expected_v, atol=1e-10), "等速运动速度应恒定"

    def test_rise_unknown_law_raises(self, common_params):
        """未知运动规律应抛出异常"""
        delta_arr, delta_0, h, omega = common_params
        with pytest.raises(ValueError, match="未知的运动规律编号"):
            compute_rise(delta_arr, delta_0, h, omega, 6)


class TestComputeReturn:
    """回程运动规律测试"""

    @pytest.fixture
    def common_params(self):
        delta_ret = np.radians(90)
        h = 10.0
        omega = 1.0
        delta_arr = np.linspace(0, delta_ret, 100)
        return delta_arr, delta_ret, h, omega

    @pytest.mark.parametrize("law", [1, 2, 3, 4, 5])
    def test_return_boundary_values(self, common_params, law):
        """回程始末位移应为 h 和 0"""
        delta_arr, delta_ret, h, omega = common_params
        s, v, a = compute_return(delta_arr, delta_ret, h, omega, law)
        assert abs(s[0] - h) < 1e-6, f"回程起始位移应为{h}，实际为{s[0]}"
        assert abs(s[-1]) < 1e-6, f"回程终止位移应为0，实际为{s[-1]}"

    @pytest.mark.parametrize("law", [1, 2, 3, 4, 5])
    def test_return_monotonic(self, common_params, law):
        """回程位移应单调递减"""
        delta_arr, delta_ret, h, omega = common_params
        s, _, _ = compute_return(delta_arr, delta_ret, h, omega, law)
        assert np.all(np.diff(s) <= 1e-10), f"回程规律{law}位移非单调递减"

    def test_return_unknown_law_raises(self, common_params):
        """未知运动规律应抛出异常"""
        delta_arr, delta_ret, h, omega = common_params
        with pytest.raises(ValueError, match="未知的运动规律编号"):
            compute_return(delta_arr, delta_ret, h, omega, 0)


# ============================================================================
# 全程运动计算测试
# ============================================================================

class TestComputeFullMotion:
    """全程运动计算测试"""

    @pytest.fixture
    def motion_data(self):
        return compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)

    def test_output_length(self, motion_data):
        """输出数组长度应为 N_POINTS"""
        delta_deg, s, v, a, ds_ddelta, pb = motion_data
        assert len(delta_deg) == N_POINTS
        assert len(s) == N_POINTS
        assert len(v) == N_POINTS
        assert len(a) == N_POINTS
        assert len(ds_ddelta) == N_POINTS

    def test_phase_boundaries(self, motion_data):
        """阶段分界点应正确"""
        _, _, _, _, _, pb = motion_data
        assert pb == [0, 90, 150, 270, 360]

    def test_far_dwell_displacement(self, motion_data):
        """远休止段位移应恒为 h"""
        _, s, _, _, _, pb = motion_data
        i1, i2 = pb[1], pb[2]
        dwell_s = s[i1:i2]
        assert np.allclose(dwell_s, 10.0, atol=1e-6), "远休止段位移不恒定"

    def test_near_dwell_displacement(self, motion_data):
        """近休止段位移应恒为 0"""
        _, s, _, _, _, pb = motion_data
        i3 = pb[3]
        dwell_s = s[i3:]
        assert np.allclose(dwell_s, 0, atol=1e-6), "近休止段位移不为0"

    def test_dwell_velocity_zero(self, motion_data):
        """休止段速度应为 0"""
        _, _, v, _, _, pb = motion_data
        assert np.allclose(v[pb[1]:pb[2]], 0, atol=1e-10), "远休止段速度不为0"
        assert np.allclose(v[pb[3]:], 0, atol=1e-10), "近休止段速度不为0"

    def test_dwell_acceleration_zero(self, motion_data):
        """休止段加速度应为 0"""
        _, _, _, a, _, pb = motion_data
        assert np.allclose(a[pb[1]:pb[2]], 0, atol=1e-10), "远休止段加速度不为0"
        assert np.allclose(a[pb[3]:], 0, atol=1e-10), "近休止段加速度不为0"

    def test_ds_ddelta_equals_v_over_omega(self, motion_data):
        """ds/dδ 应等于 v/ω"""
        _, _, v, _, ds_ddelta, _ = motion_data
        omega = 1.0
        assert np.allclose(ds_ddelta, v / omega, atol=1e-10)


# ============================================================================
# 凸轮廓形测试
# ============================================================================

class TestComputeCamProfile:
    """凸轮廓形计算测试"""

    @pytest.fixture
    def profile_data(self):
        _, s, _, _, _, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        return compute_cam_profile(s, 40, 5, 1, 1)

    def test_profile_length(self, profile_data):
        """廓形坐标长度应与位移数组一致"""
        x, y, s_0 = profile_data
        assert len(x) == N_POINTS
        assert len(y) == N_POINTS

    def test_s0_value(self, profile_data):
        """初始位移 s_0 = sqrt(r_0^2 - e^2)"""
        _, _, s_0 = profile_data
        expected = np.sqrt(40**2 - 5**2)
        assert abs(s_0 - expected) < 1e-10

    def test_profile_closure(self, profile_data):
        """廓形首尾应接近闭合（1°步长，首尾间距应小于单步弧长）"""
        x, y, _ = profile_data
        # endpoint=False 导致首尾不重合，但间距应很小（约1°弧长）
        dist = np.hypot(x[0] - x[-1], y[0] - y[-1])
        # 首尾间距应小于廓形最大半径的 2° 弧长
        Rmax = np.max(np.hypot(x, y))
        assert dist < Rmax * np.radians(2), f"廓形首尾距离{dist}过大，未闭合"

    def test_zero_offset_concentric(self):
        """偏距为0时，近休止段廓形应在基圆上"""
        _, s, _, _, _, _ = compute_full_motion(90, 90, 90, 90, 10, 40, 0, 1, 1, 1)
        x, y, s_0 = compute_cam_profile(s, 40, 0, 1, 1)
        # 近休止段（270-360度）廓形半径应等于基圆半径
        R_near = np.hypot(x[270:], y[270:])
        assert np.allclose(R_near, 40, atol=1e-6), "近休止段廓形不在基圆上"


# ============================================================================
# 压力角测试
# ============================================================================

class TestComputePressureAngle:
    """压力角计算测试"""

    def test_pressure_angle_range(self):
        """压力角应在合理范围内"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        assert np.all(np.abs(alpha) <= 90), "压力角超出±90°范围"

    def test_dwell_pressure_angle_zero(self):
        """休止段压力角应接近0"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 90, 90, 90, 10, 40, 0, 1, 1, 1)
        _, _, s_0 = compute_cam_profile(s, 40, 0, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 0, 1)
        # 近休止段压力角应接近0
        assert np.allclose(alpha[270:], 0, atol=1e-6), "近休止段压力角不为0"


# ============================================================================
# 凸轮旋转测试
# ============================================================================

class TestComputeRotatedCam:
    """凸轮旋转计算测试"""

    def test_zero_rotation(self):
        """旋转0度应不变"""
        x = np.array([1.0, 0.0, -1.0])
        y = np.array([0.0, 1.0, 0.0])
        xr, yr = compute_rotated_cam(x, y, 0)
        assert np.allclose(xr, x)
        assert np.allclose(yr, y)

    def test_90_degree_rotation(self):
        """旋转90度应正确"""
        x = np.array([1.0])
        y = np.array([0.0])
        xr, yr = compute_rotated_cam(x, y, np.pi / 2)
        assert abs(xr[0] - 0.0) < 1e-10
        assert abs(yr[0] - 1.0) < 1e-10

    def test_rotation_preserves_distance(self):
        """旋转应保持到原点距离不变"""
        x = np.array([3.0, -2.0, 5.0])
        y = np.array([4.0, 1.0, -3.0])
        angle = 1.23
        xr, yr = compute_rotated_cam(x, y, angle)
        R_orig = np.hypot(x, y)
        R_rot = np.hypot(xr, yr)
        assert np.allclose(R_orig, R_rot, atol=1e-10), "旋转改变了到原点距离"


# ============================================================================
# 动画帧数据测试
# ============================================================================

class TestComputeAnimFrameData:
    """动画帧数据计算测试"""

    @pytest.fixture
    def frame_data(self):
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        return compute_anim_frame_data(s, ds_ddelta, s_0, 5, 40, 1, 1, 45, alpha)

    def test_frame_keys(self, frame_data):
        """帧数据应包含所有必要键"""
        expected_keys = {'follower_x', 'contact_y', 'nx', 'ny', 'tx', 'ty', 'alpha_i', 's_i'}
        assert set(frame_data.keys()) == expected_keys

    def test_normal_unit_vector(self, frame_data):
        """法线应为单位向量"""
        nx, ny = frame_data['nx'], frame_data['ny']
        assert abs(np.hypot(nx, ny) - 1.0) < 1e-10, "法线不是单位向量"

    def test_tangent_unit_vector(self, frame_data):
        """切线应为单位向量"""
        tx, ty = frame_data['tx'], frame_data['ty']
        assert abs(np.hypot(tx, ty) - 1.0) < 1e-10, "切线不是单位向量"

    def test_normal_tangent_perpendicular(self, frame_data):
        """法线与切线应正交"""
        dot = frame_data['nx'] * frame_data['tx'] + frame_data['ny'] * frame_data['ty']
        assert abs(dot) < 1e-10, "法线与切线不正交"


# ============================================================================
# 压力角弧线测试
# ============================================================================

class TestComputePressureAngleArc:
    """压力角弧线计算测试"""

    def test_small_angle_returns_empty(self):
        """压力角过小应返回空数组"""
        x, y = compute_pressure_angle_arc(0, 5, 0, 1, 0.3, 2.0)
        assert len(x) == 0
        assert len(y) == 0

    def test_normal_angle_returns_nonempty(self):
        """正常压力角应返回弧线坐标"""
        x, y = compute_pressure_angle_arc(0, 5, 0, 1, 15.0, 2.0)
        assert len(x) > 0
        assert len(y) > 0

    def test_arc_on_circle(self):
        """弧线点应在指定半径的圆上"""
        cx, cy = 1.0, 2.0
        arc_r = 3.0
        x, y = compute_pressure_angle_arc(cx, cy, 0, 1, 20.0, arc_r)
        if len(x) > 0:
            dist = np.hypot(x - cx, y - cy)
            assert np.allclose(dist, arc_r, atol=1e-6), "弧线点不在指定圆上"


# ============================================================================
# 参数校验测试
# ============================================================================

class TestValidateParams:
    """参数校验测试"""

    def test_valid_params(self):
        """合法参数应通过校验"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, 5, 1)
        assert ok is True
        assert err is None

    def test_angles_not_sum_360(self):
        """四角之和不为360应失败"""
        ok, err = validate_params(90, 90, 90, 91, 10, 40, 5, 1)
        assert ok is False
        assert "360" in err

    def test_non_integer_angle(self):
        """非整数角度应失败"""
        ok, err = validate_params(90.5, 60, 120, 89.5, 10, 40, 5, 1)
        assert ok is False
        assert "整数" in err

    def test_angle_too_small(self):
        """角度<=1应失败"""
        ok, err = validate_params(1, 120, 120, 119, 10, 40, 5, 1)
        assert ok is False

    def test_negative_stroke(self):
        """行程<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 0, 40, 5, 1)
        assert ok is False
        ok2, _ = validate_params(90, 60, 120, 90, -5, 40, 5, 1)
        assert ok2 is False

    def test_negative_base_radius(self):
        """基圆半径<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 0, 5, 1)
        assert ok is False

    def test_offset_exceeds_base_radius(self):
        """偏距>=基圆半径应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, 40, 1)
        assert ok is False
        ok2, _ = validate_params(90, 60, 120, 90, 10, 40, 41, 1)
        assert ok2 is False

    def test_negative_omega(self):
        """角速度<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, 5, 0)
        assert ok is False
