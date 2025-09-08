""" Test.py """
import sys
from threading import Thread
import time # sub for actual prompting

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS



from dataclasses import dataclass, asdict
import json
    
app = Flask(__name__, static_folder="../dist")
CORS(app)

@dataclass
class Data:
    """ Example dataclass for potential structuring of scene. """
    name: str
    i: int

d = None

active_prompting_threads = []
class Prompting(Thread):
    """ Class that provides a .frame and updates it as a parallel thread. """
    def __str__(self):
        return self.prompt
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        time.sleep(10)
        



@app.route("/wait")
def wait():
    if d:
        return "last_ready"
    else:
        return "last_not_ready"    

    return response
    
@app.route("/prompt", methods=['POST'])
def prompt():
    prompt = request.form["prompt"]
    print("Prompt received")
    # start prompting thread
    new_thread = Prompting(prompt)
    
    
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
            print(f"Prompt {str(thread)} complete.")
            active_prompting_threads.remove(thread)
        
        pass
finally:
    app_thread.join()
    for thread in active_prompting_threads:
        thread.join()





