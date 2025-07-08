<<<<<<< HEAD
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, world!"}
=======
from flask import Flask, request, jsonify
from cortex import Cortex
import threading
import time
from pydispatch import dispatcher 

app = Flask(__name__)

print("Running EEG API server...")


class EEGInterface:
    def __init__(self, app_client_id, app_client_secret, **kwargs):
        self.client_id = app_client_id
        self.client_secret = app_client_secret
        self.c = Cortex(app_client_id, app_client_secret, debug_mode=True, **kwargs)
        self.record_id = None
        self.is_recording = False
        self.marker_idx = 0
        dispatcher.connect(self.on_create_session_done, signal='create_session_done')
        dispatcher.connect(self.on_create_record_done, signal='create_record_done')
        dispatcher.connect(self.on_stop_record_done, signal='stop_record_done')
        dispatcher.connect(self.on_export_record_done, signal='export_record_done')
        dispatcher.connect(self.on_inject_marker_done, signal='inject_marker_done')
        dispatcher.connect(self.on_inform_error, signal='inform_error')

        # Metadata
        self.record_title = "UnrealEEGSession"
        self.record_description = "Recorded via Unreal Engine interface"
        self.marker_value = "default_marker"
        self.marker_label = "default_label"
        self.record_export_folder = './exports'
        self.record_export_data_types = ['EEG']
        self.record_export_format = 'CSV'
        self.record_export_version = 'V2'

    def start_session(self):
        self.c.open()

    def stop_record(self):
        self.c.stop_record()

    def inject_marker(self, label="event", value="event_value"):
        marker_time = time.time() * 1000
        full_label = f"{label}_{self.marker_idx}"
        self.marker_idx += 1
        self.c.inject_marker_request(marker_time, value, full_label, port="unreal_api")

    def create_record(self):
        self.c.create_record(self.record_title, description=self.record_description)

    def on_create_session_done(self, *args, **kwargs):
        print("Session created. Creating record...")
        self.create_record()

    def on_create_record_done(self, *args, **kwargs):
        self.record_id = kwargs.get('data')['uuid']
        print(f"Recording started with ID: {self.record_id}")
        self.is_recording = True

    def on_stop_record_done(self, *args, **kwargs):
        self.is_recording = False
        print(f"Recording stopped: {kwargs.get('data')}")

    def on_export_record_done(self, *args, **kwargs):
        print("Export finished:", kwargs.get('data'))
        self.c.close()

    def on_inject_marker_done(self, *args, **kwargs):
        print("Marker injected:", kwargs.get('data'))

    def on_inform_error(self, *args, **kwargs):
        print("Error:", kwargs.get('error_data'))

eeg = EEGInterface(app_client_id="YOUR_APP_CLIENT_ID", app_client_secret="YOUR_APP_CLIENT_SECRET")

@app.route('/start', methods=['POST'])
def start():
    if eeg.is_recording:
        return jsonify({"status": "already recording"}), 400
    threading.Thread(target=eeg.start_session).start()
    return jsonify({"status": "starting session"}), 200

@app.route('/stop', methods=['POST'])
def stop():
    if not eeg.is_recording:
        return jsonify({"status": "no active recording"}), 400
    eeg.stop_record()
    return jsonify({"status": "stopping session"}), 200

@app.route('/marker', methods=['POST'])
def marker():
    data = request.json
    label = data.get("label", "event")
    value = data.get("value", "event_value")
    eeg.inject_marker(label, value)
    return jsonify({"status": "marker injected", "label": label, "value": value}), 200

if __name__ == '__main__':
    app.run(port=5000)
>>>>>>> a91625e (Initial commit with .gitignore and requirements.txt)
