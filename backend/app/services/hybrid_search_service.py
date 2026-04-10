"""Hybrid search service combining semantic and keyword-based search."""

from typing import List, Dict, Optional
import re
from collections import Counter

from django.db.models import Q
from app.models import Chunk, Document, TaskDocument
from .embedding_service import embedding_service


class HybridSearchService:
    """Combines semantic search with keyword/BM25-like ranking."""
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    def _bm25_score(self, query_terms: List[str], chunk_text: str, doc_length: int = 0) -> float:
        """
        Simple BM25-like scoring for keyword relevance.
        
        BM25 parameters:
        - k1=1.5: Controls term frequency saturation
        - b=0.75: Controls how much document length affects score
        """
        if not query_terms or not chunk_text:
            return 0.0
        
        k1, b = 1.5, 0.75
        avg_doc_length = 500  # Average chunk length
        doc_length = doc_length or len(chunk_text.split())
        
        chunk_lower = chunk_text.lower()
        score = 0.0
        
        for term in query_terms:
            term_lower = term.lower()
            term_count = len(re.findall(rf'\b{re.escape(term_lower)}\b', chunk_lower))
            
            if term_count > 0:
                # BM25 formula
                idf = 1.0  # Simplified IDF (could be enhanced with corpus stats)
                numerator = idf * term_count * (k1 + 1)
                denominator = term_count + k1 * (1 - b + b * (doc_length / avg_doc_length))
                score += numerator / denominator
        
        return score
    
    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return scores
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            return {k: 0.5 for k in scores}
        
        normalized = {}
        for chunk_id, score in scores.items():
            normalized[chunk_id] = (score - min_score) / (max_score - min_score)
        
        return normalized
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        document_ids: Optional[List[int]] = None,
        task_id: Optional[int] = None,
        user=None,
    ) -> List[Dict]:
        """
        Perform hybrid search combining semantic and keyword-based ranking.
        
        Args:
            queryQuery text
            top_k: Number of top results to return
            min_score: Minimum combined score threshold
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            document_ids: Optional list of document IDs to filter
            task_id: Optional task ID to filter documents
            user: User object for RBAC
        
        Returns:
            List of result dicts with combined scores
        """
        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        semantic_weight /= total_weight
        keyword_weight /= total_weight
        
        # Get accessible documents
        accessible_docs = self._get_accessible_documents(user, document_ids, task_id)
        if not accessible_docs:
            return []
        
        # Perform semantic search
        semantic_results = self._semantic_search(query, accessible_docs, top_k * 2)
        
        # Perform keyword search
        query_terms = [term.strip() for term in re.split(r'\s+', query) if term.strip()]
        keyword_results = self._keyword_search(query_terms, accessible_docs, top_k * 2)
        
        # Combine results
        combined_scores: Dict[int, float] = {}
        chunk_data: Dict[int, Dict] = {}
        
        # Add semantic scores
        for result in semantic_results:
            chunk_id = result['chunk_id']
            combined_scores[chunk_id] = semantic_weight * result['score']
            chunk_data[chunk_id] = result
        
        # Add keyword scores
        for chunk_id, keyword_score in keyword_results.items():
            if chunk_id in combined_scores:
                combined_scores[chunk_id] += keyword_weight * keyword_score
            else:
                # If chunk not in semantic results, fetch it for keyword-only match
                try:
                    chunk = Chunk.objects.select_related('document').get(id=chunk_id)
                    combined_scores[chunk_id] = keyword_weight * keyword_score
                    chunk_data[chunk_id] = {
                        'chunk_id': chunk_id,
                        'document_id': chunk.document.id,
                        'filename': chunk.document.filename,
                        'chunk_index': chunk.chunk_index,
                        'text': chunk.chunk_text,
                        'token_count': chunk.token_count,
                        'uploaded_by': chunk.document.uploaded_by.username,
                        'score': keyword_score,
                    }
                except Chunk.DoesNotExist:
                    continue
        
        # Filter by threshold and sort
        results = []
        for chunk_id in sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True):
            score = combined_scores[chunk_id]
            if score >= min_score:
                result = chunk_data[chunk_id].copy()
                result['score'] = score
                result['semantic_score'] = result.get('score', 0)
                results.append(result)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def _semantic_search(self, query: str, document_ids: List[int], limit: int) -> List[Dict]:
        """Pure semantic search on accessible documents."""
        if self.embedding_service.index.ntotal == 0:
            return []
        
        query_embedding = self.embedding_service.generate_embedding(query)
        import numpy as np
        
        scores, indices = self.embedding_service.index.search(
            np.asarray([query_embedding], dtype=np.float32),
            min(limit, self.embedding_service.index.ntotal)
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            
            try:
                chunk = Chunk.objects.select_related('document').get(
                    document_id__in=document_ids
                ).order_by('id')[int(idx)]
                
                results.append({
                    'chunk_id': chunk.id,
                    'document_id': chunk.document.id,
                    'filename': chunk.document.filename,
                    'chunk_index': chunk.chunk_index,
                    'text': chunk.chunk_text,
                    'score': float(score),
                    'token_count': chunk.token_count,
                    'uploaded_by': chunk.document.uploaded_by.username,
                })
            except (Chunk.DoesNotExist, IndexError):
                continue
        
        return results
    
    def _keyword_search(self, query_terms: List[str], document_ids: List[int], limit: int) -> Dict[int, float]:
        """Keyword-based search using BM25-like scoring."""
        keyword_scores: Dict[int, float] = {}
        
        # Get chunks from accessible documents
        chunks = Chunk.objects.filter(
            document_id__in=document_ids
        ).values('id', 'chunk_text', 'token_count')[:limit]
        
        for chunk in chunks:
            bm25_score = self._bm25_score(query_terms, chunk['chunk_text'], chunk['token_count'])
            if bm25_score > 0:
                keyword_scores[chunk['id']] = bm25_score
        
        # Normalize scores to 0-1
        return self._normalize_scores(keyword_scores)
    
    def _get_accessible_documents(
        self,
        user,
        document_ids: Optional[List[int]] = None,
        task_id: Optional[int] = None,
    ) -> List[int]:
        """Get list of accessible document IDs based on RBAC and task filter."""
        if user is None:
            return []
        
        if user.role.role_name == 'admin':
            accessible = list(Document.objects.values_list('id', flat=True))
        else:
            # Regular users see their own + admin documents
            admin_role = None
            try:
                admin_role = user.role.__class__.objects.get(role_name='admin')
            except:
                pass
            
            query = Q(uploaded_by=user)
            if admin_role:
                query |= Q(uploaded_by__role=admin_role)
            
            accessible = list(Document.objects.filter(query).values_list('id', flat=True))
        
        # Further filter by provided document_ids
        if document_ids:
            accessible = list(set(accessible) & set(document_ids))
        
        # Filter by task if specified
        if task_id:
            task_doc_ids = TaskDocument.objects.filter(
                task_id=task_id
            ).values_list('document_id', flat=True)
            accessible = list(set(accessible) & set(task_doc_ids))
        
        return accessible


# Global instance
hybrid_search_service = HybridSearchService()
