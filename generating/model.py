from typing import List 
import json
from pathlib import Path

class WorldModel:
    pass

class UnityWorldModel(WorldModel):
    objects: List[dict]

    def __init__(self):
        super().__init__()
        self.objects = []

    def __repr__(self):
        return json.dumps(self.objects, indent=4, sort_keys=False)

    def update(self, object_data: dict):
        self.objects.append(object_data)
    
    def dump_world_model(self, path: str | Path):
        path = Path(path)
        data = {"objects": self.objects}
        with path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                sort_keys=True,
                default=str,   # safety for non-JSON types
            )
        return
        print(f"============ World Model ==========={json.dumps(
            data,
            indent=2,
            sort_keys=True,
            default=str,
        )}=========== end World Model ===========")