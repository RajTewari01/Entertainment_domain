from pathlib import Path
from shutil import rmtree
from typing import Final


def _ancestor(target:str|None=None)->Path:
    target = "Entertainment_domain"
    cwd = Path(__file__).resolve()

    while cwd.name != target:
        if cwd.parent == cwd:
            raise ValueError(f"Could not find ancestor '{target}'")

        cwd = cwd.parent
    return cwd

Base : Final[Path] = _ancestor()
Cache : Final[Path] = Base / ".cache"
if Cache.exists():
    rmtree(Cache,ignore_errors=True)
    print("Cache cleared")
(Cache).mkdir(parents=True,exist_ok=True)
print(".cache directory created")