import atexit
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from .dns_server import DNSServerManager
from .docker_monitor import DockerEventMonitor

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['HOST'] = os.getenv('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.getenv('FLASK_PORT', 5000))
app.config['SERVICE_NAME'] = os.getenv('SERVICE_NAME', 'Joyride DNS')
app.config['SERVICE_VERSION'] = os.getenv('SERVICE_VERSION', '1.0.0')
app.config['ENVIRONMENT'] = os.getenv('ENVIRONMENT', 'development')
app.config['DNS_PORT'] = int(os.getenv('DNS_PORT', 53))
app.config['DNS_BIND'] = os.getenv('DNS_BIND_ADDRESS', '0.0.0.0')

# Initialize DNS server and Docker monitor
dns_server = DNSServerManager(
    bind_address=app.config['DNS_BIND'],
    bind_port=app.config['DNS_PORT']
)


def dns_record_callback(action: str, hostname: str, ip_address: str) -> None:
    """Callback for Docker monitor to update DNS records."""
    if action == 'add':
        dns_server.add_record(hostname, ip_address)
    elif action == 'remove':
        dns_server.remove_record(hostname)


docker_monitor = DockerEventMonitor(dns_record_callback)


@app.route('/')
def status_page():
    """Main status page"""
    dns_records = dns_server.get_records()
    return render_template(
        'status.html',
        service_name=app.config['SERVICE_NAME'],
        version=app.config['SERVICE_VERSION'],
        environment=app.config['ENVIRONMENT'],
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        host=app.config['HOST'],
        port=app.config['PORT'],
        dns_records=dns_records,
        dns_port=app.config['DNS_PORT']
    )


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': app.config['SERVICE_NAME'],
        'version': app.config['SERVICE_VERSION'],
        'environment': app.config['ENVIRONMENT'],
        'timestamp': datetime.now().isoformat()
    })


@app.route('/status')
def detailed_status():
    """Detailed status information in JSON format"""
    return jsonify({
        'service': {
            'name': app.config['SERVICE_NAME'],
            'version': app.config['SERVICE_VERSION'],
            'environment': app.config['ENVIRONMENT'],
            'debug': app.config['DEBUG']
        },
        'system': {
            'timestamp': datetime.now().isoformat(),
            'host': app.config['HOST'],
            'port': app.config['PORT']
        },
        'dns': {
            'port': app.config['DNS_PORT'],
            'bind_address': app.config['DNS_BIND'],
            'records': dns_server.get_records()
        },
        'status': 'running'
    })


@app.route('/dns/records')
def dns_records():
    """Get current DNS records"""
    return jsonify({
        'records': dns_server.get_records(),
        'count': len(dns_server.get_records())
    })


# Initialize services when app starts
def initialize_services():
    """Initialize DNS server and Docker monitor."""
    try:
        dns_server.start()
        docker_monitor.start()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


# Initialize services on module import (for production)
# In testing, services won't start due to TESTING config or environment
testing_mode = (app.config.get('TESTING', False) or
                os.getenv('TESTING', '').lower() == 'true')
if not testing_mode:
    initialize_services()


# Cleanup on shutdown
def cleanup_services():
    """Cleanup services on shutdown."""
    logger.info("Shutting down services...")
    docker_monitor.stop()
    dns_server.stop()


atexit.register(cleanup_services)


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
