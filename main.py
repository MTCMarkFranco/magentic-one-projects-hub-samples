import asyncio
import sys
import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from colorama import Fore
from dotenv import load_dotenv
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

async def main() -> None:

       
    az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        model=os.getenv('COMPLETIONS_MODEL'),
        api_version=os.getenv('OPENAI_API_VERSION'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        temperature=0.4
    )
    
    local_executor = LocalCommandLineCodeExecutor(work_dir='c:\\Mark')

    m1 = MagenticOne(
        client=az_model_client,
        code_executor=local_executor
    )
    task = """
    I want you to read the contents of all files in the following folder and then summarize their contents.    
    folder: c:\\mark\\
    """
    result = await Console(m1.run_stream(task=task))
    print(result)
       
asyncio.run(main())
