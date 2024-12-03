try:
    import base64
    from logger import log_it
    from generators import generate_html
    from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
    from config import Config
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def request_handler(request):
    headers = request.headers
    query = request.query
    api_token = headers.get("API_TOKEN")
    client_ip = request.client_address
    if request.method == "GET":
        log_it("i", f"Handling request from {client_ip}...")

        if Config.AUTH_BYPASS:
            log_it("i", "Auth bypass set, HTTP authentication disabled!")
            return web_request_handler(headers, bypass_auth=True)
        
        if api_token and query == "as_json":
            return json_request_handler(api_token)

        return web_request_handler(headers, bypass_auth=False)

    log_it("i", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response


def web_request_handler(headers, bypass_auth=False):
    """
    Handles HTTP requests with optional Basic Authentication.
    
    Args:
        headers (dict): The HTTP headers received in the request.
        bypass_auth (bool): If True, skips authentication.

    Returns:
        CFSimpleHTTPResponse: The HTTP response object.
    """
    auth_header = headers.get("Authorization")
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD

    if not bypass_auth:
        if not expected_username or not expected_password:
            log_it("e", "Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
            return CFSimpleHTTPResponse(
                body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!",
                code=200
            )

        if not auth_header:
            log_it("e", "Missing Authorization header")
            response = CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
            response.headers = {
                "Content-Type": "text/plain",
                "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
            }
            return response

        try:
            encoded_credentials = auth_header.split(' ', 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
        except Exception as e:
            log_it("e", f"Authorization decoding failed: {e}")
            response = CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
            response.headers = {
                "Content-Type": "text/plain",
                "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
            }
            return response

        if username != expected_username or password != expected_password:
            log_it("e", "Invalid credentials")
            response = CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
            response.headers = {
                "Content-Type": "text/plain",
                "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
            }
            return response
    try:
        response_body = generate_html("template.html")
        response_body = response_body.encode("utf-8")
        response = CFSimpleHTTPResponse(body=response_body, code=200)
        response.headers = {
            "Content-Type": "text/html"
        }
        log_it("i", "Sending response...")
        return response
    except Exception as e:
        log_it("e", f"Error generating response: {e}")
        return CFSimpleHTTPResponse(body=b"Internal Server Error", code=500)

def json_request_handler(api_token):
    if not api_token or api_token != Config.API_TOKEN:
        response = CFSimpleHTTPResponse(body=b"Unauthorized", code=200)
        response.headers = {
        "Content-Type": "application/json"
        }
        return response