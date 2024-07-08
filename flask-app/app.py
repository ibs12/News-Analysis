from flask import Flask, jsonify
import psycopg2
from config import load_config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Load config
config = load_config()

# Establish database connection
def get_db_connection():
    conn = psycopg2.connect(**config)
    return conn


from flask import Flask

app = Flask(__name__)

@app.route('/flask', methods=['GET'])
def index():
    return "Flask server"



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
