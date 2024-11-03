import time, base64
from utils import logError, logNotice
from generators import generateHTML, generateJSON
from pycfhelpers.node.http.simple import CFSimpleHTTPRequestHandler, CFSimpleHTTPResponse
from config import Config

last_request_time = {}
rate_limit_interval = Config.RATE_LIMIT_INTERVAL

def requestHandler(request: CFSimpleHTTPRequestHandler):
    if request.method == "GET":
        if Config.RATE_LIMIT_ACTIVE:
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
    expected_username = Config.USERNAME
    expected_password = Config.PASSWORD
    expected_api_token = Config.API_TOKEN
    auth_bypass = Config.AUTH_BYPASS

    if query == "as_json":
        if not api_token:
            logError("API_TOKEN is missing in a query request. Access denied.")
            res = f'{{"Error": "Unauthorized - API_TOKEN required"}}'.encode("utf-8")
            response = CFSimpleHTTPResponse(body=res, code=200)
            response.headers = {
                "Content-Type": "application/json"
            }
            return response

        if api_token != expected_api_token:
            logError("Invalid API token.")
            res = f'{{"Error": "Invalid API token"}}'.encode("utf-8")
            response = CFSimpleHTTPResponse(body=res, code=200)
            response.headers = {
                "Content-Type": "application/json"
            }
            return response

        response_body = generateJSON()
        response = CFSimpleHTTPResponse(body=response_body.encode("utf-8"), code=200)
        response.headers = {
            "Content-Type": "application/json"
        }
        logNotice("Sending JSON response...")
        return response

    elif query:
        logError("Invalid query request.")
        res = f'{{"Error": "Invalid query request"}}'.encode("utf-8")
        response = CFSimpleHTTPResponse(body=res, code=200)
        response.headers = {
            "Content-Type": "application/json"
        }
        return response

    if not auth_bypass:
        if not expected_username or not expected_password:
            logError("Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
            response = CFSimpleHTTPResponse(
                body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!",code=200)
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

    response_body = generateHTML("template.html")
    response_body = response_body.encode("utf-8")
    response = CFSimpleHTTPResponse(body=response_body, code=200)
    response.headers = {
        "Content-Type": "text/html"
    }
    logNotice("Sending response...")
    return response
