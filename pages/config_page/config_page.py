import json
import param
import panel as pn

from panel.viewable import Viewer
import global_vars
from pages.config_page.components.agent_list import AgentList
from pages.config_page.components.step_list import StepList

pn.extension()  # for notebook

class ConfigPage(Viewer):
    task_name = param.String()
    task_req = param.String()

    def __init__(self, **params):
        super().__init__(**params)

        self.req_input = pn.widgets.TextAreaInput(
            name=self.task_name,
            auto_grow=True, 
            max_rows=50, 
            rows=20, 
            placeholder=f"任务「{self.task_name}」已知的详细信息/要求/约束",
            sizing_mode='scale_width',
            value=self.task_req)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(self.req_confirm)
        
        self.req_content = pn.Column(
            f"# 任务「{self.task_name}」的详细信息/要求/约束",
            self.req_input,
            confirm_button
        )
        req_card = pn.Card(self.req_content, title='详细信息', max_width=400)

        self.agent_list_content = pn.Column("# 请首先确认任务的详细信息/要求/约束")
        agent_card = pn.Card(self.agent_list_content, title='Agents分配', margin=(0, 20), max_width=400)

        self.step_list_content = pn.Column("# 请首先确认任务的Agents分配")
        step_card = pn.Card(self.step_list_content, title='步骤配置', max_width=400)

        self._layout = pn.Row(req_card, agent_card, step_card)

    def req_confirm(self, event):
        confirmed_req = f"## 任务「{self.task_name}」的详细信息\n{self.req_input.value}"
        self.req_content[:] = [confirmed_req]
        
        agent_list_content = AgentList(task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, agent_list_content=agent_list_content: self.agents_confirm(agent_list_content))
        
        self.agent_list_content[:] = [agent_list_content, confirm_button]
    
    def agents_confirm(self, agent_list_content):
        agent_list=agent_list_content.get_agents()
        agent_list.insert(2,{"name": "ProcessManager", "avatar": "⏩️", "system_message": "负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问","chinese_name": "进度管理员"})
        confirmed_agents = f"## 任务「{self.task_name}」的Agents分配\n"
        for agent in agent_list:
            confirmed_agents += f'## {agent["avatar"]} {agent["chinese_name"]}\n'
            confirmed_agents += agent["system_message"] + "\n\n---\n\n"
        
        step_list_content = StepList(agents=agent_list,task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, step_list_content=step_list_content: self.steps_confirm(step_list_content))

        self.agent_list_content[:] = [confirmed_agents]
        self.step_list_content[:] = [step_list_content,confirm_button]

    
    def steps_confirm(self,step_list_content):
        agent_list,step_list=step_list_content.get_lists()
        try:
            with open('config/config_multi.txt', 'w') as f:  # 使用 'w' 模式写入文件
                f.write(json.dumps(
                    {
                        "task_name":self.task_name,
                        "task_req":self.req_input.value,
                        "agent_list":agent_list,
                        "step_list":step_list
                    },ensure_ascii=False,indent=4))
            print("Config exported!")
        except Exception as e:
            print(f"Error exporting config history: {e}")
        
        global_vars.app_layout[:] = ["WebSocket服务待启用，请前往VR进行体验"]

    def __panel__(self):
        return self._layout

