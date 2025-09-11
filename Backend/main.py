""" Test.py """
import sys
from threading import Thread
import time # sub for actual prompting

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS


from dataclasses import dataclass, asdict
import json

import prompting
    
app = Flask(__name__, static_folder="../dist")
CORS(app)

last_ready = False

@dataclass
class Data:
    """ Example dataclass for potential structuring of scene. """
    name: str
    i: int

d = None

active_prompting_threads = []
class Prompting(Thread):
    """ Class that wraps prompting module """
    def __str__(self):
        return self.prompt
    
    def __init__(self, prompt, make_last):
        super().__init__()
        self.prompt = prompt
        self.make_last = make_last

    def run(self):
        global last_ready
        last_ready = False
        result = prompting.run_prompt(self.prompt, self.make_last)
        last_ready = True
        
class Correcting(Thread):
    """ Class that wraps prompting module """
    def __str__(self):
        return "Corrections to " + self.path.split("Scenes/")[-1]
    
    def __init__(self, path, errors, make_last):
        super().__init__()
        self.errors = errors
        self.path = path
        self.make_last = make_last

    def run(self):
        global last_ready
        last_ready = False
        result = prompting.run_correction(self.path, self.errors, self.make_last)
        last_ready = True



@app.route("/wait")
def wait():
    global last_ready
    if last_ready:
        last_ready = False
        return_ = "last_ready"
    else:
        return_ = "last_not_ready" 
    print(" --> processing...")
    return return_   
    
@app.route("/prompt", methods=['POST'])
def prompt():
    prompt = request.form["prompt"]
    make_last = request.form["make_last"] == "True"
    
    print("Recieved:", request.form["make_last"], "of type", type(request.form["make_last"]))
    print("Prompt received with make_last ==", make_last)
    # start prompting thread
    new_thread = Prompting(prompt, make_last)
    
    
    new_thread.start()
    active_prompting_threads.append(new_thread)
    response = "prompting"
    return response    

@app.route("/errors", methods=['POST'])
def take_errors():
    path = request.form["path"]
    errors = request.form["errors"]
    print("Errors received")
    # start prompting thread
    new_thread = Correcting(path, errors, make_last=True)
    
    
    new_thread.start()
    active_prompting_threads.append(new_thread)
    response = "prompting"
    return response 

"""      
@app.route("/prompt", methods=['POST'])

    if message == "Deploy.":
        if d:
            return json.dumps(asdict(d), indent=4)
        
        else:
            
            return "World not ready yet."

"""

def run_flask():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    print("Running on", host)
    #d = Data(name="Phil", i=2)    # Do in parallel with server
    app.run(host=host, port=5000) # Do in parallel with prompting
  

app_thread = Thread(target=run_flask)

try:
    app_thread.start()
    while True:
        print(f"\r\033[K{len(active_prompting_threads)} active threads: {[str(t) for t in active_prompting_threads]}", end="")
        threads_to_rm = []
        for thread in active_prompting_threads:
            if not thread.is_alive():
                threads_to_rm.append(thread)
        for thread in threads_to_rm:
            print(f"\nPrompt '{str(thread)}' complete.")
            active_prompting_threads.remove(thread)
        
        pass
finally:
    app_thread.join()
    for thread in active_prompting_threads:
        thread.join()





