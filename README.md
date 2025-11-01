# World Generator

<img width="1038" height="684" alt="image" src="https://github.com/user-attachments/assets/907b2cc2-a51d-44c6-b4e8-437526533501" />

<img width="2195" height="271" alt="conductor_graph" src="https://github.com/user-attachments/assets/d3d6725e-9b18-4e86-94e0-9637a2871039" />

## Usage
This project introduces a menu to Unity that provides the ability to generate virtual reality scenes from language. At this stage, the project is intended as a tool to promote therapeutic intervention. This README is for researchers who will be using some aspect of the tool.

<div align="center">
  <img width="331" height="322" alt="Menu 1" src="https://github.com/user-attachments/assets/7721e80c-5b3d-41e1-a806-011628bc1e94" />
  <br/>
  <span style="font-size: 0.9em; color: gray;">Generate — Give a prompt or select from a list of premade prompts, and watch the scene get generated.</span>
</div>

<div align="center">
  <img width="331" height="322" alt="Menu 2" src="https://github.com/user-attachments/assets/618405fd-a2fd-4cb1-82d8-ebcbf19732cd" />
  <br/>
  <span style="font-size: 0.9em; color: gray;">Generations — View past generations and enter them, providing a name of the subject for the trial.</span>
</div>

<div align="center">
  <img width="331" height="322" alt="Menu 3" src="https://github.com/user-attachments/assets/60425251-cea9-4983-998f-7afaaa4f1f38" />
  <br/>
  <span style="font-size: 0.9em; color: gray;">Settings — Select the Asset Project you want to open (not recommended to change from `acrophobia_v1`).</span>
</div>

## Install
Clone this repository
```
git clone https://github.com/ogoudey/AcroGen.git
```
### Install Asset Project (Unity Project)
The install script will automatically clone the Asset Project of your choice, and set up the Python environment.
```
./install_asset_project.sh <asset project repo name>
# or, Windows
.\install.ps1 <asset project repo name>
```
The Asset Project specifies the assets that will be used to generate with. [`acrophobia_v1`](https://github.com/ogoudey/acrophobia_v1) is recommended.

The Asset Project will be installed as `Resources/Asset Projects/X`. Open this folder as a new Unity Project.

## VR Setup 

### VIVE Pro 2
(Assuming a VIVE Pro 2 headset and a wireless adapter, a Windows computer, etc.)
1. Plug the headset into the power brick (make sure the power brick is ON)
2. Open up SteamVR (takes a minute)
3. Open up VIVE Wireless (takes a minute)
4. Import the SteamVR Plugin 2.8.0 (accept all recommended settings)


### Eyedata collection with ViveSR
5. Import the ViveSR package
6. Install the [`acrophobia_u5`](https://github.com/ogoudey/acrophobia_u5) asset project, and open it with a Unity 2019 version.
