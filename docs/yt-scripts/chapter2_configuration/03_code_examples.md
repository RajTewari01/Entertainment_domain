# Chapter 2: Code Examples

*Display these specific blocks on screen to explain Pydantic, YAML parsing, and Pytest.*

## Snippet 1: The Custom PyYAML Environment Loader

```python
import yaml
import os
import re

# This allows our YAML to dynamically read from the Docker container's environment
def yaml_constructor(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> str:
    value = loader.construct_scalar(node)

    def _substitute(match: re.Match[str]) -> str:
        key = match.group('key')
        default = match.group('default') or ''
        # Pull from the environment, or fallback to default
        return os.environ.get(key, default)

    # Replaces strings like ${DB_URL:=localhost} magically!
    pattern = re.compile(r'\$\{(?P<key>[^}:]+)(?:[:=]+(?P<default>[^}]+))?\}')
    return pattern.sub(_substitute, value)

yaml.SafeLoader.add_implicit_resolver('!env', re.compile(r'.*\$\{.*\}.*'), None)
yaml.SafeLoader.add_constructor('!env', yaml_constructor)
```

## Snippet 2: The Power of Pydantic BaseSettings

```python
from pydantic_settings import BaseSettings
from typing import Literal

class DevConfig(BaseSettings):
    # Pydantic STRICTLY enforces these types on startup
    stage: Literal['development'] = 'development'
    Debug: bool = True
    
    # Security Enforced at the Class Level
    Cookie_Samesite: Literal['Lax', 'Strict', 'None'] = "Lax"
    Cookie_Secure: bool = True
```

## Snippet 3: Pytest Parameterization Highlight

```python
import pytest
from unittest.mock import patch, mock_open
from src.backend.config.loader import ConfigSetup

# Write ONE test, run it THREE times automatically for each environment!
@pytest.mark.unit
@pytest.mark.parametrize("stage, expected_class", [
    ("development", "DevConfig"),
    ("staging", "StagingConfig"),
    ("production", "ProdConfig")
])
@patch('src.backend.config.loader.yaml.safe_load')
@patch('builtins.open', new_callable=mock_open)
def test_config_loads_all_stages(mock_file, mock_yaml, stage, expected_class):
    
    # Fake the YAML file contents so we don't touch the hard drive
    mock_yaml.return_value = {"app": {"stage": stage}}
    static_cfg, env_cfg = ConfigSetup.config(get_dict=False)
    
    # Verify it loaded the correct Pydantic class
    assert env_cfg.__class__.__name__ == expected_class
```
