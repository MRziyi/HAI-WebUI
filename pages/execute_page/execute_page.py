import asyncio
import json
import panel as pn
import param
import global_vars
from pages.execute_page.components.chat_interface import ChatInterface
from pages.execute_page.components.process_indicator import ProcessIndicator


class ExecutePage(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    steps = param.List(doc="A list of tasks.")
    task_name = param.String(doc="Name of task")
    task_req = param.String(doc="Requirements for task")
    ws_manager = param.Parameter()

    def send_to_server(self, type, data):
        asyncio.create_task(self.ws_manager.send_to_server_queue.put(json.dumps(
            {
                "type": type,
                "data": data
            },ensure_ascii=False, indent=4)))
        

    def __init__(self, **params):
        super().__init__(**params)

        confirmed_agents = f"## 任务「{self.task_name}」的Agents分配\n"
        for agent in self.agents:
            confirmed_agents += f'### {agent["avatar"]} {agent["name"]}\n'
            confirmed_agents += agent["system_message"] + "\n\n---\n\n"
        
        agent_card_content = pn.Column(
            pn.pane.Markdown(confirmed_agents, sizing_mode='stretch_both'),
            sizing_mode='stretch_height',
            max_height=350,
            scroll=True
        )
        
        agent_card = pn.Card(agent_card_content, sizing_mode='stretch_height',title='智能体分配',margin=(0, 10, 0, 0), width=350)


        global_vars.progress_indicator = ProcessIndicator(steps=self.steps)
        process_card = pn.Card(global_vars.progress_indicator, title='进度指示', sizing_mode='stretch_height',margin=(10, 10, 0, 0), width=350)
        info_card = pn.Column(agent_card,process_card)        
        
        self.chat_interface=ChatInterface(agents=self.agents)

        self._layout = pn.Row(info_card, self.chat_interface)


    def __panel__(self):
        return self._layout