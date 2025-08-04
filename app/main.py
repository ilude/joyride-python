import atexit
import logging
import os
import signal
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from pydantic import BaseModel

import swimmies
from swimmies import GossipNode

from .dns_server import DNSServerManager
from .dns_sync_manager import DNSSyncManager
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
app.config["HOSTS_DIRECTORY"] = os.getenv("HOSTS_DIRECTORY", "/app/hosts")
app.config["SEMANTIC_VERSION"] = os.getenv("SEMANTIC_VERSION", "dev")
app.config["ENABLE_DNS_SYNC"] = os.getenv("ENABLE_DNS_SYNC", "true").lower() == "true"
app.config["DISCOVERY_PORT"] = int(os.getenv("DISCOVERY_PORT", 8889))
app.config["SWIM_PORT"] = int(os.getenv("SWIM_PORT", 8890))
app.config["NODE_ID"] = os.getenv("NODE_ID", f"joyride-{os.getpid()}")


# PID file management
def get_pid_file_path():
    """Get the standard PID file path for the application."""
    # Use /tmp for development environment since /var/run requires root
    return "/tmp/joyride-dns.pid"


def create_pid_file():
    """Create PID file with current process ID."""
    pid_file = get_pid_file_path()
    try:
        with open(pid_file, "w") as f:
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

# Initialize DNS sync manager if enabled
dns_sync_manager = None
if app.config["ENABLE_DNS_SYNC"]:
    try:
        dns_sync_manager = DNSSyncManager(
            node_id=app.config["NODE_ID"],
            service_name="joyride-dns",
            discovery_port=app.config["DISCOVERY_PORT"],
            swim_port=app.config["SWIM_PORT"],
            dns_callback=None,  # Will be set after dns_record_callback is defined
            host_ip=app.config["HOSTIP"],
        )
        logger.info("DNS sync manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize DNS sync manager: {e}")
        dns_sync_manager = None


def dns_record_callback(action: str, hostname: str, ip_address: str) -> None:
    """Callback for Docker monitor and DNS sync to update DNS records."""
    if action == "add":
        dns_server.add_record(hostname, ip_address)
        # Also sync to other nodes if DNS sync is enabled
        if dns_sync_manager:
            dns_sync_manager.add_dns_record(hostname, ip_address)
    elif action == "remove":
        dns_server.remove_record(hostname)
        # Also sync removal to other nodes if DNS sync is enabled
        if dns_sync_manager:
            dns_sync_manager.remove_dns_record(hostname)


# Set DNS callback for sync manager now that it's defined
if dns_sync_manager:
    dns_sync_manager.dns_callback = dns_record_callback


docker_monitor = DockerEventMonitor(dns_record_callback, app.config["HOSTIP"])

# Initialize hosts file monitor if directory is specified
hosts_monitor = None
if app.config["HOSTS_DIRECTORY"]:
    hosts_monitor = HostsFileMonitor(
        app.config["HOSTS_DIRECTORY"], dns_record_callback, poll_interval=5.0
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

    # Get DNS cluster information if available
    dns_cluster_info = None
    if dns_sync_manager:
        try:
            dns_cluster_info = dns_sync_manager.get_cluster_status()
        except Exception as e:
            logger.warning(f"Failed to get DNS cluster status: {e}")
            dns_cluster_info = {"error": str(e)}

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
        dns_cluster_info=dns_cluster_info,
        dns_sync_enabled=app.config["ENABLE_DNS_SYNC"],
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
        "records_count": len(hosts_monitor.get_current_records())
        if hosts_monitor
        else 0,
    }

    # Add DNS sync cluster info if enabled
    dns_sync_info = {
        "enabled": dns_sync_manager is not None,
        "running": dns_sync_manager.running if dns_sync_manager else False,
    }
    if dns_sync_manager:
        dns_sync_info.update(dns_sync_manager.get_cluster_status())

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

    # Add DNS sync info to response
    response_dict = response.model_dump()
    response_dict["dns_sync_cluster"] = dns_sync_info

    return jsonify(response_dict)


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


@app.route("/dns/cluster")
def dns_cluster_status():
    """Get DNS cluster status and node information"""
    if not dns_sync_manager:
        return (
            jsonify(
                {"status": "disabled", "message": "DNS synchronization is not enabled"}
            ),
            503,
        )

    cluster_status = dns_sync_manager.get_cluster_status()
    return jsonify({"status": "success", "cluster": cluster_status})


@app.route("/dns/sync", methods=["POST"])
def force_dns_sync():
    """Force immediate DNS record synchronization across the cluster"""
    if not dns_sync_manager:
        return (
            jsonify(
                {"status": "error", "message": "DNS synchronization is not enabled"}
            ),
            503,
        )

    try:
        dns_sync_manager.force_sync()
        return jsonify(
            {"status": "success", "message": "DNS synchronization initiated"}
        )
    except Exception as e:
        logger.error(f"Error during forced DNS sync: {e}")
        return (
            jsonify(
                {"status": "error", "message": f"Failed to sync DNS records: {str(e)}"}
            ),
            500,
        )


# Initialize services when app starts
# Global flag to prevent double initialization
_services_initialized = False


def initialize_services() -> None:
    """Initialize DNS server, Docker monitor, and DNS sync manager."""
    global _services_initialized

    if _services_initialized:
        logger.warning("Services already initialized, skipping...")
        return

    try:
        dns_server.start()
        docker_monitor.start()

        # Start DNS sync manager if enabled
        if dns_sync_manager:
            dns_sync_manager.start()

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

    # Stop DNS sync manager if it exists
    if dns_sync_manager:
        dns_sync_manager.stop()

    # Stop hosts monitor if it exists
    if hosts_monitor:
        hosts_monitor.stop()

    remove_pid_file()


atexit.register(cleanup_services)


def main():
    """Main entry point for Joyride DNS service."""
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize swimmies library components
    logger.info(f"Starting Joyride with swimmies library v{swimmies.__version__}")
    gossip_node = GossipNode("joyride-main")
    logger.info(f"Created gossip node: {gossip_node.node_id}")

    # Initialize services only when running as main and not in testing mode
    testing_mode = (
        app.config.get("TESTING", False) or os.getenv("TESTING", "").lower() == "true"
    )

    # Flask reloader sets WERKZEUG_RUN_MAIN=true in the reloaded process
    is_reloaded_process = os.getenv("WERKZEUG_RUN_MAIN") == "true"

    # Initialize services only in the reloaded process or when not using reloader
    if not testing_mode and (is_reloaded_process or not app.config["DEBUG"]):
        # Create PID file only in main process when not in debug mode
        if not app.config["DEBUG"]:
            create_pid_file()
        initialize_services()

    # Start the Flask application
    logger.info(
        f"Starting Joyride DNS service on {app.config['HOST']}:{app.config['PORT']}"
    )
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
