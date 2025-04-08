import os
from typing import List, cast
import chainlit as cl
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from autogen_agentchat.teams import RoundRobinGroupChat
from dotenv import load_dotenv
import yaml

load_dotenv()

@cl.set_starters  # type: ignore
async def set_starts() -> List[cl.Starter]:
    return [
        cl.Starter(
            label="Greetings",
            message="Hello! What can you help me with today?",
        ),
        cl.Starter(
            label="Weather",
            message="Find the weather in New York City.",
        ),
    ]

@cl.step(type="tool")  # type: ignore
async def search_index(keywordQuery: str, naturalLanguageQuery: str, categories: List[str]) -> str:
    endpoint = os.environ["SEARCH_ENDPOINT"]
    index_name = os.environ["SEARCH_INDEX_NAME"]
    api_key = os.environ["SEARCH_API_QUERY_KEY"]
    
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(api_key))

    vector_queries = [  
    {  
        "kind": "text",  
        "text": "{naturalLanguageQuery}",  
        "fields": "vectorized_content",  
        "k": 5,  
        "threshold": {"kind": "vectorSimilarity", "value": 0.48}  
    }  
    ]  
    
    search_filter = " or ".join([f"search.ismatch('{category}', 'category')" for category in categories])

    search_results = search_client.search(  
        search_text=keywordQuery,  
        include_total_count=True,  
        filter=search_filter,
        query_type="semantic",  
        semantic_configuration_name="my-semantic-config",  
        query_caption="extractive",  
        query_answer="extractive",  
        query_answer_count=5,
        top=5,  
        search_mode="all",  
        select=["url", "chunk_title", "content"],  
        vector_queries=vector_queries  
    )  
    
    results = []

    for result in search_results:
        results.append(f"Title: {result['chunk_title']},, Chunk: {result['content']} URL: {result['url']}")

    return "\n".join(results)


@cl.on_chat_start  # type: ignore
async def start_chat() -> None:
    # Load model configuration and create the model client.
    with open("model_config.yaml", "r") as f:
        model_config = yaml.safe_load(f)
    model_client = ChatCompletionClient.load_component(model_config)

    # Create the assistant agent with the get_weather and search_index tools.
    assistant = AssistantAgent(
        name="assistant",
        tools=[search_index],
        model_client=model_client,
        system_message="""
        
        You are a helpful assistant that give architecture guidance.
        When requiring information you will only use search index data, you will use the search_index tool.
        you will need to specify the paraemters for the search tool which will be as follows:
        - keywordQuery: Build keywords from the user's question.
        - naturalLanguageQuery: Build a natural language question from the user's question. NOTE: you might be able to use it as is.
        - categories: The categories to filter the search results. The categories are:
        
        Select one or many categories from the list below as it pertains to the question. they are as follows:

            Infrastructure
            Architecture
            Security
            Networking
            Compliance
            Integration
            Data
            Operation
            Backup
            Licenses
            Logging
            Exception Handling
            AI and Machine Learning
            Analytics
            Compute
            Containers
            Developer Tools
            DevOps
            Hybrid Cloud
            Identity
            IoT
            Messaging
            Monitoring
            Storage
            Web
            Migration
            Virtual Desktop Infrastructure
            Resiliency
            Disaster Recovery
            Scaling
            Performance
            Miscellaneous

        """,
        model_client_stream=True,  # Enable model client streaming.
        reflect_on_tool_use=True,  # Reflect on tool use.
    )

    # Set the assistant agent in the user session.
    cl.user_session.set("prompt_history", "")  # type: ignore
    cl.user_session.set("agent", assistant)  # type: ignore


@cl.on_message  # type: ignore
async def chat(message: cl.Message) -> None:
    # Get the assistant agent from the user session.
    agent = cast(AssistantAgent, cl.user_session.get("agent"))  # type: ignore
    # Construct the response message.
    response = cl.Message(content="")
    async for msg in agent.on_messages_stream(
        messages=[TextMessage(content=message.content, source="user")],
        cancellation_token=CancellationToken(),
    ):
        if isinstance(msg, ModelClientStreamingChunkEvent):
            # Stream the model client response to the user.
            await response.stream_token(msg.content)
        elif isinstance(msg, Response):
            # Done streaming the model client response. Send the message.
            await response.send()