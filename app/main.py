import atexit
import logging
import os
import signal
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from pydantic import BaseModel

from .dns_server import DNSServerManager
from .docker_monitor import DockerEventMonitor
from .hosts_monitor import HostsFileMonitor


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
    hosts_monitor: Dict[str, Any]
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
app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")
app.config["DNS_PORT"] = int(os.getenv("DNS_PORT", 5353))
app.config["DNS_BIND"] = os.getenv("DNS_BIND_ADDRESS", "0.0.0.0")
app.config["HOSTIP"] = os.getenv("HOSTIP", "127.0.0.1")
app.config["HOSTS_DIRECTORY"] = os.getenv("HOSTS_DIRECTORY", "")
app.config["SEMANTIC_VERSION"] = os.getenv("SEMANTIC_VERSION", "dev")


# PID file management
def get_pid_file_path():
    """Get the standard PID file path for the application."""
    # Use /tmp for development environment since /var/run requires root
    return "/tmp/joyride-dns.pid"


def create_pid_file():
    """Create PID file with current process ID."""
    pid_file = get_pid_file_path()
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        logger.debug(f"Created PID file: {pid_file}")
        return pid_file
    except Exception as e:
        logger.warning(f"Could not create PID file {pid_file}: {e}")
        return None


def remove_pid_file():
    """Remove PID file if it exists."""
    pid_file = get_pid_file_path()
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
            logger.debug(f"Removed PID file: {pid_file}")
    except Exception as e:
        logger.warning(f"Could not remove PID file {pid_file}: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.debug(f"Received signal {signum}, shutting down gracefully...")
    cleanup_services()
    remove_pid_file()
    exit(0)


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


docker_monitor = DockerEventMonitor(dns_record_callback, app.config["HOSTIP"])

# Initialize hosts file monitor if directory is specified
hosts_monitor = None
if app.config["HOSTS_DIRECTORY"]:
    hosts_monitor = HostsFileMonitor(
        app.config["HOSTS_DIRECTORY"],
        dns_record_callback,
        poll_interval=5.0
    )


@app.route("/")
def status_page():
    """Main status page"""
    dns_records = dns_server.get_records()
    hosts_info = None
    if hosts_monitor:
        hosts_info = {
            "directory": app.config["HOSTS_DIRECTORY"],
            "running": hosts_monitor.running,
            "records_count": len(hosts_monitor.get_current_records()),
        }
    
    return render_template(
        "status.html",
        service_name=app.config["SERVICE_NAME"],
        version=app.config["SEMANTIC_VERSION"],
        environment=app.config["ENVIRONMENT"],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        host=app.config["HOST"],
        port=app.config["PORT"],
        dns_records=dns_records,
        dns_port=app.config["DNS_PORT"],
        hosts_info=hosts_info,
    )


@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    response = HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service=app.config["SERVICE_NAME"],
        version=app.config["SEMANTIC_VERSION"],
    )
    return jsonify(response.model_dump())


@app.route("/status")
def detailed_status():
    """Detailed status information in JSON format"""
    hosts_monitor_info = {
        "enabled": hosts_monitor is not None,
        "directory": app.config["HOSTS_DIRECTORY"] if hosts_monitor else None,
        "running": hosts_monitor.running if hosts_monitor else False,
        "records_count": len(hosts_monitor.get_current_records()) if hosts_monitor else 0,
    }
    
    response = DetailedStatusResponse(
        status="running",
        timestamp=datetime.now().isoformat(),
        service=app.config["SERVICE_NAME"],
        version=app.config["SEMANTIC_VERSION"],
        environment=app.config["ENVIRONMENT"],
        dns_server={
            "port": app.config["DNS_PORT"],
            "bind_address": app.config["DNS_BIND"],
            "running": True,
        },
        docker_monitor={"running": True},
        hosts_monitor=hosts_monitor_info,
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
        dns_server.start()
        docker_monitor.start()
        
        # Start hosts monitor if configured
        if hosts_monitor:
            hosts_monitor.start()
            
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
    logger.debug("Shutting down services...")
    docker_monitor.stop()
    dns_server.stop()
    
    # Stop hosts monitor if it exists
    if hosts_monitor:
        hosts_monitor.stop()
        
    remove_pid_file()


atexit.register(cleanup_services)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize services only when running as main and not in Flask reloader
    testing_mode = (
        app.config.get("TESTING", False) or os.getenv("TESTING", "").lower() == "true"
    )

    # Flask reloader sets WERKZEUG_RUN_MAIN=true in the reloaded process
    is_reloaded_process = os.getenv("WERKZEUG_RUN_MAIN") == "true"

    if not testing_mode and not is_reloaded_process:
        # Create PID file
        create_pid_file()
        initialize_services()

    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
