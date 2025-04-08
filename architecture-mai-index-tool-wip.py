import asyncio
import os
from typing import AsyncGenerator
from autogen_core.models import UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from dotenv import load_dotenv
import chainlit as cl

load_dotenv()

async def azure_chat(message: str) -> AsyncGenerator[str, None]:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    model_name = os.environ["COMPLETIONS_MODEL"]

    #print(f"Using model: {model_name}")  # Debugging
    #print(f"Input message to Azure Chat: {message}")  # Debugging

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(os.environ["AZURE_OPENAI_API_KEY"])
    )

    response = client.complete(
        stream=True,
        messages=[
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content=message)  # Use the actual user input
        ],
        max_tokens=800,
        temperature=1.0,
        top_p=1.0,
        model=model_name
    )
    
    for update in response:
        print(f"Update received: {update}")  # Debugging the full update object
        if update.choices:
            result = update.choices[0].delta.content
            if result:  # Only yield non-None content
                #print(f"Chunk content: {result}")  # Debugging
                yield result

    client.close()
    

@cl.on_message
async def on_message(message: cl.Message):
    """Chainlit handler for incoming messages."""
    message_content = message.content

    # Create a Chainlit message object
    chainlit_message = cl.Message(content="")
    await chainlit_message.send()  # Send an empty message to initialize streaming

    # Stream the response from the async generator
    async for chunk in azure_chat(message_content):
        if chunk:  # Only send non-empty chunks
            await chainlit_message.stream_token(chunk)

    # Finalize the message (optional, but ensures the message is marked as complete)
    await chainlit_message.update()
