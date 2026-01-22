from dataclasses import dataclass, asdict
from datetime import datetime
import platform
import sys

@dataclass
class RunMetadata:
    run_name: str
    timestamp: str
    python_version: str
    platform: str
    notes: str = ""

    @staticmethod
    def create(run_name, notes=""):
        return RunMetadata(
            run_name=run_name,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            notes=notes,
        )
