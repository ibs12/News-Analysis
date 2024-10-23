# app.py
from flask import Flask, jsonify, request
import psycopg2
from rich import _console
from config import load_config
from newsapi import NewsApiClient
from dotenv import load_dotenv
import os
from datetime import datetime
from flask_cors import CORS
from celery_config import make_celery
import sys
import json 
# Initialize Flask app
app = Flask(__name__)
CORS(app)
load_dotenv()

# Load config
config = load_config()
newsapi = NewsApiClient(api_key=os.getenv('API_KEY'))

# Initialize Celery
celery = make_celery(app)
print(celery.tasks)  # This should show registered tasks, including 'tasks.fetch_data'


# Define the base URL of your Node.js server
node_server_url = 'http://localhost:3001'
articles = []

def get_db_connection():
    conn = psycopg2.connect(**config)
    return conn

@app.route('/fetch-articles', methods=['GET'])
def trigger_fetch_articles():
    from tasks import fetch_data  # Import here to avoid circular import
    fetch_data.delay()
    return "Fetch articles task initiated!", 200

@app.route('/test-celery')
def test_celery():
    from tasks import test_task  # Import here to avoid circular import
    test_task.delay()  # Execute task asynchronously
    return "Test task initiated!", 200




from getSentiment import analyze_sentiment 

@app.route('/get-sentiment', methods=['POST'])
def get_sentiment():
    data = request.json
    content = data.get('content')

    # Ensure the content is provided
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    # Call the function from getSentiment.py
    sentiment = analyze_sentiment(content)
    
    

    return jsonify(sentiment)

@app.route('/search-articles', methods=['GET'])
def fetch_articles():
    search_term = request.args.get('search_term')

    if not search_term:
        return jsonify({"error": "Search term is required"}), 400

    try:
        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # Prepare the search term for full-text search
        search_query = """
        SELECT source_id, source_name, author, title, description, url, url_to_image, published_at, content,
               ts_rank_cd(
                   setweight(to_tsvector(coalesce(title, '')), 'A') || 
                   setweight(to_tsvector(coalesce(description, '')), 'B') || 
                   setweight(to_tsvector(coalesce(content, '')), 'C'), 
                   to_tsquery(%s)
               ) AS rank
        FROM articles
        WHERE to_tsvector(coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(content, ''))
              @@ to_tsquery(%s)
        ORDER BY rank DESC, published_at DESC
        LIMIT 50
        """
        
        # Convert the search term into a tsquery format (handle spaces for AND logic)
        search_term_tsquery = ' & '.join(search_term.split())
        
        # Execute the query with the search term
        cursor.execute(search_query, (search_term_tsquery, search_term_tsquery))

        # Fetch all matching articles
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"error": "No articles found"}), 404

        # Convert the database rows into a list of articles in JSON format
        articles = []
        for row in rows:
            article_data = {
                "source_id": row[0],
                "source_name": row[1],
                "author": row[2],
                "title": row[3],
                "description": row[4],
                "url": row[5],
                "url_to_image": row[6],
                "published_at": row[7],
                "content": row[8]
            }
            articles.append(article_data)
        
        # Return the full list of articles
        return jsonify({"articles": articles}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}", file=sys.stderr)



if __name__ == "__main__":
    app.run(port=5000, debug=True)



