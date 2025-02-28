import json
import sys
import panel as pn
import global_vars
from pages.config_page.config_page import ConfigPage

pn.extension()

# 创建 Panel 服务器
def init_web_page():
    if len(sys.argv) < 3:
        print("Usage: python config_web_app.py <task_name>")
        sys.exit

    index1 = int(sys.argv[1])
    index2 = int(sys.argv[2])

    with open('config/taskDef.json', 'r', encoding='utf-8') as f:
        task_def = json.load(f)

    task_name = task_def.get("taskName", "")
    task_description = task_def.get("taskDescription", "")
    task_options = task_def.get("taskOptions", [])

    task_req=f'{task_description}\n\n 我选择：{task_options[index1].get("optionInfo")}\n 我的朋友选择：{task_options[index2].get("optionInfo")}'
    
    config = ConfigPage(task_name=task_name,task_req=task_req)
    global_vars.app_layout[:] = [config]
    global_vars.app = pn.template.VanillaTemplate(title='VELVET')
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()