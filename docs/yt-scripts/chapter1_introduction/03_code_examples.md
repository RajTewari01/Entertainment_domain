# Chapter 1: Code Examples

*Display these clean, real-world code snippets on screen to provide concrete examples during your introductory theory. These are pulled directly from your project's source code.*

## Snippet 1: The Power of Makefiles & `.PHONY`
*Explain how simple shortcuts replace complex commands, and explicitly break down the `.PHONY` keyword.*

```makefile
# We declare our targets as .PHONY so Make knows these are 'actions', not 'files'.
.PHONY : clear_cache
clear_cache :
	python -m shortcuts.Makefile.clr_cache

.PHONY : move_logs
move_logs :
	python -m shortcuts.Makefile.mov_logs
```

## Snippet 2: Why We Use Python for Scripts Instead of Bash
*Show them the `mov_logs.py` script. Explain that a simple bash `mv *.log data/logs` crashes if a file with the same name already exists. We wrote this script to handle UUID collision generation!*

```python
from pathlib import Path
from typing import Final
from shutil import rmtree, move
import uuid

# Find our project root dynamically
def _ancestor(target: str | None = None) -> Path:
    target = "Entertainment_domain"
    cwd = Path(__file__).resolve()

    while cwd.name != target:
        if cwd.parent == cwd:
            raise ValueError(f"Could not find ancestor '{target}'")
        cwd = cwd.parent
    return cwd

BaseDir: Final[Path] = _ancestor()
LogsDir: Final[Path] = BaseDir / "data" / "logs"

LogsDir.mkdir(parents=True, exist_ok=True)

# Recursively find all logs, and safely move them without crashing on collisions
for log in BaseDir.rglob('*.log'):
    # Don't move logs that are already in the correct folder!
    if log.parent == LogsDir:
        continue
        
    dest: Path = LogsDir / log.name
    
    # COLLISION HANDLING: If a file with this name already exists, 
    # generate a random 4-character hex UUID to prevent overwriting!
    while dest.exists():
        name: str = f'{log.stem}_{uuid.uuid4().hex[:4]}{log.suffix}'
        renamed: Path = LogsDir / f'{name}'
        dest = renamed
        print(f'Renamed {log} -> {name}')

    move(str(log), str(dest))
    print(f'Moved : .\{log.name} -> {dest.relative_to(BaseDir)}')

print('All logs moved successfully')
```
