from dotenv import load_dotenv
import os
import panel as pn
import autogen

load_dotenv()  # 加载 .env 文件中的所有环境变量

app = None
app_layout= pn.Column("Modal")
modal_content = pn.Column("Modal")

chat_interface = None
chat_status = None
markdown_display = None
progress_indicator = None

input_future=None
chat_task=None
groupchat=None
groupchat_manager=None
is_interrupted=None

execute_page=None