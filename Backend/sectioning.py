import sys
from threading import Thread
import time # sub for actual prompting

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS


from dataclasses import dataclass, asdict
import json
import random

import prompting
import yamling

from agents import Agent, Runner, function_tool
from pydantic import BaseModel
import asyncio

from dataclasses import dataclass, asdict

import assets
prefab_tree = assets.get_found(".prefab")
material_tree = assets.get_found(".mat")

MODEL="o3-mini"

RESTRICTIONS="""In fact, only describe objects that are commonly found in scenes built in the game engine Unity. IN FACT, ONLY USE THESE ASSETS:\n"""+str(prefab_tree)+"""."""

class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()

    def add_skybox(self, meta_file):
        guid = yamling.get_guid(meta_file)
        self.yaml.set_skybox(guid)
    
    def add_prefab(self, meta_file, transform):
        guid = yamling.get_guid(meta_file)
        prefab_path = meta_file.removesuffix(".meta")
        self.yaml.add_prefab_instance(guid, prefab_path, transform)
        #print(self.yaml.wrapped)
        
    def done_and_write(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
        
global unity


class Designation(BaseModel):
    asset_path: str
    #next_agent: str

@function_tool
async def objectConsult(object_description: str, location: str, important_info: str) -> str:
    """ I get the object, I find the asset """
    agent = Agent(
        name="ObjectConsultant" + str(random.randint(100, 999)),
        output_type = Designation,
        instructions="Given the directory structure (asset tree), return the path to the file of the desired asset. If, for some reason, you cannot retrieve the asset, return some reason (e.g. this library seems to cover X instead).",
        model=MODEL  
    )
    
    prompt = {"Object description": object_description,
                "Relevant information": important_info,
                "Asset tree": prefab_tree}
    
    result = await Runner.run(agent, json.dumps(prompt))
    
    asset_path = result.final_output.asset_path + ".meta"
    
    
    try:
        json_location = json.loads(location)
    except Exception as e:
        print(e)
        print("Could not JSONify")
        return f"Failed to add object with description '{object_description}' to {location} in the scene. Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        global unity
        print(f"An object with description '{object_description}' is going to be added to: {location}")
        unity.add_prefab(asset_path, json_location)
        return f"Successfully added object with description '{object_description}' to {location} in the scene."
    except Exception as e:
        return f"Could not add asset, likely because nothing an object with a description '{object_description}' is available in the library of assets. {asset_path}"

@function_tool
async def createObject(description: str, location: str, other_important_info: str) -> str:
    """ 
        Location is a str: \"\"\"{"x": float, "y": float, "z": float}", for example, "{"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}\"\"\"
    """
    agent = Agent(
        name="ObjectCreator" + str(random.randint(100, 999)),
        tools=[objectConsult],
        #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
        instructions= "Name the object and use the objectConsult tool to retrieve the asset path.",
        model=MODEL
    )
    
    prompt = {"Description of object": description,
                "Intended location of object": location,
                "Other important info": other_important_info}
    
    await Runner.run(agent, json.dumps(prompt))
    
    return f"Successfully called objectConsult."

@function_tool
async def createSectionL0(description: str, region: str):
    """ Handle coming soon... """

    """ This function is currently equipped with RESTRICTIONS """
    


    agent = Agent(
        name="SectionLeader" + str(random.randint(100, 999)),
        tools=[createObject],
        instructions="You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset." + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": description, "Region to work in": region}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."

@function_tool
async def createSectionL1(description: str, region: str):
    agent = Agent(
        name="SectionLeader" + str(random.randint(100, 999)),
        tools=[createSectionL0, createObject],
        instructions="You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": description, "Region to work in": region}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."
 
@function_tool
async def createSectionL2(description: str, region: str):
    agent = Agent(
        name="SectionLeader" + str(random.randint(100, 999)),
        tools=[createSectionL1, createObject],
        instructions="You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": description, "Region to work in": region}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."


@function_tool
async def skyboxConsult(skybox_description: str, important_info: str="skybox1 has blue sky, skybox2 has cloudy sky") -> Designation:
    agent = Agent(
        name="SkyboxConsultant" + str(random.randint(100, 999)),
        output_type = Designation,
        instructions="Given the directory structure (asset tree), return the path to the file of the desired asset.",
        model=MODEL
        
    )
    prompt = {"Object description": skybox_description,
                "Available assets": material_tree}

    result = await Runner.run(agent, json.dumps(prompt))
    asset_path = result.final_output.asset_path
    
    global unity
    unity.add_skybox(asset_path + ".meta")
    
    return f"Successfully added skybox with description '{skybox_description}' to the scene."

async def createSkyboxLeader(description: str="Plain blue sky"):
    
    agent = Agent(
        name="SkyboxLeader",
        tools=[skyboxConsult],
        instructions="You will be given a description of an intended Unity scene and you are to prompt an agent (through the skyboxConsult tool) to select the right asset. Name the object and use the objectConsult tool to retrieve the asset path. The agent you prompt will be looking for a skybox that corresponds to your prompt."
    )
    
    prompt = {"Description of scene": description}
    result = await Runner.run(agent, json.dumps(prompt))
    
    return f"Successfully added skybox given description '{description}'"
   
   
async def main(prompt):
    global unity
    unity = UnityFile("test0")
    
    await createSkyboxLeader(prompt)


    
    agent = Agent(
        name="SectionLeader0",
        tools=[createSectionL2, createObject],
        instructions="You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(agent, json.dumps(prompt))
    
    unity.done_and_write() # writes


""" Tests """

async def createObjectNotAsTool(description: str, location: str, other_important_info: str) -> str:
    """ 
        Helper
    """
    agent = Agent(
        name="ObjectCreator" + str(random.randint(100, 999)),
        tools=[objectConsult],
        #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
        instructions= """
        Name the object and use the objectConsult tool to retrieve the asset path. Make sure the when you call the tool, make sure the location arg is in proper form, a dumped json of the form:
        {
            "x": float
            "y": float
            "z": float
        }
        """,
        model=MODEL
    )
    
    prompt = {"Description of object": description,
                "Intended location of object": location,
                "Other important info": other_important_info}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully called objectConsult."

async def test_skybox(prompt="A forest with the sun out"):
    

    global unity
    unity = UnityFile("test_skybox" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    unity.done_and_write()

async def test_leaves(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_leaves" + str(random.randint(100, 999)))
    
    await createObjectNotAsTool(description="a spruce tree", location={"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    await createObjectNotAsTool(description="a spruce tree", location={"x": -1145.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    await createObjectNotAsTool(description="a rock", location={"x": -1145.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    
    unity.done_and_write()
    


async def test_stem(prompt="Two trees"):
    

    global unity
    unity = UnityFile("test_stem" + str(random.randint(100, 999)))
    
    #await createSkyboxLeader(prompt) # success/fail
    
    section_leader0 = Agent(
        name="SectionLeaderL0",
        tools=[createObject],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leader0, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_stem_and_sky(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_stem_and_sky" + str(random.randint(100, 999)))
    
    await createSkyboxLeader(prompt) # success/fail
    
    section_leader0 = Agent(
        name="SectionLeaderL0",
        tools=[createObject],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leader0, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_L1(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_L1" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    section_leaderL1 = Agent(
        name="SectionLeaderL1",
        tools=[createSectionL0, createObject],
        instructions="""You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. If you do use createObject, reference only one object per call, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leaderL1, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_bridge_L1(prompt="A bridge in a forest"):
    global unity
    unity = UnityFile("test_bridge_L1" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    section_leaderL1 = Agent(
        name="SectionLeaderL1",
        tools=[createSectionL0, createObject],
        instructions="""You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. If you do use createObject, reference only one object per call, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leaderL1, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_lab(prompt="A laboratory"):
    global unity
    unity = UnityFile("test_laboratory" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    section_leaderL1 = Agent(
        name="SectionLeaderL1",
        tools=[createSectionL0, createObject],
        instructions="""You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. If you do use createObject, reference only one object per call, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leaderL1, json.dumps(prompt))
    
    unity.done_and_write()
    

test_dispatcher = {"test_leaves": test_leaves, "test_stem": test_stem, "test_skybox": test_skybox, "test_stem_and_sky": test_stem_and_sky, "test_L1": test_L1, "test_bridge_L1": test_bridge_L1, "test_lab": test_lab}

import sys
if __name__ == "__main__":
    prompt = "A forest"
    if sys.argv[1]:
        asyncio.run(test_dispatcher[sys.argv[1]]())
    else:
        asyncio.run(main(prompt))


















