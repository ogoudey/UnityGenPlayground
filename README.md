# World Generator
<div align="center">
<img width="519" height="342" alt="image" src="https://github.com/user-attachments/assets/907b2cc2-a51d-44c6-b4e8-437526533501" />
  <br/>
  <span style="font-size: 0.9em; color: gray;">A world generated with something like "Generate me a world with a bridge"</span>
</div>

<br>

<div align="center">
  <img width="2195" height="271" alt="conductor_graph" src="https://github.com/user-attachments/assets/d3d6725e-9b18-4e86-94e0-9637a2871039" />
  <br/>
  <span style="font-size: 0.9em; color: gray;">The array of tools available for the Conductor agent to use, some of which run further agents.</span>
</div>


## Getting started
```mermaid
graph TD
    A[Asset Projects] --> B[Acrophobia Asset Project]
    C(World Generator) --> D(Acrophobia World Generator)
    subgraph B[Acrophobia Asset Project]
        D
    end
```

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
