"""CamForge 参数模型与随机参数生成

ParameterModel 封装所有凸轮设计参数，提供类型安全的属性访问、
字典转换和参数校验。generate_random_params() 用于随机填充演示。
"""

import random


# ---------------------------------------------------------------------------
# 参数字段定义：(类型, 默认值)
# ---------------------------------------------------------------------------
PARAM_FIELDS = {
    'delta_0':         (int,   90),
    'delta_01':        (int,   60),
    'delta_ret':       (int,  120),
    'delta_02':        (int,   90),
    'h':               (float, 10.0),
    'r_0':             (float, 40.0),
    'e':               (float,  5.0),
    'omega':           (float,  1.0),
    'r_r':             (float,  0.0),
    'n_points':        (int,  360),
    'alpha_threshold': (float, 30.0),
    'tc_law':          (int,    1),
    'hc_law':          (int,    1),
    'sn':              (int,    1),
    'pz':              (int,    1),
}


class ParameterModel:
    """凸轮设计参数的数据模型。

    提供类型安全的属性访问、字典转换和参数校验。
    所有角度参数为整数（度），几何参数为浮点数。

    Attributes
    ----------
    delta_0, delta_01, delta_ret, delta_02 : int
        推程、远休、回程、近休角度（度），四角之和必须为 360。
    h : float
        从动件最大位移 (mm)。
    r_0 : float
        基圆半径 (mm)。
    e : float
        偏距 (mm)。
    omega : float
        角速度 (rad/s)。
    r_r : float
        滚子半径 (mm)，0 表示尖底从动件。
    n_points : int
        离散点数。
    alpha_threshold : float
        压力角阈值 (度)。
    tc_law, hc_law : int
        推程/回程运动规律编号 (1-5)。
    sn : int
        旋向符号 (+1顺时针, -1逆时针)。
    pz : int
        偏距方向符号 (+1正偏距, -1负偏距)。
    """

    def __init__(self, **kwargs):
        for name, (typ, default) in PARAM_FIELDS.items():
            val = kwargs.get(name, default)
            try:
                setattr(self, name, typ(val))
            except (ValueError, TypeError):
                setattr(self, name, default)

    def to_dict(self) -> dict:
        """转换为字典（向后兼容，用于 sim_data 构建）。"""
        return {name: getattr(self, name) for name in PARAM_FIELDS}

    @classmethod
    def from_dict(cls, d: dict) -> 'ParameterModel':
        """从字典创建模型实例。"""
        return cls(**{k: v for k, v in d.items() if k in PARAM_FIELDS})

    def validate(self) -> tuple[bool, str | tuple | None]:
        """校验参数合法性（使用 cam_mechanics.validate_params）。

        Returns
        -------
        (ok, detail) : tuple[bool, str | tuple | None]
            ok=True 表示参数合法；ok=False 时 detail 为错误描述
            （str 或 tuple，与 cam_mechanics.validate_params 返回格式一致）。
        """
        from cam_mechanics import validate_params
        return validate_params(
            self.delta_0, self.delta_01, self.delta_ret, self.delta_02,
            self.h, self.r_0, self.e, self.omega,
        )

    def angles_sum_to_360(self) -> bool:
        """检查四角之和是否为 360°。"""
        return abs(self.delta_0 + self.delta_01 + self.delta_ret + self.delta_02 - 360) <= 0.01


def generate_random_params() -> dict:
    """生成随机凸轮参数（用于演示）。

    Returns
    -------
    dict
        随机参数字典，包含 sn=±1, pz=±1 的实际符号值。
    """
    while True:
        af = random.randint(1, 33) * 10
        bf = random.randint(1, 34 - af // 10) * 10
        cf = random.randint(1, 35 - af // 10 - bf // 10) * 10
        df = 360 - af - bf - cf
        if af >= 40 and bf >= 40 and cf >= 40 and df >= 40:
            break

    ff = random.randint(10, 100)   # 基圆半径
    gf = random.randint(0, ff - 1)  # 偏距
    ef = random.randint(1, ff)      # 推杆最大位移
    hf = random.randint(1, 100)     # 角速度
    tc_law = random.randint(1, 5)
    hc_law = random.randint(1, 5)
    sn = 1 if random.randint(1, 2) == 1 else -1
    pz = 1 if random.randint(1, 2) == 1 else -1

    return {
        'delta_0': af, 'delta_01': bf,
        'delta_ret': cf, 'delta_02': df,
        'h': ef, 'r_0': ff, 'e': gf, 'omega': hf,
        'tc_law': tc_law, 'hc_law': hc_law,
        'sn': sn, 'pz': pz,
    }