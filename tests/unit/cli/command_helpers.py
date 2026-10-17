"""Mock owners shared by the monolithic and extracted CLI implementations."""

from importlib import import_module
from types import ModuleType

from src.cli import main


def command_owner(name: str) -> ModuleType:
    return import_module(getattr(main, name).__module__)


CREATE = command_owner("create")
INSTALL = command_owner("install")
UPDATES = command_owner("upgrade")

# Remove these test-only name mappings once the source extraction has merged.
resolve_context = getattr(
    INSTALL, "resolve_context" if hasattr(INSTALL, "resolve_context") else "_resolve_install_context"
)
CONTEXT = import_module(resolve_context.__module__)
InstallContext = getattr(CONTEXT, "InstallContext" if hasattr(CONTEXT, "InstallContext") else "_InstallContext")
report_failure = getattr(INSTALL, "report_failure" if hasattr(INSTALL, "report_failure") else "_report_install_failure")
PATH_UPDATE_NAME = "apply_path_update" if hasattr(INSTALL, "apply_path_update") else "_apply_path_update"
