#
#       To start the GUI, run 
#       
#       python3 flask_server.py
#       
#       and go to localhost:5000

print("Before imports")


import os
import json
import asyncio
import time

print("STandard imports done")


from flask import Flask, request, render_template, jsonify, Response, stream_with_context
from multiprocessing import Process

print("Kess standard mports done")

from worldgen import AcrophobiaWorldGen, VRWorldGen

print("wiorld gen imports done")


from logger import queue

current_process = None  # global process handle

MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"  
    

app = Flask(__name__)

def get_all_asset_projects(dir="../Resources/Asset Projects"):
    try:
        return [
            name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))
        ]
    except Exception as e:
        print("Error listing folders:", e)
        return []


@app.route('/', methods=['GET', 'POST'])
def index():
    global current_process
    asset_projects = get_all_asset_projects()
    if request.method == 'GET':
        if current_process is not None and current_process.is_alive():
            print("Killing old process due to page reload...")
            current_process.terminate()
            current_process.join(timeout=1)
            current_process = None
            print("Clearing chat!")
            return render_template('index.html', asset_projects=asset_projects, clear_chat="true")
    elif request.method == 'POST':
        try:
            prompt = request.form['prompt']
            selected_asset_project = request.form.get('asset_project')
            print(selected_asset_project)
            if current_process is not None and current_process.is_alive():
                current_process.terminate()
                current_process.join(timeout=1)
            current_process = Process(target=run, args=(prompt, selected_asset_project))
            current_process.daemon = True
            current_process.start()
            return render_template('index.html', prompt="Running", asset_projects=asset_projects, selected_asset_project=selected_asset_project)
        except Exception:
            print("Bad post method.")
            render_template('index.html', prompt="Running", asset_projects=asset_projects)
    return render_template('index.html', prompt="Running", asset_projects=asset_projects)

async def async_run(prompt, asset_project_path):
    Class_Name = Class_from_Asset_Project[asset_project_path]
    gen = Class_Name(asset_project_path)
    await gen.load()
    final_output = await gen.regime(prompt)

def run(prompt, asset_project_path):
    asyncio.run(async_run(prompt, asset_project_path))

@app.route('/status_stream')
def status_stream():
    def generate():
        while True:
            try:
                if not queue.empty():
                    log_entry = queue.get_nowait()
                    print("Queue has:", log_entry)
                    payload = json.dumps(log_entry)  # {"message": "...", "type": "..."}
                    print("Sending payload")
                    yield f"data: {payload}\n\n"
                else:
                    # Always yield something periodically to keep the connection alive
                    yield ": keep-alive\n\n"
                    time.sleep(0.1)
            except Exception as e:
                print("Error in SSE:", e)
                time.sleep(1)
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables buffering in nginx, etc.
            "Connection": "keep-alive",
        }
    )


    

Class_from_Asset_Project = {
    "Acrophobia_v1": AcrophobiaWorldGen,
}

if __name__ == '__main__':
    print("Server restart...")
    app.run(debug=True) # 
    