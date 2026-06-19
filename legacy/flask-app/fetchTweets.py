import requests

# Replace with your Bearer Token
import os
# SECURITY: a real bearer token was previously hardcoded here and committed.
# It must be rotated (it still lives in git history). Load from env instead.
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# URL you want to find replies for
url_to_search = "https://www.foxnews.com/media/woman-served-trump-mcdonalds-drive-thru-reveals-details-behind-viral-exchange-former-president"

# Endpoint for searching recent tweets containing the URL
search_url = "https://api.twitter.com/2/tweets/search/recent"

# Function to fetch tweets containing the URL
def fetch_tweets_with_url(url):
    query_params = {
        'query': f"url:\"{url}\"",
        'tweet.fields': 'id,author_id,conversation_id,created_at,text',
        'max_results': 10
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(search_url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

# Function to fetch replies to a specific tweet
def fetch_replies(conversation_id):
    query_params = {
        'query': f'conversation_id:{conversation_id}',
        'tweet.fields': 'id,author_id,created_at,text,in_reply_to_user_id',
        'max_results': 10
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(search_url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

# Step 1: Get tweets containing the URL
tweets_with_url = fetch_tweets_with_url(url_to_search)

print(f"Found {len(tweets_with_url)} tweets containing the URL.")
print(tweets_with_url)

# # Step 2: For each tweet, fetch replies 
# for tweet in tweets_with_url:
#     print(f"Original Tweet: {tweet['text']} by {tweet['author_id']}\n")
#     replies = fetch_replies(tweet['id'])
#     for reply in replies:
#         print(f"Reply: {reply['text']} by {reply['author_id']}")
#         print(f"Created at: {reply['created_at']}\n")
        
