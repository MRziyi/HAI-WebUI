import asyncio
import json
import re
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import panel as pn
import param

import global_vars

class StepList(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    steps = param.List(doc="A list of tasks.")
    task_name =param.String(doc="Name of task")
    task_req = param.String(doc="Requirements of task")
    
    
    def __init__(self, **params):
        super().__init__(**params)
        self._layout = pn.Column(
            pn.pane.GIF('https://upload.wikimedia.org/wikipedia/commons/b/b1/Loading_icon.gif', sizing_mode='stretch_width'),
            "正在推荐合适的步骤..."
            )
        asyncio.create_task(self.generate_step_list())

    async def generate_step_list(self):
        cancellation_token = CancellationToken()
        raw_step_list = await global_vars.global_assistant.on_messages([
            TextMessage(source='user',content=f'''You need to recommend appropriate steps for the task described in the <task> tag and assign the agents from the <agents> tag to each step. Please refer to the example task in the <example_task> tag and respond using the format provided in the <example_output> tag. Only return the JSON format.
<task>{self.task_name}: {self.task_req}</task>
<agents>{self.agents}</agents>'''+'''
<example_task>Debate material preparation: I need to prepare materials for a debate, with the theme "Human nature is inherently evil", and prepare corresponding debate materials.</example_task>

<example_output>
[
    {
        "name": "Define key concepts",
        "content": "DefinitionAgent will collect and organize relevant definitions to ensure clarity."
    },
    {
        "name": "Provide background information",
        "content": "BackgroundAgent will provide background information, including history and current status, to help understand the premise of the debate."
    },
    {
        "name": "Collect key arguments",
        "content": "ArgumentAgent will gather supporting arguments for the 'human nature is inherently evil' position, providing relevant facts, theories, and data."
    },
    {
        "name": "Prepare rebuttal points",
        "content": "RebuttalAgent will predict potential attacks from the opposing side and prepare rebuttal materials."
    },
    {
        "name": "Integrate materials",
        "content": "ProcessManager will integrate all collected materials to ensure logical coherence and completeness."
    }
]
</example_output>

Note: Ensure that the `name` and `content` fields are in Chinese.''')], cancellation_token=cancellation_token
        )

        json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        json_match = json_pattern.search(raw_step_list.chat_message.content)
        if json_match:
            json_content = json_match.group(1)
        else:
            json_content = raw_step_list.chat_message.content
        try:
            self.steps = json.loads(json_content)
        except json.JSONDecodeError as e:
            self._layout.clear()
            self._layout = pn.Column(f"解析失败：\n原始输出：\n{raw_step_list.chat_message.content}\n错误：{e}")
        self.update_step_list()

    def get_lists(self):
        print(self.agents)
        return self.agents,self.steps

    def update_step_list(self):
        self._layout.clear()
        for idx, step in enumerate(self.steps):
            step_info = f'## {idx+1}. {step["name"]}\n'
            step_info += step["content"] + "\n\n---\n\n"
            edit_button = pn.widgets.Button(name="Edit")
            edit_button.on_click(lambda event, idx=idx: self.open_edit_modal(idx))
            
            step_panel = pn.Row(pn.pane.Markdown(step_info,width=290), edit_button)
            self._layout.append(step_panel)
        
        add_step_button = pn.widgets.Button(name='Add Step')
        add_step_button.on_click(self.open_add_modal)
        self._layout.append(add_step_button)
        
    def open_edit_modal(self, idx):
        def confirm_update(event):
            self.steps[idx] = {
                "name": name_input.value,
                "content": content_input.value
            }
            self.update_step_list()
            global_vars.app.close_modal()

        step = self.steps[idx]
        name_input = pn.widgets.TextInput(name="步骤名", value=step["name"])
        content_input = pn.widgets.TextInput(name="步骤内容", value=step["content"])
        confirm_button = pn.widgets.Button(name="Confirm Edit", button_type='primary')
        delete_button = pn.widgets.Button(name="Delete", button_type='danger')
        delete_button.on_click(lambda event, idx=idx: self.delete_step(idx))
        
        confirm_button.on_click(confirm_update)
        modal_content = pn.Row(name_input, content_input)
        buttons = pn.Row(confirm_button, delete_button)
        global_vars.modal_content[:] = [modal_content,buttons]
        global_vars.app.open_modal()


        
    def open_add_modal(self, event):
        name_input = pn.widgets.TextInput(name="Name", value="")
        avatar_input = pn.widgets.TextInput(name="Avatar", value="")
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value="")
        confirm_button = pn.widgets.Button(name="Confirm Add", button_type='primary')
        
        def confirm_add(event):
            self.steps.append({
                "name": name_input.value,
                "content": content_input.value
            })
            self.update_step_list()
            global_vars.app.close_modal()
        
        name_input = pn.widgets.TextInput(name="步骤名")
        content_input = pn.widgets.TextInput(name="步骤内容")
        confirm_button.on_click(confirm_add)
        modal_content = pn.Row(name_input, content_input)
        global_vars.modal_content[:] = [modal_content,confirm_button]
        global_vars.app.open_modal()

    def delete_step(self, idx):
        global_vars.app.close_modal()
        self.steps.pop(idx)
        self.update_step_list()

    def __panel__(self):
        return self._layout