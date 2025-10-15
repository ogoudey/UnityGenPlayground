import os
import json
import asyncio
import time
from flask import Flask, request, render_template, jsonify, Response
from multiprocessing import Process
from flask_sock import Sock

from worldgen import AcrophobiaWorldGen, VRWorldGen

from logger import queue

MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"  
    

app = Flask(__name__)
sock = Sock(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        process = Process(target=run, args=(prompt, queue))
        process.daemon = True
        process.start()
        return render_template('index.html', prompt=prompt)
    return render_template('index.html')

def generate():
    while True:
        try:
            if not queue.empty():
                log_entry = queue.get_nowait()
                print("Queue has:", log_entry)
                payload = json.dumps(log_entry)  # {"message": "...", "type": "..."}
                yield f"data: {payload}\n\n"
        except Exception:

            time.sleep(0.1)

@app.route('/status_stream')
def status_stream():
    return Response(generate(), content_type='text/event-stream')

async def async_run(prompt):
    gen = AcrophobiaWorldGen(prompt)
    await gen.load()
    final_output = await gen.run(prompt)

def run(prompt, queue):
    asyncio.run(async_run(prompt))
    



if __name__ == '__main__':
    app.run(debug=True)