import logging
import threading
from socketserver import BaseRequestHandler, ThreadingUDPServer
from typing import Dict, Optional

from dnslib import QTYPE, RR, A, DNSHeader, DNSRecord

logger = logging.getLogger(__name__)


class DNSRequestHandler(BaseRequestHandler):
    """Handles individual DNS requests."""

    def __init__(self, dns_records: Dict[str, str], *args, **kwargs):
        self.dns_records = dns_records
        super().__init__(*args, **kwargs)

    def handle(self):
        """Handle incoming DNS request."""
        try:
            data = self.request[0]
            socket = self.request[1]

            # Parse DNS request
            request = DNSRecord.parse(data)
            qname = str(request.q.qname).rstrip(".")
            qtype = request.q.qtype

            logger.debug(f"DNS query: {qname} ({QTYPE[qtype]})")

            # Create response
            reply = DNSRecord(
                DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q
            )

            # Add answer if we have the record
            if qtype == QTYPE.A and qname in self.dns_records:
                ip_address = self.dns_records[qname]
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip_address), ttl=60))
                logger.debug(f"Resolved {qname} -> {ip_address}")
            else:
                logger.debug(f"No record found for {qname}")

            # Send response
            socket.sendto(reply.pack(), self.client_address)

        except Exception as e:
            logger.error(f"Error handling DNS request: {e}")


class DNSServerManager:
    """Manages the DNS server lifecycle and record updates."""

    def __init__(self, bind_address: str = "0.0.0.0", bind_port: int = 53):
        self.bind_address = bind_address
        self.bind_port = bind_port
        self.dns_records: Dict[str, str] = {}
        self.server: Optional[ThreadingUDPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the DNS server in a background thread."""
        if self.server is not None:
            logger.warning("DNS server already running")
            return

        try:
            # Create custom handler class with access to dns_records
            def create_handler(*args, **kwargs):
                return DNSRequestHandler(self.dns_records, *args, **kwargs)

            self.server = ThreadingUDPServer(
                (self.bind_address, self.bind_port), create_handler
            )
            self.server_thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.server_thread.start()

            logger.info(f"DNS server started on {self.bind_address}:{self.bind_port}")
        except Exception as e:
            logger.error(f"Failed to start DNS server: {e}")
            raise

    def stop(self) -> None:
        """Stop the DNS server."""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            logger.debug("DNS server stopped")

    def add_record(self, hostname: str, ip_address: str) -> None:
        """Add or update a DNS record."""
        with self._lock:
            self.dns_records[hostname] = ip_address
            logger.info(f"Added DNS record: {hostname} -> {ip_address}")

    def remove_record(self, hostname: str) -> None:
        """Remove a DNS record."""
        with self._lock:
            if hostname in self.dns_records:
                del self.dns_records[hostname]
                logger.info(f"Removed DNS record: {hostname}")

    def get_records(self) -> Dict[str, str]:
        """Get a copy of all DNS records."""
        with self._lock:
            return self.dns_records.copy()
