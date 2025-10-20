# World Generator

## Main Setup
To use this project,

1. Clone this repository
```
git clone https://github.com/ogoudey/AcroGen.git
```

2. Run the bringup script with the Asset Project of your choice (currently there's a choice of 1).
```
./bringup.sh <asset project repo>
```
where `<asset project repo>` is [`acrophobia_v1`](https://github.com/ogoudey/acrophobia_v1) - a bare Unity project linked to .

There are a few options for interfacing with the world generators. This way opens a GUI in the browser, where you can converse and prompt the chatbot to generate VR worlds with the provided Asset Project. One a world is generated, open the Asset Project in Unity and go to `File / Open Scene / <the generated scene>`.

Alternatively, you can use the command line. Do
```
cd Backend
. .venv/bin/activate
python3 tests.py
```
Then open the Asset Project in Unity and open the generated scene.


### More:
Make sure that skyboxes in the Skybox Materials folder work, and that ground textures in the Ground Textures folder works.

## VR Setup
(Assuming a VIVE headset and a wireless adapter, a Windows computer, etc.)
1. Plug the headset into the power brick (make sure the power brick is ON)
2. Open up SteamVR (takes a minute)
3. Open up VIVE Wireless (takes a minute)
