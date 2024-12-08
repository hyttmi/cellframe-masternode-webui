from config import Config
from generators import generate_data
from logger import log_it
from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
import base64, hashlib

def generate_cookie(username, password):
    data = f"{username}:{password}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def request_handler(request):
    headers = request.headers
    query = request.query
    client_ip = request.client_address
    if request.method == "GET":
        log_it("i", f"Handling request from {client_ip}...")
        if Config.AUTH_BYPASS:
            log_it("i", "Auth bypass set, HTTP authentication disabled!")
            return web_request_handler(headers, bypass_auth=True)
        if query == "as_json":
            log_it("i", f"Got a JSON request...")
            return json_request_handler(headers)
        return web_request_handler(headers, bypass_auth=False)
    log_it("i", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response


def web_request_handler(headers, bypass_auth=False):
    auth_header = headers.get("Authorization")
    cookie_header = headers.get("Cookie")
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD
    expected_cookie = generate_cookie(expected_username, expected_password)

    if not bypass_auth:
        if not expected_username or not expected_password:
            log_it("e", "Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
            return CFSimpleHTTPResponse(
                body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!",
                code=200
            )

        if cookie_header:
            cookies = dict(item.split("=") for item in cookie_header.split("; "))
            auth_cookie = cookies.get("auth_cookie")
            print(f"Got {auth_cookie}")
            if auth_cookie and auth_cookie == expected_cookie: # Oooh, a chocolate chip cookie!
                try:
                    response_body = generate_data("template.html").encode("utf-8")
                    return CFSimpleHTTPResponse(body=response_body,
                                                code=200,
                                                headers = {"Content-Type": "text/html"})
                except Exception as e:
                    log_it("e", f"Error generating response: {e}")
                    return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=200)

        if not auth_header:
            log_it("e", "Missing Authorization header")
            return CFSimpleHTTPResponse(body=b"Unauthorized",
                                            code=401,
                                            headers = {
                                                "Content-Type": "text/plain",
                                                "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                                            })
        try:
            encoded_credentials = auth_header.split(' ', 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
        except Exception as e:
            log_it("e", f"Authorization decoding failed: {e}")
            return CFSimpleHTTPResponse(body=b"Unauthorized",
                                        code=401,
                                        headers = {
                                            "Content-Type": "text/plain",
                                            "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                                        })

        if username != expected_username or password != expected_password:
            log_it("e", "Invalid credentials")
            return CFSimpleHTTPResponse(body=b"Unauthorized",
                                        code=401,
                                        headers = {
                                            "Content-Type": "text/plain",
                                            "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                                        })
    try:
        response_body = generate_data("template.html").encode("utf-8")
        return CFSimpleHTTPResponse(body=response_body,
                                    code=200,
                                    headers = {
                                        "Content-Type": "text/html",
                                        "Set-Cookie": f"auth_cookie={expected_cookie}; HttpOnly; Path=/"
                                        }
                                    )
    except Exception as e:
        log_it("e", f"Error generating response: {e}")
        return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=200)

def json_request_handler(headers):
    api_token = headers.get("API_TOKEN")
    log_it("i", "Processing JSON request...")
    if not api_token or api_token != Config.API_TOKEN:
        log_it("e", "Invalid API token!")
        return CFSimpleHTTPResponse(body=b'{"error": "Unauthorized"}',
                                    code=200,
                                    headers = {"Content-Type": "application/json"})

    log_it("i", "Authorized JSON request.")
    response_body = generate_data(None, return_as_json=True).encode("utf-8")
    return CFSimpleHTTPResponse(body=response_body,
                                code=200,
                                headers = {"Content-Type": "application/json"})