# import subprocess

# subprocess.Popen([
#     "/Users/poy/envs/face_env/bin/python",
#     "/Users/poy/project/new/back_end/back_end_ai/flask_API/app_copy_back.py"
# ])

# import subprocess

# # 🔧 log ไปที่ face_recognition.log โดยตรง
# log_path = "/Users/poy/scripts/face_recognition.log"

# with open(log_path, "a") as out:
#     subprocess.Popen([
#         "/Users/poy/envs/face_env/bin/python",
#         "/Users/poy/project/new/back_end/back_end_ai/flask_API/app_fastAPI_back.py"
#     ], stdout=out, stderr=out)

import subprocess
log_path = "/Users/poy/scripts/face_recognition_back.log"
with open(log_path, "a") as log_file:
    subprocess.Popen([
        "/Users/poy/envs/face_env/bin/uvicorn",  # ✅ เรียก uvicorn ตรงจาก virtualenv
        "app_fastAPI_back:app",                        # ✅ module:object (ต้อง import ได้)
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "warning"
        "--access-log", "false" 
    ], stdout=log_file, stderr=log_file)