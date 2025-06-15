from config import Config, Globals
from datetime import datetime, timedelta, timezone
from generators import generate_data
from logger import log_it
from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
import base64, hashlib, gzip, traceback, json, http.cookies, threading
from urllib.parse import parse_qs
from utils import is_cli_ready, restart_node, cli_command
from uuid import uuid4

def generate_cookie(username, password):
    data = f"{username}:{password}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def generate_token_cookie(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def request_handler(request):
    url = request.url
    headers = request.headers
    query = request.query
    client_ip = request.client_address
    body = request.body
    if request.method == "GET":
        log_it("i", f"Handling GET request from {client_ip} and url of {url}...")
        if Config.AUTH_BYPASS:
            log_it("i", "Auth bypass set, HTTP authentication disabled!")
            return GET_request_handler(headers, bypass_auth=True)
        if query == "as_json":
            log_it("i", f"Got a JSON request...")
            return JSON_request_handler(headers)
        return GET_request_handler(headers, bypass_auth=False, query=query)
    if request.method == "POST":
        log_it("i", f"Handling POST request from {client_ip}")
        if body:
            try:
                payload = body.decode("utf-8")
                return POST_request_handler(headers, payload)
            except UnicodeDecodeError:
                return CFSimpleHTTPResponse(body=b'{"error": "malformed payload"}',
                                        code=500,
                                        headers={
                                            "Content-Type": "application/json"
                                        })
        else:
            return CFSimpleHTTPResponse(body=b'{"error": "payload missing"}',
                                        code=500,
                                        headers={
                                            "Content-Type": "application/json"
                                        })
    log_it("i", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response

def GET_request_handler(headers, bypass_auth=False, query=None):
    log_it("d", f"Got GET request with headers: {headers}, query: {query}")
    auth_header = headers.get("Authorization")
    cookie_header = headers.get("Cookie")
    cookie_expires = (datetime.now(timezone.utc) + timedelta(days=14)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD
    access_token = Config.ACCESS_TOKEN
    auth_cookie = None
    Globals.POST_AUTH_COOKIE = str(uuid4())
    expected_cookie = generate_cookie(expected_username, expected_password)
    expected_token_cookie = generate_token_cookie(access_token)
    url = Config.PLUGIN_URL
    if not is_cli_ready():
        errmsg = f"<h1>CLI is not ready, wait for a moment!</h1>"
        return CFSimpleHTTPResponse(body=errmsg.encode("utf-8"), code=500)
    if query:
        parsed_token = parse_qs(query).get("access_token", [None])[0]
        if parsed_token is None:
            log_it("e", "No access_token in query")
            return CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
        if parsed_token != str(Config.ACCESS_TOKEN):
            log_it("e", f"Invalid access_token: got '{parsed_token}', expected '{Config.ACCESS_TOKEN}'")
            return CFSimpleHTTPResponse(body=b"Unauthorized", code=401)
        if parsed_token and parsed_token == access_token:
            log_it("d", f"Parsed token: {parsed_token}, Expected: {access_token}")
            try:
                response_body = generate_data("template.html").encode("utf-8")
                compressed_body = compress_content(response_body)
                return CFSimpleHTTPResponse(
                    body=compressed_body,
                    code=302,
                    headers={
                        "Content-Type": "text/html",
                        "Content-Encoding": "gzip",
                        "Set-Cookie": (
                            f"auth_cookie={expected_token_cookie}; HttpOnly; Path=/; Expires={cookie_expires}\r\n"
                            f"Set-Cookie: post_auth_cookie={Globals.POST_AUTH_COOKIE}; Path=/;"
                        ),
                        "Location": f"/{url}"
                    }
                )
            except Exception as e:
                log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
                errmsg = f"<h1>Internal Server Error</h1><pre>{traceback.format_exc()}</pre>"
                return CFSimpleHTTPResponse(body=errmsg.encode("utf-8"), code=500)
    if not bypass_auth:
        log_it("i", "Checking authentication...")
        if cookie_header:
            cookies = dict(item.split("=", 1) for item in cookie_header.split("; "))
            auth_cookie = cookies.get("auth_cookie")
            if auth_cookie in [expected_cookie, expected_token_cookie]:
                try:
                    response_body = generate_data("template.html").encode("utf-8")
                    compressed_body = compress_content(response_body)
                    return CFSimpleHTTPResponse(
                        body=compressed_body,
                        code=200,
                        headers={
                            "Content-Type": "text/html",
                            "Content-Encoding": "gzip",
                            "Set-Cookie": (
                                f"auth_cookie={expected_token_cookie}; HttpOnly; Path=/; Expires={cookie_expires}\r\n"
                                f"Set-Cookie: post_auth_cookie={Globals.POST_AUTH_COOKIE}; Path=/;"
                            )
                        }
                    )
                except Exception as e:
                    log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
                    errmsg = f"<h1>Internal Server Error</h1><pre>{traceback.format_exc()}</pre>"
                    return CFSimpleHTTPResponse(body=errmsg.encode("utf-8"), code=500)
        if not auth_header:
            log_it("e", "Missing Authorization header")
            return CFSimpleHTTPResponse(
                body=b"Unauthorized",
                code=401,
                headers={
                    "Content-Type": "text/plain",
                    "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                }
            )
        try:
            encoded_credentials = auth_header.split(" ", 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception as e:
            log_it("e", f"Authorization decoding failed: {e}")
            return CFSimpleHTTPResponse(
                body=b"Unauthorized",
                code=401,
                headers={
                    "Content-Type": "text/plain",
                    "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                }
            )
        if username != expected_username or password != expected_password:
            log_it("e", "Invalid credentials")
            return CFSimpleHTTPResponse(
                body=b"Unauthorized",
                code=401,
                headers={
                    "Content-Type": "text/plain",
                    "WWW-Authenticate": 'Basic realm="Cellframe node webui"'
                }
            )
        auth_cookie = expected_cookie
    try:
        response_body = generate_data("template.html").encode("utf-8")
        compressed_body = compress_content(response_body)
        return CFSimpleHTTPResponse(
            body=compressed_body,
            code=200,
            headers={
                "Content-Type": "text/html",
                "Content-Encoding": "gzip",
                "Set-Cookie": (
                    f"auth_cookie={expected_token_cookie}; HttpOnly; Path=/; Expires={cookie_expires}\r\n"
                    f"Set-Cookie: post_auth_cookie={Globals.POST_AUTH_COOKIE}; Path=/;"
                )
            }
        )
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        errmsg = f"<h1>Internal Server Error</h1><pre>{traceback.format_exc()}</pre>"
        return CFSimpleHTTPResponse(body=errmsg.encode("utf-8"), code=500)

def POST_request_handler(headers, payload):
    try:
        payload = json.loads(payload)
        log_it("d", f"Got payload {payload} with auth_header {headers}")
        cookies = http.cookies.SimpleCookie()
        auth_token = None
        if "Cookie" in headers:
            cookies.load(headers["Cookie"])
            cookie_value = cookies.get("post_auth_cookie")
            if cookie_value:
                auth_token = cookie_value.value

        if auth_token != Globals.POST_AUTH_COOKIE:
            log_it("e", "Invalid or missing post_auth_cookie")
            log_it("d", f"Expected: {Globals.POST_AUTH_COOKIE}, got: {auth_token}")
            return CFSimpleHTTPResponse(
                body=b'{"error": "Unauthorized, post_auth_cookie is invalid or missing"}',
                code=403,
                headers={"Content-Type": "application/json"}
            )

        action = payload.get("action")
        if not action:
            return CFSimpleHTTPResponse(
                body=b'{"error": "Action is missing!"}',
                code=400,
                headers={"Content-Type": "application/json"}
            )

        if action == "restart":
            threading.Timer(1.0, restart_node).start()
            restart_node()
            return CFSimpleHTTPResponse(
                body=b'{"status": "Node restart triggered"}',
                code=200,
                headers={"Content-Type": "application/json"}
            )

        elif action == "cli":
            command = payload.get("command", "").strip()
            if not command:
                return CFSimpleHTTPResponse(
                    body=b'{"error": "No command provided"}',
                    code=400,
                    headers={"Content-Type": "application/json"}
                )
            try:
                disallowed_commands = []
                if Config.CLI_DISALLOWED_COMMANDS:
                    if isinstance(Config.CLI_DISALLOWED_COMMANDS, str):
                        disallowed_commands.append(Config.CLI_DISALLOWED_COMMANDS)
                    elif isinstance(Config.CLI_DISALLOWED_COMMANDS, list):
                        disallowed_commands.extend(Config.CLI_DISALLOWED_COMMANDS)

                log_it("d", f"Disallowed commands: {disallowed_commands}")

                log_it("i", f"Executing CLI command: {command}")
                if not is_cli_ready():
                    log_it("e", "CLI is not ready, cannot execute command")
                    return CFSimpleHTTPResponse(
                        body=b'{"error": "CLI is not ready"}',
                        code=500,
                        headers={"Content-Type": "application/json"}
                    )
                split_command = command.split()
                if split_command[0] in disallowed_commands:
                    log_it("e", f"CLI command '{command}' is not allowed!")
                    return CFSimpleHTTPResponse(
                        body=b'{"error": "This CLI command is not allowed!"}',
                        code=403,
                        headers={"Content-Type": "application/json"}
                    )

                result = cli_command(command)
                if not result:
                    log_it("e", "CLI command returned no result")
                    return CFSimpleHTTPResponse(
                        body=b'{"error": "CLI command returned no result"}',
                        code=500,
                        headers={"Content-Type": "application/json"}
                    )
                return CFSimpleHTTPResponse(
                    body=json.dumps({"output": result}).encode("utf-8"),
                    code=200,
                    headers={"Content-Type": "application/json"}
                )
            except Exception as e:
                log_it("e", f"An error occurred while executing CLI command: {e}", exc=traceback.format_exc())
                return CFSimpleHTTPResponse(
                    body=b'{"error": "Failed to execute CLI command"}',
                    code=500,
                    headers={"Content-Type": "application/json"}
                )
        else:
            return CFSimpleHTTPResponse(
                body=b'{"error": "Unsupported POST request!"}',
                code=400,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return CFSimpleHTTPResponse(
            body=b'{"error": "Internal server error"}',
            code=500,
            headers={"Content-Type": "application/json"}
        )

def JSON_request_handler(headers):
    try:
        access_token = headers.get("ACCESS_TOKEN")
        log_it("i", "Processing JSON request...")
        if not access_token or access_token != Config.ACCESS_TOKEN:
            log_it("e", f"Invalid access token ({access_token})!")
            return CFSimpleHTTPResponse(body=b'{"error": "Unauthorized"}',
                                        code=401,
                                        headers={
                                            "Content-Type": "application/json"
                                        })
        log_it("i", "Authorized JSON request.")
        response_body = compress_content(generate_data(None, return_as_json=True).encode("utf-8"))
        return CFSimpleHTTPResponse(body=response_body,
                                    code=200,
                                    headers={
                                        "Content-Type": "application/json"
                                    })
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return CFSimpleHTTPResponse(body=b'{"error": "Internal server error"}',
                                        code=500,
                                        headers={
                                            "Content-Type": "application/json"
                                    })

def compress_content(content):
    try:
        log_it("d", f"Content original size: {len(content)} bytes")
        compressed_content = gzip.compress(content)
        log_it("d", f"Content compressed size: {len(compressed_content)} bytes")
        return compressed_content
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
