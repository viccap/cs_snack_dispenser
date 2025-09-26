from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

print("running...")


def describe_selfie(selfie_path: Optional[Path]) -> str:

    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    print("imported everything...")

    #'qwen-3-235b-a22b-thinking-2507'
    #https://docs.hpc.gwdg.de/services/chat-ai/models/index.html#meta-llama-33-70b-instruct

    api_key = os.getenv("LLM_API_KEY") # Replace with your API key
    print("got api key...: ", api_key)
    base_url = os.getenv("LLM_BASE_URL", "https://chat-ai.academiccloud.de/v1")
    model ='openai-gpt-oss-120b'#"meta-llama-3.3-70b-instruct" #"gemma-3-27b-it" # Choose any available model

    #meta-llama/Llama-3.3-70B-Instruct
    client = OpenAI(api_key = api_key, base_url = base_url)

    print("prompting...")
    chat_completion = client.chat.completions.create(messages=[{"role":"system","content":"you are health and you represent this value with everything you do. nothing is more important to you than health."},
                                                            {"role":"user","content":"hey do you think it is okay for me to eat a piece of cake for my bithday?"}],
                                                            model=model)

    print(chat_completion) 

    return (
        "LLM description pending: run describe_selfie once LLM credentials are configured. "
        f"Payload targets {base_url} with model gpt-4o-mini."
    )
