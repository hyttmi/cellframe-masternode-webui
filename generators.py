try:
    from utils import generate_general_info
    from logger import log_it, log_debug
    from config import Config
except ImportError as e:
    log_it("e", f"ImportError: {e}")

@log_debug
def generate_html(template_name):
    try:
        info = generate_general_info(format_time=True)
        log_it("i", info)
        if generate_general_info:
            template = Config.TEMPLATE
            template_path = f"{template}/{template_name}"
            log_it("i", "Generating HTML content...")
            env = Config.jinja_environment()
            template = env.get_template(template_path)
            return template.render(info)
    except Exception as e:
        log_it("e", f"Error: {e}")
