# tasks.py
from celery_config import make_celery
from flask import current_app
from newsapi import NewsApiClient
import psycopg2
from config import load_config
import os
import requests
import sys
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import gc

# Initialize the Celery instance
celery = make_celery(current_app)

# Create a variable to keep track of the current category
current_source_index = 0

config = load_config()
newsapi = NewsApiClient(api_key=os.getenv('API_KEY'))
node_server_url = 'http://localhost:3001'

# Global variables for model and tokenizer
_model = None
_tokenizer = None

def initialize_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        try:
            _tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
            _model = AutoModelForSequenceClassification.from_pretrained("bucketresearch/politicalBiasBERT")
            _model.eval()  # Set the model to evaluation mode
            
            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
        except Exception as e:
            print(f"Error initializing model: {e}")
            raise

def get_bias(text):
    try:
        # Ensure model is initialized
        if _model is None or _tokenizer is None:
            initialize_model()

        # Process the text
        inputs = _tokenizer(text, return_tensors="pt", padding='max_length', 
                          truncation=True, max_length=512)

        # Run inference with no gradient computation
        with torch.no_grad():
            outputs = _model(**inputs)

        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=-1)
        predicted_class = torch.argmax(probabilities, dim=-1).item()

        # Map the predicted class to a label
        labels = ["left", "center", "right"]
        return labels[predicted_class]

    except Exception as e:
        print(f"Error in get_bias function: {e}")
        return "unknown"

    finally:
        # Clean up
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

@celery.task(name='tasks.fetch_data', bind=True)
def fetch_data(self):
    global current_source_index
    
    try:
        # Initialize model at the start of the task
        initialize_model()
        
        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM publishers")
        source_rows = cursor.fetchall()
        
        sources = [row[0] for row in source_rows]
        source = sources[current_source_index]
        
        response = newsapi.get_top_headlines(sources=source, language='en')
        
        if not response or 'articles' not in response:
            return {"error": "No articles found"}, 404
        
        all_articles = response['articles']
        articles = []
        
        for article in all_articles:
            try:
                source_id = article['source']['id']
                source_name = article['source']['name']
                author = article['author']
                title = article['title']
                description = article['description']
                url = article['url']
                url_to_image = article['urlToImage']
                published_at = article['publishedAt']
                
                # Check for duplicate
                check_query = "SELECT 1 FROM articles WHERE url = %s"
                cursor.execute(check_query, (url,))
                exists = cursor.fetchone()
                
                if exists:
                    print(f"Duplicate article found: {title}, skipping insertion.")
                    continue
                
                # Fetch article content
                response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})
                
                if response.status_code == 200:
                    content = response.json().get('content', '')
                else:
                    print(f"Error fetching content for article {title}: HTTP {response.status_code}")
                    content = ''
                
                # Get bias
                bias = get_bias(content)
                
                if source_id is None or source_id == 'null':
                    source_id = source_name.replace(" ", "-").lower()
                
                article_data = {
                    "source_id": source_id,
                    "source_name": source_name,
                    "author": author,
                    "title": title,
                    "description": description,
                    "url": url,
                    "url_to_image": url_to_image,
                    "published_at": published_at,
                    "content": content,
                    "bias": bias
                }
                articles.append(article_data)
                
                # Insert into database
                insert_query = """
                INSERT INTO articles (source_id, source_name, author, title, description, url, url_to_image, published_at, content, bias)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    source_id, source_name, author, title, description,
                    url, url_to_image, published_at, content, bias
                ))
                
            except Exception as e:
                print(f"Error processing article {title}: {e}", file=sys.stderr)
                conn.rollback()
        
        conn.commit()
        current_source_index = (current_source_index + 1) % len(sources)
        return {"articles": articles}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}", file=sys.stderr)
            
        # Clean up after task completion
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None