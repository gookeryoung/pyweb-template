"""pyweb_template 基础冒烟测试."""

from __future__ import annotations

import pyweb_template


def test_version_is_string() -> None:
    """__version__ 应为非空字符串."""
    assert isinstance(pyweb_template.__version__, str)
    assert pyweb_template.__version__


def test_package_importable() -> None:
    """包应可正常导入."""
    assert hasattr(pyweb_template, "__all__")
    assert "__version__" in pyweb_template.__all__
