#
#       To start the GUI, run 
#       
#       python3 flask_server.py
#       
#       and go to localhost:5000




import os
import json
import asyncio
import time
from flask import Flask, request, render_template, jsonify, Response, stream_with_context
from multiprocessing import Process

from worldgen import AcrophobiaWorldGen, VRWorldGen

from logger import queue

MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"  
    

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            prompt = request.form['prompt']
            process = Process(target=run, args=(prompt, queue))
            process.daemon = True
            process.start()
            #return render_template('index.html', status="Running")
        except Exception:
            print("Bad post method.")
            render_template('index.html')
    return render_template('index.html')



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

async def async_run(prompt):
    gen = AcrophobiaWorldGen(prompt)
    await gen.load()
    final_output = await gen.regime(prompt)

"""
async def async_run(prompt):
    gen = AcrophobiaWorldGen(prompt)
    await gen.load()
    final_output = await gen.run(prompt)
"""
def run(prompt, queue):
    asyncio.run(async_run(prompt))
    



if __name__ == '__main__':
    print("Server restart...")
    app.run(debug=True) # 
    