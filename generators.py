from utils import *
import handlers

def generateHTML(template_name):
    sys_stats = getSysStats()
    is_update_available, curr_version, latest_version = checkForUpdate()

    info = {
        'update_available': is_update_available,
        'current_version': curr_version,
        'latest_version': latest_version,
        "title": PLUGIN_NAME,
        "hostname": getHostname(),
        "external_ip": getExtIP(),
        "system_uptime": sys_stats["system_uptime"],
        "node_uptime": sys_stats["node_uptime"],
        "node_version": getCurrentNodeVersion(),
        "latest_node_version": getLatestNodeVersion(),
        "cpu_utilization": sys_stats["node_cpu_usage"],
        "memory_utilization": sys_stats["node_memory_usage_mb"],
        "header_text": getConfigValue("webui", "header_text", default=False),
        "net_info": generateNetworkData()
    }

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
