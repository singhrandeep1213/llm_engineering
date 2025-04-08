import json
import os

import boto3
from botocore.exceptions import ClientError
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI, responses

load_dotenv(override=True)
openai_api_key=os.getenv("OPENAI_API_KEY")

import gradio as gr

if openai_api_key:
    print(f"open AI API key is present and begins with {openai_api_key[:8]}")

openai=OpenAI()

# A generic system message - no more snarky adversarial AIs!
system_message = "You are a helpful assistant that responds in markdown"


# # Let's wrap a call to GPT-4o-mini in a simple function
# def message_gpt(prompt):
#     messages=[
#         {
#             "role":"system","content":system_message,
#             "role":"user","content":prompt
#         }
#     ]
#     completion=openai.chat.completions.create(
#         model='gpt-4o-mini',
#         messages=messages,
#     )
#     return completion.choices[0].message.content
#
# # This can reveal the "training cut off", or the most recent date in the training data
# print(message_gpt("what day is it today?"))
#
# # here's a simple function
# def shout(text):
#     print(f"Shout has been called with input text: {text}")
#     return text.upper()

#(shout("hello"))

# The simplicty of gradio. This might appear in "light mode" - I'll show you how to make this in dark mode later.
#gr.Interface(fn=shout, inputs="textbox", outputs="textbox").launch()

# Adding share=True means that it can be accessed publically
# A more permanent hosting is available using a platform called Spaces from HuggingFace, which we will touch on next week
# NOTE: Some Anti-virus software and Corporate Firewalls might not like you using share=True. If you're at work on on a work network, I suggest skip this test.
#gr.Interface(fn=shout, inputs="textbox", outputs="textbox", flagging_mode="never").launch(share=True)

# Adding inbrowser=True opens up a new browser window automatically
#gr.Interface(fn=shout, inputs="textbox", outputs="textbox", flagging_mode="never").launch(inbrowser=True)


# view= gr.Interface(
#     fn=message_gpt,
#     inputs=[gr.Textbox(label="Your message", lines=6)],
#     outputs=[gr.Textbox(label="Response:", lines=8)],
#     flagging_mode="never"
# )

#view.launch(inbrowser=True)

# Let's create a call that streams back results
# If you'd like a refresher on Generators (the "yield" keyword),
# Please take a look at the Intermediate Python notebook in week1 folder.

def stream_gpt(prompt):
    messages=[
        {"role": "system","content":system_message},
        {"role": "user","content":prompt}
    ]
    stream=openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    result=""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(prompt):
    # Create a Bedrock Runtime client in the AWS Region you want to use.
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Set the model ID, e.g., Claude 3 Haiku.
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    # Format the request payload using the model's native structure.

    conversation= [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        }
    ]

    try:
        # Invoke the model with the streaming response.
        streaming_response = client.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "temperature": 0.5,
                "system": system_message,
                "messages":conversation
            })
        )
        result = ""
        # Extract and print the response text in real-time.
        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk["type"] == "content_block_delta":
                result += chunk["delta"].get("text", "") or ""
                yield  result

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")


class Website:
    url:str
    title:str
    text: str
    def __init__(self, url):
        self.url=url
        response   =requests.get(url)
        self.body=response.content
        soup=BeautifulSoup(self.body,'html.parser')
        self.title=soup.title.string if soup.title  else "No title found"
        for irrelevant in soup.body(["script","style","img","input"]):
            irrelevant.decompose()
        self.text=soup.get_text(separator="\n", strip=True)

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}"

# With massive thanks to Bill G. who noticed that a prior version of this had a bug! Now fixed.

system_message = "You are an assistant that analyzes the contents of a company website landing page and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown."

def stream_brochure(company_name, url, model):
    prompt=f"please generate a company brochure for {company_name}. Here is their landing page:\n"
    prompt += Website(url).get_contents()
    if model=="GPT":
        result=stream_gpt(prompt)
    elif model=="Claude":
        result=stream_claude(prompt)
    else:
        raise ValueError("Unknown Model")
    yield from result

view= gr.Interface(
    fn=stream_brochure,
    inputs=[
        gr.Textbox(label="Company name:"),
        gr.Textbox(label="Landing page URL incluin http:// or https://"),
        gr.Dropdown(["GPT","Claude"], label="Select Model")],
    outputs=[gr.Markdown(label="Brochure")],
    flagging_mode="never"
)

view.launch(inbrowser=True)