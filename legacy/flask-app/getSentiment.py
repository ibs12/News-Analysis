from newsapi import NewsApiClient
import psycopg2
import sys
import requests
from config import load_config
import argparse

# Libraries for sentiment analysis
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from collections import Counter

# Load configuration and connect to the database
config = load_config()
conn = psycopg2.connect(**config)
cursor = conn.cursor()




from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
import numpy as np
from scipy.special import softmax
import warnings

def analyze_sentiment(text):
    # Load the model, tokenizer, and config
    MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    config = AutoConfig.from_pretrained(MODEL)
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*weights of the model checkpoint.*")
        model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    # Tokenize the input text with truncation and padding
    encoded_input = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    output = model(**encoded_input)

    # Apply softmax to get probabilities for each class (Negative, Neutral, Positive)
    scores = output.logits[0].detach().numpy()  # Use logits attribute to access output
    scores = softmax(scores)

    # Sort by highest probability and return the top sentiment and its score
    ranking = np.argsort(scores)[::-1]
    top_label = config.id2label[ranking[0]]
    top_score = scores[ranking[0]]

    return {"label": top_label, "score": np.round(float(top_score), 4)}

