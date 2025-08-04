#!/usr/bin/env python3
"""
Joyride DNS Service Entry Point

This module provides the main entry point for the Joyride DNS service.
It can be run directly or via the 'joyride' command after installation.
"""

import sys
from app.main import app, initialize_services, create_pid_file, cleanup_services
import atexit
import logging
import os
import signal
import swimmies
from swimmies import GossipNode

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup_services()
    sys.exit(0)


def main():
    """Main entry point for Joyride DNS service."""
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Register cleanup on exit
    atexit.register(cleanup_services)
    
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
    logger.info(f"Starting Joyride DNS service on {app.config['HOST']}:{app.config['PORT']}")
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
