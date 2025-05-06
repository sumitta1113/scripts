#!/bin/bash

LOG_FILE="/Users/poy/scripts/check_and_run.log"
/Users/poy/envs/face_env/bin/python /Users/poy/scripts/check_and_run.py >> "$LOG_FILE" 2>&1

# เก็บแค่ 400 บรรทัดล่าสุด
tail -n 400 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_F