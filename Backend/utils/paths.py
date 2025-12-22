from pathlib import Path
from dataclasses import dataclass

@dataclass
class RelativePath:
    # Path relative to Backend, useful for writing files
    path: Path


from pydantic import BaseModel

class AssetsRelativePathStr(BaseModel):
    # A POSIX path like Assets/yada/daba/doo.suffix. Found in asset_catalog and the synopses. Also used as an output type for agents.
    path: str