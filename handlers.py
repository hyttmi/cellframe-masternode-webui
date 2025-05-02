from config import Config
from datetime import datetime, timedelta, timezone
from generators import generate_data
from io import BytesIO
from logger import log_it
from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
import base64, hashlib, gzip, traceback
from urllib.parse import parse_qs

def generate_cookie(username, password):
    data = f"{username}:{password}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def generate_token_cookie(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def request_handler(request):
    headers = request.headers
    query = request.query
    client_ip = request.client_address
    if request.method == "GET":
        log_it("i", f"Handling request from {client_ip}...")
        if Config.AUTH_BYPASS or client_ip in ["127.0.0.1", "localhost"]:
            log_it("i", "Auth bypass set, HTTP authentication disabled!")
            return web_request_handler(headers, bypass_auth=True)
        if query == "as_json":
            log_it("i", f"Got a JSON request...")
            return json_request_handler(headers)
        return web_request_handler(headers, bypass_auth=False, query=query)
    log_it("i", f"Unsupported method: {request.method}")
    response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
    return response

def web_request_handler(headers, bypass_auth=False, query=None):
    auth_header = headers.get("Authorization")
    cookie_header = headers.get("Cookie")
    cookie_expires = (datetime.now(timezone.utc) + timedelta(days=14)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD
    access_token = Config.ACCESS_TOKEN
    expected_cookie = generate_cookie(expected_username, expected_password)
    expected_token_cookie = generate_token_cookie(access_token)
    url = Config.PLUGIN_URL

    if query:
        parsed_token = parse_qs(query).get("access_token", [None])[0]
        if parsed_token and parsed_token == access_token:
            try:
                response_body = generate_data("template.html").encode("utf-8")
                compressed_body = compress_content(response_body)
                return CFSimpleHTTPResponse(
                    body=compressed_body,
                    code=302,
                    headers={
                        "Content-Type": "text/html",
                        "Content-Encoding": "gzip",
                        "Set-Cookie": f"auth_cookie={expected_token_cookie}; HttpOnly; Path=/; Expires={cookie_expires}",
                        "Location": f"/{url}"
                    }
                )
            except Exception as e:
                log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
                return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=500)

    if not bypass_auth:
        log_it("i", "Checking authentication...")
        auth_cookie = None
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
                            "Set-Cookie": f"auth_cookie={auth_cookie}; HttpOnly; Path=/; Expires={cookie_expires}"
                        }
                    )
                except Exception as e:
                    log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
                    return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=500)

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
                "Set-Cookie": f"auth_cookie={auth_cookie}; HttpOnly; Path=/; Expires={cookie_expires}"
            }
        )
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return CFSimpleHTTPResponse(body=b"<h1>Internal Server Error</h1>", code=500)

def json_request_handler(headers):
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

def compress_content(content):
    try:
        log_it("d", f"Content original size: {len(content)} bytes")
        compressed_content = gzip.compress(content)
        log_it("d", f"Content compressed size: {len(compressed_content)} bytes")
        return compressed_content
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
