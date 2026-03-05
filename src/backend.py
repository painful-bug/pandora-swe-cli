from deepagents.backends import (
    CompositeBackend,
    LocalShellBackend,
    StateBackend,
    StoreBackend,
)
from src.config import PROJECT_ROOT


def create_composite_backend(runtime):
    return CompositeBackend(
        default=LocalShellBackend(
            root_dir=str(PROJECT_ROOT),
            inherit_env=True,
            timeout=120,
        ),
        routes={
            "/workspace/": StateBackend(runtime),
            "/memories/": StoreBackend(runtime),
        },
    )
