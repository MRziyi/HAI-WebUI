import asyncio
import json
from typing import Optional
import global_vars
from server.components.utilities import VAgent, get_user_input, print_message_callback, selector_func
from server.components.websocket_manager import WebSocketManager

from autogen_agentchat.conditions import  TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.base import TaskResult

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.agents import AssistantAgent

class ExecuteCore():

    def init_config(self,config_url):
        try:
            with open(config_url, 'r') as f:  # 使用 'r' 模式读取文件
                text = f.read()
            results = json.loads(text)
            task_name = results.get("task_name")
            task_req = results.get("task_req")
            agent_list = results.get("agent_list")
            step_list = results.get("step_list")
        
            print('-------agent_list-------')
            print(agent_list)
            print('-------step_list-------')
            print(step_list)
            print('-----------------------')
        except FileNotFoundError:
            print("Chat history file not found!")
        except json.JSONDecodeError:
            print("Error decoding chat history!")

        self.agents=agent_list
        self.steps=step_list
        self.task_name=task_name
        self.task_req=task_req

    def init_agent_list(self) -> list[BaseChatAgent]:
        agent_list=[]
        # Generate Introductions for each agent
        agents_intro="User: Human User, Administrator\n"
        for agent_info in self.agents:
            agents_intro+=f"{agent_info['name']}: {agent_info['system_message']}\n"

        for agent_info in self.agents:
            if(agent_info['name']=="ProcessManager"):
                agent = VAgent(
                    name="ProcessManager",
                    model_client=global_vars.cached_process_manager_model,
                    description="Manages task progress, assigns tasks to Agents, coordinating efforts, and communicates with users.",
                    system_message=f'''You are ProcessManager, responsible for managing task execution progress, assigning tasks to Agents, coordinating efforts, and communicating with users.
You need to:
- Assign tasks, guide progress, and coordinate with team members and the human user based on the team member descriptions in the `<teamMember>` tag.
- Use the task steps provided in the `<steps>` tag to determine the current task progress:

<steps>
{self.steps}
</steps>

<teamMember>
{agents_intro}
</teamMember>

Important:
- 使用中文
- You are **forbidden** to proceed to the next step on your own. After completing one step, you **must** ask the user for approval before proceeding to the next step.
- Your responsibility is to manage task execution progress and assign tasks to Agents. You are **forbidden** from executing tasks yourself.

Output Format:
- In the `target` field, specify the team member you want to interact with (e.g., if you need to ask the user or gather more information, specify `User`; if you want to communicate with another Agent, delegate tasks, or seek advice, specify the Agent's name).
- In the `answer` field, provide the content you want to communicate with the target team member.
- In the `current_step` field, determine and specify the current task step based on the context.
Follow the JSON format.''',
                    )
            else:
                agent = VAgent(
                    name=agent_info['name'],
                    model_client=global_vars.cached_agent_model,
                    description=f"{agent_info['system_message']}",
                    system_message=f"""You are {agent_info['name']}, {agent_info['system_message']}.
Important:
- 使用中文
- You are **forbidden** from completing the entire plan at once. You must first gather enough background information or user preferences and discuss the plan step-by-step with the user.
- Since the user has no experience with the task, you need to ask **inspiring** questions to uncover implicit constraints or user needs. These questions should help the user explore and complete the task in a detailed and comprehensive way, such as:
  - Additional information needed to solve the problem
  - Potential user needs or overlooked requirements
- When there are multiple options during the planning process, you cannot make the decision on your own. You should provide sufficient background information and ask the user for their input.
- You need to actively recommend options to the user, using specific and real information. Do not fabricate or create content.

Output Format:"""+"""
- In the `target` field, based on the team member descriptions in the `<teamMember>` tag, specify the team member (or yourself again) you want to interact with (e.g., if you need to ask the user or gather more information, specify `User`; if you want to communicate with another Agent, delegate tasks, or seek advice, specify the Agent's name; when adjusting progress (e.g., after a task is completed), communicate with ProcessManager).
- In the `answer` field, provide the content you want to communicate with the target team member.

<teamMember>
{agents_intro}
</teamMember>"""if not self.is_single else"""
- In the `target` field, just fillin "User"
- In the `answer` field, provide the content you want to communicate with User.
""",)
            agent_list.append(agent)

        agent_list.append(UserProxyAgent("User",
            input_func=get_user_input))
        
        return agent_list
    
    def __init__(self, ws_manager:WebSocketManager,is_single:bool):
        self.is_single=is_single
        self.ws_manager=ws_manager
        if is_single:
            self.init_config('config/config_single.txt')
        else:   
            self.init_config('config/config_multi.txt')

        self.send_to_client("config/info",
                    {
                        "task_name":self.task_name,
                        "task_req":self.task_req,
                        "agent_list":self.agents,
                        "step_list":self.steps
                    })
        
        termination = TextMentionTermination("TERMINATE")
        agent_list = self.init_agent_list()
        self.team = SelectorGroupChat(agent_list,
            model_client=global_vars.smaller_model,
            termination_condition=termination,
            allow_repeated_speaker=True,
            selector_func=selector_func,
        )

    def send_to_client(self, type, data):
        asyncio.create_task(self.ws_manager.send_to_client_queue.put(json.dumps(
            {
                "type": type,
                "data": data
            },ensure_ascii=False, indent=4)))
        self.ws_manager.log(type,json.dumps(data,ensure_ascii=False))
        

        
    def start_chat(self,target='',answer=''):
        if target=='' and answer=='':
            global_vars.chat_task = asyncio.create_task(self.run_team_stream('ProcessManager',f"{self.task_name}: {self.task_req}"))if not self.is_single else asyncio.create_task(self.run_team_stream(self.agents[0]['name'],f"{self.task_name}: {self.task_req}"))
        else:
            global_vars.chat_task = asyncio.create_task(self.run_team_stream(target,answer))



    async def run_team_stream(self,target,answer) -> None:
        async for message in self.team.run_stream(task=TextMessage(source='User',content=json.dumps(
                    {
                        "target": target,
                        "answer": answer
                    },ensure_ascii=False,indent=4))):
            if isinstance(message, TaskResult):
                print("Stop Reason:", message.stop_reason)
            # else:
            #     print(message)
