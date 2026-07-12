import importlib
from typing import Final
from types import ModuleType
from pathlib import Path
import importlib.util as imp
import sys
from .base import StaticConfig as StaticState

def _ancestor(target:str|None=None)->Path:
    target = StaticState().Name or "Entertainment_domain"
    cwd = Path(__file__).resolve()

    while cwd.name != target:
        if cwd.parent == cwd:
            raise ValueError(f"Could not find ancestor '{target}'")

        cwd = cwd.parent
    return cwd

def _load_module()->ModuleType:
    basedir : Final[Path] = _ancestor()
    plugins_path : Final[Path] = basedir / "src/backend/plugins/loader.py"
    spec_path : str = "src.backend.plugins.loader"
    spec = imp.spec_from_file_location(spec_path,plugins_path)
    
    assert spec is not None,"Couldnt find the plugins loader"
    assert spec.loader is not None, "Plugin loader has no valid loader"
    
    _plugins = imp.module_from_spec(spec)
    sys.modules[spec.name] = _plugins

    spec.loader.exec_module(_plugins)
    return _plugins.PluginLoader().bootstrap()

loader = _load_module()

