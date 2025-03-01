import json
import time
import param
import panel as pn

from panel.viewable import Viewer

import global_vars
from pages.execute_page.components.stt_engine import STTEngine

pn.extension()  # for notebook

class ChatInterface(Viewer):
    messages = param.List(doc="A list of messages.")
    agents = param.List(doc="A list of agents.")

    def chat_send(self,event):

        if self.send_button.icon == 'player-play':
            self.send_button.icon = 'send'
            self.send_button.button_type = 'primary'
            global_vars.execute_page.send_to_server("process/start_plan","{}")
        else:
            target_name=next((agent['name'] for agent in self.agents if self.radio_group.value == agent['avatar'] + ' ' + agent['chinese_name']), None)
            global_vars.execute_page.send_to_server("user/talk",json.dumps(
            {
                "content": self.text_input.value,
                "targetAgent": target_name
            },ensure_ascii=False, indent=4))
            self.add_message(self.text_input.value,"User",target_name)

        self.text_input.value=''

    def __init__(self, **params):
        super().__init__(**params)
        self.avatars= {agent["name"]: agent["avatar"] for agent in self.agents}
        self.avatars["User"] = "😉"
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both')

        self.refresh_messages()

        self.text_input = pn.widgets.TextAreaInput(placeholder="Chat with agents",sizing_mode='stretch_both',resizable='width')
        self.send_button = pn.widgets.Button(button_type='warning', icon="player-play",icon_size="25px",sizing_mode='stretch_height',width=50)
        self.send_button.on_click(self.chat_send)
        start_stop_button = pn.widgets.Button( button_type='primary', icon="microphone",icon_size="25px",sizing_mode='stretch_height',width=50)
        stt_engine = STTEngine(start_stop_button, self.text_input)
        start_stop_button.on_click(stt_engine.start_stop_recognition)

        options= [agent['avatar']+' '+agent["chinese_name"] for agent in self.agents]
        
        self.radio_group = pn.widgets.RadioButtonGroup(options=options, button_type='success',sizing_mode='stretch_width',height=30)

        input_texts = pn.Column(self.radio_group,self.text_input)
        input_buttons = pn.Column(self.send_button, start_stop_button)
        input_layout = pn.Row(input_texts,input_buttons)
        
        chat_card_content = pn.Column(
            self._markdown,
            sizing_mode='stretch_both',
            scroll=True
        )
        chat_card = pn.Card(chat_card_content, title='Chat With Agents',sizing_mode='stretch_both',)

        input_card = pn.Card(input_layout, collapsible=False,hide_header=True, margin=(10,0,0,0),sizing_mode='stretch_both',max_height=250)

        self._layout = pn.Column(chat_card,input_card)

    def __panel__(self):
        return self._layout
    
    def agent_req_answer(self,req_agent_name):
        self.radio_group.value = next((agent['avatar'] + ' ' + agent['chinese_name'] for agent in self.agents if agent['name'] == req_agent_name), None)

    def refresh_messages(self):
        self.content=""
        for message in self.messages:
            source_name = message.get("source_name")
            recipient_name = message.get("recipient_name")
            self.content += f"## {self.avatars.get(source_name)} {source_name} → {self.avatars.get(recipient_name)} {recipient_name}\n"
            self.content += message["content"] + "\n\n---\n\n"
        self._markdown.object = self.content

    def add_message(self, content, source_name, recipient_name):
        self.messages.append({'content':content,'source_name':source_name,'recipient_name':recipient_name})
        self.content += f"## {self.avatars.get(source_name)} {source_name} → {self.avatars.get(recipient_name)} {recipient_name}\n"
        self.content += content+ "\n\n---\n---\n\n"
        self._markdown.object = self.content