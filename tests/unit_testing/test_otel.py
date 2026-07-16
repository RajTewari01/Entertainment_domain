"""
Unit tests for src.backend.core.otel

The otel module has heavy module-level imports that trigger the full plugin
bootstrap chain. We must inject mock modules into sys.modules BEFORE the
import ever happens, so conftest.py handles that via a session-scoped fixture.
"""
import sys
import pytest #type:ignore[import]
from unittest.mock import patch, MagicMock, call
from types import MappingProxyType, ModuleType
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT #type:ignore[import]
from opentelemetry.sdk.trace import TracerProvider #type:ignore[import]
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, ConsoleSpanExporter #type:ignore[import]
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter #type:ignore[import]


MOCK_CONFIG : MappingProxyType = MappingProxyType({
    'Name': 'Test_Entertainment',
    'stage': 'development',
    'Otel_Endpoint': 'https://localhost:4317',
    'Otel_Processor': 'Otel',
    'Otel_Exporter': 'Batch',
})


def _build_mock_loader() -> ModuleType:
    """
    Build a fake `src.backend.core.loader` module that provides
    loader.ConfigService.config.Config -> MOCK_CONFIG
    without triggering the real plugin bootstrap.
    """
    mock_config_module = MagicMock(spec=ModuleType)
    mock_config_module.config.Config = MOCK_CONFIG

    mock_loader = MagicMock(spec=ModuleType)
    mock_loader.ConfigService = mock_config_module
    return mock_loader


@pytest.fixture(autouse=True)
def otel_module():
    """
    Injects a mock loader into sys.modules before importing otel,
    then cleans up after each test to prevent state leakage.
    """
    mock_loader = _build_mock_loader()

    # Keys that may have been cached from a previous import
    otel_key = 'src.backend.core.otel'
    core_key = 'src.backend.core'

    # Remove any cached imports so otel re-imports cleanly
    saved_modules = {}
    for key in [otel_key, core_key]:
        if key in sys.modules:
            saved_modules[key] = sys.modules.pop(key)

    # Inject a fake core package that exposes our mock loader
    fake_core = ModuleType(core_key)
    fake_core.loader = mock_loader
    sys.modules[core_key] = fake_core

    # Now import otel — it will pick up our fake core.loader
    import src.backend.core.otel as otel #type:ignore[import]
    yield otel

    # Cleanup: remove our fakes, restore originals if any
    for key in [otel_key, core_key]:
        sys.modules.pop(key, None)
    for key, mod in saved_modules.items():
        sys.modules[key] = mod


# ================================================================
#  OtelConfig Tests
# ================================================================

@pytest.mark.unit
def test_otel_config_defaults(otel_module):
    """OtelConfig should populate fields from the module-level config values."""
    config = otel_module.OtelConfig()

    assert config.service_name == 'Test_Entertainment'
    assert config.environment == 'development'
    assert config.otel_endpoint == 'https://localhost:4317'


# ================================================================
#  setup_metadata Tests
# ================================================================

@pytest.mark.unit
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_setup_metadata_contains_service_name(mock_otlp, otel_module):
    """Resource should contain SERVICE_NAME and DEPLOYMENT_ENVIRONMENT."""
    instance = otel_module.OtelSetup()
    resource : Resource = instance.setup

    attrs = dict(resource.attributes)
    assert attrs[SERVICE_NAME] == 'Test_Entertainment'
    assert attrs[DEPLOYMENT_ENVIRONMENT] == 'development'


# ================================================================
#  setup_exporter Tests — Processor Mode x Exporter Mode matrix
# ================================================================

@pytest.mark.unit
@pytest.mark.parametrize("processor_mode, exporter_mode, expected_count, expected_types", [
    ("Console", "Batch",  1, [BatchSpanProcessor]),
    ("Console", "Simple", 1, [SimpleSpanProcessor]),
    ("Otel",    "Batch",  1, [BatchSpanProcessor]),
    ("Otel",    "Simple", 1, [SimpleSpanProcessor]),
    ("Both",    "Batch",  2, [BatchSpanProcessor, BatchSpanProcessor]),
    ("Both",    "Simple", 2, [SimpleSpanProcessor, SimpleSpanProcessor]),
])
@patch('opentelemetry.trace.set_tracer_provider')
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_setup_exporter_processor_matrix(
    mock_otlp, mock_set_provider,
    otel_module, processor_mode, exporter_mode, expected_count, expected_types
):
    """
    Verifies that setup_exporter wires the correct number and type of
    span processors for every combination of ProcessorMode x ExporterMode.
    """
    instance = otel_module.OtelSetup()
    instance.processor = processor_mode
    instance.exporter = exporter_mode

    with patch.object(TracerProvider, 'add_span_processor') as mock_add:
        instance.setup_exporter()

        assert mock_add.call_count == expected_count, (
            f"Expected {expected_count} processor(s) for mode={processor_mode}/{exporter_mode}, "
            f"got {mock_add.call_count}"
        )

        for i, (call_args, expected_type) in enumerate(zip(mock_add.call_args_list, expected_types)):
            processor = call_args[0][0]
            assert isinstance(processor, expected_type), (
                f"Processor #{i} should be {expected_type.__name__}, "
                f"got {type(processor).__name__}"
            )


# ================================================================
#  setup_exporter sets global tracer provider
# ================================================================

@pytest.mark.unit
@patch('opentelemetry.trace.set_tracer_provider')
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_setup_exporter_sets_global_provider(mock_otlp, mock_set_provider, otel_module):
    """setup_exporter must call trace.set_tracer_provider exactly once."""
    instance = otel_module.OtelSetup()
    instance.setup_exporter()

    mock_set_provider.assert_called_once()
    provider = mock_set_provider.call_args[0][0]
    assert isinstance(provider, TracerProvider)


# ================================================================
#  setup_exporter returns self (fluent chaining)
# ================================================================

@pytest.mark.unit
@patch('opentelemetry.trace.set_tracer_provider')
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_setup_exporter_returns_self(mock_otlp, mock_set_provider, otel_module):
    """setup_exporter should return self to allow method chaining."""
    instance = otel_module.OtelSetup()
    result = instance.setup_exporter()

    assert result is instance


# ================================================================
#  init_otel_span_exporter uses configured endpoint
# ================================================================

@pytest.mark.unit
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_otlp_exporter_uses_configured_endpoint(mock_otlp, otel_module):
    """OTLPSpanExporter must be created with the endpoint from config."""
    instance = otel_module.OtelSetup()

    mock_otlp.assert_called_with(endpoint='https://localhost:4317')


# ================================================================
#  init_tracer_provider returns TracerProvider with Resource
# ================================================================

@pytest.mark.unit
@patch.object(OTLPSpanExporter, '__init__', return_value=None)
def test_init_tracer_provider_returns_provider(mock_otlp, otel_module):
    """init_tracer_provider should return a TracerProvider."""
    instance = otel_module.OtelSetup()
    provider = instance.init_tracer_provider()

    assert isinstance(provider, TracerProvider)
