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
        global_vars.execute_page.send_to_server("user/talk",{ 
            "content": self.text_input.value,
            "targetAgent": "ProcessManager" #TODO: change to real target agent
        })


    def __init__(self, **params):
        super().__init__(**params)
        self.avatars= {agent["name"]: agent["avatar"] for agent in self.agents}
        self.avatars["User"] = "😉"
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both')

        self.refresh_messages()

        self.text_input = pn.widgets.TextAreaInput(placeholder="Chat with agents",sizing_mode='stretch_both',resizable='width')
        send_button = pn.widgets.Button(button_type='primary', icon="send",icon_size="25px",sizing_mode='stretch_height',width=50)
        send_button.on_click(self.chat_send)
        start_stop_button = pn.widgets.Button( button_type='primary', icon="microphone",icon_size="25px",sizing_mode='stretch_height',width=50)
        stt_engine = STTEngine(start_stop_button, self.text_input)
        start_stop_button.on_click(stt_engine.start_stop_recognition)
        
        input_buttons = pn.Column(send_button, start_stop_button)
        input_layout = pn.Row(self.text_input,input_buttons)
        
        chat_card_content = pn.Column(
            self._markdown,
            sizing_mode='stretch_both',
            scroll=True
        )
        chat_card = pn.Card(chat_card_content, title='Chat With Agents',
            sizing_mode='stretch_both',)
        input_card = pn.Card(input_layout, collapsible=False,hide_header=True, margin=(10,0,0,0),sizing_mode='stretch_both',max_height=250)

        self._layout = pn.Column(chat_card,input_card)

    def __panel__(self):
        return self._layout

    def refresh_messages(self):
        self.content=""
        for message in self.messages:
            name = message.get("name")
            self.content += f"## {self.avatars.get(name)} {name}\n"
            self.content += message["content"] + "\n\n---\n\n"
        self._markdown.object = self.content

    def add_message(self, content,name):
        self.messages.append({'content':content,'name':name})
        self.content += f"## {self.avatars.get(name)} {name}\n"
        self.content += content+ "\n\n---\n\n"
        self._markdown.object = self.content