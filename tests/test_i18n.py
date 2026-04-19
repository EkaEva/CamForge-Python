"""i18n 模块辅助函数测试"""

import pytest

from i18n import (
    t, SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP, LANG_DISPLAY_NAMES,
    get_motion_law_list, get_rotation_list, get_offset_dir_list,
    get_lang_display_list, detect_mpl_fonts, TRANSLATIONS,
)


class TestI18nHelpers:
    """i18n 辅助函数测试"""

    def test_get_motion_law_list_zh(self):
        lst = get_motion_law_list('zh')
        assert len(lst) == 6
        assert all(isinstance(s, str) for s in lst)

    def test_get_motion_law_list_en(self):
        lst = get_motion_law_list('en')
        assert len(lst) == 6

    def test_get_rotation_list(self):
        lst = get_rotation_list('zh')
        assert len(lst) == 2

    def test_get_offset_dir_list(self):
        lst = get_offset_dir_list('en')
        assert len(lst) == 2

    def test_get_lang_display_list(self):
        lst = get_lang_display_list()
        assert len(lst) == len(SUPPORTED_LANGS)

    def test_detect_mpl_fonts_zh(self):
        fonts = detect_mpl_fonts('zh')
        assert isinstance(fonts, list)
        assert len(fonts) > 0
        assert 'DejaVu Sans' in fonts

    def test_detect_mpl_fonts_en(self):
        fonts = detect_mpl_fonts('en')
        assert isinstance(fonts, list)
        assert len(fonts) > 0

    def test_supported_langs(self):
        assert 'zh' in SUPPORTED_LANGS
        assert 'en' in SUPPORTED_LANGS

    def test_font_map_has_all_langs(self):
        for lang in SUPPORTED_LANGS:
            assert lang in FONT_MAP
            assert 'tk' in FONT_MAP[lang]
            assert 'mpl' in FONT_MAP[lang]

    def test_lang_display_names(self):
        for lang in SUPPORTED_LANGS:
            assert lang in LANG_DISPLAY_NAMES
