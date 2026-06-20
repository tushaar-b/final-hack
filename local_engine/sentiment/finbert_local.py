import os
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import torch
from transformers import pipeline

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_finbert_inference():
    logger.info("Starting local FinBERT sentiment inference...")
    
    # Fetch pending rows
    try:
        response = supabase.table("news_sentiment").select("*").is_("sentiment_score", "null").execute()
        pending_rows = response.data
    except Exception as e:
        logger.error(f"Failed to fetch pending rows from Supabase: {e}")
        return False
        
    if not pending_rows:
        logger.info("No pending headlines to score. Exiting.")
        return True
        
    logger.info(f"Found {len(pending_rows)} headlines pending sentiment analysis.")
    logger.info("Initializing FinBERT model... (This will download ~400MB on the first run. Please wait.)")
    
    # Initialize FinBERT
    try:
        device = 0 if torch.cuda.is_available() else -1
        # top_k=None returns all scores for the sequence
        nlp = pipeline("text-classification", model="ProsusAI/finbert", tokenizer="ProsusAI/finbert", top_k=None, device=device)
    except Exception as e:
        logger.error(f"Failed to load FinBERT model: {e}")
        return False
        
    logger.info("FinBERT loaded successfully. Scoring headlines...")
    
    headlines = [row['headline'] for row in pending_rows]
    
    # Process batch
    try:
        results = nlp(headlines)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return False
        
    updates = []
    
    for row, scores in zip(pending_rows, results):
        # scores is a list of dicts like: [{'label': 'positive', 'score': 0.8}, {'label': 'negative', 'score': 0.1}, {'label': 'neutral', 'score': 0.1}]
        pos_score = 0.0
        neg_score = 0.0
        
        for score_dict in scores:
            if score_dict['label'] == 'positive':
                pos_score = score_dict['score']
            elif score_dict['label'] == 'negative':
                neg_score = score_dict['score']
                
        final_score = round(pos_score - neg_score, 4)
        
        updates.append({
            "id": row['id'],
            "symbol": row['symbol'],
            "headline": row['headline'],
            "source": row['source'],
            "published_at": row['published_at'],
            "created_at": row['created_at'],
            "sentiment_score": final_score
        })
        
    logger.info(f"Computed scores for {len(updates)} headlines. Updating Supabase...")
    
    # Update Supabase
    try:
        supabase.table("news_sentiment").upsert(updates).execute()
        logger.info("Successfully updated sentiment scores in Supabase.")
        
        # Print a few samples for verification
        num_to_print = min(5, len(updates))
        logger.info(f"--- VERIFICATION: {num_to_print} Scored Samples ---")
        for u in updates[:num_to_print]:
            logger.info(f"[{u['symbol']}] Score: {u['sentiment_score']:>6.4f} | Headline: {u['headline'][:75]}...")
            
        return True
    except Exception as e:
        logger.error(f"Failed to update scores in Supabase: {e}")
        return False

if __name__ == "__main__":
    run_finbert_inference()
