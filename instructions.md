# Requirements (Full Experiment)

python > 3.9

Unity > 5

A Unity login

Access to a Windows Command Prompt

## Setup
There are two main components to this project: the Unity project - where the assets live, along with any C# packages required for the hardware; and the World Generator (this repo), the Python code that generates the Unity scenes.

The two projects must have a certain file structure relative to each other, for the World Generator to work properly.

```
.
├── Resources
│   ├── Asset Projects
│   │   ├── Asset Project - a Unity project with a certain structure
```

Setup proceeds in two or three steps:
1. Set up the World Generator
2. Set up the Asset Project
3. (Optional) Install data analysis tool

### 1. Set up the World Generator
1. Make sure python is installed.
2. Clone this repository.
3. Set up the python virtual environment:
```
cd Backend
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up the Asset Project
1. Make a new Unity project in the `Asset Projects` directory of the World Generator.
2. Add the following Assets to your Unity account: 
- [AllSkyFree](https://assetstore.unity.com/packages/2d/textures-materials/sky/allsky-free-10-sky-skybox-set-146014)
- [Blue Polygon's Rope Bridge 3D](https://assetstore.unity.com/packages/3d/environments/rope-bridge-3d-222563)
- [CastlePack](https://assetstore.unity.com/packages/3d/environments/castle-pack-by-progru-185976)
- [BridgesPack from MaximeBrunoni](https://assetstore.unity.com/packages/3d/props/bridges-pack-212950)
- [Low Poly Nature from Oode Studios](https://assetstore.unity.com/packages/3d/environments/low-poly-nature-260306)
- [Stylized Nature Pack from Proxy Games](https://assetstore.unity.com/packages/3d/environments/unl-ultimate-nature-lite-176906)
- [POLYGON City Pack](https://assetstore.unity.com/packages/3d/environments/urban/city-package-107224)
- [Yughes Ground Materials](https://assetstore.unity.com/packages/2d/textures-materials/nature/yughues-free-ground-materials-13001)
3. Download/import those Assets into the Unity project
4. Now to the certain structure. Clone the [special assets](https://github.com/ogoudey/Special-Unity-Scripts) into the Unity project's root directory:
```
Resources/Asset Projects/the new asset project
├── Special-Unity-Assets <- here
├── Assets
│   ├── Blue Polygon
│   ├── CastlePack
│   ├── ...

```
5. Then do:
```
move Special-Unity-Assets\asset_catalog.json .

xcopy Special-Unity-Assets\* Assets\ /E /I /H /Y
rmdir /S /Q Special-Unity-Assets
```

6. Move a selection of ground materials (`.mat`) and skybox materials (`.mat`) from AllSky and Yughes'. The folder structure should look like this:
```
└── Resources
    ├── Asset Projects
    │   ├── name_of_asset_project
    │   │   ├── asset_catalog.json
    │   │   ├── Assets
    │   │   │   ├── AllSkyFree
    │   │   │   ├── Blue Polygon
    │   │   │   ├── CastlePack
    │   │   │   ├── CastlePack.meta
    │   │   │   ├── Generations
    │   │   │   ├── Generations.json
    │   │   │   ├── Ground Materials
    │   │   │   ├── Manifest
    │   │   │   ├── MaximeBrunoni
    │   │   │   ├── Oode studios
    │   │   │   ├── Oode studios.meta
    │   │   │   ├── POLYGON city pack
    │   │   │   ├── POLYGON city pack.meta
    │   │   │   ├── Proxy Games
    │   │   │   ├── Scenes
    │   │   │   ├── Scripts
    │   │   │   │   ├── gen_menu.cs
    │   │   │   │   ├── PCPS.cs
    │   │   │   │   └── EyeTrackingManager.cs
    │   │   │   ├── Scripts.meta
    │   │   │   ├── Skybox Materials
    │   │   │   │   ├── ... a selection of skybox materials ...
    │   │   │   ├── Sounds
    │   │   │   └── YughuesFreeGroundMaterials
```
7. Finally, register the Asset Project by adding the AcrophobiaWorldGen class to `worldgen.py`'s `Generator_Class_from_Asset_Project_Name`.
8. Done! Go to the Generation Window to generate worlds.

### 3. Setup Data Analysis Tool
For data analysis, you can use [`EyeDataAnalysis`](https://github.com/ogoudey/EyeDataAnalysis). It's not a fully developed UI. Use `python multiplotter.py <path-to-eye-data-for-subj1.csv> <path-to-eye-data-for-subj2.csv>`
1. Clone the repo
2. Set up another Python virtual environment:
```
python -m venv .venv
.venv\Scripts\activate
pip install matplotlib pandas numpy
```








