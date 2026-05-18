import os
import subprocess
import time
import requests
import json
import signal
import urllib.parse

INPUT_FILE = "data/raw/raw_file.csv"
OUTPUT_FILE = "data/cleaned/cleaned_file.csv"
OPERATIONS_FILE = "operations/operations.json"
BASE_URL = "http://127.0.0.1:3333"

os.makedirs("data/cleaned", exist_ok=True)


# OpenRefine headless

server = subprocess.Popen(
    ["/opt/openrefine/refine", "-i", "0.0.0.0", "-p", "3333", "-m", "4096M"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Ootame serveri käivitumist, kuni see on valmis päringuid vastu võtma (kuni 60 sekundit)
def wait_for_server():
    for _ in range(60):
        try:
            requests.get(BASE_URL)
            return
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    raise RuntimeError("OpenRefine failed to start")

wait_for_server()
print("OpenRefine is running")


# Alustame sessiooni, et säilitada küpsised ja CSRF tokenid
session = requests.Session()

def get_csrf():
    session.get(BASE_URL)
    for _ in range(10):
        try:
            resp = session.get(f"{BASE_URL}/command/core/get-csrf-token")
            resp.raise_for_status()
            token = resp.json().get("token")
            if token:
                return token
        except Exception:
            time.sleep(1)
    raise RuntimeError("Failed to get a valid CSRF token")

csrf = get_csrf()
print("CSRF token acquired:", csrf)


# Loome projekti CSV failist

with open(INPUT_FILE, "rb") as f:
    resp = session.post(
        f"{BASE_URL}/command/core/create-project-from-upload",
        params={"csrf_token": csrf},
        files={"project-file": f},
        data={
            "project-name": "cleaning_project",
            "format": "text/csv"
        },
        allow_redirects=False
    )

resp.raise_for_status()
if resp.status_code == 302:
    location = resp.headers.get("Location")
    if not location:
        raise RuntimeError("Project creation redirected but no Location header found")
    parse_result = urllib.parse.urlparse(location)
    query = urllib.parse.parse_qs(parse_result.query)
    project_id_list = query.get("project")
    if not project_id_list:
        raise RuntimeError(f"Unable to parse project ID from redirect location: {location}")
    project_id = project_id_list[0]
    print("Project created via redirect:", project_id)
else:
    try:
        result = resp.json()
    except ValueError:
        raise RuntimeError("Unexpected response when creating project")
    if result.get("code") == "error":
        raise RuntimeError(result["message"])
    project_id = result.get("projectID")
    if not project_id:
        raise RuntimeError("Project creation did not return a project ID")
    print("Project created:", project_id)


# Ootame, kuni projekt on täielikult valmis, enne kui proovime operatsioone rakendada (kuni 60 sekundit)

def wait_for_project(session, project_id, timeout=60):
    last_error = None
    for i in range(timeout):
        try:
            resp = session.get(
                f"{BASE_URL}/command/core/get-project-metadata",
                params={"project": project_id},
                timeout=5
            )
            if resp.status_code == 200:
                return
        except Exception as e:
            last_error = e
            time.sleep(1)
            continue
        time.sleep(1)
    raise RuntimeError(f"Project {project_id} not ready after {timeout} seconds. Last error: {last_error}")

wait_for_project(session, project_id)
print("Project is ready")


# Laeme operatsioonid failist

with open(OPERATIONS_FILE, "r") as f:
    operations = json.load(f)


# Rakendame operatsioonid projekti

csrf = get_csrf()  

resp = session.post(
    f"{BASE_URL}/command/core/apply-operations",
    data={
        "project": project_id,
        "csrf_token": csrf,
        "operations": json.dumps(operations)
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)
resp.raise_for_status()
print("Operations applied")


# Eksportime puhtad read CSV faili

csrf = get_csrf()  
export_url = f"{BASE_URL}/command/core/export-rows"
resp = session.post(
    export_url,
    data={
        "project": project_id,
        "format": "text/csv"
    }
)
resp.raise_for_status()

with open(OUTPUT_FILE, "wb") as f:
    f.write(resp.content)
print("Export complete:", OUTPUT_FILE)


# Sulgeme serveri

server.send_signal(signal.SIGTERM)
try:
    server.wait(timeout=10)
except subprocess.TimeoutExpired:
    server.kill()

print("Done")