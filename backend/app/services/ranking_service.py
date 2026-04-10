"""Advanced ranking and scoring service for search results."""

from typing import List, Dict
from datetime import datetime, timedelta
from django.utils import timezone
from app.models import Chunk, Document, ActivityLog


class RankingService:
    """Improve search result ranking using multiple signals."""
    
    @staticmethod
    def calculate_ranking_score(
        result: Dict,
        base_semantic_score: float,
        boost_recency: bool = True,
        boost_popularity: bool = True,
        boost_quality: bool = True,
    ) -> float:
        """
        Calculate enhanced ranking score combining multiple signals.
        
        Signals:
        - Semantic similarity (base score from search)
        - Recency: Newer documents scored higher
        - Popularity: Frequently accessed documents scored higher
        - Quality: Longer/more comprehensive chunks scored higher
        
        Args:
            result: Search result dict containing chunk_id, document_id, token_count, etc.
            base_semantic_score: Base semantic similarity score (0-1)
            boost_recency: Whether to boost recently uploaded documents
            boost_popularity: Whether to boost popular documents
            boost_quality: Whether to boost document quality signals
        
        Returns:
            Combined ranking score
        """
        score = base_semantic_score
        
        try:
            chunk = Chunk.objects.select_related('document').get(id=result['chunk_id'])
            doc = chunk.document
            
            # Recency boost: Documents uploaded in last 7 days get bonus
            if boost_recency:
                days_old = (timezone.now() - doc.upload_date).days
                if days_old <= 7:
                    recency_boost = 0.1 * (1 - days_old / 7)
                    score += recency_boost * 0.1  # Max 1% boost
            
            # Popularity boost: Frequently accessed documents
            if boost_popularity:
                try:
                    access_count = ActivityLog.objects.filter(
                        details__contains=f'"document_id": {doc.id}'
                    ).count()
                    
                    # Normalize access count (assuming max 100 accesses for full boost)
                    popularity_boost = min(access_count / 100.0, 1.0) * 0.1
                    score += popularity_boost * 0.05  # Max 0.5% boost
                except:
                    pass
            
            # Quality boost: Longer chunks might indicate more content
            if boost_quality:
                if result.get('token_count', 0) > 200:
                    quality_boost = 0.05
                    score += quality_boost * 0.05  # Max 0.25% boost
        
        except Chunk.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error calculating ranking score: {e}")
        
        # Ensure score stays in valid range [0, 1.5] for display purposes
        return min(max(score, 0), 1.5)
    
    @staticmethod
    def rerank_results(
        results: List[Dict],
        strategy: str = 'combined',
    ) -> List[Dict]:
        """
        Rerank search results using specified strategy.
        
        Strategies:
        - combined: Use all signals
        - recency: Prioritize newer documents
        - popularity: Prioritize frequently accessed
        - relevance: Stick with semantic similarity
        
        Args:
            results: List of search result dicts
            strategy: Ranking strategy to apply
        
        Returns:
            Reranked results
        """
        if not results:
            return results
        
        reranked = []
        
        for result in results:
            original_score = result.get('score', 0)
            
            if strategy == 'combined':
                new_score = RankingService.calculate_ranking_score(
                    result, original_score,
                    boost_recency=True,
                    boost_popularity=True,
                    boost_quality=True,
                )
            elif strategy == 'recency':
                try:
                    chunk = Chunk.objects.get(id=result['chunk_id'])
                    days_old = (timezone.now() - chunk.document.upload_date).days
                    new_score = original_score + (1.0 / (days_old + 1)) * 0.2
                except:
                    new_score = original_score
            elif strategy == 'popularity':
                try:
                    access_count = ActivityLog.objects.filter(
                        details__contains=f'"document_id": {result["document_id"]}'
                    ).count()
                    new_score = original_score + (access_count / 100.0) * 0.2
                except:
                    new_score = original_score
            else:  # 'relevance' or default
                new_score = original_score
            
            result_copy = result.copy()
            result_copy['original_score'] = original_score
            result_copy['ranking_score'] = min(max(new_score, 0), 1.5)
            reranked.append(result_copy)
        
        # Sort by ranking score descending
        reranked.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
        
        return reranked
    
    @staticmethod
    def apply_diversity_penalty(
        results: List[Dict],
        max_per_document: int = 3,
    ) -> List[Dict]:
        """
        Apply diversity penalty to avoid showing too many chunks from same document.
        
        Args:
            results: List of search result dicts
            max_per_document: Maximum chunks from any single document
        
        Returns:
            Deduplicated results with diversity applied
        """
        doc_count: Dict[int, int] = {}
        filtered = []
        
        for result in results:
            doc_id = result.get('document_id')
            if doc_count.get(doc_id, 0) < max_per_document:
                doc_count[doc_id] = doc_count.get(doc_id, 0) + 1
                filtered.append(result)
        
        return filtered


# Global instance
ranking_service = RankingService()
