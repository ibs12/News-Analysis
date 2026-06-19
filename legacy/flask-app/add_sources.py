# tasks.py
from celery_config import make_celery
from flask import current_app, jsonify
from newsapi import NewsApiClient
import psycopg2
from config import load_config
import os
import sys

config = load_config()
newsapi = NewsApiClient(api_key=os.getenv('API_KEY'))
node_server_url = 'http://localhost:3001'

def fetch_data():

    try:
        # Establish database connection
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        response = newsapi.get_top_headlines(language='en', country='us')

        # Check if the response contains sources
        if not response or 'sources' not in response:
            return {"error": "No sources found"}, 404  # Return a plain dict
        
        all_sources = response['sources']
        sources = []

        for source in all_sources:
            try:
                source_id = source['id']
                source_name = source['name']
                source_description = source['description']
                source_url = source['url']
                source_category = source['category']
                source_language = source['language']
                source_country = source['country']
                
                # Check if publisher with the same URL already exists in the database
                check_query = "SELECT 1 FROM publishers WHERE url = %s"
                cursor.execute(check_query, (source_url,))
                exists = cursor.fetchone()

                # if exists:
                #     print(f"Duplicate source found: {source_name}, skipping insertion.")
                #     continue  # Skip if the article already exists

                # Generate source_id if not provided
                if not source_id:
                    source_id = source_name.replace(" ", "-").lower()

                # Prepare and insert the source data into the database
                sources.append({
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_description": source_description,
                    "source_url": source_url,
                    "source_category": source_category,
                    "source_language": source_language,
                    "source_country": source_country
                })

                insert_query = """
                INSERT INTO publishers (id, name, description, url, category, language, country)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    source_id,
                    source_name,
                    source_description,
                    source_url,
                    source_category,
                    source_language,
                    source_country
                ))

            except Exception as e:
                print(f"Error processing publisher {source_name}: {e}", file=sys.stderr)
                conn.rollback()  # Rollback the transaction on error

        # Commit the transaction to save all publishers in the database
        conn.commit()

        return {"sources": sources}, 200  # Return the list of sources

    except Exception as e:
        return {"error": str(e)}, 500  # Return the error as a plain dict

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}", file=sys.stderr)
            
if __name__ == "__main__":
    result, status_code = fetch_data()
    if status_code == 200:
        print("Data fetched and inserted into the database successfully.")
    else:
        print(f"Error: {result.get('error')}")