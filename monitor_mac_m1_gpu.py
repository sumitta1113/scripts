import psutil
import subprocess
from datetime import datetime
import os
log_path = "/Users/poy/scripts/mac_m1_monitor.log"
max_mb = 10
max_bytes = max_mb * 1024 * 1024  # 10MB

# ✅ ถ้า log เกิน 10MB → ลบทิ้งด้วย rm -f
if os.path.exists(log_path):
    file_size = os.path.getsize(log_path)
    if file_size > max_bytes:
        # เขียน log ก่อนลบ (optional)
        with open(log_path, "a") as f:
            f.write(f"{datetime.now()}: 🔁 ลบ log เพราะเกิน {max_mb}MB ({file_size} bytes)\n")
        
        # 🔥 ใช้ rm -f แบบเดียวกับ bash
        subprocess.call(["rm", "-f", log_path])


# ✅ ดึง powermetrics
def get_powermetrics_output():
    try:
        return subprocess.check_output(
            ["sudo", "/usr/bin/powermetrics", "--show-all", "-n", "1"],
            stderr=subprocess.DEVNULL,
            timeout=10
        ).decode("utf-8")
    except Exception as e:
        return f"Error running powermetrics: {e}"

def extract_temperature(text):
    temperature = None
    for line in text.splitlines():
        if "average die temperature" in line.lower():
            temperature = line.strip()
            break
    return temperature or "🌡️ Temperature: -"

# ✅ ดึง GPU Info จาก powermetrics output
def extract_gpu_info(text):
    gpu_power = None
    frequency = None
    residency = None

    lines = text.splitlines()

    # ดึงค่าล่าสุด (ไม่ใช่แค่บรรทัดแรก)
    for line in lines:
        line_stripped = line.strip().lower()

        if "gpu power:" in line_stripped:
            gpu_power = line.strip()  # เอาอันล่าสุด
        elif "gpu hw active frequency" in line_stripped:
            frequency = line.strip()
        elif "gpu hw active residency" in line_stripped:
            residency = line.strip()

    # ถ้ายังหาไม่เจอ ใส่ "-"
    gpu_power = gpu_power or "GPU Power: -"
    frequency = frequency or "GPU HW active frequency: -"
    residency = residency or "GPU HW active residency: -"

    return gpu_power, frequency, residency

pm_output = get_powermetrics_output()
temperature = extract_temperature(pm_output)
gpu_power, gpu_freq, gpu_residency = extract_gpu_info(pm_output)

# ✅ เขียน log
with open(log_path, "a") as f:
    f.write(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    f.write(f"{temperature}\n")
    # CPU
    f.write(f"🔸 CPU Usage: {psutil.cpu_percent(interval=1)}%\n")

    # RAM
    mem = psutil.virtual_memory()
    f.write(f"🔸 RAM: {mem.percent}% ({mem.used / 1024**3:.2f} GB / {mem.total / 1024**3:.2f} GB)\n")
    per_core = psutil.cpu_percent(interval=1, percpu=True)
    for i, percent in enumerate(per_core):
        f.write(f"   🧠 CPU Core {i}: {percent}%\n")

    # Disk
    disk = psutil.disk_usage('/')
    f.write(f"🔸 Disk: {disk.percent}% used ({disk.used / 1024**3:.2f} GB)\n")

    # Network
    net = psutil.net_io_counters()
    f.write(f"🔸 Network Sent: {net.bytes_sent / 1024**2:.2f} MB | Received: {net.bytes_recv / 1024**2:.2f} MB\n")

    # GPU
    
    f.write(f"🎮 {gpu_power}\n")
    f.write(f"📶 {gpu_freq}\n")
    f.write(f"📊 {gpu_residency}\n")

    f.write("--------------------------------------------------\n")
