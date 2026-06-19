# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer

# import os
# os.environ["TOKENIZERS_PARALLELISM"] = "false"


# # Load model and tokenizer
# model_name = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
# model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")
# tokenizer = AutoTokenizer.from_pretrained(model_name)

# # List of articles
# articles = [
#     """Tesla has announced a new version of its Model 3, which comes with a longer range and enhanced autopilot features. 
#     Elon Musk, the CEO, mentioned that this update is part of the company's goal to make autonomous vehicles mainstream by 2030.""",
    
#     """Apple just released its latest iPhone 15, featuring a 48-megapixel camera, faster A17 chip, and a new dynamic island design. 
#     This iPhone is set to revolutionize mobile photography with its advanced camera system, which supports enhanced low-light performance 
#     and a wider color range.""",
    
#     """NASA has successfully launched its new Mars Rover, Perseverance, as part of its ongoing mission to explore the Red Planet. 
#     The rover's primary objective is to search for signs of ancient life and collect soil samples for future study.""",
    
#     """The Federal Reserve hddas raised interest rates again, this time by 0.25%, in an effort to combat rising inflation in the United States.
#     Analysts believe that this move could help cool off the economy, but some fear it may also lead to slower job growth and a potential recession."""
# ]

# # Process each article
# # Ensure tokens are set and moved to the correct device
# pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
# eos_token_id = tokenizer.eos_token_id

# # Process each article
# for article in articles:
#     prompt = f"Summarize the key current event from this article: {article}"
#     messages = [{"role": "user", "content": prompt}]
    
#     # Tokenize and move inputs to MPS
#     tokenized_message = tokenizer.apply_chat_template(
#         messages,
#         tokenize=True,
#         add_generation_prompt=True,
#         return_tensors="pt",
#         return_dict=True
#     )
#     input_ids = tokenized_message['input_ids'].to("mps")
#     attention_mask = tokenized_message['attention_mask'].to("mps")
    
#     # Generate response with padding and EOS tokens correctly set
#     response_token_ids = model.generate(
#         input_ids,
#         attention_mask=attention_mask,
#         max_new_tokens=500,
#         pad_token_id=pad_token_id,
#         eos_token_id=eos_token_id
#     )
    
#     # Decode and display generated text
#     generated_tokens = response_token_ids[:, len(input_ids[0]):]
#     generated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
#     print(f"Article summary:\n{generated_text}\n")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)

prompt = "How many r in strawberry?"
messages = [{"role": "user", "content": prompt}]

tokenized_message = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True)
response_token_ids = model.generate(tokenized_message['input_ids'].to('mps'),attention_mask=tokenized_message['attention_mask'].to('mps'),  max_new_tokens=4096, pad_token_id = tokenizer.eos_token_id)
generated_tokens =response_token_ids[:, len(tokenized_message['input_ids'][0]):]
generated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
print(generated_text)
