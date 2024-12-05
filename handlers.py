try:
    import base64
    from logger import log_it
    from generators import generate_data
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
        if query == "as_json" and api_token:
            log_it("i", f"Got a JSON request...")
            return json_request_handler(api_token)
        return web_request_handler(headers, bypass_auth=False)
    log_it("i", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response


def web_request_handler(headers, bypass_auth=False):
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
        response_body = generate_data("template.html")
        response_body = response_body.encode("utf-8")
        response = CFSimpleHTTPResponse(body=response_body, code=200)
        response.headers = {
            "Content-Type": "text/html"
        }
        log_it("i", "Sending response...")
        return response
    except Exception as e:
        log_it("e", f"Error generating response: {e}")
        return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=200)

def json_request_handler(api_token):
    log_it("i", "Processing JSON request...")
    if api_token != Config.API_TOKEN:
        log_it("e", "Invalid API token!")
        response = CFSimpleHTTPResponse(body=b'{"message": "Unauthorized"}', code=200)
        response.headers = {"Content-Type": "application/json"}
        return response
    log_it("i", "Authorized JSON request.")
    response_body = generate_data(None, return_as_json=True).encode("utf-8")
    response = CFSimpleHTTPResponse(body=b, code=200)
    response.headers = {"Content-Type": "application/json"}
    return response