## Acrophobia World Gen VR Instructions
For instructions on generating VR worlds (offline), go to [README.md](.../README).

For instructions on setting up things to go into certain VR worlds (like the ones generated), this is in the right place.

### VR Setup
0. Clone this repo.

** Path A for just using VR **
1. Make/put the Asset Project (Unity Project) in `Resources/Asset Projects/`. The Asset Project should be identical to that which was used by the world generator.

2. Open the project from the Unity Hub by adding it from disk. Make sure it has the right Unity version. 

3. Assert that the right assets are in the scene. Then pick up at step 6.


** Path B for gathering eye data with VR**
1. Clone the Asset Project repo. We'll use [acrophobia_u5](TBD) for experimenting. The project's version should be Unity 2019.4. 

2. Open the project from the Unity Hub by adding it from disk. Make sure it has the right Unity version. 

3. Import the ViveSR .unitypackage ([Where is this package?](TBD)). After, the `Assets/` project folder should have ViveSR.

4. Import SteamVR Plugin (recommended: 2.8.0) ([Where is SteamVR Plugin?](TBD)). The import may ask to use Legacy VR or OpenXR. Choose OpenXR. Accept the recommended settings. SteamVR and other related packages should be in `Assets/` now. Restart the editor as recommended (necessary?).

5. Assert that the right assets are in the scene to enter VR.

Things to test:
- Player tag

** Paths A + B **
Turning on the hardware. At Tufts we use a VIVE Pro Eye.

6. Turn on the battery. Plug headset into battery. Headset (it's wireless adapter) should have a green light.

7. Open VIVE Wireless. If not already paired (headset's green light is flashing), pair it. Open SteamVR. Should show it's connected through to the headset. Path A pick up at step 10.

** Path B **
For gathering data
- Run calibration (??)

9. Turn on SRanipalRuntime

** Path A + B **
10. Press Play on Unity. If asked to "generate actions", do so. If asked to create actions.json, do so. And click Generate and Save.

** Path B **
11. To start logging data, inspect the SRanipal Eye Framework prefab and check Enable Eye Data Callback. Data is saved to the desktop in `AcroGenData/<sceneName>/<timestamp>/eye_tracking_log_test.csv`.