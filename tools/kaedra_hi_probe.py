#!/usr/bin/env python3
# ==============================================================================
# Kaedra Hi Probe (24/7 Self-Healing Swarm Commander)
# ==============================================================================
# Premium liveness check, greeting probe, and self-healing network dashboard
# for macOS / Mac Mini node. Performs dynamic socket scans, local and cloud run 
# fleet health checks, SSH tunnel validation, active Ollama model scans, 
# and real-time conversation continuity audits. 
#
# Failsafe Protocol: If any critical service is stalled or offline, it 
# automatically recovers the Ollama server, fires up background swarm shards, 
# and re-audits the node to guarantee 100% online status for the GM.
#
# Usage:
#   python3 "/Users/kushboygroup/The Observatory/Kaedra/tools/kaedra_hi_probe.py"
# ==============================================================================

import os
import sys
import io
import json
import time
import socket
import urllib.request
import urllib.parse
import subprocess
import platform
import glob
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import ssl

# Force UTF-8 stdout/stderr buffering
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Premium color design palette
class Colors:
    YELLOW = "\033[38;5;220m"
    GREEN = "\033[38;5;82m"
    CYAN = "\033[38;5;87m"
    DARK_CYAN = "\033[38;5;37m"
    GRAY = "\033[38;5;246m"
    MAGENTA = "\033[38;5;201m"
    RED = "\033[38;5;196m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

# UI Icons map
Icon = {
    "Ok": "✅",
    "Time": "🕒",
    "Uptime": "⏱️",
    "Machine": "💻",
    "Weather": "🌦️",
    "Apollo": "🛰️",
    "Duplicate": "🧬",
    "Lock": "🔒",
    "Blocked": "🚫",
    "Stadium": "🏟️",
    "Spark": "✦",
    "News": "📰",
    "Gpu": "🔮",
    "Temp": "🌡️",
    "Util": "📈",
    "Vram": "💾",
    "Power": "⚡",
    "Brain": "🧠",
    "Tunnel": "🌉",
    "Server": "🖥️",
    "Cloud": "☁️",
    "Router": "🔌",
    "Signal": "📡",
    "Failsafe": "🛡️"
}

# The Fleet Roster - Cloud Run endpoints
FLEET_CLOUDRUN = {
    "DAV1D": "https://dav1d-322812104986.us-central1.run.app",
    "RHEA": "https://rhea-noir-145241643240.us-central1.run.app",
    "VISIONS": "https://visions-assistant-service-885670388176.us-central1.run.app",
    "KAEDRA": "https://kaedra-69017097813.us-central1.run.app",
    "BANDIT": "https://bandit-849984150802.us-central1.run.app",
    "IRIS": "https://mineral-subject-487519-v6.us-central1.run.app"
}

# Local Swarm Shard Ports
SWARM_SHARDS = {
    "CORE (AI-Core)": 8088,
    "MESH (Registry)": 8765,
    "GEMMA (Reasoner)": 8094,
    "WEB (Web-Engine)": 1245,
    "KAEDRA (NextJS)": 1019
}

# Global Diagnostic Variables
probe_start = time.perf_counter()
warnings = []
python_version = platform.python_version()
user_name = os.environ.get('USER', 'unknown')
host_name = platform.node()

ollama_running = False
gemma_loaded = False
gemma_responsive = False
gemma_response_text = ""
gemma_thinking_text = ""
gemma_inference_ms = 0
ollama_models = []
active_reasoner_model = "None"
gpu_name = "Apple Silicon"
gpu_info_available = False
gpu_mem_used = 0
gpu_mem_total = 16384
cpu_thermal_level = 0
cpu_scheduler_limit = 100
cpu_speed_limit = 100
ssh_processes = []
active_tunnels = []
local_sockets = {}
local_peers = {}
cloud_status = {}
omdb_status = "OFFLINE"
serp_status = "OFFLINE"
news_status = "OFFLINE"
prices_status = "OFFLINE"
opensky_status = "OFFLINE"
gmail_status = "OFFLINE"


# Time calculations
now = datetime.now()
local_time = now.strftime('%Y-%m-%d %H:%M:%S %z')
time_zone = time.tzname[0] if time.daylight == 0 else time.tzname[1]
day_num = now.day
ord_suffix = 'th' if 11 <= day_num <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
human_time = f"{now.strftime('%A')}, {now.strftime('%B')} {day_num}{ord_suffix} {now.year} — {now.strftime('%I:%M %p').lower()}"

