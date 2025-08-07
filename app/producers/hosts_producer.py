"""Hosts file event producer for monitoring hosts file changes."""

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.joyride.events import EventBus
from app.producers.event_producer import EventProducer
from app.producers.hosts_events import (
    HostsBackupEvent,
    HostsEntryEvent,
    HostsFileEvent,
    HostsFileEventType,
    HostsFileModificationEvent,
    HostsParseErrorEvent,
)

logger = logging.getLogger(__name__)


class HostsFileEventProducer(EventProducer):
    """Producer for hosts file events."""

    def __init__(
        self,
        event_bus: EventBus,
        producer_name: str = "hosts_file_event_producer",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize hosts file event producer.

        Args:
            event_bus: Event bus to publish events to
            producer_name: Name of this producer instance
            config: Configuration options including:
                - hosts_file_paths: List of hosts files to monitor (default: [/etc/hosts])
                - polling_interval: Polling interval in seconds (default: 5)
                - create_backups: Create backups on changes (default: True)
                - backup_directory: Directory for backups (default: /tmp/hosts_backups)
                - max_backups: Maximum number of backups to keep (default: 10)
                - parse_entries: Parse individual entries (default: True)
        """
        super().__init__(event_bus, producer_name, config)

        # Configuration
        default_hosts = ["/etc/hosts"]
        self._hosts_file_paths = config.get("hosts_file_paths", default_hosts)
        self._polling_interval = config.get("polling_interval", 5)
        self._create_backups = config.get("create_backups", True)
        self._backup_directory = Path(
            config.get("backup_directory", "/tmp/hosts_backups")
        )
        self._max_backups = config.get("max_backups", 10)
        self._parse_entries = config.get("parse_entries", True)

        # State tracking
        self._file_states: Dict[str, Dict[str, Any]] = {}
        self._last_checksums: Dict[str, str] = {}
        self._file_watchers: Dict[str, Any] = {}

        # Supported event types
        self._supported_event_types = {
            event_type.value for event_type in HostsFileEventType
        }

    async def _start_producer(self) -> None:
        """Start the hosts file event producer."""
        logger.info(f"Starting hosts file monitoring for: {self._hosts_file_paths}")

        # Create backup directory if needed
        if self._create_backups:
            self._backup_directory.mkdir(parents=True, exist_ok=True)

        # Initialize file states
        await self._initialize_file_states()

    async def _stop_producer(self) -> None:
        """Stop the hosts file event producer."""
        logger.info("Stopping hosts file event producer")

        # Cleanup any file watchers
        self._file_watchers.clear()

    async def _run_producer(self) -> None:
        """Main producer loop for hosts file monitoring."""
        logger.info("Starting hosts file monitoring loop")

        while self._is_running:
            try:
                # Check each monitored hosts file
                for file_path in self._hosts_file_paths:
                    await self._check_hosts_file(file_path)

                # Clean up old backups
                if self._create_backups:
                    await self._cleanup_old_backups()

                # Wait for next check
                await asyncio.sleep(self._polling_interval)

            except asyncio.CancelledError:
                logger.info("Hosts file monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in hosts file monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _initialize_file_states(self) -> None:
        """Initialize state tracking for monitored files."""
        for file_path in self._hosts_file_paths:
            try:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    checksum = await self._calculate_file_checksum(file_path)

                    self._file_states[file_path] = {
                        "exists": True,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:],
                        "checksum": checksum,
                    }
                    self._last_checksums[file_path] = checksum

                    logger.info(f"Initialized monitoring for: {file_path}")
                else:
                    self._file_states[file_path] = {"exists": False}
                    logger.warning(f"Hosts file does not exist: {file_path}")

            except Exception as e:
                logger.error(f"Error initializing state for {file_path}: {e}")
                self._file_states[file_path] = {"exists": False, "error": str(e)}

    async def _check_hosts_file(self, file_path: str) -> None:
        """Check a hosts file for changes."""
        try:
            current_exists = os.path.exists(file_path)
            previous_state = self._file_states.get(file_path, {})
            previous_exists = previous_state.get("exists", False)

            # Handle file creation
            if current_exists and not previous_exists:
                await self._handle_file_created(file_path)
                return

            # Handle file deletion
            if not current_exists and previous_exists:
                await self._handle_file_deleted(file_path)
                return

            # Handle file modification
            if current_exists:
                await self._check_file_modification(file_path)

        except Exception as e:
            logger.error(f"Error checking hosts file {file_path}: {e}")

    async def _handle_file_created(self, file_path: str) -> None:
        """Handle hosts file creation."""
        try:
            stat = os.stat(file_path)
            checksum = await self._calculate_file_checksum(file_path)

            # Update state
            self._file_states[file_path] = {
                "exists": True,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:],
                "checksum": checksum,
            }
            self._last_checksums[file_path] = checksum

            # Publish event
            event = HostsFileEvent(
                hosts_event_type=HostsFileEventType.FILE_CREATED,
                source=self._producer_name,
                file_path=file_path,
                file_size=stat.st_size,
                file_permissions=oct(stat.st_mode)[-3:],
                filesystem_event=True,
            )

            await self.publish_event(event)
            logger.info(f"Hosts file created: {file_path}")

        except Exception as e:
            logger.error(f"Error handling file creation {file_path}: {e}")

    async def _handle_file_deleted(self, file_path: str) -> None:
        """Handle hosts file deletion."""
        try:
            # Update state
            previous_state = self._file_states.get(file_path, {})
            self._file_states[file_path] = {"exists": False}

            # Publish event
            event = HostsFileEvent(
                hosts_event_type=HostsFileEventType.FILE_DELETED,
                source=self._producer_name,
                file_path=file_path,
                file_size=previous_state.get("size"),
                filesystem_event=True,
            )

            await self.publish_event(event)
            logger.warning(f"Hosts file deleted: {file_path}")

        except Exception as e:
            logger.error(f"Error handling file deletion {file_path}: {e}")

    async def _check_file_modification(self, file_path: str) -> None:
        """Check for file modifications."""
        try:
            current_stat = os.stat(file_path)
            current_checksum = await self._calculate_file_checksum(file_path)
            previous_state = self._file_states.get(file_path, {})
            previous_checksum = self._last_checksums.get(file_path, "")

            # Check if file has been modified
            if current_checksum != previous_checksum:
                await self._handle_file_modified(
                    file_path, previous_state, current_stat, current_checksum
                )

        except Exception as e:
            logger.error(f"Error checking file modification {file_path}: {e}")

    async def _handle_file_modified(
        self,
        file_path: str,
        previous_state: Dict,
        current_stat: os.stat_result,
        current_checksum: str,
    ) -> None:
        """Handle hosts file modification."""
        try:
            # Create backup if enabled
            backup_path = None
            if self._create_backups:
                backup_path = await self._create_backup(file_path)

            # Analyze changes
            changes = await self._analyze_file_changes(file_path, previous_state)

            # Update state
            self._file_states[file_path] = {
                "exists": True,
                "size": current_stat.st_size,
                "mtime": current_stat.st_mtime,
                "permissions": oct(current_stat.st_mode)[-3:],
                "checksum": current_checksum,
            }
            self._last_checksums[file_path] = current_checksum

            # Publish modification event
            event = HostsFileModificationEvent(
                hosts_event_type=HostsFileEventType.FILE_MODIFIED,
                source=self._producer_name,
                file_path=file_path,
                file_size=current_stat.st_size,
                file_permissions=oct(current_stat.st_mode)[-3:],
                filesystem_event=True,
                modification_type="content_change",
                lines_added=changes.get("lines_added", 0),
                lines_removed=changes.get("lines_removed", 0),
                lines_modified=changes.get("lines_modified", 0),
                checksum_before=previous_state.get("checksum"),
                checksum_after=current_checksum,
                backup_created=backup_path is not None,
                backup_path=backup_path,
            )

            await self.publish_event(event)

            # Parse and publish entry events if enabled
            if self._parse_entries:
                await self._parse_and_publish_entry_events(file_path)

            logger.info(f"Hosts file modified: {file_path}")

        except Exception as e:
            logger.error(f"Error handling file modification {file_path}: {e}")

    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""

    async def _analyze_file_changes(
        self, file_path: str, previous_state: Dict
    ) -> Dict[str, int]:
        """Analyze what changed in the file."""
        try:
            # TODO: Implement detailed diff analysis
            # For now, return basic change counts
            current_size = os.path.getsize(file_path)
            previous_size = previous_state.get("size", 0)

            # Estimate line changes based on size difference
            size_diff = abs(current_size - previous_size)
            estimated_line_changes = size_diff // 20  # Assume ~20 chars per line

            return {
                "lines_added": estimated_line_changes
                if current_size > previous_size
                else 0,
                "lines_removed": estimated_line_changes
                if current_size < previous_size
                else 0,
                "lines_modified": 1 if size_diff > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Error analyzing changes for {file_path}: {e}")
            return {"lines_added": 0, "lines_removed": 0, "lines_modified": 0}

    async def _create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of hosts file."""
        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{Path(file_path).name}_{timestamp}.backup"
            backup_path = self._backup_directory / backup_name

            # Copy file
            import shutil

            shutil.copy2(file_path, backup_path)

            # Publish backup event
            backup_event = HostsBackupEvent(
                hosts_event_type=HostsFileEventType.BACKUP_CREATED,
                source=self._producer_name,
                file_path=file_path,
                backup_path=str(backup_path),
                backup_size=os.path.getsize(backup_path),
                operation_type="backup",
                triggered_by="file_modification",
                auto_generated=True,
                operation_successful=True,
            )

            await self.publish_event(backup_event)
            return str(backup_path)

        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None

    async def _cleanup_old_backups(self) -> None:
        """Remove old backup files."""
        try:
            if not self._backup_directory.exists():
                return

            backup_files = list(self._backup_directory.glob("*.backup"))
            if len(backup_files) <= self._max_backups:
                return

            # Sort by modification time and remove oldest
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            files_to_remove = backup_files[: -self._max_backups]

            for backup_file in files_to_remove:
                backup_file.unlink()
                logger.debug(f"Removed old backup: {backup_file}")

        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

    async def _parse_and_publish_entry_events(self, file_path: str) -> None:
        """Parse hosts file and publish entry events."""
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    # Parse hosts entry
                    parts = line.split()
                    if len(parts) >= 2:
                        ip_address = parts[0]
                        hostnames = parts[1:]

                        # Publish entry event
                        event = HostsEntryEvent(
                            hosts_event_type=HostsFileEventType.ENTRY_ADDED,
                            source=self._producer_name,
                            file_path=file_path,
                            ip_address=ip_address,
                            hostnames=hostnames,
                            line_number=line_num,
                            original_line=line,
                        )

                        await self.publish_event(event)

                except Exception as e:
                    # Publish parse error event
                    error_event = HostsParseErrorEvent(
                        hosts_event_type=HostsFileEventType.PARSE_ERROR,
                        source=self._producer_name,
                        file_path=file_path,
                        error_type="parse_error",
                        error_message=str(e),
                        line_number=line_num,
                        line_content=line,
                        can_recover=True,
                        suggested_fix="Check IP address and hostname format",
                    )

                    await self.publish_event(error_event)

        except Exception as e:
            logger.error(f"Error parsing hosts file {file_path}: {e}")

    def get_supported_event_types(self) -> Set[str]:
        """Get set of supported hosts file event types."""
        return self._supported_event_types.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for hosts file event producer."""
        health_data = await super().health_check()

        # Add hosts file specific health information
        hosts_health = {
            "monitored_files": self._hosts_file_paths,
            "polling_interval": self._polling_interval,
            "create_backups": self._create_backups,
            "backup_directory": str(self._backup_directory),
            "max_backups": self._max_backups,
            "parse_entries": self._parse_entries,
            "file_states": {},
        }

        # Check status of each monitored file
        for file_path in self._hosts_file_paths:
            file_state = self._file_states.get(file_path, {})
            hosts_health["file_states"][file_path] = {
                "exists": file_state.get("exists", False),
                "size": file_state.get("size"),
                "readable": os.access(file_path, os.R_OK)
                if os.path.exists(file_path)
                else False,
                "writable": os.access(file_path, os.W_OK)
                if os.path.exists(file_path)
                else False,
            }

        health_data["hosts_file"] = hosts_health
        return health_data
