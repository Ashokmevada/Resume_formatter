import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

MODEL_NAME = "gpt-5.6-sol"

response = client.responses.create(
    model=MODEL_NAME,
    input="Say hello and tell me what model you are."
)

print(response.output_text)