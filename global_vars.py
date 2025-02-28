from dotenv import load_dotenv
import os
import panel as pn
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.cache import ChatCompletionCache, CHAT_CACHE_VALUE_TYPE
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache
from pydantic import BaseModel


load_dotenv()  # 加载 .env 文件中的所有环境变量

app = None
app_layout= pn.Column("Modal")
modal_content = pn.Column("Modal")

input_future=None
chat_task=None
groupchat=None
groupchat_manager=None

execute_core=None
req_ans_agent_name=''


cache_store = DiskCacheStore[CHAT_CACHE_VALUE_TYPE](Cache('cache/'))

# The response format for the agent as a Pydantic base model.
class AgentResponse(BaseModel):
    answer: str
    target: str

class ProcessManagerResponse(BaseModel):
    answer: str
    current_step: int
    target: str

process_manager_model = OpenAIChatCompletionClient(
    model="gpt-4o",
    response_format=ProcessManagerResponse,
    api_key=os.environ["OPENAI_API_KEY"],)

cached_process_manager_model = ChatCompletionCache(process_manager_model, cache_store)

agent_model = OpenAIChatCompletionClient(
    model="gpt-4o",
    response_format=AgentResponse,
    api_key=os.environ["OPENAI_API_KEY"],)

cached_agent_model = ChatCompletionCache(agent_model, cache_store)

advanced_model = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"],)

cached_advanced_model = ChatCompletionCache(advanced_model, cache_store)

# advanced_model = OpenAIChatCompletionClient(
#     model="deepseek-v3",
#     api_key=os.getenv("DASHSCOPE_API_KEY"),  
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


global_assistant= AssistantAgent(
            name='Assistant',
            system_message='You are the Assistant. Please refer to the given examples, fulfill the user\'s request and provide the output formatted according to the user’s requirements.',
            model_client=cached_advanced_model
        )


smaller_model = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"],)


cached_smaller_model = ChatCompletionCache(smaller_model, cache_store)

global_formatter= AssistantAgent(
            name='Formatter',
            system_message='You are the Formatter. Please provide the output formatted according to the user’s requirements',
            model_client=cached_smaller_model
        )