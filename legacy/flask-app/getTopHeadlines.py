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

# Load config
config = load_config()
newsapi = NewsApiClient(api_key=os.getenv('API_KEY'))

# Initialize global variables
_model = None
_tokenizer = None

# Define the base URL of your Node.js server
node_server_url = 'http://localhost:3001'

# Function to initialize model
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

# Function to get bias
def get_bias(text):
    try:
        if _model is None or _tokenizer is None:
            initialize_model()

        inputs = _tokenizer(text, return_tensors="pt", padding='max_length', 
                          truncation=True, max_length=512)

        with torch.no_grad():
            outputs = _model(**inputs)

        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=-1)
        predicted_class = torch.argmax(probabilities, dim=-1).item()

        labels = ["left", "center", "right"]
        return labels[predicted_class]

    except Exception as e:
        print(f"Error in get_bias function: {e}")
        return "unknown"

    finally:
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

def fetch_data():
    cursor = None  # Initialize cursor to None
    conn = None  # Initialize connection to None
    
    try:
        # Initialize model
        initialize_model()

        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        

        sources_response = newsapi.get_sources(country='us')

        # Filter sources to get those with the category 'general'
        general_sources = [source['id'] for source in sources_response['sources'] if source['category'] == 'general']

        # Fetch top headlines from the filtered sources
        response = newsapi.get_top_headlines(
            sources=','.join(general_sources),  # Combine the general sources into a single string
            language='en')


        if not response or 'articles' not in response:
            print({"error": "No articles found"}, 404)
            return

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
                check_query = "SELECT 1 FROM top_headlines_us WHERE url = %s"
                cursor.execute(check_query, (url,))
                exists = cursor.fetchone()
                
                if exists:
                    print(f"Duplicate article found: {title}, skipping insertion.")
                    continue
                
                try:
                    response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url}, timeout=5)
                    if response.status_code == 200:
                        content = response.json().get('content', '')
                    else:
                        print(f"Error fetching content for article {title}: HTTP {response.status_code}")
                        content = ''
                except requests.exceptions.RequestException as e:
                    print(f"Request failed: {e}")
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
                INSERT INTO top_headlines_us (source_id, source_name, author, title, description, url, url_to_image, published_at, content, bias)
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
        print({"articles": articles}, 200)
        
    except Exception as e:
        print({"error": str(e)}, 500)
        
    finally:
        try:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}", file=sys.stderr)
            
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

# To call the fetch_data function, use:
if __name__ == '__main__':
    fetch_data()  # This will run the fetch_data function when the script is executed
