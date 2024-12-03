try:
    import base64
    from logger import logger
    from generators import generate_html, generate_json
    from pycfhelpers.node.http.simple import CFSimpleHTTPRequestHandler, CFSimpleHTTPResponse
    from config import Config
except ImportError as e:
    logger("error", f"ImportError: {e}")

def request_handler(request: CFSimpleHTTPRequestHandler):
    headers = request.headers
    query = request.query
    api_token = headers.get("API_TOKEN")
    client_ip = request.client_address
    if request.method == "GET":
        logger("notice", f"Handling request from {client_ip}...")

        if Config.AUTH_BYPASS:
            logger("notice", "Auth bypass set, HTTP authentication disabled!")
            return web_request_handler(request, headers, bypass_auth=True)
        
        if api_token and query == "as_json":
            return json_request_handler(request, api_token)

        return web_request_handler(request, headers, bypass_auth=False)

    logger("error", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response


def web_request_handler(request: CFSimpleHTTPRequestHandler, headers, bypass_auth):
    auth_header = headers.get("Authorization")
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD

    if not bypass_auth:
        if not expected_username or not expected_password:
            logger("error", "Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
            response = CFSimpleHTTPResponse(
                body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!",code=200)
            return response
    try:
        encoded_credentials = auth_header.split(' ', 1)[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
    except (IndexError, ValueError):
        response = CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
        response.headers = {
            "Content-Type": "text/plain",
            "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
        }
        return response
    
    if username != expected_username or password != expected_password:
        response = CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
        response.headers = {
            "Content-Type": "text/plain",
            "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
        }
        return response

    response_body = generate_html("template.html")
    response_body = response_body.encode("utf-8")
    response = CFSimpleHTTPResponse(body=response_body, code=200)
    response.headers = {
        "Content-Type": "text/html"
    }
    logger("notice", "Sending response...")
    return response

def json_request_handler(request: CFSimpleHTTPRequestHandler, api_token):
    if not api_token or api_token != Config.API_TOKEN:
        response = CFSimpleHTTPResponse(body=b"Unauthorized", code=200)
        response.headers = {
        "Content-Type": "application/json"
        }
        return response