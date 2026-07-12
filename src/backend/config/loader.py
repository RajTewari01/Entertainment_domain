
from __future__ import annotations
from typing import Pattern,Final,overload,Literal,Any,Tuple,TypeAlias,Dict
from functools import cache,lru_cache
from types import MappingProxyType
from yaml.nodes import ScalarNode
from pathlib import Path
from sys import stdout
import yaml
import re
import os
from . import loader as plugins_loader

BaseSettingsConfig = plugins_loader.ConfigService.base.BaseConfig
StaticConfig      = plugins_loader.ConfigService.base.StaticConfig
DevConfig          = plugins_loader.ConfigService.dev.DevConfig
StagingConfig      = plugins_loader.ConfigService.stage.StagingConfig
ProdConfig         = plugins_loader.ConfigService.prod.ProdConfig

ConfigType : TypeAlias = StagingConfig | DevConfig | ProdConfig

EnvPattern : Pattern[str] = re.compile(r'\${(?P<key>[A-Za-z][A-Za-z0-9\_-]*)(:=(?P<value>[^}]*))?}')
SoftPattern : Pattern[str] = re.compile(r'\${.*}.*')

def yaml_constructor(
    loader : yaml.SafeLoader,
    node : ScalarNode
) -> str:
    value = loader.construct_scalar(node)

    def _subtitute(match:re.Match[str])-> str:
        key = match.group('key')
        value = match.group('value') if match.group('value') else ''
        return os.environ.get(key,value)

    EnvString : str = EnvPattern.sub(_subtitute,value)    
    return EnvString

yaml.SafeLoader.add_implicit_resolver('!env', SoftPattern,['$'])
yaml.SafeLoader.add_constructor('!env', yaml_constructor)

def _ancestor(target : str | None = None)->Path:
    
    target : Final[str] = StaticConfig().Name or 'Entertainment_domain'
    cwd : Final[Path] = Path(__file__).resolve()
    current : Path = cwd

    while current.name != target:
        if current == current.parent:
            raise ValueError('Cannot find the directory')
        current = current.parent
    
    return current

BaseDir : Final[Path] = _ancestor()
ConfigYml : Final[Path] = BaseDir / "config/app_config/AppConfig.yml"


class ConfigSetup:
    @classmethod
    @overload
    def config(cls,get_dict:Literal[True]=True)->MappingProxyType[str,Any]:
        ...
    @classmethod
    @overload
    def config(cls,get_dict:Literal[False]=False)->Tuple[StaticConfig,ConfigType]:
        ...
    @classmethod
    def config(cls,get_dict:bool=True)->Tuple[StaticConfig,ConfigType] | MappingProxyType[str,Any]:
        try:
            with open(ConfigYml,'r',encoding='utf-8') as file:
                env : str = yaml.safe_load(file)
                stage : Final[str] = env.get("app", {}).get("stage", "development")
        except Exception as e:
            raise RuntimeError(str(e)) from e
        
        match stage:
            case 'development':
                cfg = DevConfig()
            case "staging":
                cfg = StagingConfig()
            case "production":
                cfg = ProdConfig()
            case _:
                raise ValueError(f"Unknown stage: {stage}")
        
        if get_dict:

            StaticDict : Dict[str,Any] = {k:v for k,v in vars(StaticConfig).items() if not k.startswith('_')}
            CfgDict : Dict[str,Any] = cfg.model_dump()
            MergedDict : Dict[str,Any] = StaticDict | CfgDict
            ImmutableDict : MappingProxyType = MappingProxyType(MergedDict)

            return ImmutableDict
        return(
            StaticConfig(),cfg
        )
    
    @classmethod
    @lru_cache(maxsize=10)
    def _get_env(cls) ->  MappingProxyType[str,Any]:
        return cls.config(get_dict=True)


Config : MappingProxyType[str,Any] = ConfigSetup.config()


if __name__ == '__main__':
    print(Config,file=stdout)

    







