"""Actual CLI dispatch with controlled serving dependencies, not live Uvicorn."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from looking_glass import cli
from looking_glass.services.image_retirement import collect, storage_use


class NoDatabaseAccess:
    def connect(self):
        pytest.fail('collector reached database instead of refusing the serving lock')


def test_cli_holds_lock_while_serving_and_releases(monkeypatch, settings):
    monkeypatch.setattr(cli, 'load_settings', lambda config: settings)
    entered = []
    async def serve(value):
        assert value is settings
        entered.append(True)
        with pytest.raises(RuntimeError, match='busy'):
            collect(NoDatabaseAccess(), settings.maps_dir)
    monkeypatch.setattr(cli, '_serve', serve)
    assert cli.main(['serve']) == 0 and entered == [True]
    with storage_use(settings.maps_dir, exclusive=True):
        pass


def test_collector_lock_prevents_cli_start(monkeypatch, settings):
    monkeypatch.setattr(cli, 'load_settings', lambda config: settings)
    entered = []
    async def serve(value):
        entered.append(value)
    monkeypatch.setattr(cli, '_serve', serve)
    with storage_use(settings.maps_dir, exclusive=True):
        assert cli.main(['serve']) == 1
    assert entered == []


@pytest.mark.parametrize('exception', [ValueError, RuntimeError])
def test_server_failure_propagates_and_releases_lock(monkeypatch, settings, exception):
    monkeypatch.setattr(cli, 'load_settings', lambda config: settings)
    async def serve(value):
        with pytest.raises(RuntimeError, match='busy'):
            collect(NoDatabaseAccess(), settings.maps_dir)
        raise exception('injected server failure')
    monkeypatch.setattr(cli, '_serve', serve)
    with pytest.raises(exception, match='server failure'):
        cli.main(['serve'])
    with storage_use(settings.maps_dir, exclusive=True):
        pass


def test_cli_lock_covers_executor_shutdown(monkeypatch, settings):
    monkeypatch.setattr(cli, 'load_settings', lambda config: settings)
    worker_ready, release, shutting_down = (threading.Event() for _ in range(3))
    errors = []
    real_shutdown = ThreadPoolExecutor.shutdown
    def shutdown(executor, *args, **kwargs):
        shutting_down.set()
        return real_shutdown(executor, *args, **kwargs)
    monkeypatch.setattr(ThreadPoolExecutor, 'shutdown', shutdown)
    def worker():
        worker_ready.set()
        assert release.wait(10), 'executor worker release timed out'
    async def serve(value):
        asyncio.get_running_loop().run_in_executor(None, worker)
        assert worker_ready.wait(10)
    monkeypatch.setattr(cli, '_serve', serve)
    def run():
        try:
            assert cli.main(['serve']) == 0
        except BaseException as exc:
            errors.append(exc)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        assert worker_ready.wait(10) and shutting_down.wait(10)
        with pytest.raises(RuntimeError, match='busy'):
            collect(NoDatabaseAccess(), settings.maps_dir)
        assert thread.is_alive()
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive() and not errors
    with storage_use(settings.maps_dir, exclusive=True):
        pass
