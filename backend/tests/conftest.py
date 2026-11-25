import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Las pruebas async corren sobre asyncio, igual que la app."""
    return "asyncio"
