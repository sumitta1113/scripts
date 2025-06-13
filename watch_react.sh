#!/bin/bash

REACT_DIR="/Users/poy/project/new/display_ai/my-react-app/my-react-app"
PORT=5173
LOG_FILE="/Users/poy/scripts/react_watchdog.log"
MAX_MB=10

# ✅ เพิ่ม PATH ของ npm
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 🔁 ถ้า log เกิน 10MB → ลบทิ้ง
if [ -f "$LOG_FILE" ]; then
  FILE_SIZE_MB=$(du -m "$LOG_FILE" | cut -f1)
  if [ "$FILE_SIZE_MB" -gt "$MAX_MB" ]; then
    echo "$(date): 🧹 ลบ log เพราะเกิน ${MAX_MB}MB" > "$LOG_FILE"
  fi
fi


# ✅ เช็คว่ามี process ของ React dev server (Vite) รันอยู่หรือไม่
if pgrep -f "vite" > /dev/null; then
  echo "$(date): ✅ React Dev Server is running" >> "$LOG_FILE"
else
  echo "$(date): ❌ React Dev Server is NOT running → starting it now..." >> "$LOG_FILE"
  cd "$REACT_DIR" || exit
  npm run dev >> "$LOG_FILE" 2>&1 &
fi
