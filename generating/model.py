from typing import List 
import json
from pathlib import Path
import random
import uuid

class WorldModel:
    def __init__(self, world_name, preexisting_world_model_list: List = []):
        self.name = world_name
        pass

class UnityWorldModel(WorldModel):
    scene_data: List[dict]

    def __init__(self, world_name: str, preexisting_world_model_list: List = []):
        super().__init__(world_name, preexisting_world_model_list)
        self.scene_data = preexisting_world_model_list

    def __repr__(self):
        return json.dumps(self.scene_data, indent=4, sort_keys=False)

    def update(self, object_data: dict):
        data = object_data.copy()
        
        self.scene_data.append(data)
        self.dump_world_model(f"generating/models/{self.name}.json")
    
    def dump_world_model(self, path: str | Path):
        path = Path(path)
        data = {"scene": self.scene_data}
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