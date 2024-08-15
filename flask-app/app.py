from flask import Flask, jsonify, request
import psycopg2
from config import load_config
import requests
import subprocess
from newsapi import NewsApiClient


app = Flask(__name__)
from flask_cors import CORS
CORS(app)

# Load config
config = load_config()

newsapi = NewsApiClient(api_key='fee8e0fcf150466ab960b6b5043be353')

# Define the base URL of your Node.js server
node_server_url = 'http://localhost:3001'

# Establish database connection
def get_db_connection():
    conn = psycopg2.connect(**config)
    return conn

# @app.route('/scrape', methods=['POST'])
# def scrape_and_update():
#     # Example endpoint to trigger scraping from Node.js server
#     url = 'http://localhost:3001/scrape-articles'  # Adjust URL as per your Node.js server setup

#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             return "Scraping and updating started successfully."
#         else:
#             return "Failed to start scraping and updating."
#     except Exception as e:
#         return f"Error: {str(e)}"
    
    
# @app.route('/api/search', methods=['POST'])
# def search_articles():
#     search_term = request.json.get('searchTerm')
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     query = """
#     SELECT * FROM articles
#     WHERE title ILIKE %s OR description ILIKE %s OR content ILIKE %s
#     """
#     cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
#     articles = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     articles_list = []
#     for article in articles:
#         articles_list.append({
#             'source_id': article[0],
#             'source_name': article[1],
#             'author': article[2],
#             'title': article[3],
#             'description': article[4],
#             'url': article[5],
#             'url_to_image': article[6],
#             'published_at': article[7],
#             'content': article[8]
#         })

#     return jsonify(articles_list)


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
        all_articles = newsapi.get_everything(q=search_term, language='en')
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

                # Fetch content from Node.js server
                response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})

                if response.status_code == 200:
                    content = response.json().get('content', '')
                else:
                    print(f"Error fetching content for article {title}: HTTP {response.status_code}")
                    content = ''  # Fallback to empty content

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





# @app.route('/api/articles', methods=['GET'])
# def get_articles():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM articles')
#     articles = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     articles_list = []
#     for article in articles:
#         articles_list.append({
#             'source_id': article[0],
#             'source_name': article[1],
#             'author': article[2],
#             'title': article[3],
#             'description': article[4],
#             'url': article[5],
#             'url_to_image': article[6],
#             'published_at': article[7],
#             'content': article[8]
#         })

#     return jsonify(articles_list)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
