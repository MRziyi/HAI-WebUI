import argparse
import asyncio
import json
import sys
import websockets
import panel as pn
import uvicorn

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import global_vars
from pages.execute_page.components.websocket_manager import WebSocketManager
from pages.execute_page.execute_page import ExecutePage

async def send_to_server_listener(ws_manager: WebSocketManager):
    while True:
        msg_to_send = await ws_manager.send_to_server_queue.get()
        await ws_manager.websocket.send(msg_to_send)

async def recv_from_server_listener(ws_manager: WebSocketManager):
    while True:
        raw_input = await ws_manager.websocket.recv()
        try:
            json_input = json.loads(raw_input)
            type = json_input.get("type")
            data = json_input.get("data")
            try:
                json_data = json.loads(data)
            except:
                json_data=data
                print("JSON Data: "+str(data))
        except Exception as e:
            print("raw_data decode ERROR: "+str(e))
        
        if type == "config/info":
            task_name = json_data.get("task_name")
            task_req = json_data.get("task_req")
            agent_list = json_data.get("agent_list")
            step_list = json_data.get("step_list")
            
            global_vars.execute_page = ExecutePage(task_name=task_name,task_req=task_req,agents=agent_list,steps=step_list,ws_manager=ws_manager)
            global_vars.app_layout[:] = [global_vars.execute_page]
          

ws_url="ws://localhost:8002/ws"

async def websocket_connection():
    async with websockets.connect(ws_url) as websocket:
        ws_manager = WebSocketManager(websocket=websocket)
        try:
            global_vars.app_layout[:] = ['# 欢迎来到 VELVET', f'### 已连接！等待任务信息...']
            # Start listeners as tasks
            send_task = asyncio.create_task(send_to_server_listener(ws_manager))
            recv_task = asyncio.create_task(recv_from_server_listener(ws_manager))
            
            # Wait for both listeners and chat to complete
            await asyncio.gather(send_task, recv_task)
        except Exception as e:
            print("ERROR:", str(e))

css = """
#input{
  font-size: 120%;
}
"""
pn.extension(raw_css=[css])

asyncio.create_task(websocket_connection())
# 创建 Panel 服务器
global_vars.app = pn.template.VanillaTemplate(title='VELVET')
global_vars.app.main.append(global_vars.app_layout)
global_vars.app.modal.append(global_vars.modal_content)

# 运行 Panel 服务器
global_vars.app.servable()

global_vars.app_layout[:] = ['# 欢迎来到 VELVET', f'### 正在连接至: {ws_url}...']
    