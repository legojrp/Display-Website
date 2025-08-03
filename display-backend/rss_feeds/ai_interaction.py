import os
import json
import logging
import time
from typing import List, Dict, Optional
import google.generativeai as genai

from .db_handler import DatabaseHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiArticleRanker:
    """
    Article ranking system using Google's Gemini API Flash 2.5.
    
    This system processes articles to:
    - Generate AI summaries explaining article content and importance
    - Assign ranking scores (0-100) based on quality and relevance
    - Store both summary and reasoning in the database's ai_summary field
    """
    
    def __init__(self, api_key: str = None, db_path: str = "articles.db", batch_size: int = 5):
        """
        Initialize the Gemini Article Ranker.
        
        Args:
            api_key (str): Gemini API key (if None, will try to get from environment)
            db_path (str): Path to the SQLite database
            batch_size (int): Number of articles to process in one request
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.db_handler = DatabaseHandler(db_path)
        self.batch_size = batch_size
    
    def _create_ranking_prompt(self, articles: List[Dict]) -> str:
        """
        Create a structured prompt for ranking multiple articles with summaries.
        
        Args:
            articles (List[Dict]): List of article dictionaries
            
        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = """You are an expert article ranker. For each article below, you must:
1. First provide a brief summary of the article content and key points
2. Then provide a ranking score (0-100) (100 being the best) based on importance and relevance

User preferences:
- Prefers informative and newsworthy content
- Interested in science, technology, government, geopolitical, political, NFL, or educational topics
- Dislikes simple sensationalism, local crime, or repetitive/low-impact content
- Values articles with lasting relevance and educational value

Articles to analyze:

"""
        
        for i, article in enumerate(articles, 1):
            prompt += f"\n--- Article {i} ---\n"
            prompt += f"Title: {article.get('title', 'No title')}\n"
            prompt += f"Description: {article.get('description', 'No description')[:400]}...\n"
            if article.get('source'):
                prompt += f"Source: {article.get('source')}\n"
        
        prompt += """

Respond with a JSON array where each element contains both summary and score for the corresponding article:

[
  {
    "summary": "Brief summary explaining what this article is about and why it matters",
    "score": 85,
    "reasoning": "Brief explanation of why this score was given"
  },
  {
    "summary": "Brief summary explaining what this article is about and why it matters", 
    "score": 67,
    "reasoning": "Brief explanation of why this score was given"
  }
]

The order must match the article order above. Provide exactly """ + str(len(articles)) + """ objects in the array."""
        
        return prompt
    
    def _make_api_request(self, prompt: str) -> Optional[str]:
        """
        Make a request to the Gemini API.
        
        Args:
            prompt (str): The ranking prompt
            
        Returns:
            Optional[str]: API response text or None if failed
        """
        try:
            # Generate content with specific configuration
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            
            logger.info("Successfully got response from Gemini API")
            logger.info(f"AI Response: {response.text}")
            return response.text
                        
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None
    
    def _parse_ranking_response(self, response_text: str) -> Optional[List[Dict]]:
        """
        Parse the Gemini API response to extract structured ranking data.
        
        Args:
            response_text (str): Raw API response text
            
        Returns:
            Optional[List[Dict]]: List of ranking objects with summary, score, and reasoning or None if failed
        """
        try:
            logger.info(f"Parsing response text: {response_text}")
            
            # Try to find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                logger.error("No JSON array found in API response")
                logger.error(f"Response text: {response_text}")
                return None
            
            json_str = response_text[start_idx:end_idx + 1]
            rankings = json.loads(json_str)
            
            # Validate structure
            if not isinstance(rankings, list):
                logger.error("Response is not a list")
                return None
            
            logger.info(f"Found {len(rankings)} rankings in response")
            
            # Validate each ranking object
            validated_rankings = []
            for i, ranking in enumerate(rankings):
                if not isinstance(ranking, dict):
                    logger.error(f"Ranking {i} is not a dictionary")
                    continue
                
                # Ensure required fields exist
                if 'score' not in ranking:
                    logger.error(f"Ranking {i} missing score field")
                    continue
                
                # Normalize the ranking object
                normalized_ranking = {
                    'summary': ranking.get('summary', 'No summary provided'),
                    'score': float(ranking['score']),
                    'reasoning': ranking.get('reasoning', 'No reasoning provided')
                }

                # Validate score range
                if not (0 <= normalized_ranking['score'] <= 100):
                    logger.warning(f"Score {normalized_ranking['score']} out of range 0-100, clamping")
                    normalized_ranking['score'] = max(0, min(100, normalized_ranking['score']))
                
                validated_rankings.append(normalized_ranking)
            
            logger.info(f"Successfully parsed {len(validated_rankings)} valid rankings")
            return validated_rankings
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse rankings from API response: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing ranking response: {e}")
            return None
    
    def rank_articles_batch(self, articles: List[Dict]) -> List[tuple]:
        """
        Rank a batch of articles using Gemini API with structured response.
        
        Args:
            articles (List[Dict]): List of article dictionaries
            
        Returns:
            List[tuple]: List of (article_id, score, ranking_data)
        """
        if not articles:
            return []
        
        # Limit batch size
        if len(articles) > self.batch_size:
            articles = articles[:self.batch_size]
            logger.warning(f"Batch size limited to {self.batch_size} articles")
        
        logger.info(f"Processing batch of {len(articles)} articles")
        
        # Create prompt and make API request
        prompt = self._create_ranking_prompt(articles)
        response_text = self._make_api_request(prompt)
        
        if not response_text:
            return []
        
        # Parse rankings
        rankings = self._parse_ranking_response(response_text)
        if not rankings:
            logger.error("Failed to parse rankings from API response")
            return []
        
        logger.info(f"Successfully parsed {len(rankings)} rankings")
        
        # Match rankings back to article IDs
        results = []
        for i, ranking in enumerate(rankings):
            if i < len(articles):
                article_id = articles[i]['id']
                score = ranking['score']
                ranking_data = {
                    'summary': ranking['summary'],
                    'reasoning': ranking['reasoning'],
                    'title': articles[i].get('title', 'No title')
                }
                results.append((article_id, float(score), ranking_data))
                logger.info(f"Article {article_id}: {score}/100")
                logger.debug(f"  Summary: {ranking['summary']}")
                logger.debug(f"  Reasoning: {ranking['reasoning']}")
        
        logger.info(f"Returning {len(results)} ranking results")
        return results
    
    def rank_pending_articles(self, limit: int = None, save_debug_info: bool = True) -> int:
        """
        Rank all pending articles in the database.
        
        Args:
            limit (int): Maximum number of articles to process (None for all)
            save_debug_info (bool): Whether to save summary and reasoning for debugging
            
        Returns:
            int: Number of articles successfully ranked
        """
        logger.info("Starting article ranking process...")
        
        # Get pending articles
        pending_articles = self.db_handler.get_articles_by_status('pending', limit=limit)
        
        if not pending_articles:
            logger.info("No pending articles found")
            return 0
        
        logger.info(f"Found {len(pending_articles)} pending articles to rank")
        
        total_ranked = 0
        ranking_debug_log = []
        
        # Process in batches
        for i in range(0, len(pending_articles), self.batch_size):
            batch = pending_articles[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(pending_articles) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")
            
            try:
                rankings = self.rank_articles_batch(batch)
                
                # Update database with rankings
                for article_id, score, ranking_data in rankings:
        
                    # Update the article
                    success = self.db_handler.update_article(
                        article_id,
                        ranking_score=score,
                        status='ranked',
                        ai_summary=ranking_data['summary'],
                        ai_reasoning=ranking_data['reasoning'],
                    )
                    
                    if success:
                        total_ranked += 1
                        
                        # Save debug information if requested
                        if save_debug_info:
                            debug_entry = {
                                'article_id': article_id,
                                'title': ranking_data['title'],
                                'score': score,
                                'summary': ranking_data['summary'],
                                'reasoning': ranking_data['reasoning'],
                                'batch': batch_num
                            }
                            ranking_debug_log.append(debug_entry)
                    else:
                        logger.error(f"Failed to update article {article_id}")
                
                logger.info(f"Batch {batch_num} completed: {len(rankings)} articles ranked")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                continue
        
        # Save debug log if requested
        if save_debug_info and ranking_debug_log:
            debug_file = f"ranking_debug_{int(time.time())}.json"
            try:
                with open(debug_file, 'w') as f:
                    json.dump(ranking_debug_log, f, indent=2)
                logger.info(f"Debug information saved to {debug_file}")
            except Exception as e:
                logger.error(f"Failed to save debug information: {e}")
        
        logger.info(f"Article ranking completed: {total_ranked}/{len(pending_articles)} articles ranked")
        return total_ranked
    
    def get_recent_rankings(self, limit: int = 10) -> List[Dict]:
        """
        Get recently ranked articles for debugging purposes.
        
        Args:
            limit (int): Number of recent rankings to retrieve
            
        Returns:
            List[Dict]: List of recently ranked articles with their scores
        """
        recent_articles = self.db_handler.get_articles_by_status('ranked', limit=limit)
        rankings = []
        
        for article in recent_articles:
            ranking_info = {
                'id': article['id'],
                'title': article.get('title', 'No title'),
                'score': article.get('ranking_score', 0),
                'url': article.get('link', 'No URL'),
                'source': article.get('source', 'Unknown'),
                'description': article.get('description', 'No description')[:200] + '...',
                'ai_summary': article.get('ai_summary', 'No AI summary available')
            }
            rankings.append(ranking_info)
        
        return rankings
    
# Convenience function for easy usage
def rank_articles(api_key: str = None, limit: int = None, db_path: str = "articles.db", 
                 batch_size: int = 5, save_debug_info: bool = True) -> int:
    """
    Convenience function to rank articles.
    
    Args:
        api_key (str): Gemini API key
        limit (int): Maximum number of articles to process
        db_path (str): Database path
        batch_size (int): Number of articles to process in one request
        save_debug_info (bool): Whether to save debug information
        
    Returns:
        int: Number of articles ranked
    """
    ranker = GeminiArticleRanker(api_key=api_key, db_path=db_path, batch_size=batch_size)
    return ranker.rank_pending_articles(limit=limit, save_debug_info=save_debug_info)

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Rank articles using Gemini AI')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--limit', type=int, help='Maximum number of articles to process')
    parser.add_argument('--db-path', default='articles.db', help='Database path')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of articles to process in one request')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug information saving')
    
    args = parser.parse_args()
    
    ranked = rank_articles(
        api_key=args.api_key, 
        limit=args.limit, 
        db_path=args.db_path, 
        batch_size=args.batch_size,
        save_debug_info=not args.no_debug
    )
    print(f"Successfully ranked {ranked} articles")
    if not args.no_debug:
        print("Debug information saved to ranking_debug_*.json")
