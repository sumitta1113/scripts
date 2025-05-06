import subprocess
import datetime
import pytz
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
import time

load_dotenv()

# =========== CONFIG ===========

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
TIMEZONE = os.getenv('TIMEZONE')
LAST_RUN_FILE = os.getenv('LAST_RUN_FILE')

SCRIPT_PATHS = {
    'start_morning': os.getenv('START_MORNING_SCRIPT'),
    'stop_morning': os.getenv('STOP_MORNING_SCRIPT'),
    'start_review': os.getenv('START_REVIEW_SCRIPT'),
    'stop_review': os.getenv('STOP_REVIEW_SCRIPT'),
    'start_back': os.getenv('START_BACK_SCRIPT'),
    'stop_back': os.getenv('STOP_BACK_SCRIPT')
}
# =========== END CONFIG ===========

def load_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_last_run(data):
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(data, f)

def run_script(script):
    print(f"🔧 Running: {script}")
    subprocess.Popen(['/Users/poy/envs/face_env/bin/python', script])

def stop_script(pattern, port=None):
    print(f"🛑 Stopping: {pattern}")
    subprocess.run(['pkill', '-f', pattern])

    # check if process is dead
    for i in range(20):
        time.sleep(1)
        result = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True)
        if result.stdout.strip() == '':
            print(f"✅ Process '{pattern}' stopped")
            break
        else:
            print(f"⏳ Waiting for '{pattern}' to stop... (try {i+1}/10)")
    else:
        print(f"⚠️ Timeout: forcing kill for '{pattern}'")
        subprocess.run(['pkill', '-9', '-f', pattern])

    # check port is free
    if port:
        env = os.environ.copy()
        env["PATH"] = "/usr/sbin:" + env["PATH"]
        for i in range(20):
            time.sleep(1)
            result = subprocess.run(['/usr/sbin/lsof', '-i', f':{port}'], capture_output=True, text=True, env=env)
            if result.stdout.strip() == '':
                print(f"✅ Port {port} is now free")
                return
            else:
                # force kill by port owner if needed
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    pid = lines[1].split()[1]
                    print(f"⚠️ Force killing PID {pid} on port {port}")
                    subprocess.run(['kill', '-9', pid])
            print(f"⏳ Waiting for port {port} to be free... (try {i+1}/10)")
        print(f"⚠️ Timeout: Port {port} still in use after wait")

def is_time_to_run(now, target_time):
    return now.hour == target_time.hour and now.minute == target_time.minute

def main():
    print("🚀 Starting check_and_run.py")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    doc = collection.find_one()
    print(f"✅ Fetched document from MongoDB: {doc}")

    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz).replace(second=0, microsecond=0)
    print(f"⏰ Current time: {now}")

    events = {
        'start_morning': doc['start_morning'],
        'stop_morning': doc['stop_morning'],
        'start_evening': doc['start_evening'],
        'stop_evening': doc['stop_evening']
    }

    # map stop_morning → run stop_face.py + start_face_review.py
    # map start_evening → run stop_face_review.py + start_face_back.py
    # map stop_evening → run stop_face_back.py

    actions = {
        'start_morning': lambda: run_script(SCRIPT_PATHS['start_morning']),
        'stop_morning': lambda: (stop_script('start_face.py', port=8000), run_script(SCRIPT_PATHS['start_review'])),
        'start_evening': lambda: (stop_script('start_face_review.py', port=8000), run_script(SCRIPT_PATHS['start_back'])),
        'stop_evening': lambda: stop_script('start_face_back.py', port=8000)
     }
    last_run = load_last_run()
    print(f"📦 Last run data: {last_run}")
    now_time = now.time()
    for key, iso_time in events.items():
        if iso_time is None:
           continue
        if iso_time.tzinfo is None:
          iso_time = iso_time.replace(tzinfo=pytz.UTC)
        target_time = iso_time.astimezone(tz).time()
        print(f"🔍 Checking event '{key}' → target time: {target_time}")
        if is_time_to_run(now_time, target_time):
            print(f"⏰ Time match for {key}")
            if last_run.get(key) != now.strftime('%H:%M'):
               print(f"🚀 Triggering {key} at {now}")
               actions[key]()
               last_run[key] = now.strftime('%H:%M')
            else:
              print(f"⚠️ Already triggered {key} for this minute → skipping")
        else:
           print(f"⏭️ Not time for {key} yet")
    save_last_run(last_run)
    print("✅ Finished cycle\n")

if __name__ == "__main__":
    main()
