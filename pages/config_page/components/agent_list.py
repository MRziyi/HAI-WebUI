import asyncio
import json
import re
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import panel as pn
import param

import global_vars

class AgentList(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    task_name =param.String(doc="Name of task")
    task_req = param.String(doc="Requirements of task")

    def __init__(self, **params):
        super().__init__(**params)
        self._layout = pn.Column(
            pn.pane.GIF('https://upload.wikimedia.org/wikipedia/commons/b/b1/Loading_icon.gif', sizing_mode='stretch_width'),
            "正在推荐合适的多Agent阵容..."
            )
        asyncio.create_task(self.generate_agent_list())

    async def generate_agent_list(self):
        cancellation_token = CancellationToken()
        raw_agent_list = await global_vars.global_assistant.on_messages([
            TextMessage(source='user',content=f'''Recommend a suitable multi-Agent team for the task in the <task> tag. Refer to the example task in <example_task> and respond in the format provided in <example_output>, with only a JSON output.
<task>{self.task_name}: {self.task_req}</task>'''+'''
<example_task>Travel itinerary: Lead a team of 4 to Southeast University for an academic conference and visit famous landmarks in Nanjing. Consider time management, transportation, budget, and the preferences of each team member. Please provide a balanced and reasonable itinerary.</example_task>
<example_output>
[
    {
        "name": "BudgetAgent",
        "avatar": "💵",
        "system_message": "负责预算分配，确保总花费在预算范围内。",
        "chinese_name": "预算专家"
    },
    {
        "name": "TrafficAgent",
        "avatar": "🚗",
        "system_message": "优化交通路线，避免晕车问题，提供合适的交通工具。",
        "chinese_name": "交通专家"
    },
    {
        "name": "DiningAgent",
        "avatar": "🍽️",
        "system_message": "安排餐饮，满足成员饮食偏好。",
        "chinese_name": "餐饮专家"
    },
    {
        "name": "AccommodationAgent",
        "avatar": "🏨",
        "system_message": "选择酒店，平衡预算和成员偏好。",
        "chinese_name": "住宿专家"
    }
]
</example_output>

Important:
- name should be in camel case, avatar should use relevant emojis, system_message and chinese_name should be in Chinese.
- Decide the number of agents based on task requirements, with a maximum of 4 agents.''')], cancellation_token=cancellation_token
        )
        json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        json_match = json_pattern.search(raw_agent_list.chat_message.content)
        if json_match:
            json_content = json_match.group(1)
        else:
            json_content = raw_agent_list.chat_message.content
        try:
            self.agents = json.loads(json_content)
        except json.JSONDecodeError as e:
            self._layout.clear()
            self._layout = pn.Column(f"解析失败：\n原始输出：\n{raw_agent_list.chat_message.content}\n错误：{e}")
        self.update_agents_list()


    def update_agents_list(self):
        self._layout.clear()
        for idx, agent in enumerate(self.agents):
            agent_info = f'## {agent["avatar"]} {agent["chinese_name"]}\n'
            agent_info += agent["system_message"] + "\n\n---\n\n"
            update_button = pn.widgets.Button(name="Update")
            update_button.on_click(lambda event, idx=idx: self.open_update_popup(idx))
            agent_panel = pn.Row(pn.pane.Markdown(agent_info,width=290), update_button)
            self._layout.append(agent_panel)
        
        add_agent_button = pn.widgets.Button(name='Add Agent')
        add_agent_button.on_click(self.open_add_popup)
        self._layout.append(add_agent_button)
        
    def open_update_popup(self, idx):

        def confirm_update(event):
            self.agents[idx] = {
                "name": name_input.value,
                "avatar": avatar_input.value,
                "system_message": system_message_input.value
            }
            self.update_agents_list()
            global_vars.app.close_modal()

        agent = self.agents[idx]
        name_input = pn.widgets.TextInput(name="Name", value=agent["name"])
        avatar_input = pn.widgets.TextInput(name="Avatar", value=agent["avatar"])
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value=agent["system_message"])
        confirm_button = pn.widgets.Button(name="Confirm Update", button_type='primary')
        delete_button = pn.widgets.Button(name="Delete", button_type='danger', width=80)
        delete_button.on_click(lambda event, idx=idx: self.delete_agent(idx))
        
        confirm_button.on_click(confirm_update)
        popup_content = pn.Row(name_input, avatar_input, system_message_input)
        buttons = pn.Row(confirm_button, delete_button)
        global_vars.modal_content[:] = [popup_content,buttons]
        global_vars.app.open_modal()

    def get_agents(self):
        return self.agents
        
    def open_add_popup(self, event):
        name_input = pn.widgets.TextInput(name="Name", value="")
        avatar_input = pn.widgets.TextInput(name="Avatar", value="")
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value="")
        confirm_button = pn.widgets.Button(name="Confirm Add", button_type='primary')
        
        def confirm_add(event):
            self.agents.append({
                "name": name_input.value,
                "avatar": avatar_input.value,
                "system_message": system_message_input.value
            })
            self.update_agents_list()
            global_vars.app.close_modal()
        
        confirm_button.on_click(confirm_add)
        popup_content = pn.Column(name_input, avatar_input, system_message_input, confirm_button)
        popup_content = pn.Row(name_input, avatar_input, system_message_input)
        global_vars.modal_content[:] = [popup_content,confirm_button]
        global_vars.app.open_modal()

    def add_agent(self, event):
        self.update_agents_list()

    def delete_agent(self, idx):
        global_vars.app.close_modal()
        self.agents.pop(idx)
        self.update_agents_list()

    def __panel__(self):
        return self._layout