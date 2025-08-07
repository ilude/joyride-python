
import asyncio
import types
from unittest.mock import MagicMock, patch

import psutil
import pytest

from app.joyride.events import EventBus
from app.producers.system_events import SystemEventType
from app.producers.system_producer import SystemEventProducer


@pytest.mark.asyncio
async def test_run_producer_cancelled_error_branch(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    producer._monitor_system_resources = lambda: asyncio.sleep(0)
    producer._monitor_network_interfaces = lambda: asyncio.sleep(0)
    producer._monitor_processes = lambda: asyncio.sleep(0)
    producer._perform_health_checks = lambda: asyncio.sleep(0)
    
    async def fake_sleep(interval):
        raise asyncio.CancelledError()
    monkeypatch.setattr("asyncio.sleep", fake_sleep)
    logs = []
    
    class DummyLogger:
        def info(self, msg):
            logs.append(msg)
        
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())
    await producer._run_producer()
    assert any("System monitoring cancelled" in m for m in logs)


@pytest.mark.asyncio
async def test_run_producer_exception_branch(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    producer._monitor_system_resources = lambda: asyncio.sleep(0)
    producer._monitor_network_interfaces = lambda: asyncio.sleep(0)
    producer._monitor_processes = lambda: asyncio.sleep(0)
    producer._perform_health_checks = lambda: asyncio.sleep(0)
    
    sleep_calls = []
    async def fake_sleep(interval):
        if not sleep_calls:
            sleep_calls.append(interval)
            producer._is_running = False
            raise Exception("fail")
        return None
    monkeypatch.setattr("asyncio.sleep", fake_sleep)
    logs = []
    
    class DummyLogger:
        def info(self, msg):
            logs.append(msg)
        
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())
    await producer._run_producer()
    assert any("Error in system monitoring" in str(m) for m in logs)


def test_initialize_baseline_states_network(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={"monitor_network": True})
    # Simulate network interfaces and stats
    net_if_addrs = {"eth0": [types.SimpleNamespace(address="192.168.1.2")], "lo": [types.SimpleNamespace(address="127.0.0.1")]}
    net_if_stats = {"eth0": types.SimpleNamespace(isup=True), "lo": types.SimpleNamespace(isup=False)}
    monkeypatch.setattr("psutil.net_if_addrs", lambda: net_if_addrs)
    monkeypatch.setattr("psutil.net_if_stats", lambda: net_if_stats)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(producer._initialize_baseline_states())
    assert producer._last_network_states["eth0"]["is_up"] is True
    assert producer._last_network_states["lo"]["is_up"] is False
    assert "192.168.1.2" in producer._last_network_states["eth0"]["addresses"]
    assert "127.0.0.1" in producer._last_network_states["lo"]["addresses"]


