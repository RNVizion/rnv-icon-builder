"""
RNV Icon Builder - Multi-Resolution ICO File Creator

A comprehensive PyQt6 desktop application for creating multi-resolution
ICO files from PNG images with advanced features including image adjustments,
batch processing, theme support, and detailed ICO analysis.

Packages:
    core: Business logic & data processing
    ui: User interface components & dialogs
    utils: Utilities, configuration & helpers
"""

from utils.config import APP_VERSION, APP_NAME

__version__ = APP_VERSION
__app_name__ = APP_NAME


# ─────────────────────────────────────────────────────────────────────────
# Lazy re-export of IconBuilderApp / main from the sibling RNV_Icon_Builder.py
# ─────────────────────────────────────────────────────────────────────────
# The project layout has a folder named RNV_Icon_Builder (this package) AND
# a file named RNV_Icon_Builder.py inside it. Python imports the package
# first, so `import RNV_Icon_Builder` would normally not see IconBuilderApp.
#
# PEP 562's module-level __getattr__ lets us load RNV_Icon_Builder.py only
# when someone actually requests IconBuilderApp or main — keeping
# `from RNV_Icon_Builder import APP_VERSION` cheap (no QApplication setup,
# no widget construction at import time).

_main_module_cache = None


def _load_main_module():
    """Load RNV_Icon_Builder.py from disk as a standalone module."""
    global _main_module_cache
    if _main_module_cache is not None:
        return _main_module_cache

    import importlib.util
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(here, "RNV_Icon_Builder.py")
    if not os.path.exists(main_py):
        return None

    spec = importlib.util.spec_from_file_location(
        "_rnv_icon_builder_main", main_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _main_module_cache = mod
    return mod


def __getattr__(name):
    """Lazy-load main-module attributes on first access (PEP 562)."""
    if name in ("IconBuilderApp", "main"):
        mod = _load_main_module()
        if mod is not None and hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
