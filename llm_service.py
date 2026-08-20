from dotenv import load_dotenv
from openai import OpenAI
import base64
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def extract_image_text(file):

    image_bytes = file.read()

    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract all useful information from this image.

Include:
- visible text
- diagrams
- labels
- charts
- tables
- important details

Answer in pointwise format.
Start each point with a new line and a hyphen.

Return only the extracted information.
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                            f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content


def ask_llm(prompt):

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content