# World Generator
## Testing
```
python3 main.py test_acro_<skycraper, bridge, mountain, platform, etc.>
```
<img width="1304" height="725" alt="image" src="https://github.com/user-attachments/assets/b756c450-57a1-4101-86a1-e6da76c283be" />



## World generator architecture
<img width="930" height="494" alt="image" src="https://github.com/user-attachments/assets/16e6c626-21c1-47da-8b51-a5d3b6240690" /> 


## Project history
### Part I
<img width="1050" height="554" alt="Screenshot from 2025-09-15 15-29-56" src="https://github.com/user-attachments/assets/57bc1d64-c561-40b6-b337-2398c673fb1e" />

**Prompt**: A forest

**Available assets**: a small deck of prefabs from /Prefabs in [Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)

**Settings**: Two levels of agents generate this. L1 agents call L0 agents who create the objects.

**Notes**: 
* Groundless - generating ground meshes is hard.

### Part II
<img width="886" height="439" alt="image" src="https://github.com/user-attachments/assets/bed46219-9fec-473b-b71e-4f6ab472f20a" />

**Prompt**: A river cutting through a terrain with some foliage, and a bridge going over it connecting two banks.

**Available assets**: a small deck of prefabs from /Prefabs in [Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)

**Settings**:
1. One main agent plans with the help of subagents, and then places the objects its planned. The ground is a generated heightmap. Then
2. The positions of the objects are checked against the ground, these checks go into a list of feedbacks.
3. The feedback is considered by a third agent who reforms the objects given the feedback.

**Notes**: 
* Either LLM's "short term memory" issue, or a miscommunication issue - each asset is locally different from the others, affecting correct __visual__ placement.

### Part III
<img width="858" height="587" alt="Oct 1 Unity Gen" src="https://github.com/user-attachments/assets/2124e9a7-e1c3-403e-86fe-0914c97705a2" />

**Prompt**: "I'm scared of heights over 5m. I just can't do bridges." 

**Available assets**: same assets as before [Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)

**Settings**: Patient message goes through intepretation to a world-generating coordinator. This takes 5 minutes with on OpenAI's `o4-mini`.

**Notes**: Still getting the orientation of bulky objects wrong.
 
## Installation
Put contents of this repo in a Unity project folder.

Then do (Linux):
```
export OPENAI_API_KEY="..."
cd Backend
python3 -m venv .venv
# install requirements
python3 main.py <arg>
```
(Windows):
```
setx OPENAI_API_KEY="..."
# open up a new command prompt to load the environment variable
cd Backend
.\.venv\Scripts\activate.bat
# install requirements
python3 main.py <arg>
```


Used assets:
[Nature stuff](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)
[Bridge](https://assetstore.unity.com/packages/3d/environments/rope-bridge-3d-222563)
[Ground textures](https://assetstore.unity.com/packages/2d/textures-materials/nature/yughues-free-ground-materials-13001)	
[Bridges Pack](https://assetstore.unity.com/packages/3d/props/bridges-pack-212950)
... and more.

## VR Setup
(Assuming a VIVE headset and a wireless adapter, a Windows computer, etc.)
1. Plug the headset into the power brick (make sure the power brick is ON)
2. Open up the Unity project (through the Unity Hub, takes a minute)
3. Open up SteamVR (takes a minute)
4. Open up VIVE Wireless (takes a minute)
5. Open up a Unity world with the OpenVR package imported.
6. Hit play to send the game to the headset.

### Note:
Change Quality / Rendering / Rendering Pipeline Asset to None
