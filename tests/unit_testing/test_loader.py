import pytest #type:ignore[import]
from unittest.mock import patch, mock_open
from types import MappingProxyType
from src.backend.config.loader import ConfigSetup,_get_env #type:ignore[import]

@pytest.mark.unit
@pytest.mark.parametrize("stage", ["development", "staging", "production"])
@patch('src.backend.config.loader.yaml.safe_load')
@patch('builtins.open', new_callable=mock_open)
def test_config_loads_all_stages_immutable(mock_file, mock_yaml, stage):
    mock_yaml.return_value = {"app": {"stage": stage}}
    result = ConfigSetup.config(get_dict=True)
    
    assert isinstance(result, MappingProxyType), f"Failed for {stage}: Not a MappingProxyType"
    assert result.get('stage') == stage, f"Failed for {stage}: Stage mismatch in dictionary"

@pytest.mark.unit
@pytest.mark.parametrize("stage, expected_class", [
    ("development", "DevConfig"),
    ("staging", "StagingConfig"),
    ("production", "ProdConfig")
])
@patch('src.backend.config.loader.yaml.safe_load')
@patch('builtins.open', new_callable=mock_open)
def test_config_loads_all_stages_tuple(mock_file, mock_yaml, stage, expected_class):
    mock_yaml.return_value = {"app": {"stage": stage}}
    static_cfg, env_cfg = ConfigSetup.config(get_dict=False)
    
    assert env_cfg.__class__.__name__ == expected_class, f"Failed for {stage}: Expected {expected_class}"
    assert static_cfg.__class__.__name__ == 'StaticConfig', "First element should be StaticConfig"

@pytest.mark.unit
@patch('src.backend.config.loader.yaml.safe_load')
@patch('builtins.open', new_callable=mock_open)
def test_config_invalid_stage_raises_error(mock_file, mock_yaml):
    # Testing that an unknown stage throws a ValueError
    mock_yaml.return_value = {"app": {"stage": "testing"}}
    
    with pytest.raises(ValueError, match="Unknown stage: testing"):
        ConfigSetup.config()

@pytest.mark.unit
@patch.object(ConfigSetup, 'config')
def test_get_env_caching(mock_config):

    mock_config.return_value = MappingProxyType({"cached": True})

    _get_env.cache_clear()
    res1 = _get_env()
    res2 = _get_env()
    
    assert res1 is res2, "The returned object should be the exact same cached instance"
    mock_config.assert_called_once_with(get_dict=True)