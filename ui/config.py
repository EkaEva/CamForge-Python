"""
配置管理器 - 管理用户偏好设置
支持参数记忆、导出选项记忆等功能
"""

import json
import os
from pathlib import Path
from typing import Any


class ConfigManager:
    """用户配置管理器"""

    DEFAULT_CONFIG = {
        'last_params': None,
        'export_options': {
            'dl_motion': True,
            'dl_profile': True,
            'dl_csv': True,
            'dl_excel': True,
            'dl_geom': True,
            'dl_anim': True,
            'dl_svg': True,
            'dl_preset': True,
        },
        'ui': {
            'language': 'zh',
            'dark_mode': False,
            'speed': 3,
        },
        'quick_presets': [],
    }

    def __init__(self, config_dir: str | None = None):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为 ~/.camforge/
        """
        if config_dir is None:
            config_dir = os.path.join(Path.home(), '.camforge')
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'config.json')
        self.config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # 合并默认配置和加载的配置
                self.config = self._merge_config(self.DEFAULT_CONFIG.copy(), loaded)
            except (json.JSONDecodeError, IOError):
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()

    def _merge_config(self, base: dict, override: dict) -> dict:
        """递归合并配置"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def save(self) -> None:
        """保存配置到文件"""
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_last_params(self) -> dict | None:
        """获取上次使用的参数"""
        return self.config.get('last_params')

    def set_last_params(self, params: dict) -> None:
        """保存当前参数"""
        self.config['last_params'] = params
        self.save()

    def get_export_options(self) -> dict[str, bool]:
        """获取导出选项"""
        return self.config.get('export_options', self.DEFAULT_CONFIG['export_options'].copy())

    def set_export_options(self, options: dict[str, bool]) -> None:
        """保存导出选项"""
        self.config['export_options'] = options
        self.save()

    def get_ui_settings(self) -> dict:
        """获取 UI 设置"""
        return self.config.get('ui', self.DEFAULT_CONFIG['ui'].copy())

    def set_ui_settings(self, settings: dict) -> None:
        """保存 UI 设置"""
        self.config['ui'] = settings
        self.save()

    def get_quick_presets(self) -> list[dict]:
        """获取快速预设列表"""
        return self.config.get('quick_presets', [])

    def add_quick_preset(self, name: str, params: dict) -> None:
        """添加快速预设"""
        presets = self.get_quick_presets()
        # 检查是否已存在同名预设
        for i, p in enumerate(presets):
            if p.get('name') == name:
                presets[i] = {'name': name, 'params': params}
                break
        else:
            presets.append({'name': name, 'params': params})
        # 最多保存 10 个快速预设
        if len(presets) > 10:
            presets = presets[-10:]
        self.config['quick_presets'] = presets
        self.save()

    def remove_quick_preset(self, name: str) -> None:
        """移除快速预设"""
        presets = self.get_quick_presets()
        self.config['quick_presets'] = [p for p in presets if p.get('name') != name]
        self.save()
