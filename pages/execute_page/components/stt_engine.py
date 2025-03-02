import panel as pn
import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import pyaudio

# 初始化全局变量
recording_results = ""
ws = None
ws_param = None
status = None

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn",
                             "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: ws-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'),
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        return url + '?' + urlencode(v)
    

class STTEngine():
    def __init__(self,start_stop_button:pn.widgets.Button,text_input:pn.widgets.TextInput) -> None:
        self.start_stop_button=start_stop_button
        self.text_input=text_input
        self.is_recording=False


    def on_open(self,ws):
        def run(*args):
            global status
            status = STATUS_FIRST_FRAME
            CHUNK = 520
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            print("---------------开始录音-----------------")
            for i in range(0, int(RATE / CHUNK * 60)):
                if not self.is_recording:
                    break
                buf = stream.read(CHUNK)
                if not buf:
                    status = STATUS_LAST_FRAME
                if status == STATUS_FIRST_FRAME:
                    d = {"common": ws_param.CommonArgs,
                        "business": ws_param.BusinessArgs,
                        "data": {"status": 0, "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    status = STATUS_CONTINUE_FRAME
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "raw"}}
                    ws.send(json.dumps(d))
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
        thread.start_new_thread(run, ())

    def on_message(self,ws, message):
        global recording_results
        try:
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                errMsg = json.loads(message)["message"]
                print(f"sid:{sid} call error:{errMsg} code is:{code}")
            else:
                data = json.loads(message)["data"]["result"]["ws"]
                result = ""
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
                if result not in ['。', '.。', ' .。', ' 。']:
                    print(f"{result}")
                    recording_results = result
                    self.text_input.value += recording_results
        except Exception as e:
            print("receive msg,but parse exception:", e)

    def on_error(self,ws, error):
        print("### error ### : ", error)
        if ws:
            ws.close()
        self.start_stop_button.name = '开始识别'
        self.start_stop_button.button_type = 'primary'
        self.is_recording = False

    def on_close(self,ws, close_status_code, close_msg):
        print("### closed ###")


    def run(self):
        global ws_param, ws
        ws_param = Ws_Param(APPID='5d27dbc6',
                            APIKey='d61163a9bdb5d0a0508f98dee66e0383',
                            APISecret='ZTQ5NTAwZTk0YzQ5MDdhNWViZjcyYjVh')
         
        websocket.enableTrace(False)
        wsUrl = ws_param.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=2)


    def start_stop_recognition(self,event=None):
        if self.is_recording:
            if ws:
                ws.close()
            self.start_stop_button.icon = 'microphone'
            self.start_stop_button.button_type = 'success'
        else:
            thread.start_new_thread(self.run, ())
            self.start_stop_button.icon = 'microphone-off'
            self.start_stop_button.button_type = 'danger'
        self.is_recording = not self.is_recording
