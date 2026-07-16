from __future__ import annotations
from pydantic_settings import BaseSettings #type:ignore[import]
from typing import Final,overload,TypeAlias,Optional,Literal
from importlib.metadata import version
from pathlib import Path

AncestorMode : TypeAlias = Literal['path','depth']

@overload
def _get_ancestor(
    target : str,
    mode : AncestorMode = 'depth'
) -> int | None:...

@overload
def _get_ancestor(
    target : str,
    mode : AncestorMode = 'path'
) -> Path | None:...

def _get_ancestor(
    target : str|None = None,
    mode : AncestorMode = 'path'
)->Path | int | None:

    target_name : Final[str] = target or "Entertainment_domain"
    current : Final[Path] = Path(__file__).resolve()
    cwd : Path = current
    counter : int = 0
    
    while cwd.name != target_name:
        if cwd.parent == cwd:
            raise ValueError('Target directory not found.')
        counter += 1
        cwd = cwd.parent
    
    match mode:
        case 'depth':
            return counter
        case 'path':
            return cwd
        case _:
            raise ValueError(f'Invalid mode,\'{mode}\' is not available.')

class StaticConfig:
    
    Name : Final[str] = str(_get_ancestor(mode='path').name)
    Company_Email : str = 'tewari765@gmail.com'
    Contact_Info : str = '+91-6297446078'
    Owner : str = 'Biswadeep Tewari'
    
    try:
        Version : str =  version('Entertainment_domain')
    except:    
        Version : str = '0.0.0'
    

class BaseConfig(BaseSettings):
    
    stage : Literal['development','staging','production']
    Debug : bool
    Grafana_Endpoint : str
    Ensure_Files : bool
    Deferred_Execution : bool

    # Sessionware_Token : str|bytes]
    Sessionware_Algorithm : str
    Cookie_Samesite : Literal['Lax','Strict','None']
    Cookie_Secure : bool
    Refresh_token_limit : float
    Access_token_limit : float
    Jwt_Algorithm : str

    Canary_percentage : float|int
    Canary_Enabled : bool
    
    Otel_Processor : Literal['Console','Otel','Both']
    Otel_Exporter : Literal['Batch','Simple']
    Otel_Endpoint : str 

    Cleaning_Worker_Thread_Count : int
    Cleaning_Max_Worker : int

    Dns_Endpoint : str
    

    


    



    
