import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
)


if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT is missing.")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY is missing.")

if not EMBEDDING_DEPLOYMENT:
    raise ValueError(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT is missing."
    )


base_url = (
    AZURE_OPENAI_ENDPOINT.rstrip("/")
    + "/openai/v1/"
)


client = OpenAI(
    base_url=base_url,
    api_key=AZURE_OPENAI_API_KEY,
)


def generate_embedding(text: str) -> list[float]:
   cleaned_text = text.strip()
   if not cleaned_text:
       raise ValueError("Embedding text cannot be empty.")
   response = client.embeddings.create(
       model=EMBEDDING_DEPLOYMENT,
       input=cleaned_text
   )
   return response.data[0].embedding