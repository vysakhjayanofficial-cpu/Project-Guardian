from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
from llm import llm
load_dotenv()
def image_to_data_url(image_path):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:image/jpeg;base64,{base64_image}"


# image_url = image_to_data_url("chest_xray.jpg")

image_process = RunnableLambda(lambda image_path: {"image_url": image_to_data_url(image_path["image_path"])})

def process_image(image_dict):
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "Analyze this medical image"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_dict["image_url"]
                }
            }
        ]
    )

    response = llm.invoke([message])
    return {"summary": response.content}

llm_out = RunnableLambda(lambda image_val: process_image(image_val))

image_chain = image_process | llm_out