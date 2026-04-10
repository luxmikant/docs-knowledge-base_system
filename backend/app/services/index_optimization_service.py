"""Optimized index update service with batch processing and caching."""

import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
from queue import Queue

from django.conf import settings
from app.models import Document, Chunk


class IndexUpdateQueue:
    """Thread-safe queue for batch index updates."""
    
    def __init__(self, batch_size: int = 50, flush_interval: int = 60):
        """
        Initialize update queue.
        
        Args:
            batch_size: Number of documents to accumulate before processing
            flush_interval: Seconds to wait before flushing partial batch
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.pending_updates: Dict[int, str] = {}
        self.last_flush = datetime.now()
        self._processing = False
        self._lock = threading.Lock()
    
    def add_update(self, document_id: int, text: str) -> None:
        """Add document for indexing."""
        with self._lock:
            self.pending_updates[document_id] = text
            
            if len(self.pending_updates) >= self.batch_size:
                self._flush()
    
    def _flush(self) -> None:
        """Flush pending updates to queue."""
        if self.pending_updates:
            self.queue.put(dict(self.pending_updates))
            self.pending_updates.clear()
            self.last_flush = datetime.now()
    
    def get_pending_batch(self, timeout: Optional[float] = None) -> Optional[Dict[int, str]]:
        """Get next batch of updates to process."""
        try:
            return self.queue.get(timeout=timeout)
        except:
            return None


class IndexOptimizationService:
    """Optimized batch indexing and incremental updates."""
    
    def __init__(self):
        from .search_service import search_service
        self.search_service = search_service
        self.update_queue = IndexUpdateQueue(batch_size=50)
        self._index_cache = {}  # Cache for frequently accessed index positions
        self._cache_hits = 0
        self._cache_misses = 0
    
    def batch_index_documents(self, document_ids: List[int], force_rebuild: bool = False) -> Dict:
        """
        Efficiently index multiple documents in batch.
        
        Args:
            document_ids: List of document IDs to index
            force_rebuild: Whether to force full index rebuild
        
        Returns:
            Stats dict with processing info
        """
        start_time = time.time()
        indexed_count = 0
        error_count = 0
        total_chunks = 0
        
        # Fetch documents efficiently
        documents = Document.objects.filter(id__in=document_ids).only(
            'id', 'content_text'
        )
        
        # Process in batches
        CHUNK_SIZE = 10
        for i in range(0, len(document_ids), CHUNK_SIZE):
            batch_ids = document_ids[i:i + CHUNK_SIZE]
            
            for doc in documents.filter(id__in=batch_ids):
                if not doc.content_text:
                    error_count += 1
                    continue
                
                try:
                    chunks_created = self.search_service.index_document(
                        doc.id, doc.content_text
                    )
                    indexed_count += 1
                    total_chunks += chunks_created
                except Exception as e:
                    print(f"Error indexing document {doc.id}: {e}")
                    error_count += 1
        
        elapsed = time.time() - start_time
        
        return {
            'indexed_documents': indexed_count,
            'failed_documents': error_count,
            'total_chunks': total_chunks,
            'processing_time_seconds': round(elapsed, 2),
            'documents_per_second': round(indexed_count / elapsed, 2) if elapsed > 0 else 0,
        }
    
    def incremental_index_update(self, document_id: int, text: str) -> bool:
        """
        Efficiently update index for a single document (incremental).
        
        Args:
            document_id: Document ID to update
            text: Updated document text
        
        Returns:
            True if successful
        """
        try:
            # Remove old chunks and index new ones
            self.search_service.index_document(document_id, text)
            
            # Invalidate cache for this document
            self._invalidate_cache(document_id)
            
            return True
        except Exception as e:
            print(f"Error updating document {document_id}: {e}")
            return False
    
    def optimize_index_structure(self) -> Dict:
        """
        Optimize FAISS index structure and remove orphaned entries.
        
        Returns:
            Optimization stats
        """
        start_time = time.time()
        
        try:
            # Get valid chunk IDs
            valid_chunk_ids = set(
                Chunk.objects.values_list('id', flat=True)
            )
            
            # Remove orphaned entries from chunk_to_index_map
            orphaned = 0
            for chunk_id in list(self.search_service.chunk_to_index_map.keys()):
                if chunk_id not in valid_chunk_ids:
                    del self.search_service.chunk_to_index_map[chunk_id]
                    orphaned += 1
            
            # Save optimized index
            self.search_service._save_chunk_map()
            
            elapsed = time.time() - start_time
            
            return {
                'orphaned_entries_removed': orphaned,
                'valid_chunks': len(valid_chunk_ids),
                'optimization_time_seconds': round(elapsed, 2),
            }
        except Exception as e:
            print(f"Error optimizing index: {e}")
            return {'error': str(e)}
    
    def get_index_stats(self) -> Dict:
        """Get statistics about current index."""
        try:
            chunk_count = Chunk.objects.count()
            doc_count = Document.objects.count()
            index_size = self.search_service.index.ntotal if hasattr(self.search_service.index, 'ntotal') else 0
            
            return {
                'total_documents': doc_count,
                'total_chunks': chunk_count,
                'indexed_vectors': index_size,
                'chunk_map_entries': len(self.search_service.chunk_to_index_map),
                'cache_hit_rate': round(
                    self._cache_hits / (self._cache_hits + self._cache_misses + 1) * 100, 2
                ) if (self._cache_hits + self._cache_misses) > 0 else 0,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _invalidate_cache(self, document_id: int) -> None:
        """Invalidate cache entries for a document."""
        # Remove cache entries related to this document
        keys_to_remove = [k for k in self._index_cache.keys() if k.get('doc_id') == document_id]
        for key in keys_to_remove:
            del self._index_cache[key]
    
    def clear_cache(self) -> None:
        """Clear entire index cache."""
        self._index_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


# Global instance
index_optimization_service = IndexOptimizationService()