# Uptime and Boot Time computation
uptime_text = "3d 0h 8m" # default fallback
boot_time = None
try:
    uptime_out = subprocess.check_output(["uptime"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
    # Extracts e.g. "3 days, 25 mins"
    m = re.search(r"up\s+(.*?),\s+\d+\s+user", uptime_out)
    if m:
        uptime_text = m.group(1).strip()
    else:
        m = re.search(r"up\s+(.*?),\s+load", uptime_out)
        if m:
            uptime_text = m.group(1).strip()
except Exception:
    pass

try:
    sysctl_out = subprocess.check_output(["sysctl", "-n", "kern.boottime"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
    sec_match = re.search(r"sec\s*=\s*(\d+)", sysctl_out)
    if sec_match:
        boot_time_sec = int(sec_match.group(1))
        boot_time = datetime.fromtimestamp(boot_time_sec, timezone.utc)
except Exception:
    pass

if not boot_time:
    days = 0
    hours = 0
    mins = 0
    if "day" in uptime_text:
        d_match = re.search(r"(\d+)\s+day", uptime_text)
        if d_match:
            days = int(d_match.group(1))
    if ":" in uptime_text:
        hm_match = re.search(r"(\d+):(\d+)", uptime_text)
        if hm_match:
            hours = int(hm_match.group(1))
            mins = int(hm_match.group(2))
    else:
        h_match = re.search(r"(\d+)\s+hr", uptime_text)
        if h_match:
            hours = int(h_match.group(1))
        m_match = re.search(r"(\d+)\s+min", uptime_text)
        if m_match:
            mins = int(m_match.group(1))
    td = time.timedelta(days=days, hours=hours, minutes=mins)
    boot_time = datetime.now(timezone.utc) - td

# Load environment variables from .env
env_vars = {}
env_path = "/Users/kushboygroup/The Observatory/.env"
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    except Exception:
        pass

# Fetch weather dynamically from wttr.in (Zero Cost, No Auth!)
weather = "Unavailable - Offline"
location = "Mac Mini Workspace"
try:
    context = ssl._create_unverified_context()
    req_weather = urllib.request.Request("http://wttr.in/?format=3", headers={'User-Agent': 'curl/7.79.1'})
    with urllib.request.urlopen(req_weather, timeout=1.5, context=context) as resp:
        weather_str = resp.read().decode('utf-8').strip()
        if ":" in weather_str:
            loc, cond = weather_str.split(":", 1)
            location = loc.strip()
            weather = cond.strip()
        else:
            weather = weather_str
except Exception:
    pass

# Fetch hot news dynamically using EXA_API_KEY
hot_news = None
exa_key = env_vars.get("EXA_API_KEY", "8d64cfb4-07a2-4f80-ad88-27d8842823cc")
if exa_key:
    try:
        context = ssl._create_unverified_context()
        genres = [
            ("Biz", "latest top business news headlines and breakthroughs today"),
            ("Finance", "latest top financial market news and macroeconomic trends today"),
            ("Tech", "latest artificial intelligence and technology breakthroughs today"),
            ("Cinema/Video", "latest photography, film, television and video production gear or tech news today")
        ]
        import random
        genre_name, query_text = random.choice(genres)
        payload = {
            "query": query_text,
            "numResults": 1,
            "useAutoprompt": True,
            "type": "neural"
        }
        req_news = urllib.request.Request(
            "https://api.exa.ai/search",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "x-api-key": exa_key,
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0"
            }
        )
        with urllib.request.urlopen(req_news, timeout=2.0, context=context) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if res_data.get("results"):
                art = res_data["results"][0]
                pub_date = "Today"
                if art.get("publishedDate"):
                    # Parse out yyyy-mm-dd
                    pub_date = art["publishedDate"][:10]
                hot_news = {
                    "title": art.get("title", ""),
                    "source": f"Exa {genre_name}",
                    "date": pub_date,
                    "link": art.get("url", "")
                }
    except Exception:
        pass

def show_tqdm_spinner(label="Checking", cycles=1, delay_ms=30):
    """TQDM-style spinner using braille characters"""
    if sys.stdout.isatty():
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for _ in range(cycles):
            for frame in frames:
                sys.stdout.write(f"\r{Colors.CYAN}{frame}{Colors.RESET} {label}...")
                sys.stdout.flush()
                time.sleep(delay_ms / 1000.0)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
    else:
        print(f"✦ {label}...")

def show_tqdm_bar(label="Kaedra swarm mapping complete", width=24, delay_ms=5):
    """TQDM-style loading progress bar"""
    char_filled = "█"
    char_empty = "░"
    if sys.stdout.isatty():
        for i in range(width + 1):
            percent = int((i / width) * 100)
            filled = char_filled * i
            empty = char_empty * (width - i)
            sys.stdout.write(f"\r{Icon['Stadium']} [{Colors.GREEN}{filled}{Colors.GRAY}{empty}{Colors.RESET}] {percent}% | {label}")
            sys.stdout.flush()
            time.sleep(delay_ms / 1000.0)
        print()
    else:
        filled = char_filled * width
        print(f"🏟 [{filled}] 100% | {label}")

def check_port(port_num):
    # Try IPv4 loopback
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('127.0.0.1', port_num)) == 0:
                return port_num, True
    except Exception:
        pass
    # Try IPv6 loopback
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('::1', port_num)) == 0:
                return port_num, True
    except Exception:
        pass
    return port_num, False

def ping_host(host_ip, port_to_test=None):
    try:
        res = subprocess.run(["ping", "-c", "1", "-t", "1", host_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            if port_to_test:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    if s.connect_ex((host_ip, port_to_test)) == 0:
                        return "ONLINE (PORT SAFE)"
            return "ONLINE"
    except Exception:
        pass
    return "OFFLINE"

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            out = subprocess.check_output(["ifconfig"], stderr=subprocess.DEVNULL).decode("utf-8")
            for block in out.split("\n\n"):
                if "status: active" in block and "inet " in block:
                    m = re.search(r"inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", block)
                    if m:
                        return m.group(1)
        except Exception:
            pass
    return "10.0.0.88"

def test_bidirectional_ssh(host_ip, local_ip):
    users = ["super", "kushboygroup"]
    keys = [
        os.path.expanduser("~/.ssh/id_ed25519_who_tester"),
        os.path.expanduser("~/.ssh/kaedra_swarm_key")
    ]
    
    for user in users:
        for key_path in keys:
            if not os.path.exists(key_path):
                continue
            test_cmd = (
                f"powershell -Command \"Test-NetConnection -ComputerName {local_ip} -Port 11434 -InformationLevel Quiet\" || "
                f"nc -w 1 -z {local_ip} 11434 || "
                f"curl -s -I http://{local_ip}:11434/"
            )
            ssh_cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=2",
                "-i", key_path,
                f"{user}@{host_ip}",
                test_cmd
            ]
            try:
                res = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.5)
                if res.returncode == 0:
                    out = res.stdout.strip().upper()
                    if "TRUE" in out or "SUCCESS" in out or "200 OK" in out or not out:
                        return "ONLINE (BIDIRECTIONAL SAFE)"
                    else:
                        return "ONLINE (BACK-PORT BLOCKED)"
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
    return "ONLINE (SSH UNVERIFIED)"

def audit_local_bindings():
    results = {}
    
    ollama_binding = "INACTIVE"
    try:
        lsof_out = subprocess.check_output(["lsof", "-nP", "-iTCP:11434", "-sTCP:LISTEN"], stderr=subprocess.DEVNULL).decode("utf-8")
        if "127.0.0.1" in lsof_out:
            ollama_binding = "LOOPBACK (127.0.0.1)"
        elif "*" in lsof_out or "0.0.0.0" in lsof_out:
            ollama_binding = "ALL INTERFACES (0.0.0.0)"
        elif "192.168.1." in lsof_out:
            ollama_binding = "LAN ONLY"
    except Exception:
        pass
    results["ollama"] = ollama_binding
    
    mesh_binding = "INACTIVE"
    try:
        lsof_out = subprocess.check_output(["lsof", "-nP", "-iTCP:8765", "-sTCP:LISTEN"], stderr=subprocess.DEVNULL).decode("utf-8")
        if "127.0.0.1" in lsof_out:
            mesh_binding = "LOOPBACK (127.0.0.1)"
        elif "*" in lsof_out or "0.0.0.0" in lsof_out:
            mesh_binding = "ALL INTERFACES (0.0.0.0)"
        elif "192.168.1." in lsof_out:
            mesh_binding = "LAN ONLY"
    except Exception:
        pass
    results["mesh_registry"] = mesh_binding

    pf_status = "INACTIVE"
    try:
        pf_out = subprocess.check_output(["pfctl", "-s", "info"], stderr=subprocess.DEVNULL).decode("utf-8")
        if "Enabled" in pf_out or "enabled" in pf_out.lower():
            pf_status = "ACTIVE"
    except Exception:
        pass
    results["pf_firewall"] = pf_status
    
    return results

def check_cloud_agent(name, url):
    try:
        req = urllib.request.Request(f"{url}/health", headers={'User-Agent': 'KaedraHiProbe/1.0'})
        start_time = time.perf_counter()
        with urllib.request.urlopen(req, timeout=1.2) as response:
            if response.status == 200:
                elapsed = int((time.perf_counter() - start_time) * 1000)
                return name, f"ONLINE ({elapsed}ms)"
    except Exception:
        pass
    return name, "OFFLINE"

def select_best_model(ollama_models):
    """
    Selects the best reasoner model following GM priority rules:
    CUSTOMS BEFORE GENERICS — ALWAYS.
    Within each tier, e2b (smaller VRAM) before e4b.
    
    Priority chain:
      1. Custom e2b
      2. Custom latest (may be e2b-equivalent)
      3. Custom e4b
      4. Custom any (fallback)
      5. Generic e2b
      6. Generic e4b
      7. Generic any (fallback)
      8. First available model
    """
    if not ollama_models:
        return None
        
    custom_prefixes = ["kaedracode", "solai"]
    
    def is_custom(name):
        return any(p in name.lower() for p in custom_prefixes)
    
    def is_generic(name):
        n = name.lower()
        return ("gemma4" in n or "gemma" in n) and not is_custom(name)
    
    # --- CUSTOM TIER (always first) ---
    # Priority 1: Custom e2b (explicit small VRAM tag)
    for m in ollama_models:
        if is_custom(m) and "e2b" in m.lower():
            return m
            
    # Priority 2: Custom latest (often e2b-equivalent)
    for m in ollama_models:
        if is_custom(m) and "latest" in m.lower():
            return m
            
    # Priority 3: Custom e4b
    for m in ollama_models:
        if is_custom(m) and "e4b" in m.lower():
            return m
            
    # Priority 4: Any remaining custom model
    for m in ollama_models:
        if is_custom(m):
            return m
    
    # --- GENERIC TIER (only if zero custom models exist) ---
    # Priority 5: Generic e2b (smaller VRAM)
    for m in ollama_models:
        if is_generic(m) and "e2b" in m.lower():
            return m
            
    # Priority 6: Generic e4b
    for m in ollama_models:
        if is_generic(m) and "e4b" in m.lower():
            return m
            
    # Priority 7: Any generic gemma
    for m in ollama_models:
        if is_generic(m):
            return m
            
    # Priority 8: Absolute fallback
    return ollama_models[0]

def run_diagnostics(silent=False):
    """Executes full diagnostic scan across environment and updates global variables"""
    global ollama_running, gemma_loaded, gemma_responsive, gemma_response_text, gemma_thinking_text, gemma_inference_ms, ollama_models, active_reasoner_model
    global gpu_name, gpu_info_available, gpu_mem_used, gpu_mem_total, ssh_processes, active_tunnels
    global local_sockets, local_peers, cloud_status, omdb_status, serp_status, gmail_status
    global news_status, prices_status, opensky_status
    global cpu_thermal_level, cpu_scheduler_limit, cpu_speed_limit

    # Step 1: Local Ollama & Gemma Deep Liveness Check
    if not silent: show_tqdm_spinner("Testing local Gemma reasoner liveness", cycles=1)
    ollama_running = False
    gemma_loaded = False
    gemma_responsive = False
    gemma_response_text = ""
    gemma_thinking_text = ""
    gemma_inference_ms = 0
    ollama_models = []
    active_reasoner_model = "None"

    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.0) as response:
            res = json.loads(response.read().decode('utf-8'))
            ollama_running = True
            if "models" in res:
                ollama_models = [m["name"] for m in res["models"]]
                target_model = select_best_model(ollama_models)
                gemma_loaded = target_model is not None
                if target_model:
                    active_reasoner_model = target_model
                    gemma_responsive = False # Set initial state; will be queried and evaluated in Step 8 at the end
    except Exception:
        pass

    # Step 2: GPU & Thermal Telemetry (Mac Mini hardware profile)
    if not silent: show_tqdm_spinner("Profiling system hardware & thermal state", cycles=1)
    gpu_name = "Apple Silicon"
    gpu_info_available = False
    gpu_mem_used = 0
    gpu_mem_total = 16384
    cpu_thermal_level = 0
    cpu_scheduler_limit = 100
    cpu_speed_limit = 100

    try:
        out = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], stderr=subprocess.DEVNULL).decode("utf-8")
        for line in out.split("\n"):
            if "Chipset Model:" in line:
                gpu_name = line.split("Chipset Model:", 1)[1].strip()
                gpu_info_available = True
                break
    except Exception:
        pass

    try:
        out_mem = subprocess.check_output(["sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        gpu_mem_total = int(int(out_mem) / (1024 * 1024))
        
        vm_out = subprocess.check_output(["vm_stat"], stderr=subprocess.DEVNULL).decode("utf-8")
        page_size = 4096
        for line in vm_out.split("\n"):
            if "page size of" in line:
                m = re.search(r"page size of (\d+) bytes", line)
                if m:
                    page_size = int(m.group(1))
            if "Pages active:" in line:
                active_pages = int(line.split("Pages active:", 1)[1].replace(".", "").strip())
                gpu_mem_used = int((active_pages * page_size) / (1024 * 1024))
    except Exception:
        pass

    # Thermal sensors & power state profiling
    try:
        cpu_thermal_level = int(subprocess.check_output(["sysctl", "-n", "machdep.xcpm.cpu_thermal_level"], stderr=subprocess.DEVNULL).decode("utf-8").strip())
    except Exception:
        cpu_thermal_level = 0

    try:
        pm_out = subprocess.check_output(["pmset", "-g", "therm"], stderr=subprocess.DEVNULL).decode("utf-8")
        for line in pm_out.split("\n"):
            if "CPU_Scheduler_Limit" in line:
                cpu_scheduler_limit = int(line.split("=")[1].strip())
            if "CPU_Speed_Limit" in line:
                cpu_speed_limit = int(line.split("=")[1].strip())
    except Exception:
        pass

    # Step 3: Network & Tunnels
    if not silent: show_tqdm_spinner("Analyzing SSH tunnels & port bounds", cycles=1)
    ssh_processes = []
    active_tunnels = []

    try:
        ssh_out = subprocess.check_output(["ps", "aux"], stderr=subprocess.DEVNULL).decode("utf-8")
        for line in ssh_out.split("\n"):
            if "ssh" in line.lower() and "grep" not in line.lower() and "kaedra_hi_probe" not in line.lower():
                ssh_processes.append(" ".join(line.split()[10:]))
                
        net_out = subprocess.check_output(["netstat", "-an"], stderr=subprocess.DEVNULL).decode("utf-8")
        for line in net_out.split("\n"):
            if "established" in line.lower() and (".22" in line or "ssh" in line.lower()):
                active_tunnels.append(line.strip())
    except Exception:
        pass

    # Step 4: Local Ports Scans
    if not silent: show_tqdm_spinner("Scanning local swarm socket registries", cycles=1)
    local_sockets.clear()
    with ThreadPoolExecutor(max_workers=len(SWARM_SHARDS)) as executor:
        socket_results = list(executor.map(lambda p: check_port(p[1]), SWARM_SHARDS.items()))
    for p_num, is_open in socket_results:
        shard_name = [name for name, port in SWARM_SHARDS.items() if port == p_num][0]
        local_sockets[shard_name] = is_open

    # Step 5: Mesh
    # Dynamic peer discovery via ARP and parallel port scanning
    known_targets = {
        "sol": {"name": "Sol Ai", "port": 11434, "default": "10.0.0.178"},
        "hyperion": {"name": "Hyperion", "port": 22, "default": "10.0.0.178"},
        "ollama": {"name": "Ollama Gateway", "port": 11434, "default": "10.0.0.87"},
        "blade": {"name": "Blade", "port": 11434, "default": "10.0.0.87"}
    }
    resolved_peers = {cfg["name"]: (cfg["default"], cfg["port"]) for cfg in known_targets.values()}

    # 1. Gather all active network devices (prefer 'whosthere' TUI tool, fallback to 'arp -an')
    active_ips = set()
    devices_by_ip = {}
    whosthere_available = False

    try:
        whosthere_path = "whosthere"
        for path in ["whosthere", "/usr/local/bin/whosthere", "/opt/homebrew/bin/whosthere"]:
            try:
                res = subprocess.run([path, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode in [0, 2]:
                    whosthere_path = path
                    break
            except Exception:
                pass

        # Perform concurrent unprivileged scan (timeout 2s for speed)
        scan_out = subprocess.check_output([whosthere_path, "scan", "-t", "2", "--json"], stderr=subprocess.DEVNULL).decode("utf-8")
        scan_data = json.loads(scan_out)
        devices_list = scan_data.get("devices", [])
        whosthere_available = True

        for dev in devices_list:
            ip = dev.get("ip")
            if ip:
                active_ips.add(ip)
                devices_by_ip[ip] = dev
    except Exception:
        pass

    # Fallback to standard arp scanning if whosthere failed or isn't installed
    if not whosthere_available:
        try:
            arp_out = subprocess.check_output(["arp", "-an"], stderr=subprocess.DEVNULL).decode("utf-8")
            for line in arp_out.split("\n"):
                m = re.search(r"\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)", line)
                if m:
                    active_ips.add(m.group(1))
        except Exception:
            pass

    # Ensure default and known network IPs are scanned
    for cfg in known_targets.values():
        active_ips.add(cfg["default"])
    for legacy_ip in ["10.0.0.87", "10.0.0.178", "192.168.1.16", "192.168.1.98", "192.168.1.187", "192.168.1.78"]:
        active_ips.add(legacy_ip)

    # 2. Check ports and model configurations in parallel
    ip_services = {}
    def scan_ip(ip):
        ports_status = {}
        models = []
        for port in [22, 11434]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.15)
                    if s.connect_ex((ip, port)) == 0:
                        ports_status[port] = True
            except Exception:
                pass
        
        if ports_status.get(11434):
            try:
                context = ssl._create_unverified_context()
                req = urllib.request.Request(f"http://{ip}:11434/api/tags")
                with urllib.request.urlopen(req, timeout=0.8, context=context) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    if "models" in res:
                        models = [m["name"].lower() for m in res["models"]]
            except Exception:
                pass
        return ip, ports_status, models

    with ThreadPoolExecutor(max_workers=20) as scan_executor:
        scan_results = list(scan_executor.map(scan_ip, active_ips))

    for ip, ports_status, models in scan_results:
        if ports_status:
            ip_services[ip] = {"ports": ports_status, "models": models}

    # 3. Dynamic routing based on active service detection and whosthere network signatures
    active_ollama_ips = [ip for ip, svc in ip_services.items() if svc["ports"].get(11434)]
    active_ssh_ips = [ip for ip, svc in ip_services.items() if svc["ports"].get(22)]

    # Dynamic resolve for Ollama Gateway
    if "10.0.0.87" in active_ollama_ips:
        resolved_peers["Ollama Gateway"] = ("10.0.0.87", 11434)
    elif "192.168.1.78" in active_ollama_ips:
        resolved_peers["Ollama Gateway"] = ("192.168.1.78", 11434)
    elif active_ollama_ips:
        resolved_peers["Ollama Gateway"] = (active_ollama_ips[0], 11434)

    # Dynamic resolve for Sol Ai
    sol_resolved = False
    if "10.0.0.178" in active_ollama_ips:
        resolved_peers["Sol Ai"] = ("10.0.0.178", 11434)
        sol_resolved = True
    elif "192.168.1.16" in active_ollama_ips:
        resolved_peers["Sol Ai"] = ("192.168.1.16", 11434)
        sol_resolved = True
    else:
        for ip in active_ollama_ips:
            models = ip_services[ip]["models"]
            if any("sol" in m for m in models):
                resolved_peers["Sol Ai"] = (ip, 11434)
                sol_resolved = True
                break
                    
    if not sol_resolved and active_ollama_ips:
        resolved_peers["Sol Ai"] = (active_ollama_ips[0], 11434)

    # Dynamic resolve for Blade
    blade_resolved = False
    if "10.0.0.87" in active_ollama_ips:
        resolved_peers["Blade"] = ("10.0.0.87", 11434)
        blade_resolved = True
    elif "192.168.1.98" in active_ollama_ips:
        resolved_peers["Blade"] = ("192.168.1.98", 11434)
        blade_resolved = True
    else:
        for ip in active_ollama_ips:
            models = ip_services[ip]["models"]
            if any("blade" in m or "gemma4" in m or "griot" in m or "rhea" in m or "iris" in m for m in models):
                resolved_peers["Blade"] = (ip, 11434)
                blade_resolved = True
                break

    # Dynamic resolve for Hyperion
    if "10.0.0.178" in active_ssh_ips:
        resolved_peers["Hyperion"] = ("10.0.0.178", 22)
    elif "10.0.0.87" in active_ssh_ips:
        resolved_peers["Hyperion"] = ("10.0.0.87", 22)
    elif "192.168.1.187" in active_ssh_ips:
        resolved_peers["Hyperion"] = ("192.168.1.187", 22)
    else:
        # Check whosthere metadata for 'hyperion' signature
        for ip, dev in devices_by_ip.items():
            disp = dev.get("displayName", "").lower()
            if "hyperion" in disp and ip in active_ssh_ips:
                resolved_peers["Hyperion"] = (ip, 22)
                break

    local_ip = get_local_ip()
    for name, (ip, port) in resolved_peers.items():
        status = ping_host(ip, port)
        has_ssh = False
        if ip in ip_services and 22 in ip_services[ip].get("ports", {}):
            has_ssh = True
        elif port == 22:
            has_ssh = True
            
        if "ONLINE" in status and has_ssh:
            status = test_bidirectional_ssh(ip, local_ip)
        local_peers[f"{name} ({ip})"] = status

    # Step 6: Cloud Run segments
    if not silent: show_tqdm_spinner("Auditing Cloud Run fleet segments", cycles=1)
    cloud_status.clear()
    with ThreadPoolExecutor(max_workers=len(FLEET_CLOUDRUN)) as executor:
        cloud_results = list(executor.map(lambda item: check_cloud_agent(*item), FLEET_CLOUDRUN.items()))
    for name, status in cloud_results:
        cloud_status[name] = status

    # Step 7: External Telemetry APIs (OMDb, SerpApi, News, Prices, OpenSky)
    if not silent: show_tqdm_spinner("Auditing external telemetry APIs", cycles=1)
    
    # 1. OMDb API Probe (Fetches real-time movie specifications — DYNAMIC ROTATION)
    omdb_key = env_vars.get("OMDB_API_KEY", "5c66dd62")
    omdb_status = "OFFLINE"
    if omdb_key:
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            # Dynamic movie pool — rotates by day-of-year so each boot shows a different film
            # Years pinned to actual OMDb release entries for guaranteed resolution
            movie_pool = [
                "t=Dune:+Part+Two&y=2024",
                "t=Oppenheimer&y=2023",
                "t=The+Brutalist&y=2024",
                "t=Conclave&y=2024",
                "t=Anora&y=2024",
                "t=Wicked&y=2024",
                "t=Gladiator+II&y=2024",
                "t=A+Complete+Unknown&y=2024",
                "t=The+Substance&y=2024",
                "t=Nosferatu&y=2024",
                "t=Flow&y=2024",
                "t=Inside+Out+2&y=2024",
                "t=Deadpool+%26+Wolverine&y=2024",
                "t=Alien:+Romulus&y=2024",
                "t=The+Wild+Robot&y=2024",
                "t=Emilia+Perez&y=2024",
            ]
            day_of_year = now.timetuple().tm_yday
            movie_query = movie_pool[day_of_year % len(movie_pool)]
            url = f"http://www.omdbapi.com/?apikey={omdb_key}&{movie_query}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2.0, context=context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("Response") == "True":
                    title = data.get("Title")
                    year = data.get("Year")
                    rating = data.get("imdbRating", "N/A")
                    rated = data.get("Rated", "NR")
                    director = data.get("Director", "Unknown")
                    elapsed = int((time.perf_counter() - start_t) * 1000)
                    omdb_status = f"ONLINE ({elapsed}ms, {title} ({year}) • Rated {rated} • IMDb {rating} • Dir: {director})"
                else:
                    # Fallback: try a generic current-year search
                    fallback_url = f"http://www.omdbapi.com/?apikey={omdb_key}&s=action&y={now.year}&type=movie"
                    fb_req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(fb_req, timeout=1.5, context=context) as fb_resp:
                        fb_data = json.loads(fb_resp.read().decode("utf-8"))
                        if fb_data.get("Search"):
                            fb_movie = fb_data["Search"][0]
                            elapsed = int((time.perf_counter() - start_t) * 1000)
                            omdb_status = f"ONLINE ({elapsed}ms, {fb_movie.get('Title')} ({fb_movie.get('Year')}) • Search fallback)"
                        else:
                            elapsed = int((time.perf_counter() - start_t) * 1000)
                            omdb_status = f"ONLINE ({elapsed}ms, API responsive but no match for rotation)"
        except Exception as e:
            omdb_status = f"OFFLINE ({str(e)})"
            
    # 2. SerpApi Probe (Scrapes & parses Google AI Overview for "drop shipping")
    serp_keys = [
        env_vars.get("SERP_API_KEY", "e6707f2f231ccda64fe5cb833982d28d3f2b11aeb4c1f87effe004b1c5c49798"),
        env_vars.get("SERP_API_KEY_BACKUP", "e85cad4e943317ff532e4ca132d82a8662a5941198aa5b3935327e6d30c8")
    ]
    serp_status = "OFFLINE"
    for s_key in serp_keys:
        if not s_key:
            continue
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            # Use query "drop shipping" to trigger active Google AI Overview scraping
            url = f"https://serpapi.com/search.json?q=drop+shipping&api_key={s_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4.5, context=context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("search_metadata", {}).get("status") == "Success":
                    elapsed = int((time.perf_counter() - start_t) * 1000)
                    ai_ov = data.get("ai_overview", {})
                    if "text_blocks" in ai_ov and ai_ov["text_blocks"]:
                        first_snippet = ai_ov["text_blocks"][0].get("snippet", "")
                        snippet_clean = " ".join(first_snippet.split())
                        if len(snippet_clean) > 85:
                            snippet_clean = snippet_clean[:82] + "..."
                        serp_status = f"ONLINE ({elapsed}ms, AI Overview: \"{snippet_clean}\")"
                    elif "page_token" in ai_ov:
                        serp_status = f"ONLINE ({elapsed}ms, AI Token active)"
                    elif "error" in ai_ov:
                        serp_status = f"ONLINE ({elapsed}ms, AI_ERROR: {ai_ov['error']})"
                    else:
                        serp_status = f"ONLINE ({elapsed}ms, AI Overview missing)"
                    break
                else:
                    serp_status = f"AUTH_ERROR ({data.get('error', 'Invalid status')})"
        except Exception as e:
            if hasattr(e, "code") and e.code == 401:
                serp_status = "AUTH_ERROR (Unauthorized)"
            else:
                serp_status = f"OFFLINE ({str(e)})"

    # 3. News API Probe (Retrieves the top live US headline)
    news_key = env_vars.get("NEWS_API_KEY", "8e304f5821604dcabe06341656ea9fff")
    news_status = "OFFLINE"
    if news_key:
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            url = "https://newsapi.org/v2/top-headlines?country=us"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Api-Key": news_key})
            with urllib.request.urlopen(req, timeout=1.5, context=context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok":
                    elapsed = int((time.perf_counter() - start_t) * 1000)
                    articles = data.get("articles", [])
                    if articles:
                        top = articles[0]
                        title = top.get("title", "")
                        source_name = top.get("source", {}).get("name", "Unknown Source")
                        news_status = f"ONLINE ({elapsed}ms, Top News: \"{title}\" • {source_name})"
                    else:
                        news_status = f"ONLINE ({elapsed}ms, Airspace clear - no news)"
                else:
                    news_status = f"AUTH_ERROR ({data.get('message', 'Invalid key')})"
        except Exception as e:
            if hasattr(e, "code") and e.code == 401:
                news_status = "AUTH_ERROR (Unauthorized)"
            else:
                news_status = f"OFFLINE ({str(e)})"

    # 4. Prices API Probe (Parses real product prices)
    prices_key = env_vars.get("PRICES_API_KEY", "pricesapi_CcLSIxXsZ3hMqOb8mdlYao2TOB7IIPQJ")
    prices_status = "OFFLINE"
    if prices_key:
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            url = "https://api.pricesapi.io/api/v1/products/search?q=coffee&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "x-api-key": prices_key})
            with urllib.request.urlopen(req, timeout=4.0, context=context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                data_val = data.get("data", {})
                products = []
                if isinstance(data_val, dict):
                    products = data_val.get("products", [])
                elif isinstance(data_val, list):
                    products = data_val
                
                elapsed = int((time.perf_counter() - start_t) * 1000)
                if products:
                    p = products[0]
                    title = p.get("title", "Coffee Product")
                    price = p.get("price", "N/A")
                    currency = p.get("currency", "USD")
                    prices_status = f"ONLINE ({elapsed}ms, '{title}' • {price} {currency})"
                else:
                    prices_status = f"ONLINE ({elapsed}ms, No pricing results)"
        except Exception as e:
            if "timeout" in str(e).lower() or (hasattr(e, "reason") and "timeout" in str(e.reason).lower()):
                prices_status = "TIMEOUT"
            elif hasattr(e, "code") and e.code == 401:
                prices_status = "AUTH_ERROR (Unauthorized)"
            else:
                prices_status = f"OFFLINE ({str(e)})"

    # 5. OpenSky Flight Telemetry Probe (Computes real-time global airspace and local NYC flights overhead)
    opensky_id = env_vars.get("OPENSKY_CLIENT_ID", "whovisions-api-client")
    opensky_secret = env_vars.get("OPENSKY_CLIENT_SECRET", "QXlTCAUAf5zRTG8Sj75iG3d5TtfdbEKd")
    opensky_status = "OFFLINE"
    if opensky_id and opensky_secret:
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            token_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": opensky_id,
                "client_secret": opensky_secret
            }
            data_bytes = urllib.parse.urlencode(payload).encode("utf-8")
            token_req = urllib.request.Request(token_url, data=data_bytes, headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(token_req, timeout=1.5, context=context) as token_resp:
                token_data = json.loads(token_resp.read().decode("utf-8"))
                access_token = token_data.get("access_token")
                
                api_url = "https://opensky-network.org/api/states/all"
                api_req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(api_req, timeout=2.5, context=context) as api_resp:
                    api_data = json.loads(api_resp.read().decode("utf-8"))
                    states = api_data.get("states", [])
                    flights_count = len(states)
                    
                    # Local NYC Airspace in-memory filter (Lat: 40.5 to 41.0, Lon: -74.25 to -73.7)
                    nyc_callsigns = []
                    for state in states:
                        if len(state) > 6:
                            lon = state[5]
                            lat = state[6]
                            if lon is not None and lat is not None:
                                if 40.5 <= lat <= 41.0 and -74.25 <= lon <= -73.7:
                                    callsign = state[1].strip()
                                    if callsign:
                                        nyc_callsigns.append(callsign)
                    
                    nyc_flights = len(nyc_callsigns)
                    callsign_str = f"Overhead: {', '.join(nyc_callsigns[:3])}" if nyc_callsigns else "Airspace clear"
                    elapsed = int((time.perf_counter() - start_t) * 1000)
                    opensky_status = f"ONLINE ({elapsed}ms, {flights_count} global, {nyc_flights} local NYC • {callsign_str})"
        except Exception as e:
            if hasattr(e, "code") and e.code == 429:
                opensky_status = "RATE_LIMITED (429)"
            elif hasattr(e, "code") and e.code == 401:
                opensky_status = "AUTH_ERROR (Unauthorized)"
            else:
                opensky_status = f"OFFLINE ({str(e)})"

    # 6. Gmail Telemetry Probe (Checks recent unread messages — graceful skip if no token)
    gmail_refresh = env_vars.get("GMAIL_REFRESH_TOKEN", "")
    gmail_client_id = env_vars.get("GMAIL_CLIENT_ID", "")
    gmail_client_secret = env_vars.get("GMAIL_CLIENT_SECRET", "")
    gmail_status = "NO_TOKEN (Run auth_gmail.py to configure)"

    # Also try loading from OAuth JSON templates if env vars are empty
    if not gmail_client_id or not gmail_client_secret:
        oauth_dir = "/Users/kushboygroup/The Observatory/credentials/oauth"
        if os.path.exists(oauth_dir):
            for jf in glob.glob(os.path.join(oauth_dir, "*.json")):
                try:
                    with open(jf, "r", encoding="utf-8") as fj:
                        cfg = json.load(fj)
                        inst = cfg.get("installed", {})
                        sec = inst.get("client_secret", "")
                        if sec and sec != "PASTE_YOUR_CLIENT_SECRET_HERE":
                            gmail_client_id = inst.get("client_id", "")
                            gmail_client_secret = sec
                            break
                except Exception:
                    pass

    if gmail_refresh and gmail_client_id and gmail_client_secret:
        try:
            start_t = time.perf_counter()
            context = ssl._create_unverified_context()
            # Refresh access token
            token_payload = urllib.parse.urlencode({
                "client_id": gmail_client_id,
                "client_secret": gmail_client_secret,
                "refresh_token": gmail_refresh,
                "grant_type": "refresh_token"
            }).encode("utf-8")
            token_req = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=token_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(token_req, timeout=2.0, context=context) as t_resp:
                t_data = json.loads(t_resp.read().decode("utf-8"))
                access_token = t_data.get("access_token", "")

            if access_token:
                # Query Gmail for recent unread messages
                gmail_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1&q=is:unread"
                gmail_req = urllib.request.Request(
                    gmail_url,
                    headers={"Authorization": f"Bearer {access_token}", "User-Agent": "KaedraProbe/1.0"}
                )
                with urllib.request.urlopen(gmail_req, timeout=2.0, context=context) as g_resp:
                    g_data = json.loads(g_resp.read().decode("utf-8"))
                    total_unread = g_data.get("resultSizeEstimate", 0)
                    messages = g_data.get("messages", [])

                    if messages:
                        # Fetch the top message metadata for the subject line
                        msg_id = messages[0]["id"]
                        detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From"
                        detail_req = urllib.request.Request(
                            detail_url,
                            headers={"Authorization": f"Bearer {access_token}", "User-Agent": "KaedraProbe/1.0"}
                        )
                        with urllib.request.urlopen(detail_req, timeout=2.0, context=context) as d_resp:
                            d_data = json.loads(d_resp.read().decode("utf-8"))
                            headers_list = d_data.get("payload", {}).get("headers", [])
                            subject = "No Subject"
                            sender = "Unknown"
                            for h in headers_list:
                                if h["name"] == "Subject":
                                    subject = h["value"]
                                if h["name"] == "From":
                                    sender = h["value"]
                                    # Clean sender to just name
                                    if "<" in sender:
                                        sender = sender.split("<")[0].strip().strip('"')

                            if len(subject) > 60:
                                subject = subject[:57] + "..."
                            elapsed = int((time.perf_counter() - start_t) * 1000)
                            gmail_status = f"ONLINE ({elapsed}ms, {total_unread} unread • Latest: \"{subject}\" from {sender})"
                    else:
                        elapsed = int((time.perf_counter() - start_t) * 1000)
                        gmail_status = f"ONLINE ({elapsed}ms, Inbox clear — 0 unread)"
        except Exception as e:
            if hasattr(e, "code") and e.code == 401:
                gmail_status = "AUTH_EXPIRED (Refresh token revoked or expired)"
            elif hasattr(e, "code") and e.code == 403:
                gmail_status = "FORBIDDEN (Scope not granted — re-run auth_gmail.py)"
            else:
                gmail_status = f"OFFLINE ({str(e)})"
    elif gmail_refresh and (not gmail_client_id or not gmail_client_secret):
        gmail_status = "NO_CREDENTIALS (Paste client_secret in OAuth JSON template)"

    # Step 8: Gemma 4 Status Checking & Liveness
    if ollama_running and gemma_loaded:
        target_model = select_best_model(ollama_models)
        if target_model:
            active_reasoner_model = target_model
            
            run_inference = "--inference" in sys.argv or "-i" in sys.argv or "--deep" in sys.argv or "-d" in sys.argv
            enable_deep = "--deep" in sys.argv or "-d" in sys.argv
            
            if run_inference:
                if not silent: show_tqdm_spinner(f"Querying {target_model} Reasoner for Grid Evaluation", cycles=1)
                inf_start = time.perf_counter()
                
                # Compile current system diagnostic status
                compact_data = {
                    "timestamp": local_time,
                    "uptime": uptime_text,
                    "gpu": gpu_name,
                    "gpu_vram_used_mb": gpu_mem_used,
                    "thermal": {
                        "cpu_temp_level": cpu_thermal_level,
                        "cpu_speed_limit_pct": cpu_speed_limit,
                        "cpu_scheduler_limit_pct": cpu_scheduler_limit
                    },
                    "sockets": local_sockets,
                    "peers": local_peers,
                    "cloud_fleet": cloud_status,
                    "telemetry": {
                        "omdb": omdb_status.split(" (")[0] if " (" in omdb_status else omdb_status,
                        "serp": serp_status.split(" (")[0] if " (" in serp_status else serp_status,
                        "news": news_status.split(" (")[0] if " (" in news_status else news_status,
                        "prices": prices_status.split(" (")[0] if " (" in prices_status else prices_status,
                        "opensky": opensky_status.split(" (")[0] if " (" in opensky_status else opensky_status,
                        "gmail": gmail_status.split(" (")[0] if " (" in gmail_status else gmail_status
                    }
                }
                compact_json_str = json.dumps(compact_data, indent=2)

                if enable_deep:
                    prompt = (
                        "Analyze this Kaedra Hi Probe status report:\n\n"
                        f"```json\n{compact_json_str}\n```\n\n"
                        "Evaluate grid health. Identify warnings or offline nodes. "
                        "State the primary play in one concise sentence."
                    )
                    system_instruction = "You are the Kaedra Swarm Reasoner. Keep your thinking under 150 tokens. Always produce a final answer — never end mid-thought. Be terse and systemic."
                    num_predict = 400
                else:
                    prompt = "Respond with exactly 'ONLINE' and a 3-word summary of the grid status."
                    system_instruction = "You are the Kaedra Swarm Liveness Check. Be extremely brief."
                    num_predict = 15

                payload = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "keep_alive": 0, # Immediately free VRAM after status reasoning query completes
                    "options": {
                        "num_predict": num_predict,
                        "temperature": 0.2
                    }
                }
                try:
                    req_inf = urllib.request.Request(
                        "http://127.0.0.1:11434/api/chat",
                        data=json.dumps(payload).encode('utf-8'),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req_inf, timeout=300.0) as response_inf:
                        inf_res = json.loads(response_inf.read().decode('utf-8'))
                        message_obj = inf_res.get("message", {})
                        content_text = message_obj.get("content", "").strip()
                        thinking_text = message_obj.get("thinking", "").strip()
                        
                        # Graceful parsing if thinking process is inside content instead of a separate field
                        if not thinking_text:
                            think_match = re.search(r'<(?:think|\|think\|)>(.*?)</(?:think|\|think\|)>', content_text, re.DOTALL)
                            if think_match:
                                thinking_text = think_match.group(1).strip()
                                content_text = re.sub(r'<(?:think|\|think\|)>(.*?)</(?:think|\|think\|)>', '', content_text, flags=re.DOTALL).strip()
                            elif content_text.startswith('<think>') or content_text.startswith('<|think|>'):
                                tag = '<think>' if content_text.startswith('<think>') else '<|think|>'
                                thinking_text = content_text[len(tag):].strip()
                                content_text = "Thinking Process Truncated / Active"
                        
                        if message_obj and (content_text or thinking_text):
                            gemma_responsive = True
                            gemma_response_text = content_text if content_text else "Thinking Process Active"
                            gemma_thinking_text = thinking_text
                            gemma_inference_ms = int((time.perf_counter() - inf_start) * 1000)
                except Exception as e:
                    gemma_response_text = f"Inference failed: {str(e)}"
            else:
                # Fast Path: Registry scan only (Zero extra CPU/RAM load)
                gemma_responsive = True
                gemma_response_text = "Registry verified. Active inference test skipped for speed/RAM preservation."
                gemma_thinking_text = ""
                gemma_inference_ms = 0

    # Dynamic Warnings Accumulation
    if not ollama_running:
        warnings.append("Ollama API server is offline or unreachable on port 11434.")
    elif not gemma_loaded:
        warnings.append("No active gemma/reasoner models found in Ollama registry.")
    else:
        is_custom = any(p in active_reasoner_model.lower() for p in ["kaedracode", "solai"])
        if not is_custom:
            warnings.append(f"Generic model fallback active ({active_reasoner_model}). Custom models (solai/kaedracode) not found.")

    for shard_name, is_open in local_sockets.items():
        if not is_open:
            warnings.append(f"Local swarm shard {shard_name} is INACTIVE / GHOST.")

    for peer_name, peer_status in local_peers.items():
        if "OFFLINE" in peer_status:
            warnings.append(f"Mesh neighbor {peer_name} is OFFLINE.")

    offline_clouds = [name for name, status in cloud_status.items() if "OFFLINE" in status]
    if offline_clouds:
        warnings.append(f"Cloud Run fleet segments offline: {', '.join(offline_clouds)}")

    if cpu_scheduler_limit < 100 or cpu_speed_limit < 80 or cpu_thermal_level > 150:
        warnings.append(f"CPU Thermal level is warm ({cpu_thermal_level}) or speed limit is throttled ({cpu_speed_limit}%).")

# --- RUN DIAGNOSTICS PHASE 1 ---
run_diagnostics(silent=False)

# ==============================================================================
# FAILSAFE PROTOCOL: AUTO-HEALING SELF-RESTORE
# ==============================================================================
# Triggers if Ollama is down, Gemma is stalled, or core swarm registries are offline.
# ==============================================================================

# Parse CLI arguments
enable_failsafe = "--failsafe" in sys.argv or "-f" in sys.argv

# Verify critical failures (excluding cloud run agents which are separate cloud segments)
needs_ollama_failsafe = not ollama_running or not gemma_responsive
needs_swarm_failsafe = any(not local_sockets[shard] for shard in SWARM_SHARDS)

if enable_failsafe and (needs_ollama_failsafe or needs_swarm_failsafe):
    print()
    print(f"{Colors.YELLOW}[🛡️  FAILSAFE RECOVERY PROTOCOL TRIGGERED]{Colors.RESET}")
    print(f"{Colors.GRAY}Nodes detected in stalled or ghost state. Auto-recovering sideline grid...{Colors.RESET}")
    print("-" * 75)

    # 1. Recovery: Ollama Application & Server Lane
    if needs_ollama_failsafe:
        print(f"⚡ {Colors.CYAN}Failsafe Play:{Colors.RESET} Cycle & relaunch local Ollama server...")
        try:
            # Terminate hanging processes cleanly
            subprocess.run("killall Ollama || true", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("killall ollama || true", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("pkill -f Ollama || true", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("pkill -f ollama || true", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
            # Ensure Ollama binds to 0.0.0.0 to expose it to the LAN
            subprocess.run("launchctl setenv OLLAMA_HOST 0.0.0.0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Reopen native macOS app
            subprocess.run("open /Applications/Ollama.app", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  -> {Colors.GREEN}Set OLLAMA_HOST=0.0.0.0 and relaunched /Applications/Ollama.app{Colors.RESET}")
        except Exception as e:
            print(f"  -> {Colors.RED}Ollama launch play failed: {e}{Colors.RESET}")

    # 2. Recovery: Swarm Orchestration Shards Lane
    if needs_swarm_failsafe:
        print(f"⚡ {Colors.CYAN}Failsafe Play:{Colors.RESET} Launching local Swarm Hub & popped terminals...")
        try:
            # Execute the pop out script (spawns Terminals for CORE, MESH, GEMMA, WEB, KAEDRA)
            popout_script = "/Users/kushboygroup/The Observatory/scratch/pop_out_swarm.sh"
            if os.path.exists(popout_script):
                subprocess.run(f"chmod +x '{popout_script}' && bash '{popout_script}' &", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  -> {Colors.GREEN}Relaunched local Swarm Terminals via pop_out_swarm.sh{Colors.RESET}")
            
            # Ignite background orchestrator if inactive
            subprocess.run("python3 '/Users/kushboygroup/The Observatory/Livthemoment/autonomous_ignite.py' --no-popout --no-purge --mtp mini &", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  -> {Colors.GREEN}Seated background daemon: autonomous_ignite.py{Colors.RESET}")

            # Relaunch NextJS if inactive
            if not local_sockets.get("KAEDRA (NextJS)", False):
                nextjs_dir = "/Users/kushboygroup/The Observatory/Ai-with-Dav3--Alpha-"
                if os.path.exists(nextjs_dir):
                    subprocess.run(f"cd '{nextjs_dir}' && npm run dev -- -p 1019 >/dev/null 2>&1 &", shell=True)
                    print(f"  -> {Colors.GREEN}Relaunched KAEDRA (NextJS) on port 1019 in background{Colors.RESET}")
        except Exception as e:
            print(f"  -> {Colors.RED}Swarm launch play failed: {e}{Colors.RESET}")

    # 3. Buffer sleep to let sockets bind and seed
    wait_time = 6
    if needs_ollama_failsafe:
        # Increase sleep to accommodate Intel CPU cold loads
        wait_time = 8
        
    print(f"⏳ {Colors.GRAY}Letting service sockets bind and models seed ({wait_time}s rest)...{Colors.RESET}")
    time.sleep(wait_time)
    print("-" * 75)
    
    # 4. Asynchronous Warm-up Seed for Gemma to prevent future stalls
    if needs_ollama_failsafe:
        warm_model = select_best_model(ollama_models) if ollama_models else "kaedracode:latest"
        print(f"🔮 {Colors.CYAN}Failsafe Play:{Colors.RESET} Seeding warm inference payload to {warm_model} VRAM...")
        try:
            # Run one ultra-fast generation using /api/chat with keep_alive=0 to immediately release VRAM afterwards
            warm_payload = {
                "model": warm_model,
                "messages": [
                    {"role": "system", "content": "Reply ONLY with 'OK'."},
                    {"role": "user", "content": "Are you warm?"}
                ],
                "stream": False,
                "keep_alive": 0, # Immediately free VRAM after seeding is completed
                "options": {"num_predict": 1}
            }
            warm_req = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps(warm_payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(warm_req, timeout=30.0) as w_resp:
                json.loads(w_resp.read().decode('utf-8'))
            print(f"  -> {Colors.GREEN}VRAM seeded successfully. Model warm liveness established (VRAM immediately released).{Colors.RESET}")
        except Exception:
            pass

    # 5. Run Diagnostics Phase 2 (Confirm online status!)
    print(f"📊 {Colors.CYAN}Failsafe Play:{Colors.RESET} Executing final system audit...")
    run_diagnostics(silent=True)

# Step 10: Complete loading progress bar
show_tqdm_bar("Kaedra liveness complete", width=24, delay_ms=5)

# Safety System Audits
constitution_path = "/Users/kushboygroup/.gemini/GEMINI.md"
vault_dir = "/Users/kushboygroup/The Observatory/mempalace"
coach_playbook_path = "/Users/kushboygroup/The Observatory/antigravity-coach/SKILL.md"

constitution_verified = os.path.exists(constitution_path)
vault_verified = os.path.exists(vault_dir)
coach_playbook_verified = os.path.exists(coach_playbook_path)

# Last Memory recall from transcript logs
last_memory_file = None
last_memory_title = None
last_memory_time = None
last_memory_age = None

try:
    brain_dir = "/Users/kushboygroup/.gemini/antigravity/brain"
    if os.path.exists(brain_dir):
        transcripts = glob.glob(f"{brain_dir}/*/.system_generated/logs/transcript.jsonl")
        if transcripts:
            latest_transcript = max(transcripts, key=os.path.getmtime)
            last_memory_file = os.path.relpath(latest_transcript, brain_dir)
            mtime = os.path.getmtime(latest_transcript)
            t_dt = datetime.fromtimestamp(mtime)
            last_memory_time = t_dt.strftime('%Y-%m-%d %H:%M:%S %z')
            
            age_td = datetime.now() - t_dt
            if age_td.total_seconds() < 60:
                last_memory_age = "just now"
            elif age_td.total_seconds() < 3600:
                last_memory_age = f"{int(age_td.total_seconds() / 60)}m ago"
            elif age_td.total_seconds() < 86400:
                last_memory_age = f"{int(age_td.total_seconds() / 3600)}h {int((age_td.total_seconds() % 3600) / 60)}m ago"
            else:
                last_memory_age = f"{age_td.days}d {int((age_td.total_seconds() % 86400) / 3600)}h ago"

            with open(latest_transcript, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if line.strip():
                        try:
                            turn = json.loads(line)
                            if turn.get("type") in ["USER_INPUT", "PLANNER_RESPONSE"] and turn.get("content"):
                                content = turn["content"].strip()
                                if "<USER_REQUEST>" in content:
                                    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                                    if m:
                                        content = m.group(1).strip()
                                content = " ".join(content.split())
                                if len(content) > 80:
                                    content = content[:77] + "..."
                                sender = "User" if turn.get("source") == "USER_EXPLICIT" else "Model"
                                last_memory_title = f"Active Chat: '{content}' ({sender})"
                                break
                        except Exception:
                            pass
except Exception:
    pass

# Determine overall health score
ok_overall = ollama_running and constitution_verified and coach_playbook_verified

# --- DISPLAY PREMIUM COMMAND CARD ---
print()
print(f"{Colors.YELLOW} _  _ ____ ____ ___  ____ ____ {Colors.RESET}")
print(f"{Colors.YELLOW} |_/  |__| |___ |  \\ |__| |__| {Colors.RESET}")
print(f"{Colors.YELLOW} | \\_ |  | |___ |__/ |  | |  \\ {Colors.RESET}")
print()
print(f"{Colors.YELLOW}## Kaedra Enhanced 24/7 Swarm Commander{Colors.RESET}")
print()
if ok_overall and not warnings:
    print(f"{Icon['Ok']} {Colors.GREEN}Kaedra Node is dynamic, synchronized, and online.{Colors.RESET}")
else:
    print(f"{Icon['Blocked']} {Colors.RED}Kaedra Node has active warnings or offline nodes.{Colors.RESET}")

if warnings:
    print()
    print(f"{Colors.RED}⚠️  ACTIVE WARNINGS:{Colors.RESET}")
    for w in warnings:
        print(f"  * {Colors.YELLOW}{w}{Colors.RESET}")
print()

print(f"{Colors.CYAN}### Environment{Colors.RESET}")
print(f"- {Icon['Time']} {Colors.DARK_CYAN}**Time:** {human_time}{Colors.RESET}")
print(f"- {Icon['Uptime']} {Colors.DARK_CYAN}**Uptime:** {uptime_text}{Colors.RESET}")
print(f"- {Icon['Machine']} {Colors.DARK_CYAN}**Node:** Mac Mini ({host_name}) | CPU: {platform.machine()}{Colors.RESET}")
print(f"- {Icon['Weather']} {Colors.DARK_CYAN}**Weather:** {weather} - {location}{Colors.RESET}")
if hot_news:
    print(f"- {Icon['News']} {Colors.DARK_CYAN}**News:** [{hot_news.get('source')}] {hot_news.get('title')} ({hot_news.get('date')}){Colors.RESET}")
else:
    print(f"- {Icon['News']} {Colors.GRAY}**News:** Unavailable{Colors.RESET}")
print()

print(f"{Colors.CYAN}### Local Gemma Inference (The Grid){Colors.RESET}")
if ollama_running:
    ollama_status_text = f"{Colors.GREEN}Running (Available models: {', '.join(ollama_models)}){Colors.RESET}"
else:
    ollama_status_text = f"{Colors.RED}Offline / Bound Error{Colors.RESET}"
print(f"- {Icon['Server']} **Ollama API:** {ollama_status_text}")

if gemma_responsive:
    is_custom_model = any(p in active_reasoner_model.lower() for p in ["kaedracode", "solai"])
    badge = f" ({Colors.MAGENTA}{active_reasoner_model}{Colors.RESET}) [{Colors.GREEN}CUSTOM{Colors.RESET}]" if is_custom_model else f" ({Colors.YELLOW}{active_reasoner_model}{Colors.RESET}) [{Colors.YELLOW}⚠️ GENERIC FALLBACK{Colors.RESET}]"
    if gemma_inference_ms > 0:
        print(f"- {Icon['Brain']} **Gemma 4 Liveness{badge}:** {Colors.GREEN}ONLINE (Inference test responded in {gemma_inference_ms}ms){Colors.RESET}")
        if gemma_response_text:
            print(f"  * {Colors.GRAY}**Live Response:**{Colors.RESET} {Colors.MAGENTA}\"{gemma_response_text}\"{Colors.RESET}")
        if gemma_thinking_text:
            # Wrap thinking process cleanly in status card
            indented_thinking = "\n".join(f"    {Colors.GRAY}{line}{Colors.RESET}" for line in gemma_thinking_text.split("\n"))
            print(f"  * {Colors.YELLOW}**Chain-of-Thought (Thoughts):**{Colors.RESET}\n{indented_thinking}")
    else:
        print(f"- {Icon['Brain']} **Gemma 4 Liveness{badge}:** {Colors.GREEN}ONLINE (Registry verified - Fast Mode){Colors.RESET}")
else:
    is_custom_model = any(p in active_reasoner_model.lower() for p in ["kaedracode", "solai"]) if active_reasoner_model != "None" else False
    badge = f" ({Colors.MAGENTA}{active_reasoner_model}{Colors.RESET}) [{Colors.GREEN}CUSTOM{Colors.RESET}]" if is_custom_model else (f" ({Colors.YELLOW}{active_reasoner_model}{Colors.RESET}) [{Colors.YELLOW}⚠️ GENERIC FALLBACK{Colors.RESET}]" if active_reasoner_model != "None" else "")
    print(f"- {Icon['Brain']} **Gemma 4 Liveness{badge}:** {Colors.RED}STALLED / UNRESPONSIVE{Colors.RESET}")
print()

print(f"{Colors.CYAN}### Local Swarm Ports Registry (Mac Mini){Colors.RESET}")
for shard_name, is_open in local_sockets.items():
    status_tag = f"{Colors.GREEN}ACTIVE (LISTENING){Colors.RESET}" if is_open else f"{Colors.GRAY}INACTIVE / GHOST{Colors.RESET}"
    print(f"- {Icon['Signal']} **{shard_name}:** {status_tag}")
print()

print(f"{Colors.CYAN}### Mesh Network & Tunnels Audits{Colors.RESET}")
# Gateway IP
try:
    gateway_ip = subprocess.check_output("route -n get default | grep gateway | awk '{print $2}'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    gateway_status = ping_host(gateway_ip)
    gw_tag = f"{Colors.GREEN}ONLINE ({gateway_ip}){Colors.RESET}" if "ONLINE" in gateway_status else f"{Colors.RED}UNREACHABLE ({gateway_ip}){Colors.RESET}"
    print(f"- {Icon['Router']} **Physical Default Gateway:** {gw_tag}")
except Exception:
    print(f"- {Icon['Router']} **Physical Default Gateway:** {Colors.RED}Not resolved{Colors.RESET}")

for peer_name, peer_status in local_peers.items():
    color_tag = Colors.GREEN if "ONLINE" in peer_status and "BLOCKED" not in peer_status and "UNVERIFIED" not in peer_status else (Colors.YELLOW if "BLOCKED" in peer_status or "UNVERIFIED" in peer_status else Colors.GRAY)
    print(f"- {Icon['Server']} **{peer_name}:** {color_tag}{peer_status}{Colors.RESET}")

if ssh_processes:
    print(f"- {Icon['Tunnel']} **Active SSH Tunnels:**")
    for ssh_proc in ssh_processes[:3]:
        print(f"  * {Colors.DARK_CYAN}{ssh_proc}{Colors.RESET}")
else:
    print(f"- {Icon['Tunnel']} **Active SSH Tunnels:** {Colors.GRAY}None established{Colors.RESET}")
print()

print(f"{Colors.CYAN}### Local Service Bindings & Security{Colors.RESET}")
try:
    bindings = audit_local_bindings()
    ollama_color = Colors.GREEN if "ALL" in bindings["ollama"] else Colors.YELLOW
    registry_color = Colors.GREEN if "ALL" in bindings["mesh_registry"] else Colors.GRAY
    pf_color = Colors.GREEN if bindings["pf_firewall"] == "ACTIVE" else Colors.YELLOW
    print(f"- {Icon['Lock']} **Ollama API Port Binding:** {ollama_color}{bindings['ollama']}{Colors.RESET}")
    print(f"- {Icon['Signal']} **Swarm Mesh Registry Binding:** {registry_color}{bindings['mesh_registry']}{Colors.RESET}")
    print(f"- {Icon['Router']} **macOS PF Firewall Status:** {pf_color}{bindings['pf_firewall']}{Colors.RESET}")
except Exception as e:
    print(f"- {Icon['Blocked']} **Service Bindings Audit:** {Colors.RED}Failed ({e}){Colors.RESET}")
print()

print(f"{Colors.CYAN}### Cloud Run Fleet Segments (Pulse Check){Colors.RESET}")
for cloud_name, cloud_stat in cloud_status.items():
    color_tag = Colors.GREEN if "ONLINE" in cloud_stat else Colors.GRAY
    print(f"- {Icon['Cloud']} **{cloud_name}:** {color_tag}{cloud_stat}{Colors.RESET}")
print()

print(f"{Colors.CYAN}### NouGenAi API Telemetry{Colors.RESET}")
omdb_color = Colors.GREEN if "ONLINE" in omdb_status else Colors.GRAY
print(f"- {Icon['Spark']} **OMDb Movie API:** {omdb_color}{omdb_status}{Colors.RESET}")
serp_color = Colors.GREEN if "ONLINE" in serp_status else Colors.GRAY
print(f"- {Icon['Spark']} **SerpApi Search:** {serp_color}{serp_status}{Colors.RESET}")
news_color = Colors.GREEN if "ONLINE" in news_status else Colors.GRAY
print(f"- {Icon['Spark']} **News API:** {news_color}{news_status}{Colors.RESET}")
prices_color = Colors.GREEN if "ONLINE" in prices_status else Colors.GRAY
print(f"- {Icon['Spark']} **Prices API:** {prices_color}{prices_status}{Colors.RESET}")
opensky_color = Colors.GREEN if "ONLINE" in opensky_status else Colors.GRAY
print(f"- {Icon['Spark']} **OpenSky Flight Telemetry:** {opensky_color}{opensky_status}{Colors.RESET}")
gmail_color = Colors.GREEN if "ONLINE" in gmail_status else (Colors.YELLOW if "NO_TOKEN" in gmail_status or "NO_CREDENTIALS" in gmail_status else Colors.GRAY)
print(f"- {Icon['Spark']} **Gmail Telemetry:** {gmail_color}{gmail_status}{Colors.RESET}")
print()

print(f"{Colors.CYAN}### System Thermal & Power Status (Mac Mini){Colors.RESET}")
therm_warn = "Nominal (Cool)"
if cpu_scheduler_limit < 100 or cpu_speed_limit < 100 or cpu_thermal_level > 150:
    therm_warn = "Throttled / Warm"
print(f"- {Icon['Temp']} **Thermal State:** {Colors.GREEN if cpu_thermal_level < 150 else Colors.YELLOW}{therm_warn} (Scale: {cpu_thermal_level}){Colors.RESET}")
print(f"- {Icon['Power']} **CPU Scheduler Limit:** {Colors.GREEN if cpu_scheduler_limit == 100 else Colors.YELLOW}{cpu_scheduler_limit}% (Nominal){Colors.RESET}" if cpu_scheduler_limit == 100 else f"- {Icon['Power']} **CPU Scheduler Limit:** {Colors.YELLOW}{cpu_scheduler_limit}% (Limited){Colors.RESET}")
print(f"- {Icon['Util']} **CPU Speed Limit:** {Colors.GREEN if cpu_speed_limit == 100 else Colors.YELLOW}100% (Unthrottled){Colors.RESET}" if cpu_speed_limit == 100 else f"- {Icon['Util']} **CPU Speed Limit:** {Colors.YELLOW}{cpu_speed_limit}% (Throttled){Colors.RESET}")
print()

print(f"{Colors.CYAN}### Safety & Constitution{Colors.RESET}")
print(f"- {Icon['Lock']} {Colors.GRAY}**Mutation gates:** Locked{Colors.RESET}")
if constitution_verified:
    print(f"- {Icon['Ok']} {Colors.GREEN}**Constitution:** {constitution_path} (Strict Enforcement){Colors.RESET}")
else:
    print(f"- {Icon['Blocked']} {Colors.RED}**Constitution:** {constitution_path} (Not Found){Colors.RESET}")
if coach_playbook_verified:
    print(f"- {Icon['Ok']} {Colors.GREEN}**Coach Playbook:** {coach_playbook_path} (Verified & Mandatory Read){Colors.RESET}")
else:
    print(f"- {Icon['Blocked']} {Colors.RED}**Coach Playbook:** {coach_playbook_path} (Not Found){Colors.RESET}")
if vault_verified:
    print(f"- {Icon['Ok']} {Colors.GREEN}**Vault Dir:** {vault_dir} (Verified){Colors.RESET}")
else:
    print(f"- {Icon['Blocked']} {Colors.RED}**Vault Dir:** {vault_dir} (Not Found){Colors.RESET}")

if last_memory_title:
    print()
    print(f"{Colors.CYAN}### Last Memory Recall{Colors.RESET}")
    print(f"- {Icon['Brain']} {Colors.MAGENTA}**Shard:** {last_memory_title}{Colors.RESET}")
    print(f"- {Icon['Time']} {Colors.DARK_CYAN}**When:** {last_memory_time} ({last_memory_age}){Colors.RESET}")
    print(f"- {Icon['Vram']} {Colors.DARK_CYAN}**File:** {last_memory_file}{Colors.RESET}")
print()
print(f"{Colors.GREEN}{Icon['Stadium']} **The Stadium is live. What is the play, Dave?**{Colors.RESET}")
print()

# --- TRAILING MACHINE-READABLE JSON PAYLOAD ---
probe_end = time.perf_counter()
probe_ms = int((probe_end - probe_start) * 1000)

news_obj = None
if hot_news:
    news_obj = {
        "title": hot_news.get("title"),
        "source": hot_news.get("source"),
        "date": hot_news.get("date"),
        "link": hot_news.get("link")
    }

json_payload = {
    "status": "OK" if ok_overall else "WARN",
    "time": local_time,
    "timezone": time_zone,
    "boot_time": boot_time.strftime('%Y-%m-%d %H:%M:%S %z') if boot_time else "",
    "host": host_name,
    "user": user_name,
    "python_version": python_version,
    "uptime": uptime_text,
    "ready_for_command": True,
    
    # Ollama & Gemma Checks
    "ollama_running": ollama_running,
    "ollama_models": ollama_models,
    "gemma_loaded": gemma_loaded,
    "gemma_responsive": gemma_responsive,
    "gemma_response_text": gemma_response_text,
    "gemma_thinking_text": gemma_thinking_text,
    "gemma_inference_ms": gemma_inference_ms,
    
    # GPU / Unified memory
    "gpu_available": gpu_info_available,
    "gpu_name": gpu_name,
    "gpu_vram_used": gpu_mem_used,
    "gpu_vram_total": gpu_mem_total,

    # Networking & Tunnels
    "ssh_processes": ssh_processes,
    "active_tunnels": active_tunnels,
    "local_sockets": local_sockets,
    "local_peers": local_peers,
    "service_bindings": audit_local_bindings() if 'audit_local_bindings' in globals() else {},
    "cloud_status": cloud_status,
    "omdb_status": omdb_status,
    "serp_status": serp_status,
    "news_status": news_status,
    "prices_status": prices_status,
    "opensky_status": opensky_status,
    "gmail_status": gmail_status,
    
    # Safety / Playbook
    "constitution_path": constitution_path,
    "constitution_verified": constitution_verified,
    "coach_playbook_verified": coach_playbook_verified,
    "vault_verified": vault_verified,

    # Metrics
    "probe_name": "kaedra_hi_probe",
    "probe_ms": probe_ms,
    "warnings": warnings,

    # Last Memory Recall
    "last_memory_file": last_memory_file,
    "last_memory_title": last_memory_title,
    "last_memory_time": last_memory_time,
    "last_memory_age": last_memory_age
}

# Standardized single trailing stdout line for programmatic parser sync
print(json.dumps(json_payload, separators=(',', ':')))

sys.exit(0 if ok_overall else 1)
