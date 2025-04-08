import asyncio
import sys
import os
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from colorama import Fore
from dotenv import load_dotenv

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
    
    # surfer = MultimodalWebSurfer(
    #     name="WebSurfer",
    #     headless=False,
    #     model_client=az_model_client,
    #     use_ocr=True
    # )

    coder = MagenticOneCoderAgent(
        name="MermaidScriptCoder",
        model_client=az_model_client,
    )

    max_msg_termination = MaxMessageTermination(max_messages=2)
    text_termination = TextMentionTermination("TERMINATE")
    combined_termination = max_msg_termination | text_termination
    
    
      # Define a team
    team = MagenticOneGroupChat([coder], model_client=az_model_client,termination_condition=combined_termination)
   
    await Console(team.run_stream(task="""can you re-create this architecture to better 
                                         understand the content located here: 
                                         https://learn.microsoft.com/en-us/azure/architecture/solution-ideas/https://learn.microsoft.com/en-us/azure/architecture/example-scenario/mainframe/rehost-ims-raincode-imsql.
                                         Output a detailed description of the article as well as a mermaid script flow diagram using 
                                         compliant mermaid markdown syntax. The recreated diagram and description will not 
                                         infringe on copyrights or protected material. we are simply creating a better medium 
                                         for understanding the content.
                                         stop when the diagram is at least 80% similar to the original article.
                                         """))
    
asyncio.run(main())