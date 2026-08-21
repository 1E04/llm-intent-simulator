import os
import json
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

def cluster_intents(intents: List[str], distance_threshold: float = 0.5) -> Dict[str, List[str]]:
    """
    Computes embeddings for intents using all-MiniLM-L6-v2 and clusters them
    based on cosine distance.
    Returns a mapping of intent -> list of sibling intents in the same cluster.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Preprocess intents for better semantic meaning (e.g., 'card_payment_fee_charged' -> 'card payment fee charged')
    processed_intents = [intent.replace("_", " ") for intent in intents]
    
    print(f"\n[Clustering] Fetching embeddings for {len(intents)} intents using all-MiniLM-L6-v2...")
    embeddings = model.encode(processed_intents)
    
    # Use Agglomerative Clustering with cosine distance
    # distance = 1 - cosine_similarity. Lower threshold means tighter clusters.
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='cosine',
        linkage='average',
        distance_threshold=distance_threshold
    )
    
    labels = clustering.fit_predict(embeddings)
    
    # Group intents by cluster label
    clusters = {}
    for intent, label in zip(intents, labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(intent)
        
    # Build the sibling mapping
    intent_to_siblings = {}
    for group in clusters.values():
        for intent in group:
            # siblings are all other intents in the same cluster
            siblings = [x for x in group if x != intent]
            intent_to_siblings[intent] = siblings
            
    print(f"[Clustering] Done. Formed {len(clusters)} distinct clusters (distance threshold = {distance_threshold}).\n")
    return intent_to_siblings

def get_intent_clusters(intents: List[str], distance_threshold: float = 0.4) -> Dict[str, List[str]]:
    """
    Cached wrapper around cluster_intents.
    """
    cache_file = "intent_clusters_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure the cache covers all requested intents
            if all(i in data for i in intents):
                return {k: v for k, v in data.items() if k in intents}
        except Exception as e:
            print(f"[Clustering] Failed to read cache: {e}")
            
    intent_to_siblings = cluster_intents(intents, distance_threshold)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(intent_to_siblings, f, indent=2)
        
    return intent_to_siblings
