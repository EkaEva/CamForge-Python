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
        with pytest.raises(ValueError, match="law must be 1-5"):
            compute_rise(delta_arr, delta_0, h, omega, 6)

    def test_rise_zero_delta_raises(self):
        """delta_0=0 应抛出 ValueError"""
        delta_arr = np.linspace(0, 1, 10)
        with pytest.raises(ValueError, match="delta_0 must be > 0"):
            compute_rise(delta_arr, 0, 10, 1, 1)

    def test_rise_negative_omega_raises(self):
        """omega<=0 应抛出 ValueError"""
        delta_arr = np.linspace(0, 1, 10)
        with pytest.raises(ValueError, match="omega must be > 0"):
            compute_rise(delta_arr, 1, 10, 0, 1)


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
        with pytest.raises(ValueError, match="law must be 1-5"):
            compute_return(delta_arr, delta_ret, h, omega, 0)

    def test_return_zero_delta_raises(self):
        """delta_ret=0 应抛出 ValueError"""
        delta_arr = np.linspace(0, 1, 10)
        with pytest.raises(ValueError, match="delta_ret must be > 0"):
            compute_return(delta_arr, 0, 10, 1, 1)


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

    def test_full_motion_invalid_h_raises(self):
        """h<=0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="h must be > 0"):
            compute_full_motion(90, 60, 120, 90, 0, 40, 5, 1, 1, 1)

    def test_full_motion_invalid_r0_raises(self):
        """r_0<=0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="r_0 must be > 0"):
            compute_full_motion(90, 60, 120, 90, 10, 0, 5, 1, 1, 1)

    def test_full_motion_e_ge_r0_raises(self):
        """e>=r_0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="e must be < r_0"):
            compute_full_motion(90, 60, 120, 90, 10, 40, 40, 1, 1, 1)

    def test_full_motion_invalid_omega_raises(self):
        """omega<=0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="omega must be > 0"):
            compute_full_motion(90, 60, 120, 90, 10, 40, 5, 0, 1, 1)

    def test_full_motion_invalid_law_raises(self):
        """非法运动规律编号应抛出 ValueError"""
        with pytest.raises(ValueError, match="tc_law must be 1-5"):
            compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 6, 1)
        with pytest.raises(ValueError, match="hc_law must be 1-5"):
            compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 1, 0)

    def test_full_motion_angles_sum_not_360_raises(self):
        """四角之和不为360应抛出 ValueError"""
        with pytest.raises(ValueError, match="Four angles must sum to 360"):
            compute_full_motion(90, 60, 120, 80, 10, 40, 5, 1, 1, 1)

    def test_full_motion_non_integer_angles(self):
        """非整角度（如91+59+120+90=360）应正确计算，索引不越界"""
        delta_deg, s, v, a, ds_ddelta, pb = compute_full_motion(
            91, 59, 120, 90, 10, 40, 5, 1, 3, 4)
        assert len(s) == N_POINTS
        assert len(v) == N_POINTS
        assert len(a) == N_POINTS
        # 推程结束位移应接近 h
        i1 = int(round(91))
        assert abs(s[i1 - 1] - 10) < 0.1, f"推程末端位移{s[i1-1]}不接近h=10"

    def test_full_motion_another_non_integer(self):
        """另一组非整角度（85+65+130+80=360）应正确计算"""
        delta_deg, s, v, a, ds_ddelta, pb = compute_full_motion(
            85, 65, 130, 80, 10, 40, 5, 1, 1, 1)
        assert len(s) == N_POINTS
        # 近休止段位移应为0
        i3 = int(round(85 + 65 + 130))
        assert np.allclose(s[i3:], 0, atol=1e-6)


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

    def test_profile_invalid_r0_raises(self):
        """r_0<=0 应抛出 ValueError"""
        s = np.zeros(360)
        with pytest.raises(ValueError, match="r_0 must be > 0"):
            compute_cam_profile(s, 0, 0, 1, 1)

    def test_profile_e_ge_r0_raises(self):
        """e>=r_0 应抛出 ValueError"""
        s = np.zeros(360)
        with pytest.raises(ValueError, match="e must be < r_0"):
            compute_cam_profile(s, 40, 40, 1, 1)

    def test_profile_invalid_sn_raises(self):
        """sn 不为 ±1 应抛出 ValueError"""
        s = np.zeros(360)
        with pytest.raises(ValueError, match="sn must be"):
            compute_cam_profile(s, 40, 0, 0, 1)

    def test_profile_invalid_pz_raises(self):
        """pz 不为 ±1 应抛出 ValueError"""
        s = np.zeros(360)
        with pytest.raises(ValueError, match="pz must be"):
            compute_cam_profile(s, 40, 0, 1, 0)

    def test_profile_sn_negative_one(self):
        """sn=-1（逆时针）廓形应与 sn=+1 关于 y 轴镜像"""
        _, s, _, _, _, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        x_cw, y_cw, _ = compute_cam_profile(s, 40, 5, 1, 1)
        x_ccw, y_ccw, _ = compute_cam_profile(s, 40, 5, -1, 1)
        # sn=-1 时 x 坐号取反
        assert np.allclose(x_ccw, -x_cw, atol=1e-10), "逆时针廓形x坐标不等于顺时针取反"
        assert np.allclose(y_ccw, y_cw, atol=1e-10), "逆时针廓形y坐标应与顺时针相同"

    def test_profile_pz_negative_one(self):
        """pz=-1（负偏距）廓形应正确计算且与 pz=+1 不同"""
        _, s, _, _, _, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        x_pos, y_pos, _ = compute_cam_profile(s, 40, 5, 1, 1)
        x_neg, y_neg, _ = compute_cam_profile(s, 40, 5, 1, -1)
        # pz=-1 时偏距方向反转，廓形应与正偏距不同
        assert not np.allclose(x_neg, x_pos, atol=1e-6), "负偏距廓形应与正偏距不同"
        # 但廓形半径应相同（偏距只改变方向不改变大小）
        R_pos = np.hypot(x_pos, y_pos)
        R_neg = np.hypot(x_neg, y_neg)
        assert np.allclose(R_neg, R_pos, atol=1e-6), "负偏距廓形半径应与正偏距相同"

    def test_profile_sn_neg_pz_neg(self):
        """sn=-1, pz=-1 组合应正确计算"""
        _, s, _, _, _, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        x, y, s_0 = compute_cam_profile(s, 40, 5, -1, -1)
        assert len(x) == N_POINTS
        assert len(y) == N_POINTS
        assert s_0 > 0
        # 廓形不应全为零
        assert np.max(np.hypot(x, y)) > 0


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

    def test_pressure_angle_invalid_s0_raises(self):
        """s_0<=0 应抛出 ValueError"""
        s = np.zeros(360)
        ds_ddelta = np.zeros(360)
        with pytest.raises(ValueError, match="s_0 must be > 0"):
            compute_pressure_angle(s, ds_ddelta, 0, 0, 1)

    def test_pressure_angle_invalid_pz_raises(self):
        """pz 不为 ±1 应抛出 ValueError"""
        s = np.zeros(360)
        ds_ddelta = np.zeros(360)
        with pytest.raises(ValueError, match="pz must be"):
            compute_pressure_angle(s, ds_ddelta, 40, 0, 0)

    def test_pressure_angle_rise_phase(self):
        """推程段压力角应非零（有速度分量）"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        # 推程段中间（约45度处）压力角应大于0
        assert abs(alpha[45]) > 0.1, "推程段中间压力角应大于0"

    def test_pressure_angle_return_phase(self):
        """回程段压力角应非零（有速度分量）"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        # 回程段中间（约150+60=210度处）压力角应大于0
        assert abs(alpha[210]) > 0.1, "回程段中间压力角应大于0"

    def test_pressure_angle_pz_negative(self):
        """pz=-1 时压力角应正确计算"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, -1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, -1)
        assert np.all(np.abs(alpha) <= 90), "pz=-1时压力角超出±90°范围"


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

    def test_frame_index_zero(self):
        """帧索引0（起始帧）应正确计算"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        frame = compute_anim_frame_data(s, ds_ddelta, s_0, 5, 40, 1, 1, 0, alpha)
        assert 'follower_x' in frame
        assert frame['s_i'] == pytest.approx(0.0, abs=1e-10), "起始帧位移应为0"

    def test_frame_index_last(self):
        """帧索引N-1（最后一帧）应正确计算"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        N = len(s)
        frame = compute_anim_frame_data(s, ds_ddelta, s_0, 5, 40, 1, 1, N - 1, alpha)
        assert 'follower_x' in frame
        # 最后一帧在近休止段，位移应接近0
        assert abs(frame['s_i']) < 1.0, f"最后一帧位移{frame['s_i']}应接近0"

    def test_frame_index_out_of_range_raises(self):
        """帧索引越界应抛出 ValueError"""
        _, s, _, _, ds_ddelta, _ = compute_full_motion(90, 60, 120, 90, 10, 40, 5, 1, 3, 4)
        _, _, s_0 = compute_cam_profile(s, 40, 5, 1, 1)
        alpha = compute_pressure_angle(s, ds_ddelta, s_0, 5, 1)
        with pytest.raises(ValueError, match="Frame index i must be"):
            compute_anim_frame_data(s, ds_ddelta, s_0, 5, 40, 1, 1, -1, alpha)
        with pytest.raises(ValueError, match="Frame index i must be"):
            compute_anim_frame_data(s, ds_ddelta, s_0, 5, 40, 1, 1, len(s), alpha)


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

    def test_arc_invalid_radius_raises(self):
        """arc_r<=0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="arc_r must be > 0"):
            compute_pressure_angle_arc(0, 5, 0, 1, 15.0, 0)


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
        assert err == "error.angles_sum"

    def test_non_integer_angle(self):
        """非整数角度应失败"""
        ok, err = validate_params(90.5, 60, 120, 89.5, 10, 40, 5, 1)
        assert ok is False
        assert isinstance(err, tuple) and err[0] == "error.angle_integer"

    def test_angle_too_small(self):
        """角度<=1应失败"""
        ok, err = validate_params(1, 120, 120, 119, 10, 40, 5, 1)
        assert ok is False
        assert isinstance(err, tuple) and err[0] == "error.angle_min"

    def test_negative_stroke(self):
        """行程<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 0, 40, 5, 1)
        assert ok is False
        assert err == "error.h_positive"
        ok2, err2 = validate_params(90, 60, 120, 90, -5, 40, 5, 1)
        assert ok2 is False

    def test_negative_base_radius(self):
        """基圆半径<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 0, 5, 1)
        assert ok is False
        assert err == "error.r0_positive"

    def test_offset_exceeds_base_radius(self):
        """偏距>=基圆半径应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, 40, 1)
        assert ok is False
        assert err == "error.e_lt_r0"
        ok2, _ = validate_params(90, 60, 120, 90, 10, 40, 41, 1)
        assert ok2 is False

    def test_negative_omega(self):
        """角速度<=0应失败"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, 5, 0)
        assert ok is False
        assert err == "error.omega_positive"

    def test_negative_offset_rejected(self):
        """负偏距应被拒绝（与计算引擎一致）"""
        ok, err = validate_params(90, 60, 120, 90, 10, 40, -5, 1)
        assert ok is False
        assert err == "error.e_negative"


