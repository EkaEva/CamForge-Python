"""CamForge 参数数据模型与随机参数生成"""

import random as _random


class ParameterModel:
    """凸轮参数数据模型，分离计算状态与 GUI 状态"""

    def __init__(self, **kwargs):
        self.delta_0 = kwargs.get('delta_0', 90)
        self.delta_01 = kwargs.get('delta_01', 60)
        self.delta_ret = kwargs.get('delta_ret', 120)
        self.delta_02 = kwargs.get('delta_02', 90)
        self.h = kwargs.get('h', 10)
        self.r_0 = kwargs.get('r_0', 40)
        self.e = kwargs.get('e', 5)
        self.omega = kwargs.get('omega', 1)
        self.tc_law = kwargs.get('tc_law', 1)
        self.hc_law = kwargs.get('hc_law', 1)
        self.sn = kwargs.get('sn', 1)
        self.pz = kwargs.get('pz', 1)

    def to_dict(self):
        """转换为字典（兼容旧接口）"""
        return {
            'delta_0': self.delta_0, 'delta_01': self.delta_01,
            'delta_ret': self.delta_ret, 'delta_02': self.delta_02,
            'h': self.h, 'r_0': self.r_0, 'e': self.e, 'omega': self.omega,
            'tc_law': self.tc_law, 'hc_law': self.hc_law,
            'sn': self.sn, 'pz': self.pz,
        }


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
