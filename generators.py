from utils import *
import handlers

def generateHTML(template_name):
    info = generateInfo(exclude=[], format_time=True)
    template_setting = getConfigValue("webui", "template", default="cards")
    template_path = f"{template_setting}/{template_name}"
    try:
        logNotice(f"Generating HTML content...")
        template = handlers.env.get_template(template_path)
        output = template.render(info)
    except Exception as e:
        error_func = logError(f"Error: {e}")
        output = json.dumps({
            "status": "error",
            "message": f"{error_func} -> {e}"
        })
    return output

def generateJSON():
    info = generateInfo(exclude=["plugin_update_available", "current_plugin_version", "latest_plugin_version", "plugin_name", "website_accent_color", "website_header_text"], format_time=False)
    try:
        logNotice(f"Generating JSON content...")
        output = json.dumps(info)
    except Exception as e:
        logError(f"Error in generating JSON: {e}")
        error_func = logError(f"Error: {e}")
        output = json.dumps({
            "status": "error",
            "message": f"{error_func} -> {e}"
        })
    return output
