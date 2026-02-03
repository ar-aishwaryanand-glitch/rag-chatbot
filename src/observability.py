"""OpenTelemetry observability integration for RAG system.

Provides:
- Distributed tracing for RAG operations
- Metrics collection (latency, throughput, errors)
- Logging integration
- Context propagation
- Custom instrumentation decorators
"""

import os
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

# Import config
from .config import Config


class ObservabilityManager:
    """Manages OpenTelemetry instrumentation for the RAG system."""

    _instance: Optional['ObservabilityManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern to ensure single observability instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize observability (only once due to singleton)."""
        if not self._initialized:
            self._setup_observability()
            ObservabilityManager._initialized = True

    def _setup_observability(self):
        """Set up OpenTelemetry providers and exporters."""
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: Config.OTEL_SERVICE_NAME,
            SERVICE_VERSION: "1.0.0",
            "deployment.environment": Config.OTEL_ENVIRONMENT,
        })

        # Setup tracing
        self._setup_tracing(resource)

        # Setup metrics
        self._setup_metrics(resource)

        print(f"🔭 OpenTelemetry initialized: {Config.OTEL_SERVICE_NAME}")
        print(f"   Environment: {Config.OTEL_ENVIRONMENT}")
        print(f"   Exporter: {Config.OTEL_EXPORTER_TYPE}")

    def _setup_tracing(self, resource: Resource):
        """Configure tracing with appropriate exporter."""
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Add span processor based on exporter type
        if Config.OTEL_EXPORTER_TYPE == "console":
            # Console exporter for development
            span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            tracer_provider.add_span_processor(span_processor)

        elif Config.OTEL_EXPORTER_TYPE == "otlp":
            # OTLP exporter for production (Jaeger, Honeycomb, etc.)
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

                otlp_exporter = OTLPSpanExporter(
                    endpoint=Config.OTEL_EXPORTER_ENDPOINT,
                    headers=self._get_exporter_headers(),
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(span_processor)

            except ImportError:
                print("⚠️  Warning: opentelemetry-exporter-otlp not installed")
                print("   Install with: pip install opentelemetry-exporter-otlp")
                # Fallback to console
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
                tracer_provider.add_span_processor(span_processor)

        elif Config.OTEL_EXPORTER_TYPE == "jaeger":
            # Jaeger exporter
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                jaeger_exporter = JaegerExporter(
                    agent_host_name=Config.JAEGER_HOST,
                    agent_port=Config.JAEGER_PORT,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                tracer_provider.add_span_processor(span_processor)

            except ImportError:
                print("⚠️  Warning: opentelemetry-exporter-jaeger not installed")
                print("   Install with: pip install opentelemetry-exporter-jaeger")
                # Fallback to console
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
                tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Get tracer for this service
        self.tracer = trace.get_tracer(__name__)

    def _setup_metrics(self, resource: Resource):
        """Configure metrics with appropriate exporter."""
        # Create metric exporter
        if Config.OTEL_EXPORTER_TYPE == "console":
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=60000  # Export every 60 seconds
            )
        elif Config.OTEL_EXPORTER_TYPE == "otlp":
            try:
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

                otlp_exporter = OTLPMetricExporter(
                    endpoint=Config.OTEL_EXPORTER_ENDPOINT,
                    headers=self._get_exporter_headers(),
                )
                metric_reader = PeriodicExportingMetricReader(
                    otlp_exporter,
                    export_interval_millis=60000
                )
            except ImportError:
                print("⚠️  Warning: Using console metrics exporter (OTLP not available)")
                metric_reader = PeriodicExportingMetricReader(
                    ConsoleMetricExporter(),
                    export_interval_millis=60000
                )
        else:
            # Default to console
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=60000
            )

        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )

        # Set global meter provider
        metrics.set_meter_provider(meter_provider)

        # Get meter for this service
        self.meter = metrics.get_meter(__name__)

        # Create RAG-specific metrics
        self._create_metrics()

    def _get_exporter_headers(self) -> Dict[str, str]:
        """Get headers for OTLP exporter (e.g., API keys)."""
        headers = {}

        if Config.OTEL_EXPORTER_HEADERS:
            # Parse headers from environment variable
            # Format: "key1=value1,key2=value2"
            for header in Config.OTEL_EXPORTER_HEADERS.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        return headers

    def _create_metrics(self):
        """Create custom metrics for RAG operations."""
        # Counters
        self.query_counter = self.meter.create_counter(
            name="rag.queries.total",
            description="Total number of RAG queries",
            unit="1"
        )

        self.document_counter = self.meter.create_counter(
            name="rag.documents.indexed",
            description="Total number of documents indexed",
            unit="1"
        )

        self.error_counter = self.meter.create_counter(
            name="rag.errors.total",
            description="Total number of errors",
            unit="1"
        )

        self.agent_action_counter = self.meter.create_counter(
            name="rag.agent.actions.total",
            description="Total number of agent actions",
            unit="1"
        )

        # Histograms for latency
        self.query_duration = self.meter.create_histogram(
            name="rag.query.duration",
            description="RAG query duration",
            unit="ms"
        )

        self.retrieval_duration = self.meter.create_histogram(
            name="rag.retrieval.duration",
            description="Document retrieval duration",
            unit="ms"
        )

        self.generation_duration = self.meter.create_histogram(
            name="rag.generation.duration",
            description="Answer generation duration",
            unit="ms"
        )

        self.agent_action_duration = self.meter.create_histogram(
            name="rag.agent.action.duration",
            description="Agent action duration",
            unit="ms"
        )

        # Up/Down counters
        self.active_queries = self.meter.create_up_down_counter(
            name="rag.queries.active",
            description="Number of active queries",
            unit="1"
        )

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        record_exception: bool = True
    ):
        """
        Context manager for tracing operations with automatic error handling.

        Args:
            operation_name: Name of the operation to trace
            attributes: Additional span attributes
            record_exception: Whether to record exceptions in the span

        Yields:
            Span object for adding additional attributes during execution

        Example:
            with observability.trace_operation("query_processing", {"query": "test"}):
                # Your code here
                pass
        """
        with self.tracer.start_as_current_span(operation_name) as span:
            # Add custom attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as e:
                if record_exception:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            else:
                span.set_status(Status(StatusCode.OK))

    def record_metric(
        self,
        metric_name: str,
        value: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Record a custom metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
            attributes: Additional metric attributes
        """
        metric_attributes = attributes or {}

        if metric_name == "query":
            self.query_counter.add(1, metric_attributes)
            self.query_duration.record(value, metric_attributes)
        elif metric_name == "retrieval":
            self.retrieval_duration.record(value, metric_attributes)
        elif metric_name == "generation":
            self.generation_duration.record(value, metric_attributes)
        elif metric_name == "document_indexed":
            self.document_counter.add(1, metric_attributes)
        elif metric_name == "error":
            self.error_counter.add(1, metric_attributes)
        elif metric_name == "agent_action":
            self.agent_action_counter.add(1, metric_attributes)
            self.agent_action_duration.record(value, metric_attributes)


# Singleton instance
_observability_manager: Optional[ObservabilityManager] = None


def get_observability() -> ObservabilityManager:
    """
    Get or create the observability manager singleton.

    Returns:
        ObservabilityManager instance
    """
    global _observability_manager

    if not Config.ENABLE_OBSERVABILITY:
        # Return a no-op manager if observability is disabled
        return NoOpObservabilityManager()

    if _observability_manager is None:
        _observability_manager = ObservabilityManager()

    return _observability_manager


class NoOpObservabilityManager:
    """No-op implementation when observability is disabled."""

    def __init__(self):
        self.tracer = None
        self.meter = None

    @contextmanager
    def trace_operation(self, operation_name: str, attributes=None, record_exception=True):
        """No-op context manager."""
        yield None

    def record_metric(self, metric_name: str, value: float, attributes=None):
        """No-op metric recording."""
        pass


# Decorator for tracing functions
def traced(operation_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to automatically trace function calls.

    Args:
        operation_name: Custom operation name (defaults to function name)
        attributes: Additional span attributes

    Example:
        @traced("process_query")
        def process_query(query: str):
            return query.upper()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            observability = get_observability()

            # Use function name if operation_name not provided
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            # Merge attributes
            span_attributes = attributes or {}

            # Add function info
            span_attributes["code.function"] = func.__name__
            span_attributes["code.namespace"] = func.__module__

            with observability.trace_operation(op_name, span_attributes):
                return func(*args, **kwargs)

        return wrapper
    return decorator


# Decorator for measuring latency
def measured(metric_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to automatically measure function latency.

    Args:
        metric_name: Name of the metric to record
        attributes: Additional metric attributes

    Example:
        @measured("query_processing")
        def process_query(query: str):
            return query.upper()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            observability = get_observability()

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Merge attributes
                metric_attributes = attributes or {}
                metric_attributes["function"] = func.__name__

                observability.record_metric(metric_name, duration_ms, metric_attributes)

        return wrapper
    return decorator


# Combined decorator for tracing and measuring
def instrumented(
    operation_name: Optional[str] = None,
    metric_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator to both trace and measure function calls.

    Args:
        operation_name: Custom operation name for tracing
        metric_name: Name of the metric to record
        attributes: Additional attributes for span and metric

    Example:
        @instrumented("process_query", "query")
        def process_query(query: str):
            return query.upper()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            observability = get_observability()

            # Use function name if operation_name not provided
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            metric = metric_name or "function_call"

            # Merge attributes
            span_attributes = attributes or {}
            span_attributes["code.function"] = func.__name__
            span_attributes["code.namespace"] = func.__module__

            start_time = time.time()

            with observability.trace_operation(op_name, span_attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.time() - start_time) * 1000

                    # Record latency in span
                    if span:
                        span.set_attribute("duration_ms", duration_ms)

                    # Record metric
                    observability.record_metric(metric, duration_ms, span_attributes)

        return wrapper
    return decorator
