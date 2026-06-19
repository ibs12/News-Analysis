from transformers import pipeline
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
import spacy
import re
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import pandas as pd
import psycopg2
from config import load_config
import os
# SECURITY: a real Google API key was previously hardcoded here and committed.
# It must be rotated (it still lives in git history). Load from env instead.
api_key = os.getenv("GOOGLE_API_KEY", "")
class DynamicEventDetector:
    def __init__(self, device=None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Using device: {self.device}")
        
        self.ner = pipeline("ner", model="jean-baptiste/roberta-large-ner-english",
                            device=0 if self.device == "cuda" else -1)
        
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        if self.device == "cuda":
            self.encoder = self.encoder.to(self.device)
            
        print("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        print("Models loaded successfully!")
    
    

    def clean_text(self, text):
        text = text.replace('Ġ', '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def merge_locations(self, locations):
        cleaned_locations = [self.clean_text(loc) for loc in locations]
        seen = set()
        merged = []
        for loc in cleaned_locations:
            if loc not in seen:
                seen.add(loc)
                merged.append(loc)
        return merged

    def extract_entities(self, text):
        entities = self.ner(text)
        merged = []
        current = None
        
        for ent in entities:
            ent['word'] = self.clean_text(ent['word'])
            if current is None:
                current = ent.copy()
            elif (current['entity'].replace('B-', '') == ent['entity'].replace('I-', '') and
                  ent['start'] == current['end'] + 1):
                current['word'] += ' ' + ent['word']
                current['end'] = ent['end']
            else:
                merged.append(current)
                current = ent.copy()
        
        if current:
            merged.append(current)
            
        final_entities = []
        for ent in merged:
            if ent['entity'] in ['B-LOC', 'I-LOC']:
                final_entities.append(ent)
        
        print(f"Found {len(final_entities)} merged entities: {[e['word'] for e in final_entities]}")
        return final_entities

    def extract_event_features(self, text):
        doc = self.nlp(text)
        entities = self.extract_entities(text)
        
        locations = []
        main_entities = []
        
        # Filter entities for location and event-related keywords
        for ent in entities:
            if ent['entity'] in ['B-LOC', 'I-LOC']:
                locations.append(ent['word'])
            elif ent['entity'] in ['B-MISC', 'B-ORG']:
                main_entities.append(ent['word'])
                
        # Include spaCy-detected locations
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                locations.append(ent.text)
        
        locations = self.merge_locations(locations)
        
        # Extract potential event keywords and key phrases
        event_keywords = []
        for token in doc:
            if token.pos_ in ['NOUN'] and token.dep_ in ['nsubj', 'ROOT']:
                event_keywords.append(token.text)
        
        # Filter key phrases for likely event descriptors like "earthquake," "flood," etc.
        relevant_events = [kw for kw in event_keywords if kw.lower() in ["earthquake", "storm", "flood", "fire", "hurricane"]]
        
        return {
            'entities': entities,
            'locations': locations,
            'dates': [ent.text for ent in doc.ents if ent.label_ == 'DATE'],
            'key_phrases': relevant_events
        }

    def cluster_articles(self, articles, eps=None, min_samples=2):
        print(f"\nClustering {len(articles)} articles...")
        
        # Encode each article using the sentence transformer
        print("Encoding articles...")
        embeddings = [self.encoder.encode(article) for article in articles]
        
        # Compute the cosine similarity matrix
        print("Computing similarity matrix...")
        similarity_matrix = cosine_similarity(embeddings)
        
        # Analyze similarity distribution and get suggested eps if not provided
        if eps is None:
            eps = self.analyze_similarity_distribution(similarity_matrix)
            print(f"\nAutomatically determined eps: {eps:.3f}")
        
        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix
        distance_matrix[distance_matrix < 0] = 0  # Ensure no negative values
        
        # Cluster with DBSCAN using the distance matrix
        print(f"Running DBSCAN clustering with eps={eps}, min_samples={min_samples}")
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        labels = clustering.fit_predict(distance_matrix)
        
        # Print clustering results
        unique_labels = sorted(set(labels))
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        print(f"Found {n_clusters} clusters")
        print(f"Noise points: {n_noise}")
        
        # Print size of each cluster
        for label in unique_labels:
            if label != -1:
                cluster_size = list(labels).count(label)
                print(f"Cluster {label} size: {cluster_size}")
        
        return labels

    def detect_events(self, clusters, api_key, prompt_message):
        print("\nDetecting events...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.5,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
        )

        cluster_summaries = {}
        print(f"Processing {len(clusters)} clusters...")
        
        for cluster_id, articles in clusters.items():
            if cluster_id == -1:  # Skip noise cluster
                continue
                
            print(f"\nProcessing cluster {cluster_id} with {len(articles)} articles")
            print(f"Sample from cluster {cluster_id}:")
            print(articles[0][:200] + "...")  # Print sample from cluster
            
            prompt = prompt_message + "\n\n".join(articles)
            try:
                response = model.start_chat().send_message(prompt)
                cluster_summaries[cluster_id] = response.text
                print(f"Successfully processed cluster {cluster_id}")
            except Exception as e:
                print(f"Error processing cluster {cluster_id}: {str(e)}")
        
        return cluster_summaries
    
    def analyze_similarity_distribution(self, similarity_matrix):
        """Analyze the distribution of similarity scores to help set clustering parameters."""
        # Get upper triangle of similarity matrix (excluding diagonal)
        upper_tri = similarity_matrix[np.triu_indices(similarity_matrix.shape[0], k=1)]
        
        percentiles = {
            "25th": np.percentile(upper_tri, 25),
            "50th": np.percentile(upper_tri, 50),
            "75th": np.percentile(upper_tri, 75),
            "90th": np.percentile(upper_tri, 90)
        }
        
        print("\nSimilarity score distribution:")
        for p, v in percentiles.items():
            print(f"{p} percentile: {v:.3f}")
            
        # Suggest eps based on distribution
        suggested_eps = 1 - percentiles["75th"]  # Use 75th percentile as cutoff
        return suggested_eps
    
# Load config and articles from the database
print("\nLoading articles from database...")
config = load_config()
conn = psycopg2.connect(**config)
cursor = conn.cursor()

cursor.execute("SELECT content FROM top_headlines_us")
articles = cursor.fetchall()
articles = [article[0] for article in articles]
print(f"Loaded {len(articles)} articles from database")

# Print first few articles for debugging
print("\nSample of first 2 articles:")
for i, article in enumerate(articles[:2]):
    print(f"\nArticle {i+1} (length: {len(article)} chars):")
    print(article[:200] + "...")

cursor.close()
conn.close()

# Initialize detector
detector = DynamicEventDetector()

# Cluster articles with automatic eps determination and reduced min_samples
clusters = detector.cluster_articles(articles, eps=None, min_samples=2)

# Group articles by their cluster labels
clustered_articles = defaultdict(list)
for idx, cluster_id in enumerate(clusters):
    clustered_articles[cluster_id].append(articles[idx])

print(f"\nCreated {len(clustered_articles)} article clusters")

# Set prompt message for event detection and summary
prompt_message = (
    "Analyze the following news articles and identify the main event or story being discussed. "
    "Provide a concise summary that includes:\n"
    "1. The main event or development\n"
    "2. Key locations mentioned\n"
    "3. Important dates\n"
    "4. Key figures or organizations involved\n"
    "5. Significant impacts or implications\n\n"
    "Articles:\n"
)

# Detect events and get summaries from the Gemini API
event_summaries = detector.detect_events(clustered_articles, api_key, prompt_message)

# Print the generated event summaries
print("\nEvent Summaries:")
if not event_summaries:
    print("No events detected in the clusters")
else:
    for cluster_id, summary in event_summaries.items():
        print(f"\nCluster {cluster_id}:")
        print(summary)

# Testing with multiple topics

    # print("Initializing DynamicEventDetector...")
    
    # from config import load_config
    # import psycopg2

    # # Load config
    # config = load_config()
    # conn = psycopg2.connect(**config)
    # cursor = conn.cursor()

    # # Query to fetch content and title from the top_headlines_us table
    # cursor.execute("SELECT title, content FROM top_headlines_us")
    # articles = cursor.fetchall()

    # # Extract titles and contents into separate lists
    # titles = [article[0] for article in articles]
    # sample_texts = [article[1] for article in articles]

    # # Check if data was retrieved
    # if not titles or not sample_texts:
    #     print("No articles found in the top_headlines_us table.")
    # else:
    #     print(f"Retrieved {len(titles)} articles from the database.")
    
    # detector = DynamicEventDetector()
    # events = detector.detect_events(sample_texts, titles, n_clusters=3)
    
    # print("\n=== Final Results ===")
    # for event in events:
    #     print(f"\nEvent: {event['event_title']}")
    #     print(f"Number of articles: {event['num_articles']}")
    #     print(f"Locations: {', '.join(event['locations'])}")
    #     print(f"Main entities: {', '.join(event['main_entities'])}")
    #     print("\nRelated articles:")
    #     for article in event['articles']:
    #         print(f"- {article['title']}")
    #         print(f"  Preview: {article['text'][:100]}...")
    
    
