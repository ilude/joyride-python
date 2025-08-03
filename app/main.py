import atexit
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from pydantic import BaseModel

from .dns_server import DNSServerManager
from .docker_monitor import DockerEventMonitor


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    service: str
    version: str


class DetailedStatusResponse(BaseModel):
    """Detailed status response model."""

    status: str
    timestamp: str
    service: str
    version: str
    environment: str
    dns_server: Dict[str, Any]
    docker_monitor: Dict[str, Any]
    uptime: str


class DNSRecord(BaseModel):
    """DNS record model."""

    hostname: str
    ip_address: str
    ttl: int = 300


class DNSRecordsResponse(BaseModel):
    """DNS records response model."""

    status: str
    total_records: int
    records: List[DNSRecord]


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "False").lower() == "true"
app.config["HOST"] = os.getenv("FLASK_HOST", "0.0.0.0")
app.config["PORT"] = int(os.getenv("FLASK_PORT", 5000))
app.config["SERVICE_NAME"] = os.getenv("SERVICE_NAME", "Joyride DNS")
app.config["SERVICE_VERSION"] = os.getenv("SERVICE_VERSION", "1.0.0")
app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")
app.config["DNS_PORT"] = int(os.getenv("DNS_PORT", 53))
app.config["DNS_BIND"] = os.getenv("DNS_BIND_ADDRESS", "0.0.0.0")

# Initialize DNS server and Docker monitor
dns_server = DNSServerManager(
    bind_address=app.config["DNS_BIND"], bind_port=app.config["DNS_PORT"]
)


def dns_record_callback(action: str, hostname: str, ip_address: str) -> None:
    """Callback for Docker monitor to update DNS records."""
    if action == "add":
        dns_server.add_record(hostname, ip_address)
    elif action == "remove":
        dns_server.remove_record(hostname)


docker_monitor = DockerEventMonitor(dns_record_callback)


@app.route("/")
def status_page():
    """Main status page"""
    dns_records = dns_server.get_records()
    return render_template(
        "status.html",
        service_name=app.config["SERVICE_NAME"],
        version=app.config["SERVICE_VERSION"],
        environment=app.config["ENVIRONMENT"],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        host=app.config["HOST"],
        port=app.config["PORT"],
        dns_records=dns_records,
        dns_port=app.config["DNS_PORT"],
    )


@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    response = HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service=app.config["SERVICE_NAME"],
        version=app.config["SERVICE_VERSION"],
    )
    return jsonify(response.model_dump())


@app.route("/status")
def detailed_status():
    """Detailed status information in JSON format"""
    response = DetailedStatusResponse(
        status="running",
        timestamp=datetime.now().isoformat(),
        service=app.config["SERVICE_NAME"],
        version=app.config["SERVICE_VERSION"],
        environment=app.config["ENVIRONMENT"],
        dns_server={
            "port": app.config["DNS_PORT"],
            "bind_address": app.config["DNS_BIND"],
            "running": True,
        },
        docker_monitor={"running": True},
        uptime="N/A",
    )
    return jsonify(response.model_dump())


@app.route("/dns/records")
def dns_records():
    """Get current DNS records"""
    records = dns_server.get_records()
    dns_record_list = [
        DNSRecord(hostname=hostname, ip_address=ip, ttl=300)
        for hostname, ip in records.items()
    ]
    response = DNSRecordsResponse(
        status="success",
        total_records=len(records),
        records=dns_record_list,
    )
    return jsonify(response.model_dump())


# Initialize services when app starts
# Global flag to prevent double initialization
_services_initialized = False


def initialize_services() -> None:
    """Initialize DNS server and Docker monitor."""
    global _services_initialized

    if _services_initialized:
        logger.warning("Services already initialized, skipping...")
        return

    try:
        logger.info("Initializing services...")
        dns_server.start()
        docker_monitor.start()
        _services_initialized = True
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


# Services will be initialized when running as main
# In testing, services won't start due to TESTING config or environment


# Cleanup on shutdown
def cleanup_services():
    """Cleanup services on shutdown."""
    logger.info("Shutting down services...")
    docker_monitor.stop()
    dns_server.stop()


atexit.register(cleanup_services)


if __name__ == "__main__":
    # Initialize services only when running as main and not in Flask reloader
    testing_mode = (
        app.config.get("TESTING", False) or os.getenv("TESTING", "").lower() == "true"
    )

    # Flask reloader sets WERKZEUG_RUN_MAIN=true in the reloaded process
    is_reloaded_process = os.getenv("WERKZEUG_RUN_MAIN") == "true"

    if not testing_mode and not is_reloaded_process:
        initialize_services()

    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
