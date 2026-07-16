from pydantic_settings import BaseSettings #type:ignore[import]
from typing import Literal
from types import ModuleType
from . import loader

loader : ModuleType = loader.ConfigService
BaseSettingsConfig = loader.base.BaseSettings

class StagingConfig(BaseSettings):
    stage : Literal['staging'] = 'staging'
    Debug : bool = True
    Grafana_Endpoint : str = "https://grafana.staging.internal:8080"
    Ensure_Files : bool = True
    Deferred_Execution : bool = True

    Sessionware_Algorithm : str = "HS256"
    Cookie_Samesite : Literal['Lax','Strict','None'] = "Strict"
    Cookie_Secure : bool = True
    Refresh_token_limit : float = 15 * 24 * 60 * 60  
    Access_token_limit : float = 15 * 60 #seconds
    Jwt_Algorithm : str = "RS256"

    Canary_percentage : float|int = 0.0
    Canary_Enabled : bool = False
    
    Otel_Processor : Literal['Console','Otel','Both'] = 'Both'
    Otel_Exporter : Literal['Batch','Simple'] = 'Batch'
    Otel_Endpoint : str = "http://otel-collector-staging:4317"

    Cleaning_Worker_Thread_Count : int = 2
    Cleaning_Max_Worker : int = 4

    Sora_Api_Endpoint : str = "https://api.staging.sora-entertainment.com"