def test_initialize_baseline_states_error_branch(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    # Simulate error in psutil.cpu_percent
    monkeypatch.setattr("psutil.cpu_percent", lambda: (_ for _ in ()).throw(Exception("fail")))
    logs = []
    
    class DummyLogger:
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(producer._initialize_baseline_states())
    assert any("Error initializing baseline states" in m for m in logs)


@pytest.mark.asyncio
async def test_monitor_processes_zombie(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # Patch _publish_process_event to track calls
    called = {}
    
    async def fake_publish_process_event(proc, event_type):
        called['proc'] = proc
        called['event_type'] = event_type
    producer._publish_process_event = fake_publish_process_event

    # Simulate a process with STATUS_ZOMBIE
    proc = types.SimpleNamespace(info={"status": "zombie"})
    monkeypatch.setattr(psutil, "STATUS_ZOMBIE", "zombie")
    
    def fake_process_iter(attrs):
        return [proc]
    monkeypatch.setattr(psutil, "process_iter", fake_process_iter)
    await producer._monitor_processes()
    assert called['event_type'] == SystemEventType.PROCESS_CRASHED

@pytest.mark.asyncio
async def test_monitor_processes_error(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # Simulate psutil.process_iter raising Exception
    
    def fake_process_iter(attrs):
        raise Exception("fail")
    monkeypatch.setattr(psutil, "process_iter", fake_process_iter)
    logs = []
    
    class DummyLogger:
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())
    await producer._monitor_processes()
    assert any("Error monitoring processes" in m for m in logs)
    

def test_health_check():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    loop = asyncio.get_event_loop()
    health = loop.run_until_complete(producer.health_check())
    assert isinstance(health, dict)

def test_health_check_with_custom_config():
    bus = EventBus()
    config = {
        "monitoring_interval": 10,
        "cpu_threshold": 50,
        "memory_threshold": 50,
        "disk_threshold": 50,
        "monitor_processes": True,
        "monitor_network": False,
        "monitor_services": True,
    }
    producer = SystemEventProducer(bus, config=config)
    loop = asyncio.get_event_loop()
    health = loop.run_until_complete(producer.health_check())
    assert isinstance(health, dict)
    assert health["system"]["monitoring_interval"] == 10
    assert health["system"]["cpu_threshold"] == 50

def test_health_check_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    # Producer not started, should still return dict
    loop = asyncio.get_event_loop()
    health = loop.run_until_complete(producer.health_check())
    assert isinstance(health, dict)


def test_get_supported_event_types():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    event_types = producer.get_supported_event_types()
    assert isinstance(event_types, set)
    assert len(event_types) > 0

  
def test_get_supported_event_types_empty():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    # forcibly clear event types
    producer._supported_event_types = set()
    event_types = producer.get_supported_event_types()
    assert isinstance(event_types, set)
    assert len(event_types) == 0

  
def test_health_check_error_branch(monkeypatch):
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    # Simulate error in psutil
    
    def bad_cpu_percent():
        raise RuntimeError("psutil error")
    monkeypatch.setattr("psutil.cpu_percent", bad_cpu_percent)
    loop = asyncio.get_event_loop()
    health = loop.run_until_complete(producer.health_check())
    assert "system_error" in health
  
@pytest.mark.asyncio
async def test_perform_health_checks_branches():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # healthy branch
    producer._last_resource_states = {"cpu_percent": 10.0, "memory_percent": 10.0, "disk_percent": 10.0}
    await producer._perform_health_checks()
    # warning branch
    producer._last_resource_states = {"cpu_percent": 85.0, "memory_percent": 10.0, "disk_percent": 10.0}
    await producer._perform_health_checks()
    # unhealthy branch
    producer._last_resource_states = {"cpu_percent": 85.0, "memory_percent": 85.0, "disk_percent": 90.0}
    await producer._perform_health_checks()

  


@pytest.mark.asyncio
async def test_publish_system_startup_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    await producer._publish_system_startup_event()

@pytest.mark.asyncio
async def test_publish_system_startup_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    # Should raise RuntimeError if not running
    with pytest.raises(RuntimeError):
        await producer._publish_system_startup_event()

  
@pytest.mark.asyncio
async def test_publish_system_shutdown_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    await producer._publish_system_shutdown_event()

@pytest.mark.asyncio
async def test_publish_system_shutdown_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    with pytest.raises(RuntimeError):
        await producer._publish_system_shutdown_event()

  
@pytest.mark.asyncio
async def test_publish_resource_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    for i in range(10):
        await producer._publish_resource_event("cpu", 90, 80, "percent")


@pytest.mark.asyncio
async def test_publish_resource_event_spam_prevention():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # Should only publish every 5th alert
    for i in range(15):
        await producer._publish_resource_event("cpu", 90, 80, "percent")
    # Alert count should be 15
    assert producer._alert_counts["cpu_alert"] == 15


@pytest.mark.asyncio
async def test_publish_resource_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    with pytest.raises(RuntimeError):
        await producer._publish_resource_event("cpu", 90, 80, "percent")



@pytest.mark.asyncio
async def test_publish_network_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    stats = types.SimpleNamespace(isup=True, speed=1000)
    addresses = ["192.168.1.1"]
    await producer._publish_network_event(
        "eth0",
        SystemEventType.NETWORK_INTERFACE_UP,
        stats,
        addresses,
    )


@pytest.mark.asyncio
async def test_publish_network_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    stats = types.SimpleNamespace(isup=True, speed=1000)
    addresses = ["192.168.1.1"]
    with pytest.raises(RuntimeError):
        await producer._publish_network_event(
            "eth0",
            SystemEventType.NETWORK_INTERFACE_UP,
            stats,
            addresses,
        )



@pytest.mark.asyncio
async def test_publish_process_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    proc = types.SimpleNamespace(info={"name": "python", "pid": 123, "status": "running"})
    await producer._publish_process_event(
        proc,
        SystemEventType.PROCESS_STARTED,
    )


@pytest.mark.asyncio
async def test_publish_process_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    proc = types.SimpleNamespace(info={"name": "python", "pid": 123, "status": "running"})
    # Should not raise, just log error
    await producer._publish_process_event(
        proc,
        SystemEventType.PROCESS_STARTED,
    )



@pytest.mark.asyncio
async def test_publish_health_event():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    await producer._publish_health_event("healthy", 1.0)
    await producer._publish_health_event("warning", 0.6)
    await producer._publish_health_event("unhealthy", 0.2)


@pytest.mark.asyncio
async def test_publish_health_event_not_running():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    with pytest.raises(RuntimeError):
        await producer._publish_health_event("healthy", 1.0)


@pytest.mark.asyncio
async def test_initialize_baseline_states_error_branch():
    event_bus = MagicMock()
    producer = SystemEventProducer(event_bus, config={})
    with patch("app.producers.system_producer.psutil.cpu_percent", side_effect=Exception("fail")):
        await producer._initialize_baseline_states()

@pytest.mark.asyncio
async def test_run_producer_error_branch():
    event_bus = MagicMock()
    producer = SystemEventProducer(event_bus, config={})
    producer._is_running = True
    # Patch _monitor_system_resources to raise Exception
    with patch.object(producer, "_monitor_system_resources", side_effect=Exception("fail")):
        # Patch asyncio.sleep to break loop after first iteration
        with patch("app.producers.system_producer.asyncio.sleep", side_effect=asyncio.CancelledError):
            try:
                await producer._run_producer()
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_monitor_system_resources_thresholds():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # CPU above threshold
    with patch("app.producers.system_producer.psutil.cpu_percent", return_value=90):
        with patch("app.producers.system_producer.psutil.virtual_memory", return_value=type('mem', (), {'percent': 70})()):
            with patch("app.producers.system_producer.psutil.disk_usage", return_value=type('disk', (), {'used': 90, 'total': 100})()):
                await producer._monitor_system_resources()
    # Memory above threshold
    with patch("app.producers.system_producer.psutil.cpu_percent", return_value=70):
        with patch("app.producers.system_producer.psutil.virtual_memory", return_value=type('mem', (), {'percent': 90})()):
            with patch("app.producers.system_producer.psutil.disk_usage", return_value=type('disk', (), {'used': 90, 'total': 100})()):
                await producer._monitor_system_resources()
    # Disk above threshold
    with patch("app.producers.system_producer.psutil.cpu_percent", return_value=70):
        with patch("app.producers.system_producer.psutil.virtual_memory", return_value=type('mem', (), {'percent': 70})()):
            with patch("app.producers.system_producer.psutil.disk_usage", return_value=type('disk', (), {'used': 90, 'total': 100})()):
                await producer._monitor_system_resources()


@pytest.mark.asyncio
async def test_monitor_network_interfaces_state_change():
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True
    # Setup last state as down
    producer._last_network_states = {"eth0": {"is_up": False, "addresses": ["192.168.1.1"]}}
    # Mock psutil to simulate interface up
    stats = type('stats', (), {'isup': True, 'speed': 1000})()
    addrs = [type('addr', (), {'address': "192.168.1.1"})()]
    with patch("app.producers.system_producer.psutil.net_if_addrs", return_value={"eth0": addrs}):
        with patch("app.producers.system_producer.psutil.net_if_stats", return_value={"eth0": stats}):
            await producer._monitor_network_interfaces()


from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_run_producer_main_loop(monkeypatch):
    from app.joyride.events import EventBus
    from app.producers.system_producer import SystemEventProducer

    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    producer._is_running = True

    # Patch all monitoring methods to raise error on first call
    async def fake_monitor_system_resources():
        raise Exception("fail resources")
    async def fake_monitor_network_interfaces():
        raise Exception("fail network")
    async def fake_monitor_processes():
        raise Exception("fail processes")
    async def fake_perform_health_checks():
        raise Exception("fail health")

    monkeypatch.setattr(producer, "_monitor_system_resources", fake_monitor_system_resources)
    monkeypatch.setattr(producer, "_monitor_network_interfaces", fake_monitor_network_interfaces)
    monkeypatch.setattr(producer, "_monitor_processes", fake_monitor_processes)
    monkeypatch.setattr(producer, "_perform_health_checks", fake_perform_health_checks)

    # Patch asyncio.sleep to break loop after first error
    async def fake_sleep(interval):
        producer._is_running = False
    monkeypatch.setattr("app.producers.system_producer.asyncio.sleep", fake_sleep)

    logs = []
    class DummyLogger:
        def info(self, msg):
            logs.append(msg)
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())

    await producer._run_producer()
    print("Captured logs:", logs)
    # Should log error for at least one monitoring method
    assert any("Error" in m for m in logs)


@pytest.mark.asyncio
async def test_perform_health_checks_error_branch(monkeypatch):
    from app.joyride.events import EventBus
    from app.producers.system_producer import SystemEventProducer

    event_bus = EventBus()
    producer = SystemEventProducer(event_bus, config={})
    producer._is_running = True
    # Simulate error in _last_resource_states
    producer._last_resource_states = None

    async def fake_publish_health_event(status, score):
        pass
    producer._publish_health_event = fake_publish_health_event

    logs = []
    class DummyLogger:
        def error(self, msg):
            logs.append(msg)
    monkeypatch.setattr("app.producers.system_producer.logger", DummyLogger())

    await producer._perform_health_checks()
    assert any("Error performing health checks" in m for m in logs)


def test_publish_system_startup_event():
    from app.joyride.events import EventBus
    from app.producers.system_producer import SystemEventProducer
    bus = EventBus()
    producer = SystemEventProducer(bus, config={})
    called = {}
    def fake_publish_event(event):
        called['event'] = event
    producer.publish_event = fake_publish_event
    loop = asyncio.get_event_loop()
    loop.run_until_complete(producer._publish_system_startup_event())
    assert called['event'].event_type == "system.startup"
