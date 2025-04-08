
import os

from dotenv import load_dotenv
from openai import OpenAI, responses
from PyPDF2 import PdfReader
load_dotenv(override=True)
openai_api_key=os.getenv("OPENAI_API_KEY")

import gradio as gr
file="test.pdf"
if openai_api_key:
    print(f"open AI API key is present and begins with {openai_api_key[:8]}")

openai=OpenAI()
MODEL = 'gpt-4o-mini'

def extract_text_pdf(file):
    if file is not None:
        pdf_reader=PdfReader(file)
        text=""
        for page in pdf_reader.pages:
            text+= page.extract_text()
        return text


pdf_data= extract_text_pdf(file)
system_message ="You are a helful assistant that can process the below data in order to provide useful and interactive response:\n"
system_message +=pdf_data
# system_message ="You are a helpful assistant in a clothes store. You should try to gently encourage the customer to try items that are on sale. Hats are 60% off, and most other items are 50% off. For example, if the customer says 'I'm looking to buy a hat', you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales event. ' Encourage the customer to buy hats if they are unsure what to get."

def chat(message, history):
    # message=[
    #     {"role":"system","content":system_message}
    # ] + history + [
    #     {"role":"user", "content":message}
    # ]
    relevant_system_message=system_message
    if 'belt' in message:
        relevant_system_message += " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."

    messages = [{"role": "system", "content": relevant_system_message}] + history + [{"role": "user", "content": message}]

    print("history: " ,history)
    print("message: " ,messages)

    stream=openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True
    )

    response=""
    for chunk in stream:
        response +=chunk.choices[0].delta.content or ''
        yield  response

system_message += "\nIf the customer asks for shoes, you should respond that shoes are not on sale today, \
but remind the customer to look at hats!"

gr.ChatInterface(fn=chat, type="messages").launch(inbrowser=True)