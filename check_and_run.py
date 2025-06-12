import subprocess
import datetime
import pytz
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
import time
import logging
import socket

def wait_for_internet(timeout=30):
    print("🌐 Checking internet connection...")
    for i in range(timeout):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            print("✅ Internet is available")
            return True
        except OSError:
            print(f"⏳ Waiting for internet... ({i + 1}s)")
            time.sleep(1)
    print("❌ No internet connection after waiting.")
    return False

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
LOG_FILE = "/Users/poy/scripts/check_and_run.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def load_last_run():
    if os.path.exists(LAST_RUN_FILE):
        file_size = os.path.getsize(LAST_RUN_FILE)
        if file_size > 5 * 1024 * 1024:  # > 5MB ถือว่าแปลกแล้ว
            logging.warning(f"⚠️ last_run.json ใหญ่ผิดปกติ ({file_size} bytes), ลบทิ้งแล้วสร้างใหม่")
            os.remove(LAST_RUN_FILE)
            return {}
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
    logging.info(f"🛑 Stopping: {pattern}")
    subprocess.run(['pkill', '-f', pattern])

    # check if process is dead
    for i in range(20):
        time.sleep(1)
        result = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True)
        if result.stdout.strip() == '':
            logging.info(f"✅ Process '{pattern}' stopped")
            break
        else:
            print(f"⏳ Waiting for '{pattern}' to stop... (try {i+1}/10)")
    else:
        logging.warning(f"⚠️ Timeout: forcing kill for '{pattern}'")
        subprocess.run(['pkill', '-9', '-f', pattern])

    # check port is free
    if port:
        env = os.environ.copy()
        env["PATH"] = "/usr/sbin:" + env["PATH"]
        for i in range(20):
            time.sleep(1)
            result = subprocess.run(['/usr/sbin/lsof', '-i', f':{port}'], capture_output=True, text=True, env=env)
            if result.stdout.strip() == '':
                logging.info(f"✅ Port {port} is now free")
                return
            else:
                # force kill by port owner if needed
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    pid = lines[1].split()[1]
                    logging.warning(f"⚠️ Force killing PID {pid} on port {port}")
                    subprocess.run(['kill', '-9', pid])
        logging.warning(f"⚠️ Timeout: Port {port} still in use after wait")


def main():
    logging.info("🚀 Starting check_and_run.py")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    #doc = collection.find_one()
    # print(f"✅ Fetched document from MongoDB: {doc}")

    # tz = pytz.timezone(TIMEZONE)
    # now = datetime.datetime.now(tz).replace(second=0, microsecond=0)
    # print(f"⏰ Current time: {now}")

    # events = {
    #     'start_morning': doc['start_morning'],
    #     'stop_morning': doc['stop_morning'],
    #     'start_evening': doc['start_evening'],
    #     'stop_evening': doc['stop_evening']
    # }
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz).replace(second=0, microsecond=0)
    print(f"⏰ Current time: {now}")
    # หาช่วงเวลาเริ่มต้นและสิ้นสุดของวันนั้น
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    print(f"🔍 Querying between {start_of_day} and {end_of_day}")

    # ค้นหา document ที่ start_morning อยู่ในช่วงวันนี้
    doc = collection.find_one({
        "start_morning": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    })

    if not doc:
        logging.warning("❌ No schedule found for today.")
        return



    # ดึงเวลาออกมา
    events = {
        'start_morning': doc.get('start_morning'),
        'stop_morning': doc.get('stop_morning'),
        'start_evening': doc.get('start_evening'),
        'stop_evening': doc.get('stop_evening')
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
    #print(f"📦 Last run data: {last_run}")
    # ====== Enhanced Time Logic ======
    def get_dt(event):
        dt = events.get(event)
        if dt and dt.tzinfo:
            dt = dt.astimezone(tz).replace(tzinfo=None)
        return dt

    now = now.replace(tzinfo=None)

    for key in ['start_morning', 'stop_morning', 'start_evening', 'stop_evening']:
        target_dt = get_dt(key)
        if not target_dt:
            continue

        last = last_run.get(key)
        already_ran = last == target_dt.strftime('%Y-%m-%d %H:%M')

        if key == 'start_morning' and now >= target_dt and not already_ran:
            logging.info(f"✅ Triggering {key}")
            actions[key]()
            last_run[key] = target_dt.strftime('%Y-%m-%d %H:%M')

        elif key == 'stop_morning' and now >= target_dt and not already_ran:
            if 'start_morning' not in last_run:
                logging.warning("⚠️ Skipping start_morning (missed) → mocking it")
                last_run['start_morning'] = get_dt('start_morning').strftime('%Y-%m-%d %H:%M')
            logging.info(f"✅ Triggering {key}")
            actions[key]()
            last_run[key] = target_dt.strftime('%Y-%m-%d %H:%M')

        elif key in ['start_evening', 'stop_evening'] and now >= target_dt and not already_ran:
            logging.info(f"✅ Triggering {key}")
            actions[key]()
            last_run[key] = target_dt.strftime('%Y-%m-%d %H:%M')

        else:
            logging.info(f"⏭️ Skipping {key} (already ran or not yet time)")

    save_last_run(last_run)
    logging.info("✅ Finished cycle\n")

if __name__ == "__main__":
    if wait_for_internet(timeout=30):
        main()
    else:
        logging.error("❌ No internet. Skipping execution.")
