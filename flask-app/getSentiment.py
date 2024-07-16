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

# Use the multi-class sentiment model
tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = logits.argmax().item()
    label_map = {0: 'very negative', 1: 'negative', 2: 'neutral', 3: 'positive', 4: 'very positive'}
    return label_map[predicted_class_id]

# Split the text into chunks
def split_into_chunks(text, chunk_size=512):
    tokens = tokenizer.tokenize(text)
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    return [tokenizer.convert_tokens_to_string(chunk) for chunk in chunks]

# Analyze sentiment for each chunk and aggregate the results
def analyze_sentiment(text):
    chunks = split_into_chunks(text)
    sentiments = [get_sentiment(chunk) for chunk in chunks]
    return sentiments

def aggregate_sentiments(sentiments):
    sentiment_counts = Counter(sentiments)
    most_common_sentiment = sentiment_counts.most_common(1)[0][0]
    return most_common_sentiment

# Fetch articles from the database
cursor.execute("SELECT id, content FROM articles")
articles = cursor.fetchall()

for article in articles:
    article_id, content = article
    sentiments = analyze_sentiment(content)
    overall_sentiment = aggregate_sentiments(sentiments)
    
    # Update the article with the sentiment
    cursor.execute("UPDATE articles SET sentiment = %s WHERE id = %s", (overall_sentiment, article_id))
    conn.commit()

print("Sentiment analysis complete and database updated.")

# Close the database connection
cursor.close()
conn.close()
