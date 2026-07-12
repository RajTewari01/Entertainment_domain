from pathlib import Path
from typing import Final
from shutil import move
from sys import stdout
import uuid

counter : float = 0.0

def _ancestor(target:str|None=None)->Path:
    target = "Entertainment_domain"
    cwd = Path(__file__).resolve()

    while cwd.name != target:
        if cwd.parent == cwd:
            raise ValueError(f"Could not find ancestor '{target}'")

        cwd = cwd.parent
    return cwd

BaseDir : Final[Path] = _ancestor()
LogsDir : Final[Path] = BaseDir / "data" / "logs"


LogsDir.mkdir(parents=True,exist_ok=True)
for log in BaseDir.rglob('*.log'):
    if log.parent == LogsDir:
        continue
    
    dest : Path = LogsDir / log.name
    while dest.exists():
        name : str = f'{log.stem}_{uuid.uuid4().hex[:4]}{log.suffix}'
        renamed : Path = LogsDir / f'{name}'
        dest = renamed
        print(f'Renamed : {log} -> {name}',file=stdout)

    counter += 1.0
    move(str(log),str(dest))
    print(f'Moved : .\\{log.name} -> {dest.relative_to(BaseDir)}',file=stdout)

print(f'All logs moved successfully\nTotal file moved : {counter}' 
        if counter >= 1.0
        else 'No logs to move',file=stdout)
