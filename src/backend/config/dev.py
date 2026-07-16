from pydantic_settings import BaseSettings #type:ignore[import]
from typing import Literal
from . import loader


class DevConfig(BaseSettings):
    
    stage : Literal['development'] = 'development'
    Debug : bool = True
    Grafana_Endpoint : str = "https://grafana:8080"
    Ensure_Files : bool = True
    Deferred_Execution : bool = True

    # Sessionware_Token : str = ""
    Sessionware_Algorithm : str = "HS256"
    Cookie_Samesite : Literal['Lax','Strict','None'] = "Lax"
    Cookie_Secure : bool = True
    Refresh_token_limit : float = 15 * 24 * 60 * 60  
    Access_token_limit : float = 15 * 60 #seconds
    Jwt_Algorithm : str = "RS256"

    Canary_percentage : float|int =0.0
    Canary_Enabled : bool = False
    
    Otel_Processor : Literal['Console','Otel','Both'] = 'Otel'
    Otel_Exporter : Literal['Batch','Simple'] = 'Batch'
    Otel_Endpoint : str = "https://localhost:4317"

    Cleaning_Worker_Thread_Count : int = 1
    Cleaning_Max_Worker : int = 2

    Dns_Endpoint : str = "https://localhost:8000"