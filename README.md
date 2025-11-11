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
