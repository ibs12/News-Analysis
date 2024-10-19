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
from newsdataapi import NewsDataApiClient 




app = Flask(__name__)
from flask_cors import CORS
CORS(app)
load_dotenv()

# Load config
config = load_config()

newsapi = NewsApiClient(api_key= os.getenv('API_KEY'))
newsDataapi = NewsDataApiClient(apikey= os.getenv('NEWS_DATA_API_KEY'))

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
        # all_articles = newsapi.get_everything(q=search_term, sort_by='relevancy')
        newsDataApiResponse = newsDataapi.latest_api( q= search_term , country = "us")


        if not newsDataApiResponse or 'results' not in newsDataApiResponse:
            return jsonify({"error": "No articles found"}), 404

        articles = []
        for article in newsDataApiResponse['results']:
            try:
                article_id = article['article_id']
                title = article['title']
                link = article['link']
                keywords = article['keywords']
                creator = article['creator']
                video_url = article['video_url']
                description = article['description']
                content = article['content']
                pubDate = article['pubDate']
                pubDateTZ = article['pubDateTZ']
                image_url = article['image_url']
                source_id = article['source_id']
                source_priority = article['source_priority']
                source_name = article['source_name']
                source_url = article['source_url']
                source_icon = article['source_icon']
                language = article['language']
                country = article['country']
                category = article['category']
                ai_tag = article['ai_tag']
                ai_region = article['ai_region']
                ai_org = article['ai_org']
                sentiment = article['sentiment']
                sentiment_stats = article['sentiment_stats']
                duplicate = article['duplicate']
 
                
                # response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})

                # if response.status_code == 200:
                #     content = response.json().get('content', '')
                # else:
                #     print(f"Error fetching content for article {article['title']}: HTTP {response.status_code}")
                #     content = ''  # Fallback to empty content

                    
                if source_id is None or 'null':
                    source_id = source_name.replace(" ", "-").lower()   
                    


                # Prepare the article data to return to the frontend
                article_data = {
                    
                'article_id' : article_id,
                'title' : title,
                'link' : link,
                'keywords' : keywords,
                'creator' : creator,
                'video_url' : video_url,
                'description' : description,
                'content' : content,
                'pubDate' : pubDate,
                'pubDateTZ' :pubDateTZ,
                'image_url' :image_url,
                'source_id' :source_id,
                'source_priority' :source_priority,
                'source_name' :source_name,
                'source_url' :source_url,
                'source_icon' :source_icon,
                'language' :language,
                'country' :country,
                'category' :category,
                'ai_tag' :ai_tag,
                'ai_region' :ai_region,
                'ai_org' :ai_org,
                'sentiment' :sentiment,
                'sentiment_stats' :sentiment_stats,
                'duplicate' :duplicate,


                }
                articles.append(article_data)
                


                # Insert the article into the database
                insert_query = """
                INSERT INTO articles (article_id,
                title,
                link,
                keywords,
                creator,
                video_url,
                description,
                content,
                pubDate,
                pubDateTZ,
                image_url,
                source_id,
                source_priority,
                source_name,
                source_url,
                source_icon,
                language,
                country,
                category,
                ai_tag,
                ai_region,
                ai_org,
                sentiment,
                sentiment_stats,
                duplicate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                article_id,
                title,
                link,
                keywords,
                creator,
                video_url,
                description,
                content,
                pubDate,
                pubDateTZ,
                image_url,
                source_id,
                source_priority,
                source_name,
                source_url,
                source_icon,
                language,
                country,
                category,
                ai_tag,
                ai_region,
                ai_org,
                sentiment,
                sentiment_stats,
                duplicate
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

