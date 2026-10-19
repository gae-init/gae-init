"""Telemetry module for configuring OpenTelemetry."""

import os

import flask
import google.auth
import google.auth.transport.requests
import grpc
from google.auth.transport.grpc import AuthMetadataPlugin
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

import config


def setup_opentelemetry(app: flask.Flask) -> None:
    """Initialize and configure OpenTelemetry for the Flask app."""
    # use 100% sampling for local dev; otherwise use environment variables
    if config.DEBUG:
        os.environ["OTEL_TRACES_SAMPLER"] = "always_on"

    # get credentials and create auth metadata plugin
    credentials, project_id = google.auth.default()
    request = google.auth.transport.requests.Request()
    auth_metadata_plugin = AuthMetadataPlugin(credentials=credentials, request=request)

    # configure the gRPC channel with authentication
    channel_creds = grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(auth_metadata_plugin),
    )

    # initialize and configure trace provider
    cloud_exporter = OTLPSpanExporter(
        credentials=channel_creds, endpoint="https://telemetry.googleapis.com:443"
    )
    resource = Resource.create(
        {
            SERVICE_NAME: config.APPLICATION_ID or project_id or "unknown-service",
            "gcp.project_id": project_id or "unknown-project",
        }
    )
    tracer_provider = TracerProvider(resource=resource)

    # add Google Cloud Trace Exporter with Batch Processor
    tracer_provider.add_span_processor(BatchSpanProcessor(cloud_exporter))
    trace.set_tracer_provider(tracer_provider)

    # automatically instrument Flask app, excluding static paths under /p/
    FlaskInstrumentor().instrument_app(
        app, excluded_urls=r"^https?://[^/]+/p/.*, .*\.(js|css|ico)$"
    )
