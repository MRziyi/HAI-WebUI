import asyncio
from datetime import datetime
import global_vars


class WebSocketManager:
    def __init__(self, websocket):
        self.websocket = websocket
        self.send_to_server_queue = asyncio.Queue()