import argparse
import asyncio
import json
import sys
from fastapi import FastAPI, WebSocket
import uvicorn

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import global_vars
from server.components.websocket_manager import WebSocketManager
from server.execute_core import ExecuteCore

ws_app = FastAPI()

parser = argparse.ArgumentParser(description="WebSocket server options")
parser.add_argument('--single', action='store_true', help='Run in single mode')

# Parse the arguments
args = parser.parse_args()

async def send_to_client_listener(ws_manager: WebSocketManager):
    while True:
        msg_to_send = await ws_manager.send_to_client_queue.get()
        await ws_manager.websocket.send_text(msg_to_send)

async def recv_from_client_listener(ws_manager: WebSocketManager):
    while True:
        raw_input = await ws_manager.websocket.receive_text()
        print("-----MSG FROM WS------\n"+raw_input)
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
        
        ws_manager.log(type,json.dumps(data,ensure_ascii=False))
        if type == "user/talk":
            text = json_data.get("content")
            target_agent_name = json_data.get("targetAgent")
            if text == '':
                return
            if global_vars.input_future and not global_vars.input_future.done():#用户的提问相应机制
                global_vars.input_future.set_result('''{
    "target": "'''+target_agent_name+'''",
    "answer": "'''+text+'''"
}''')
            else:#用户的主动打断机制
                global_vars.chat_task.cancel()  # 取消任务
                global_vars.execute_core.start_chat(target_agent_name,text)
                
        elif type=="process/start_plan":
            if(global_vars.chat_task!=None):
                global_vars.chat_task.cancel()
            global_vars.execute_core.start_chat()
        elif type=="user/confirm_solution":
            solution = json_data.get("solution")
            original_step = json_data.get("original_step")
            cancellation_token = CancellationToken()
            summary = await global_vars.global_formatter.on_messages([
                TextMessage(source='user',content=f'''Summarize the content within the <text> tag, keeping key points and presenting the result clearly and concisely. Use MarkDown format.
        <text>
        {solution}
        </text>''')],
        
        cancellation_token=cancellation_token
            )

            global_vars.execute_core.send_to_client("solution/summary",
                    {
                        "original_step":original_step,
                        "solution_summary":summary.chat_message.content
                    })


@ws_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    ws_manager = WebSocketManager(websocket=websocket)
    await ws_manager.connect()
    try:
        # Start listeners as tasks
        send_task = asyncio.create_task(send_to_client_listener(ws_manager))
        recv_task = asyncio.create_task(recv_from_client_listener(ws_manager))
        
        global_vars.execute_core = ExecuteCore(ws_manager=ws_manager,is_single=args.single)

        # Wait for both listeners and chat to complete
        await asyncio.gather(send_task, recv_task)
    except Exception as e:
        print("ERROR:", str(e))
    finally:
        await ws_manager.disconnect()

if __name__ == "__main__":
    uvicorn.run(ws_app, host="0.0.0.0", port=8002)
