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
    sources = newsapi.get_sources()
    if not sources or 'sources' not in sources:
        print("No sources found in API response", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Error fetching sources: {e}", file=sys.stderr)
    sys.exit(1)

# Print the sources to check the response
print(f"Fetched sources: {sources}")

# Define the INSERT query
insert_query = """
INSERT INTO publishers (id, name, description, url, category, language, country)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO NOTHING;
"""

# Insert data into the database
for source in sources['sources']:
    try:
        cursor.execute(insert_query, (
            source['id'],
            source['name'],
            source['description'],
            source['url'],
            source['category'],
            source['language'],
            source['country']
        ))
        print(f"Inserted source: {source['id']}")
    except Exception as e:
        print(f"Error inserting source {source['id']}: {e}", file=sys.stderr)

# Commit and close the connection
try:
    conn.commit()
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error closing database connection: {e}", file=sys.stderr)
