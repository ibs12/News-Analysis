# from newsapi import NewsApiClient
# import psycopg2
# import sys
# import requests
# from config import load_config
# import argparse

# # # Set up argument parser to accept search term
# parser = argparse.ArgumentParser(description='Fetch and store news articles.')
# parser.add_argument('search_term', type=str, help='The search term to fetch articles for')
# args = parser.parse_args()
# search_term = args.search_term
# # search_term = input("Enter Search Term:")

# # Load config
# config = load_config()

# try:
#     # Establish database connection
#     conn = psycopg2.connect(**config)
#     cursor = conn.cursor()

#     # Initialize News API client
#     newsapi = NewsApiClient(api_key='fee8e0fcf150466ab960b6b5043be353')
# # q=search_term
#     # Get sources
#     allArticles = newsapi.get_everything( q=search_term, language='en')
#     if not allArticles or 'articles' not in allArticles:
#         print("No sources found in API response", file=sys.stderr)
#         sys.exit(1)

#     # Define the base URL of your Node.js server
#     node_server_url = 'http://localhost:3001'
#     print(f"Fetching articles for search term: {search_term}")
#     print(f"Articles: {allArticles}")
    
#     articles = []
#     # Iterate over each article fetched from News API
#     for article in allArticles['articles']:
#         try:
#             # Extract article details
#             source_id = article['source']['id']
#             source_name = article['source']['name']
#             author = article['author']
#             title = article['title']
#             description = article['description']
#             url = article['url']
#             url_to_image = article['urlToImage']
#             published_at = article['publishedAt']

#             # Make a request to Node.js server to fetch article content
#             response = requests.post(f"{node_server_url}/scrape-articles", json={'url': url})

#             if response.status_code == 200:
#                 content = response.json().get('content', '')
#             else:
#                 print(f"Error fetching content for article {title}: HTTP {response.status_code}")
#                 content = ''  # Fallback to empty content

#                 # Prepare the article data to return to the frontend
#                 article_data = {
#                     "source_id": source_id,
#                     "source_name": source_name,
#                     "author": author,
#                     "title": title,
#                     "description": description,
#                     "url": url,
#                     "url_to_image": url_to_image,
#                     "published_at": published_at,
#                     "content": content
#                 }
#                 articles.append(article_data)

#             # Define the INSERT query
#             insert_query = """
#             INSERT INTO articles (source_id, source_name, author, title, description, url, url_to_image, published_at, content)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """

#             # Execute the INSERT query with article details
#             cursor.execute(insert_query, (
#                 source_id,
#                 source_name,
#                 author,
#                 title,
#                 description,
#                 url,
#                 url_to_image,
#                 published_at,
#                 content
#             ))

#             print(f"Inserted article: {title}")
            

#         except Exception as e:
#             print(f"Error processing article {title}: {e}", file=sys.stderr)
#             conn.rollback()  # Rollback the transaction on error

#     # Commit changes and close the database connection
#     conn.commit()



# except Exception as e:
#     print(f"Error: {e}", file=sys.stderr)

# finally:
#     try:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()
#             print("Database connection closed.")
#     except Exception as e:
#         print(f"Error closing database connection: {e}", file=sys.stderr)
