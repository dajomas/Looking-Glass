import pytest

from looking_glass_test_helpers import png_bytes, two_room_scene  # noqa: F401

@pytest.fixture(scope="session")
def browser():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as playwright:
        instance = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            yield instance
        finally:
            instance.close()

@pytest.fixture(autouse=True)
def close_test_contexts(request):
    if "browser" not in request.fixturenames:
        yield
        return
    instance = request.getfixturevalue("browser")
    try:
        yield
    finally:
        for context in list(instance.contexts):
            context.close()
