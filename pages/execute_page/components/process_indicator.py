import param
import panel as pn

from panel.viewable import Viewer

pn.extension()  # for notebook

class ProcessIndicator(Viewer):
    current_task = param.Integer(default=1)
    steps=param.List()

    def __init__(self, **params):
        super().__init__(**params)
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both')
        self._sync_markdown()
        self._layout = pn.Column(self._markdown,
            sizing_mode='stretch_both',
            scroll=True)

    def __panel__(self):
        return self._layout

    @param.depends('current_task', watch=True)
    def _sync_markdown(self):
        content = ""
        for i, task in enumerate(self.steps):
            if i < self.current_task - 1:
                status = f"### 🟢 {i+1}."
                state = "[Completed]"
            elif i == self.current_task - 1:
                status = f"## 🟡 {i+1}."
                state = "[In Progress]"
            else:
                status = f"### 🔴 {i+1}."
                state = "[To Do]"
            
            content += f"{status} {task['name']} {state}\n"
            content += f"{task['content']}\n\n"

        self._markdown.object = content