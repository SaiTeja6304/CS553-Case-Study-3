from transformers import pipeline, AutoConfig
from huggingface_hub import InferenceClient
import io
import base64
from PIL import Image
import torch
import os
from dotenv import load_dotenv
from fastapi import UploadFile 
from .db import create_connection, create_table, insert_log, close_connection

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

conn, cursor = create_connection()
create_table(conn, cursor)

async def generate_response_local(input_img: UploadFile, query: str, using_local_model: bool, chat_history: str):
   
    #streamlit input to PIL image
    img = Image.open(input_img.file).convert("RGB")

    response = ""

    print("LOCAL")

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": f"Here is the conversation so far: {chat_history}. Continue the conversation naturally. \n Provide responses without using special formatting, while still being descriptive."}]
        },
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": f"Answer this question: {query}"}
            ]
        }
    ]

    pipe = pipeline(
        "image-text-to-text",
        model="HuggingFaceTB/SmolVLM-500M-Instruct",
        torch_dtype=torch.float32,
        device_map="cpu"
    )

    output = pipe(messages, max_new_tokens=200)

    response = output[0]["generated_text"][-1]["content"]
    
    try:
        insert_log(conn, 
        cursor, 
        "hf-local" if using_local_model else "hf-inference", 
        query, response, chat_history)
        db_insert = "Successfully inserted log"
    except Exception as e:
        db_insert = f"Failed to insert log: {str(e)}"

    result = {
        "response": response,
        "db_insert": db_insert
    }

    return result


async def generate_response_api(input_img: UploadFile, query: str, using_local_model: bool, chat_history: str):

    #streamlit input to PIL image
    img = Image.open(input_img.file).convert("RGB")

    #Changing the PIL image to bytes so we can pass it into the message
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_as_bytes = base64.b64encode(buffer.getvalue()).decode('utf-8')

    response = ""

    print("API")
    
    messages=[
        {
            "role": "system", 
            "content": [{"type": "text", "text": f"Here is the conversation so far: {chat_history}. Continue the conversation naturally. \n Provide responses without using special formatting, while still being descriptive."}]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_as_bytes}"}}
            ],
        }
    ]
    client = InferenceClient(token=HF_TOKEN)

    completion = client.chat.completions.create(
        model="google/gemma-3-27b-it:featherless-ai",
        messages=messages,
        max_tokens=500
    )
    
    response = completion.choices[0].message.content

    try:
        insert_log(conn, 
        cursor, 
        "hf-local" if using_local_model else "hf-inference", 
        query, response, chat_history)
        db_insert = "Successfully inserted log"
    except Exception as e:
        db_insert = f"Failed to insert log: {str(e)}"

    result = {
        "response": response,
        "db_insert": db_insert
    }

    return result
    
