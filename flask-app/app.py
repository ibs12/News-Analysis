from flask import Flask, jsonify, request
import psycopg2
from config import load_config
import requests

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

# Load config
config = load_config()

# Establish database connection
def get_db_connection():
    conn = psycopg2.connect(**config)
    return conn

@app.route('/scrape', methods=['POST'])
def scrape_and_update():
    # Example endpoint to trigger scraping from Node.js server
    url = 'http://localhost:3000/scrape-articles'  # Adjust URL as per your Node.js server setup

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return "Scraping and updating started successfully."
        else:
            return "Failed to start scraping and updating."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/api/articles', methods=['GET'])
def get_articles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM top_headlines_us')
    articles = cursor.fetchall()
    cursor.close()
    conn.close()

    articles_list = []
    for article in articles:
        articles_list.append({
            'source_id': article[0],
            'source_name': article[1],
            'author': article[2],
            'title': article[3],
            'description': article[4],
            'url': article[5],
            'url_to_image': article[6],
            'published_at': article[7],
            'content': article[8]
        })

    return jsonify(articles_list)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
