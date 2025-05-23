#!/bin/bash

REACT_DIR="/Users/poy/project/new/display_ai/my-react-app/my-react-app"
PORT=5173
LOG_FILE="/Users/poy/scripts/react_watchdog.log"
MAX_MB=10

# 🔁 ถ้า log เกิน 10MB → ลบทิ้ง
if [ -f "$LOG_FILE" ]; then
  FILE_SIZE_MB=$(du -m "$LOG_FILE" | cut -f1)
  if [ "$FILE_SIZE_MB" -gt "$MAX_MB" ]; then
    echo "$(date): 🧹 ลบ log เพราะเกิน ${MAX_MB}MB" > "$LOG_FILE"
  fi
fi

# 🔍 ตรวจว่า port 5173 มีอะไรฟังอยู่ไหม
if ! lsof -i :$PORT | grep -q "LISTEN"; then
    echo "$(date): 🚀 React dev server not running — starting it now..." >> "$LOG_FILE"
    cd "$REACT_DIR"
    npm run dev >> "$LOG_FILE" 2>&1 &
else
    echo "$(date): ✅ React server already running" >> "$LOG_FILE"
fi