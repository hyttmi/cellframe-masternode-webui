import os, socket, psutil, time
from logger import log_it, log_debug

def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def get_node_pid():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "cellframe-node":
                return proc.info['pid']
        return None
    except Exception as e:
        log_it(f"Error: {e}")
        return None

def get_system_hostname():
    try:
        return socket.gethostname()
    except:
        return None

@log_debug
def get_sys_stats():
    try:
        PID = get_node_pid()
        if PID:
            process = psutil.Process(PID)
            sys_stats = {}
            cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count() # Divide by CPU cores, it's possible that only one core is @ 100%
            sys_stats['node_cpu_usage'] = cpu_usage

            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024
            sys_stats['node_memory_usage_mb'] = round(memory_usage_mb, 2)
        
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            sys_stats['node_uptime'] = uptime_seconds 

            boot_time = psutil.boot_time()
            system_uptime_seconds = time.time() - boot_time
            sys_stats['system_uptime'] = system_uptime_seconds
            
            return sys_stats
        return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None