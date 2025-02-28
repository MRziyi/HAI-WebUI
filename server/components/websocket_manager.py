import asyncio
from datetime import datetime
from fastapi import WebSocket
import global_vars


class WebSocketManager:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.send_to_client_queue = asyncio.Queue()
        now = datetime.now()
        date_str = now.strftime("%m-%d@%H:%M")
        self.file_path = f'history/{date_str}.tsv'
        # Append the log entry to the file

    async def connect(self):
        await self.websocket.accept()
        self.log("WS CONNECTED")
        print("WS Connected!")

    async def disconnect(self):
        if(global_vars.chat_task!=None):
            global_vars.chat_task.cancel()
        
        self.log("WS DISCONNECTED")
        print("WS Disconnected")

    
    def log(self,url, info=''):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        # Log entry
        log_entry = f"\"{time_str}\"\t\"{url}\"\t\"{info}\"\n"
        
        # Append the log entry to the file
        with open(self.file_path, 'a') as file:
            file.write(log_entry)