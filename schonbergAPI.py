import requests
import json

class SchonbergLabAPI:
    BASE_URL = "https://experiments.schonberglab.org/v2/workers-api/sessions"

    def __init__(self, worker_key):
        self.worker_key = worker_key

    def get_all_sessions(self):
        url = f"{self.BASE_URL}?key={self.worker_key}"
        response = requests.get(url)
        return response.json()

    def add_new_session(self, data):
        url = f"{self.BASE_URL}?key={self.worker_key}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    def get_session_with_id(self, session_id):
        url = f"{self.BASE_URL}/{session_id}?key={self.worker_key}"
        response = requests.get(url)
        return response.json()

    def update_session(self, session_id ,data):
        data["_id"] = session_id
        url = f"{self.BASE_URL}?key={self.worker_key}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()