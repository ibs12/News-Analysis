# Use a pipeline as a high-level helper
from transformers import pipeline
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"


messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe = pipeline("text-generation", model="meta-llama/Llama-2-7b-chat-hf", device=0)
pipe(messages)