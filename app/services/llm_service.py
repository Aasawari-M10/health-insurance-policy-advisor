import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


AZURE_OPENAI_BASE_URL = os.getenv(
    "AZURE_OPENAI_BASE_URL"
)

AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY"
)

CHAT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_CHAT_DEPLOYMENT"
)


if not AZURE_OPENAI_BASE_URL:
    raise ValueError(
        "AZURE_OPENAI_BASE_URL is missing."
    )

if not AZURE_OPENAI_API_KEY:
    raise ValueError(
        "AZURE_OPENAI_API_KEY is missing."
    )

if not CHAT_DEPLOYMENT:
    raise ValueError(
        "AZURE_OPENAI_CHAT_DEPLOYMENT is missing."
    )


client = OpenAI(
    base_url=AZURE_OPENAI_BASE_URL,
    api_key=AZURE_OPENAI_API_KEY,
)


def generate_answer(
    system_prompt: str,
    grounded_prompt: str,
) -> str:
    """
    Generate a grounded policy answer using
    the Microsoft Foundry chat deployment.
    """

    combined_input = (
        f"{system_prompt}\n\n"
        f"{grounded_prompt}"
    )

    response = client.responses.create(
        model=CHAT_DEPLOYMENT,
        input=combined_input,
    )

    answer = response.output_text

    if not answer:
        raise ValueError(
            "LLM returned an empty response."
        )

    return answer.strip()