from flask import Flask, jsonify, request
import psycopg2
from config import load_config
import requests
import subprocess
from newsapi import NewsApiClient
import sys
from newspaper import Article
from dotenv import load_dotenv
import os




app = Flask(__name__)
from flask_cors import CORS
CORS(app)
load_dotenv()

# Load config
config = load_config()

newsapi = NewsApiClient(api_key= os.getenv('API_KEY'))

# Define the base URL of your Node.js server
node_server_url = 'http://localhost:3001'

articles = []

# Establish database connection
def get_db_connection():
    conn = psycopg2.connect(**config)
    return conn


from flask import Flask, request, jsonify
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

@app.route('/fetch-articles', methods=['GET'])
def fetch_articles():
    search_term = request.args.get('search_term')

    if not search_term:
        return jsonify({"error": "Search term is required"}), 400

    try:
        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # Fetch articles from the News API
        all_articles = newsapi.get_everything(q=search_term, sort_by='relevancy')
        if not all_articles or 'articles' not in all_articles:
            return jsonify({"error": "No articles found"}), 404

        articles = []
        for article in all_articles['articles']:
            try:
                source_id = article['source']['id']
                source_name = article['source']['name']
                author = article['author']
                title = article['title']
                description = article['description']
                url = article['url']
                url_to_image = article['urlToImage']
                published_at = article['publishedAt']
                
                response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})

                if response.status_code == 200:
                    content = response.json().get('content', '')
                else:
                    print(f"Error fetching content for article {article['title']}: HTTP {response.status_code}")
                    content = ''  # Fallback to empty content

                    
                if source_id is None or 'null':
                    source_id = source_name.replace(" ", "-").lower()   
                    


                # Prepare the article data to return to the frontend
                article_data = {
                    "source_id": source_id,
                    "source_name": source_name,
                    "author": author,
                    "title": title,
                    "description": description,
                    "url": url,
                    "url_to_image": url_to_image,
                    "published_at": published_at,
                    "content": content

                }
                articles.append(article_data)
                


                # Insert the article into the database
                insert_query = """
                INSERT INTO articles (source_id, source_name, author, title, description, url, url_to_image, published_at, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    source_id,
                    source_name,
                    author,
                    title,
                    description,
                    url,
                    url_to_image,
                    published_at,
                    content
                ))

            except Exception as e:
                print(f"Error processing article {title}: {e}", file=sys.stderr)
                conn.rollback()  # Rollback the transaction on error

        # Commit the transaction to save all articles in the database
        conn.commit()

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


# from getBias import getBias 
# @app.route('/scrape-articles', methods=['GET'])

# def scrape_articles():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         for article in articles:
#             url = article['url']
            
#             response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})

#             if response.status_code == 200:
#                 content = response.json().get('content', '')
#             else:
#                 print(f"Error fetching content for article {article['title']}: HTTP {response.status_code}")
#                 content = ''  # Fallback to empty content
                
#             article_data = {

#                     "content": content
#                 }
#             article.append(article_data)
            
#             # Insert the article into the database
#             update_query = """
#             UPDATE articles
#             SET content = %s
#             WHERE url = %s
#             """
#             cursor.execute(update_query, (
#                 content,  # The new content
#                 url       # The URL of the article to update
#             ))

#             # Commit the transaction to save changes
#             conn.commit()

#             return jsonify({"message": "Article content updated successfully"}), 200

#     except Exception as e:
#         conn.rollback()  # Rollback the transaction on error
#         return jsonify({"error": str(e)}), 500

#     finally:
#         try:
#             if cursor:
#                 cursor.close()
#             if conn:
#                 conn.close()
#         except Exception as e:
#             print(f"Error closing database connection: {e}", file=sys.stderr)   
        
        
        




if __name__ == "__main__":
    app.run(port=5000, debug=True)

