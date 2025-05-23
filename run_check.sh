#!/bin/bash

LOCKFILE="/tmp/run_check.lock"
LOG_FILE="/Users/poy/scripts/check_and_run.log"
MAX_MB=10
MAX_BYTES=$(echo "$MAX_MB * 1024 * 1024" | bc | cut -d'.' -f1)  # แปลงเป็น byte

# ถ้ามี lock อยู่ → ไม่รันซ้ำ
if [ -f "$LOCKFILE" ]; then
    echo "$(date): Already running, skipping this round" >> "$LOG_FILE"
    exit 0
fi

# 🔁 ถ้า log เกิน 10MB ให้ลบทิ้ง
if [ -f "$LOG_FILE" ]; then
    FILE_SIZE_BYTES=$(stat -f%z "$LOG_FILE")  # ใช้ stat บน macOS
    if [ "$FILE_SIZE_BYTES" -gt "$MAX_BYTES" ]; then
        echo "$(date): 🔁 ลบ log เดิม เพราะเกิน ${MAX_MB}MB ($FILE_SIZE_BYTES bytes)" >> "$LOG_FILE"
        rm -f "$LOG_FILE"
    fi
fi

# สร้าง lock
touch "$LOCKFILE"

/Users/poy/envs/face_env/bin/python /Users/poy/scripts/check_and_run.py >> "$LOG_FILE" 2>&1


# ลบ lock หลังเสร็จ
rm -f "$LOCKFILE"