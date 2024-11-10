import json
from utils import generateInfo, logNotice, logError
from config import Config

def generateHTML(template_name):
    info = generateInfo(format_time=True)
    template_setting = Config.TEMPLATE
    template_path = f"{template_setting}/{template_name}"
    try:
        logNotice("Generating HTML content...")
        env = Config.jinjaEnv()
        template = env.get_template(template_path)
        output = template.render(info)
    except Exception as e:
        logError(f"Error: {e}")
        output = json.dumps({
            "status": "error",
            "message": f"{e}"
        })
    return output

def generateJSON():
    info = generateInfo(format_time=False)
    if Config.JSON_EXCLUDE and isinstance(Config.JSON_EXCLUDE, list):
        for key in Config.JSON_EXCLUDE:
            if key in info:
                try:
                    info.pop(key)
                except KeyError:
                    logError(f"Key {key} not found!")
                    pass
    else:
        logError("Error: json_exclude is not a list!")
    try:
        logNotice(f"Generating JSON content...")
        output = json.dumps(info)
    except Exception as e:
        logError(f"Error in generating JSON: {e}")
        logError(f"Error: {e}")
        output = json.dumps({
            "status": "error",
            "message": f"{e}"
        })
    return output
