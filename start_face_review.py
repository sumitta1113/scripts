# import subprocess

# subprocess.Popen([
#     "/Users/poy/envs/face_env/bin/python",
#     "/Users/poy/project/new/back_end/back_end_ai/flask_API/testcam.py"
# ])

import subprocess

# 🔧 log ไปที่ face_recognition.log โดยตรง
log_path = "/Users/poy/scripts/cam_stream.log"

subprocess.Popen([
    "/Users/poy/envs/face_env/bin/uvicorn",
    "testcam_fastAPI:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--log-level", "warning",  # ✅ ลด log ให้น้อยลง
    "--access-log", "false"    # (optional) ลด log HTTP request
    ], stdout=log_path, stderr=log_path)