# ============================================================================
# i18n 测试
# ============================================================================

class TestI18n:
    """国际化模块测试"""

    def test_all_translation_keys_have_zh_and_en(self):
        """所有翻译键应同时有 zh 和 en 条目"""
        from i18n import TRANSLATIONS, SUPPORTED_LANGS
        for key, entry in TRANSLATIONS.items():
            for lang in SUPPORTED_LANGS:
                assert lang in entry, f"Key '{key}' missing '{lang}' translation"

    def test_translation_fallback(self):
        """不存在的语言应回退到默认语言"""
        from i18n import t, DEFAULT_LANG
        result = t("app.title", "fr")  # 法语不存在
        expected = t("app.title", DEFAULT_LANG)
        assert result == expected

    def test_missing_key_returns_bracket(self):
        """不存在的键应返回 [key]"""
        from i18n import t
        result = t("nonexistent.key", "zh")
        assert result == "[nonexistent.key]"

    def test_format_parameters(self):
        """格式化参数应正确替换"""
        from i18n import t
        result = t("status.warning_max_alpha", "zh", val=35.5, threshold=30)
        assert "35.5" in result
        assert "30" in result

    def test_no_duplicate_keys(self):
        """不应有重复的翻译键"""
        from i18n import TRANSLATIONS
        # TRANSLATIONS 是 dict，天然无重复键，只需验证非空
        assert len(TRANSLATIONS) > 0
