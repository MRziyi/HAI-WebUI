import param
import panel as pn

from panel.viewable import Viewer

pn.extension()  # for notebook

class ProcessIndicator(Viewer):
    steps=param.List()

    def __init__(self, **params):
        super().__init__(**params)
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both')
        self.refresh_process_list(0)
        self._layout = pn.Column(self._markdown,
            sizing_mode='stretch_both',
            scroll=True)

    def __panel__(self):
        return self._layout

    def refresh_process_list(self,index):
        content = ""
        for i, task in enumerate(self.steps):
            if i < index - 1:
                status = f"### 🟢 {i+1}."
                state = "[已完成]"
            elif i == index - 1:
                status = f"## 🟡 {i+1}."
                state = "[进行中]"
            else:
                status = f"### 🔴 {i+1}."
                state = "[待办]"
            
            content += f"{status} {task['name']} {state}\n"
            content += f"{task['content']}"
            content += "\n\n---\n\n"

        self._markdown.object = content