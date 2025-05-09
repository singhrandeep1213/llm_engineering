import base64
from io import BytesIO
from PIL import Image

import json
import os


from dotenv import load_dotenv
from openai import OpenAI



load_dotenv(override=True)
openai_api_key=os.getenv("OPENAI_API_KEY")

import gradio as gr

if openai_api_key:
    print(f"open AI API key is present and begins with {openai_api_key[:8]}")

openai=OpenAI()
MODEL = 'gpt-4o-mini'

system_message = "You are a helpful assistant for an Airline called FlightAI. "
system_message += "Give short, courteous answers, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

# This function looks rather simpler than the one from my video, because we're taking advantage of the latest Gradio updates
#
# def chat(message, history):
#     messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
#     response = openai.chat.completions.create(model=MODEL, messages=messages)
#     return response.choices[0].message.content

#gr.ChatInterface(fn=chat, type="messages").launch(inbrowser=True)


ticket_prices={"london":"$375", "paris": "$549", "tokyo":"$234","berlin":"$1234"}

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city=destination_city.lower()
    return ticket_prices.get(city,"unknown")

print(get_ticket_price("berlin"))

# There's a particular dictionary structure that's required to describe our function:

price_function={
    "name":"get_ticket_price",
    "description":"Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters":{
        "type":"object",
        "properties":{
            "destination_city":{
                "type":"string",
                "description":"The city that customer wants to travel to",
            },
        },
        "required":["destination_city"],
        "additionalProperties":False
    }
}

# And this is included in a list of tools:
tools=[{"type":"function","function":price_function}]



def handle_tool_call(message):
    tool_call=message.tool_calls[0]
    arguments=json.loads(tool_call.function.arguments)
    city= arguments.get('destination_city')
    price=get_ticket_price(city)
    response={
        "role":"tool",
        "content":json.dumps({"destination_city":city, "price":price}),
        "tool_call_id":tool_call.id
    }
    print("response here:")
    print(response)
    return response,city


#gr.ChatInterface(fn=chat, type="messages").launch(inbrowser=True)

def artist(city):
    image_response= openai.images.generate(
        model="dall-e-3",
        prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    image_base64=image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))


def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    image = None

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, city = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        image = artist(city)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    # Comment out or delete the next line if you'd rather skip Audio for now..
    # talker(reply)

    return history, image

# More involved Gradio code as we're not using the preset Chat interface!
# Passing in inbrowser=True in the last line will cause a Gradio window to pop up immediately.

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.Button("Clear")

    def do_entry(message,history):
        history += [{"role":"user", "content":message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)


ui.launch(inbrowser=True)