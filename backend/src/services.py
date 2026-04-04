from transformers import pipeline
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

LOCAL_VLM_MODEL = "HuggingFaceTB/SmolVLM-500M-Instruct"

pipe = pipeline(
    "image-text-to-text",
    model=LOCAL_VLM_MODEL,
    dtype=torch.float32,
    device_map="cpu",
    trust_remote_code=True,
)


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

    try:
        output = pipe(text=messages, max_new_tokens=200)
        print(f"Raw pipeline output: {output[0]["generated_text"]}")
        response = output[0]["generated_text"][-1]["content"]
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise
    
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

    try:
        client = InferenceClient(token=HF_TOKEN, provider="featherless-ai")
        completion = client.chat.completions.create(
            model="google/gemma-3-27b-it",
            messages=messages,
            max_tokens=500
        )
        response = completion.choices[0].message.content
    except Exception as e:
        print(f"Inference API error: {e}")
        raise

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
    
