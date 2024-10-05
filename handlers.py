from utils import *
from generators import generateHTML
import base64
from pycfhelpers.node.http.simple import CFSimpleHTTPRequestHandler, CFSimpleHTTPResponse
from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("cellframe-masternode-webui"),
    autoescape=select_autoescape()
)
def requestHandler(request: CFSimpleHTTPRequestHandler):
    if request.method == "GET":
        return getRequestHandler(request)
    else:
        logError(f"Unsupported method: {request.method}")
        response = CFSimpleHTTPResponse(body=b"Unsupported method", code=200)
        return response

def getRequestHandler(request: CFSimpleHTTPRequestHandler):
    logNotice(f"Handling request from {request.client_address}...")
    headers = request.headers
    auth_header = headers.get('Authorization')
    expected_username = getConfigValue("webui", "username")
    expected_password = getConfigValue("webui", "password")
    if not expected_username or not expected_password:
        logError(f"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!")
        response = CFSimpleHTTPResponse(body=b"Missing configuration in cellframe-node.cfg. Username or password is not set, plugin will be unavailable!", code=200)
        return response
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
    response_body = generateHTML(template_name="template.html")
    response_body = response_body.encode("utf-8")
    response = CFSimpleHTTPResponse(body=response_body, code=200)
    response.headers = {
        "Content-Type": "text/html"
    }
    logNotice("Sending response...")
    return response