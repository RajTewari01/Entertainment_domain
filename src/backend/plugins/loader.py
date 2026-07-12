"""
Plugin Loader — Manifest-driven module registry.

Reads XML manifests from manifest/, resolves sys.path once,
and exposes declared modules as clean attributes.

Usage:
    from src.backend.plugins.loader import PluginLoader

    loader = PluginLoader()
    loader.bootstrap()

    # Access core modules directly
    Paths       = loader.core_service.paths.Paths
    fetch_key   = loader.core_service.api_config.fetch_apikey
    capture     = loader.core_service.capture_exceptions.capture_exceptions

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional


# ── Constants ────────────────────────────────────────────────────────

ROOT: Path = Path(__file__).parents[3].resolve().absolute()
MANIFEST_DIR: Path = Path(__file__).parent / "manifest"


# ── Data Structures ─────────────────────────────────────────────────

@dataclass
class PythonDependency:
    package: str
    version: str = ""


@dataclass
class PluginManifest:
    id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""
    description: str = ""
    enabled: bool = True
    priority: int = 100

    # name → dotted.module.path
    modules: Dict[str, str] = field(default_factory=dict)

    # third-party deps
    python_deps: List[PythonDependency] = field(default_factory=list)

    manifest_path: Optional[Path] = None


def _dotted_to_filepath(dotted_path: str) -> Path:
    """Convert 'src.backend.core.paths' → ROOT / 'src/backend/core/paths.py'."""
    parts = dotted_path.split(".")
    file_path = ROOT / Path(*parts).with_suffix(".py")
    if file_path.is_file():
        return file_path
    # Could be a package (__init__.py)
    package_path = ROOT / Path(*parts) / "__init__.py"
    if package_path.is_file():
        return package_path
    raise FileNotFoundError(
        f"Cannot resolve '{dotted_path}' — tried:\n"
        f"  {file_path}\n  {package_path}"
    )


def _load_module(dotted_path: str) -> ModuleType:
    """Load a module by dotted path using importlib.util — no sys.path needed."""
    file_path = _dotted_to_filepath(dotted_path)
    spec = importlib.util.spec_from_file_location(dotted_path, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for '{dotted_path}' at {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PluginNamespace:
    """
    Lightweight namespace that lazily loads modules on attribute access.

    loader.core_service.api_config  →  loads src/backend/core/api_config.py
    """

    def __init__(self, plugin_id: str, modules: Dict[str, str]) -> None:
        self._plugin_id = plugin_id
        self._module_map = modules       # name → dotted path
        self._cache: Dict[str, ModuleType] = {}

    def __getattr__(self, name: str) -> ModuleType:
        if name.startswith("_"):
            raise AttributeError(name)

        if name in self._cache:
            return self._cache[name]

        dotted_path = self._module_map.get(name)
        if dotted_path is None:
            available = ", ".join(self._module_map.keys())
            raise AttributeError(
                f"Plugin '{self._plugin_id}' has no module '{name}'. "
                f"Available: [{available}]"
            )

        module = _load_module(dotted_path)
        self._cache[name] = module
        return module

    def __repr__(self) -> str:
        loaded = list(self._cache.keys())
        available = list(self._module_map.keys())
        return f"PluginNamespace({self._plugin_id}, loaded={loaded}, available={available})"


# ── XML Parser ──────────────────────────────────────────────────────

def _text(element: Optional[ET.Element], default: str = "") -> str:
    if element is None:
        return default
    return (element.text or "").strip()


def _bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes")


def parse_manifest(xml_path: Path) -> PluginManifest:
    """Parse a single XML manifest into a PluginManifest."""

    tree = ET.parse(xml_path)
    root = tree.getroot()
    plugin_el = root.find("plugin")

    if plugin_el is None:
        raise ValueError(f"No <plugin> element in {xml_path}")

    manifest = PluginManifest(manifest_path=xml_path)
    manifest.id = plugin_el.get("id", "")

    # metadata
    meta = plugin_el.find("metadata")
    if meta is not None:
        manifest.name = _text(meta.find("name"))
        manifest.version = _text(meta.find("version"))
        manifest.author = _text(meta.find("author"))
        manifest.description = _text(meta.find("description"))

    # runtime
    runtime = plugin_el.find("runtime")
    if runtime is not None:
        manifest.enabled = _bool(_text(runtime.find("enabled"), "true"))
        manifest.priority = int(_text(runtime.find("priority"), "100"))

    # modules
    modules_el = plugin_el.find("modules")
    if modules_el is not None:
        for mod in modules_el.findall("module"):
            alias = mod.get("name", "")
            dotted = (mod.text or "").strip()
            if alias and dotted:
                manifest.modules[alias] = dotted

    # dependencies
    deps_el = plugin_el.find("dependencies")
    if deps_el is not None:
        for pkg in deps_el.findall("package"):
            manifest.python_deps.append(
                PythonDependency(
                    package=(pkg.text or "").strip(),
                    version=pkg.get("version", ""),
                )
            )

    return manifest


# ── Validation ──────────────────────────────────────────────────────

class PluginError(RuntimeError):
    """
    """


def validate_python_deps(manifest: PluginManifest) -> List[str]:
    """Return list of missing package names."""
    missing: List[str] = []
    for dep in manifest.python_deps:
        import_name = dep.package.replace("-", "_")
        if importlib.util.find_spec(import_name) is None:
            missing.append(dep.package)
    return missing


# ── Plugin Loader ───────────────────────────────────────────────────

class PluginLoader:
    """
    Discovers and loads plugin manifests from XML files.

    After bootstrap(), each plugin is accessible as an attribute:

        loader = PluginLoader().bootstrap()
        loader.core_service.api_config.fetch_apikey("pixels_api_key")
    """

    def __init__(self, manifest_dir: Path = MANIFEST_DIR) -> None:
        self._manifest_dir = manifest_dir
        self._manifests: Dict[str, PluginManifest] = {}
        self._namespaces: Dict[str, PluginNamespace] = {}

    # ── Discovery ────────────────────────────────────────────────

    def discover(self) -> List[PluginManifest]:
        self._manifests.clear()

        if not self._manifest_dir.exists():
            raise FileNotFoundError(f"Manifest dir not found: {self._manifest_dir}")

        for xml_file in sorted(self._manifest_dir.glob("*.xml")):
            manifest = parse_manifest(xml_file)

            if not manifest.enabled:
                continue

            if manifest.id in self._manifests:
                raise PluginError(
                    f"Duplicate plugin id '{manifest.id}' — "
                    f"{xml_file} vs {self._manifests[manifest.id].manifest_path}"
                )

            self._manifests[manifest.id] = manifest

        return list(self._manifests.values())

    # ── Validation ───────────────────────────────────────────────

    def validate(self) -> None:
        errors: List[str] = []
        for pid, manifest in self._manifests.items():
            missing = validate_python_deps(manifest)
            if missing:
                errors.append(f"[{pid}] Missing packages: {', '.join(missing)}")

        if errors:
            raise PluginError(
                "Plugin validation failed:\n  • " + "\n  • ".join(errors)
            )

    # ── Bootstrap ────────────────────────────────────────────────

    def bootstrap(self) -> 'PluginLoader':
        """Discover → validate → register namespaces. One call, done."""
        self.discover()
        self.validate()

        # Sort by priority (lower = first) and register namespaces
        ordered = sorted(self._manifests.values(), key=lambda m: m.priority)
        for manifest in ordered:
            self._namespaces[manifest.id] = PluginNamespace(
                plugin_id=manifest.id,
                modules=manifest.modules,
            )

        return self

    # ── Access ───────────────────────────────────────────────────

    def __getattr__(self, name: str) -> PluginNamespace:
        if name.startswith("_"):
            raise AttributeError(name)

        ns = self._namespaces.get(name)
        if ns is None:
            available = ", ".join(self._namespaces.keys())
            raise AttributeError(
                f"No plugin '{name}'. Available: [{available}]"
            )
        return ns

    def get(self, plugin_id: str) -> Optional[PluginNamespace]:
        return self._namespaces.get(plugin_id)

    @property
    def plugins(self) -> List[str]:
        return list(self._namespaces.keys())

    def __repr__(self) -> str:
        return f"PluginLoader(plugins={self.plugins})"
