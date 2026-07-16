from __future__ import annotations
from pydantic import BaseModel,Field
from types import MappingProxyType
from pydantic_settings import BaseSettings #type:ignore[import]
from opentelemetry import trace, metrics #type:ignore[import]
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT #type:ignore[import]
from opentelemetry.sdk.trace import TracerProvider #type:ignore[import]
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor,ConsoleSpanExporter #type:ignore[import]
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter #type:ignore[import]
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor #type:ignore[import]
from prometheus_client import make_asgi_app #type:ignore[import]
from typing import Literal,Final,TypeAlias
from types import ModuleType
from . import loader

ConfigModule : ModuleType = loader.ConfigService
ConfigLoader : ModuleType = ConfigModule.config
Config : MappingProxyType[str, str] = ConfigLoader.Config

service_name : Final[str] = Config['Name']
environment : Final[str] = Config['stage']
endpoint : Final[str] = Config['Otel_Endpoint']
processor_type : Final[str] = Config['Otel_Processor']
exporter_type : Final[str] = Config['Otel_Exporter']

ProcessorMode : TypeAlias = Literal['Console','Otel','Both']
ExporterMode : TypeAlias = Literal['Batch','Simple']
SpanProcessorType : TypeAlias = BatchSpanProcessor | SimpleSpanProcessor

class OtelConfig(BaseSettings):
    service_name : str = Field(default=service_name)
    environment : str = Field(default=environment)
    otel_endpoint : str = Field(default=endpoint)
    otel_processor : ProcessorMode = Field(default_factory=lambda:processor_type)
    otel_exporter : ExporterMode = Field(default_factory=lambda:exporter_type)

class OtelSetup(OtelConfig):
    def __init__(self)->None:
        self.config : Final[OtelConfig] = OtelConfig()
        self.setup : Final[Resource] = self.setup_metadata()
        self.init_otel_exporter : Final[OTLPSpanExporter] = self.init_otel_span_exporter()
        self.processor : Final[ProcessorMode] = self.config.otel_processor
        self.exporter : Final[ExporterMode] = self.config.otel_exporter
    
    def setup_metadata(self) -> Resource:
        return Resource.create({
            SERVICE_NAME : self.config.service_name,
            DEPLOYMENT_ENVIRONMENT : self.config.environment
        })

    def init_tracer_provider(self) -> TracerProvider:
        provider : TracerProvider = TracerProvider(self.setup)
        return provider
    
    def init_otel_span_exporter(self) -> OTLPSpanExporter:
        return OTLPSpanExporter(endpoint=self.config.otel_endpoint)

    def setup_exporter(self) -> 'OtelSetup':
        provider : TracerProvider = self.init_tracer_provider()
        is_batch : bool = self.exporter == 'Batch'

        match self.processor:
            case 'Console':
                console_exporter : ConsoleSpanExporter = ConsoleSpanExporter()
                processor : SpanProcessorType = BatchSpanProcessor(console_exporter) if is_batch else SimpleSpanProcessor(console_exporter)
                provider.add_span_processor(processor)
            case 'Otel':
                otlp_processor : SpanProcessorType = BatchSpanProcessor(self.init_otel_exporter) if is_batch else SimpleSpanProcessor(self.init_otel_exporter)
                provider.add_span_processor(otlp_processor)
            case 'Both':
                console_exporter : ConsoleSpanExporter = ConsoleSpanExporter()
                console_processor : SpanProcessorType = BatchSpanProcessor(console_exporter) if is_batch else SimpleSpanProcessor(console_exporter)
                provider.add_span_processor(console_processor)
                otlp_processor : SpanProcessorType = BatchSpanProcessor(self.init_otel_exporter) if is_batch else SimpleSpanProcessor(self.init_otel_exporter)
                provider.add_span_processor(otlp_processor)

        trace.set_tracer_provider(provider)
        return self

otel : OtelSetup = OtelSetup()
otel.setup_exporter()


if __name__ == '__main__':
    print(Config,service_name,environment,endpoint,exporter_type,file=__import__('sys').stdout,sep='\n',end='\n')


