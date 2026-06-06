# modules/__init__.py
import importlib
import inspect
from pathlib import Path
from modules.imodule import IModule

REGISTRY: dict[str, type[IModule]] = {}

for path in Path(__file__).parent.glob("*.py"):
    if path.stem in ("__init__", "imodule"):
        continue
    try:
        module = importlib.import_module(f"modules.{path.stem}")
    except ImportError as e:
        print(f"Error importing module {path.stem}: {e}")
        continue

    for _, cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls, IModule) and cls is not IModule:
            REGISTRY[path.stem] = cls