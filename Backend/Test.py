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

MODEL="o3-mini"

class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()

    def addSkybox(self, meta_file):
        guid = yamling.get_guid(meta_file)
        self.yaml.set_skybox(guid)
    
    def add_prefab(self, name, meta_file, transform):
        guid = yamling.get_guid(meta_file)
        prefab_path = meta_file.removesuffix(".meta")
        self.yaml.add_prefab_instance(guid, prefab_path, transform)
        # fill out prefab based on guid, then add to self.file
        pass
        
    """
    def add_game_object(self, name, meta_file)
        # Only takes prefabs for now #
        guid = self.yaml.get_guid(meta_file)
        transform_ID = self.yaml.add_transform(guid)
        
        game_object_ID = self.yaml.add_game_object(guid, transform_ID)
        
        prefab_path = meta_file.removesuffix(".meta")
        self.yaml.add_prefab_instance(guid, prefab_path)
        return name
    """
    def done(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.dump(file_name)
        
global unity

@dataclass
class Designation(BaseModel):
    asset_path: str
    #next_agent: str
"""
@dataclass
class DesignedObject(BaseModel):
    name_of_object: str
    explanation: str
    #next_agent: str
"""  

#reference_blame = {}
 
@dataclass
class DesignedObject(BaseModel):
    game_object_name: str
    asset_path: str

 

@function_tool
def objectConsult(object_description: str, important_info: str) -> Designation:
    """ I get the object, I find the asset """
    """
    agent = Agent(
        name="ObjectConsultant" + random.randint(100, 999),
        tools=[createSectionLeader, createObject],
        output_type = Designation
        instructions="Return the path to the metafile of the desired asset." 
        model=MODEL
        
    )
    result = Runner.run(agent)
    return result.final_output
    """
    meta = "/home/olin/My project/Assets/Proxy Games/Stylized Nature Kit Lite/Prefabs/Foliage/Trees/Spruce 2.prefab.meta"
    
    return meta

    
    #global reference_blame[name] = "this agent"
  
@function_tool
def createObjectTool(description: str, location, other_important_info: str) -> DesignedObject:
    """ 
        Location is a dict: {"x": float, "y": float, "z": float}, for example, {"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}
    """  
    createObject(description, location, other_important_info)

def createObject(description: str, location, other_important_info: str) -> DesignedObject:
    """ 
        Location is a dict: {"x": float, "y": float, "z": float}, for example, {"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}
    """
    
    """
    prompt = {"Description of object": description}
    agent = Agent(
        name="ObjectCreator" + random.randint(100, 999),
        tools=[objectConsult],
        #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
        instructions= "Name the object and use the objectConsult tool to find retrieve the asset path."
        output_type=DesignedObject,
        model=MODEL
    )
    
    result = await Runner.run(agent, prompt)
    
    name = result.final_output.game_object_name

    unity.add_prefab(name, result.final_output.asset_path, location)
    """
    global unity
    
    unity.add_prefab("fsf", "/home/olin/My project/Assets/Proxy Games/Stylized Nature Kit Lite/Prefabs/Foliage/Trees/Spruce 2.prefab.meta", location)
    
    
    return
    return result.final_output
    
@function_tool
async def createSectionLeader(description: str, region: str):
    prompt = {"Description of your section": decription, "Region to work in": region}
    agent = Agent(
        name="SectionLeader" + random.randint(100, 999),
        tools=[createSectionLeader, createObject],
        instructions="You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene restricted to a region. (",
        model=MODEL
    )
    result = await Runner.run(agent, prompt)
    return result.final_output

def createSkyboxLeader(description: str="Plain blue sky"):
    """
    agent = Agent(
        name="SkyboxLeader",
        tools=[objectConsult]
    )
    """
    #asset_meta = objectConsult("skybox 2/ blue sky")
    asset_meta = "../Assets/Proxy Games/Stylized Nature Kit Lite/Materials/Skybox 2.mat.meta"
    
    global unity
    unity.addSkybox(asset_meta)
   
async def main(prompt):
    global unity
    unity = UnityFile("test0")
    
    createSkyboxLeader()

    createObject("a spruce tree", {"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}, "Clear for placement.")

    """
    agent = Agent(
        name="SectionLeader0",
        tools=[createSectionLeader, createObject],
        instructions="You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene restricted to a region",
    )
    
    result = await Runner.run(agent, prompt)
    """
    unity.done()

def select(function, prompt):
    result = function(prompt)   
     

if __name__ == "__main__":
    asyncio.run(main("Nothing"))

