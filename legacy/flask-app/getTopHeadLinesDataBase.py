from flask import jsonify
import psycopg2
from config import load_config
import os
import sys
import gc

# Load config
config = load_config()

def fetch_topheadlines_us_database():
    cursor = None
    conn = None
    
    try:
        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # Query to fetch all articles from top_headlines_us table
        fetch_articles_query = """
            SELECT source_id, source_name, author, title, description, url, 
                   url_to_image, published_at, content, bias 
            FROM top_headlines_us
        """
        cursor.execute(fetch_articles_query)
        all_articles = cursor.fetchall()

        articles = []
        for article in all_articles:
            source_id, source_name, author, title, description, url, url_to_image, published_at, content, bias = article
            
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

        # Query to fetch all publishers from the publishers table
        fetch_publishers_query = """
            SELECT publisher_id, name, description, url, category, language, country
            FROM publishers
        """
        cursor.execute(fetch_publishers_query)
        all_publishers = cursor.fetchall()

        publishers = []
        for publisher in all_publishers:
            publisher_id, name, description, url, category, language, country = publisher
            
            publisher_data = {
                "publisher_id": publisher_id,
                "name": name,
                "description": description,
                "url": url,
                "category": category,
                "language": language,
                "country": country
            }
            publishers.append(publisher_data)

        # Return JSON response with both articles and publishers
        return jsonify({"articles": articles, "publishers": publishers}), 200
        
    except Exception as e:
        print({"error": str(e)}, 500)
        return jsonify({"error": str(e)}), 500
        
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
        gc.collect()
