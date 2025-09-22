# Unity Scene Generation Demo
## Part I
<img width="1050" height="554" alt="Screenshot from 2025-09-15 15-29-56" src="https://github.com/user-attachments/assets/57bc1d64-c561-40b6-b337-2398c673fb1e" />

**Prompt**: A forest

**Available assets**: a small deck of prefabs from /Prefabs in [Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)

**Settings**: Two levels of agents generate this. L1 agents call L0 agents who create the objects.

**Notes**: 
* Groundless - generating ground meshes is hard.

## Part II
<img width="886" height="439" alt="image" src="https://github.com/user-attachments/assets/bed46219-9fec-473b-b71e-4f6ab472f20a" />

**Prompt**: A river cutting through a terrain with some foliage, and a bridge going over it connecting two banks.

**Available assets**: a small deck of prefabs from /Prefabs in [Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)

**Settings**: One main agent plans the scene with help of others, and then places the objects in XYZ space. The ground is a generated heightmap.

**Notes**: 
* Either LLM's "short term memory" issue, or a miscommunication issue - each asset is locally different from the others, affecting correct __visual__ placement.
 
## Installation
Put contents of this repo in a Unity project folder.

Then do
```
cd Backend
python3 -m venv .venv
# install requirements
python3 Test.py
```


Used assets:
[Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)
[Bridge](https://assetstore.unity.com/packages/3d/environments/rope-bridge-3d-222563)




Note:
Change Quality / Rendering / Rendering Pipeline Asset to None
