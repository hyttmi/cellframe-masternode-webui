from utils import *
import handlers

def getInfo(exclude=None, format_time=True):
    if exclude is None:
        exclude = []
    sys_stats = getSysStats()
    is_update_available, curr_version, latest_version = checkForUpdate()

    info = {
        'update_available': is_update_available,
        'current_version': curr_version,
        'latest_version': latest_version,
        "title": PLUGIN_NAME,
        "hostname": getHostname(),
        "external_ip": getExtIP(),
        "system_uptime": formatUptime(sys_stats["system_uptime"]) if format_time else sys_stats["system_uptime"],
        "node_uptime": formatUptime(sys_stats["node_uptime"]) if format_time else sys_stats["node_uptime"],
        "node_version": getCurrentNodeVersion(),
        "latest_node_version": getLatestNodeVersion(),
        "cpu_utilization": sys_stats["node_cpu_usage"],
        "memory_utilization": sys_stats["node_memory_usage_mb"],
        "header_text": getConfigValue("webui", "header_text", default=False),
        "accent_color": validateHex(getConfigValue("webui", "accent_color", default="B3A3FF")),
        "net_info": generateNetworkData()
    }
    
    for key in exclude:
        info.pop(key)
    return info

def generateHTML(template_name):
    info = getInfo(exclude=[], format_time=True)
    template_setting = getConfigValue("webui", "template", default="cards")
    template_path = f"{template_setting}/{template_name}"
    try:
        logNotice(f"Generating HTML content...")
        template = handlers.env.get_template(template_path)
        output = template.render(info)
    except Exception as e:
        logError(f"Error in generating HTML: {e}")
        output = f"<h1>Got an error: {e}</h1>"
    return output

def generateJSON():
    info = getInfo(exclude=["update_available", "current_version", "latest_version", "title", "accent_color", "header_text"], format_time=False)
    try:
        logNotice(f"Generating JSON content...")
        output = json.dumps(info)
    except Exception as e:
        logError(f"Error in generating JSON: {e}")
        output = json.dumps({"Error": str(e)})
    return output
