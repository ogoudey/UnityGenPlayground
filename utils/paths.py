from pathlib import Path
from dataclasses import dataclass

@dataclass
class RelativePath:
    # Path relative to Backend, useful for writing files
    path: Path

    def to_dict(self) -> dict:
        return {
            "__type__": "RelativePath",
            "path": str(self.path),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RelativePath":
        return cls(Path(d["path"]))

from pydantic import BaseModel

class AssetsRelativePathStr(BaseModel):
    # A POSIX path like Assets/yada/daba/doo.suffix. Found in asset_catalog and the synopses. Also used as an output type for agents.
    path: str