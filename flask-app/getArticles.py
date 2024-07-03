from newsapi import NewsApiClient
import psycopg2
import sys

from config import load_config

# Load config
config = load_config()

# Establish database connection
try:
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
except Exception as e:
    print(f"Database connection error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize News API client
newsapi = NewsApiClient(api_key='fee8e0fcf150466ab960b6b5043be353')

# Get sources
try:
    top_headlines = newsapi.get_top_headlines(country='us')
    if not top_headlines or 'articles' not in top_headlines:
        print("No sources found in API response", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Error fetching sources: {e}", file=sys.stderr)
    sys.exit(1)

# Print the sources to check the response
print(f"Fetched sources: {top_headlines}")

# Define the INSERT query
insert_query = """
INSERT INTO top_headlines_US (source_id, source_name, author, title, description, url, url_to_image, published_at, content)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO NOTHING;
"""
for article in top_headlines['articles']:
    try:
        source_id = article['source']['id']
        source_name = article['source']['name']
        author = article['author']
        title = article['title']
        description = article['description']
        url = article['url']
        url_to_image = article['urlToImage']
        published_at = article['publishedAt']
        content = article['content']
        
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
        print(f"Inserted article: {title}")
    except Exception as e:
        print(f"Error inserting article {title}: {e}", file=sys.stderr)
# Commit and close the connection
try:
    conn.commit()
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error closing database connection: {e}", file=sys.stderr)
