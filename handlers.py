from utils import *
from generators import generateHTML, generateJSON
import base64
from pycfhelpers.node.http.simple import CFSimpleHTTPRequestHandler, CFSimpleHTTPResponse
from jinja2 import Environment, PackageLoader, select_autoescape
from urllib.parse import parse_qs

env = Environment(
    loader=PackageLoader("cellframe-masternode-webui"),
    autoescape=select_autoescape()
)
env.policies['json.dumps_kwargs'] = {'sort_keys': False}

last_request_time = {}
rate_limit_interval = 15

def requestHandler(request: CFSimpleHTTPRequestHandler):
    if request.method == "GET":
        rate_limit_active = getConfigValue("webui", "rate_limit", default=False)
        if rate_limit_active:
            client_ip = request.client_address
            current_time = time.time()

            if client_ip in last_request_time:
                elapsed_time = current_time - last_request_time[client_ip]

                if elapsed_time < rate_limit_interval:
                    remaining_time = rate_limit_interval - elapsed_time
                    res = f'{{"Error": "Rate limit exceeded. Please wait {int(remaining_time)} seconds."}}'.encode("utf-8")
                    response = CFSimpleHTTPResponse(
                        body=res,
                        code=200
                    )
                    response.headers = {
                        "Content-Type": "application/json"
                    }
                    logError(f"Rate limit exceeded from {client_ip}")
                    return response

            last_request_time[client_ip] = current_time
            return getRequestHandler(request)
        else:
            return getRequestHandler(request)
    else:
        logError(f"Unsupported method: {request.method}")
        response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
        return response

def getRequestHandler(request: CFSimpleHTTPRequestHandler):
    logNotice(f"Handling request from {request.client_address}...")
    headers = request.headers
    query = request.query
    api_token = headers.get("API_TOKEN")
    auth_header = headers.get("Authorization")
    expected_username = getConfigValue("webui", "username")
    expected_password = getConfigValue("webui", "password")
    expected_api_token = getConfigValue("webui", "api_token", default=False)

    if not expected_username or not expected_password:
        logError("Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
        response = CFSimpleHTTPResponse(
            body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!",
            code=200
        )
        return response

    if query:
        logNotice("Query found! Checking API_TOKEN...")
        if not api_token:
            logError("API_TOKEN is missing in a query request. Access denied.")
            response = CFSimpleHTTPResponse(body=b"Unauthorized - API_TOKEN required", code=401)
            response.headers = {
                "Content-Type": "text/plain"
            }
            return response
        if api_token != expected_api_token:
            logError("Invalid API token.")
            response = CFSimpleHTTPResponse(body=b"Invalid API Token", code=401)
            response.headers = {
                "Content-Type": "text/plain"
            }
            return response

    if not api_token:
        logNotice("No API_TOKEN provided, performing Basic Authentication...")
        if not auth_header or not auth_header.startswith('Basic '):
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

    if query:
        logNotice("Got a query GET request with valid API_TOKEN...")

        if "as_json" in query:
            response_body = generateJSON()
            response = CFSimpleHTTPResponse(body=response_body.encode("utf-8"), code=200)
            response.headers = {
                "Content-Type": "application/json"
            }
            logNotice("Sending JSON response...")
            return response

        logNotice("No valid query parameter found, skipping JSON response.")

    response_body = generateHTML("template.html")
    response_body = response_body.encode("utf-8")
    response = CFSimpleHTTPResponse(body=response_body, code=200)
    response.headers = {
        "Content-Type": "text/html"
    }
    logNotice("Sending response...")
    return response
