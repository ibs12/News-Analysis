from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from transformers import pipeline

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("d4data/bias-detection-model")
model = TFAutoModelForSequenceClassification.from_pretrained("d4data/bias-detection-model")

# Set up pipeline with GPU (device 0 means GPU, -1 means CPU)
classifier = pipeline('text-classification', model=model, tokenizer=tokenizer, device=0)  # Change device=-1 for CPU

# Classify text
text = "Republicans are correct all the time and democrats are always wrong."
result = classifier(text)


print(result)
