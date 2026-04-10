"""Semantic search service that orchestrates chunking, embedding, and indexing."""

from typing import List, Dict, Optional
import pickle
import os
from pathlib import Path

from django.conf import settings
from app.models import Chunk, Document
from .embedding_service import embedding_service
from .chunking_service import chunking_service


class SearchService:
    """Unified service for semantic search on chunks."""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.chunking_service = chunking_service
        self.chunk_to_index_map = {}  # Maps chunk_id → FAISS index position
        self._load_chunk_map()
    
    def _load_chunk_map(self):
        """Load chunk-to-index mapping from disk."""
        chunk_map_path = Path(settings.FAISS_INDEX_PATH) / 'chunk_map.pkl'
        if os.path.exists(chunk_map_path):
            try:
                with open(chunk_map_path, 'rb') as f:
                    self.chunk_to_index_map = pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load chunk map: {e}")
                self.chunk_to_index_map = {}
    
    def _save_chunk_map(self):
        """Persist chunk-to-index mapping to disk."""
        chunk_map_path = Path(settings.FAISS_INDEX_PATH) / 'chunk_map.pkl'
        os.makedirs(chunk_map_path.parent, exist_ok=True)
        with open(chunk_map_path, 'wb') as f:
            pickle.dump(self.chunk_to_index_map, f)
    
    def index_document(self, document_id: int, text: str) -> int:
        """
        Index a document by chunking and generating embeddings.
        
        Args:
            document_id: ID of the document
            text: Full text of the document
        
        Returns:
            Number of chunks created
        """
        # Remove old chunks for this document
        chunks_to_delete = Chunk.objects.filter(document_id=document_id)
        old_chunk_ids = list(chunks_to_delete.values_list('id', flat=True))
        chunks_to_delete.delete()
        
        # Remove old embeddings from FAISS index
        for chunk_id in old_chunk_ids:
            if chunk_id in self.chunk_to_index_map:
                del self.chunk_to_index_map[chunk_id]
        
        # Chunk the document
        chunks = self.chunking_service.chunk_document(text)
        if not chunks:
            return 0
        
        # Create Chunk records and embeddings
        chunk_objects = []
        embeddings = []
        chunk_ids = []
        
        for chunk_data in chunks:
            chunk = Chunk(
                document_id=document_id,
                chunk_index=chunk_data['index'],
                chunk_text=chunk_data['text'],
                token_count=chunk_data['token_count'],
            )
            chunk_objects.append(chunk)
        
        # Bulk create chunks
        created_chunks = Chunk.objects.bulk_create(chunk_objects)
        
        # Generate embeddings for each chunk
        for chunk in created_chunks:
            embedding = self.embedding_service.generate_embedding(chunk.chunk_text)
            embeddings.append(embedding)
            chunk_ids.append(chunk.id)
        
        # Add embeddings to FAISS index
        if embeddings:
            import numpy as np
            self.embedding_service.index.add(
                np.asarray(embeddings, dtype=np.float32)
            )
            
            # Map chunk IDs to FAISS index positions
            start_idx = self.embedding_service.index.ntotal - len(chunk_ids)
            for i, chunk_id in enumerate(chunk_ids):
                self.chunk_to_index_map[chunk_id] = start_idx + i
        
        # Persist indexes
        self.embedding_service.save_index()
        self._save_chunk_map()
        
        return len(created_chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        document_ids: Optional[List[int]] = None,
        task_id: Optional[int] = None,
        user=None,
    ) -> List[Dict]:
        """
        Search for relevant chunks using semantic similarity with RBAC and task filtering.
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            min_score: Minimum similarity score (0-1)
            document_ids: Filter to specific documents (None = all accessible)
            task_id: Filter to documents associated with task
            user: User object for RBAC filtering
        
        Returns:
            List of dicts with chunk_id, document_id, text, score, etc.
        """
        if self.embedding_service.index.ntotal == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []
        
        import numpy as np
        try:
            # Search FAISS index
            scores, indices = self.embedding_service.index.search(
                np.asarray([query_embedding], dtype=np.float32),
                min(top_k * 2, self.embedding_service.index.ntotal)  # Fetch more to filter
            )
        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            return []
        
        # Determine accessible document IDs based on user role (RBAC) and task
        accessible_doc_ids = self._get_accessible_documents(user, document_ids, task_id)
        if not accessible_doc_ids:
            return []
        
        results = []
        seen_chunks = set()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            
            # Find chunk_id from index position
            chunk_id = None
            for cid, cidx in self.chunk_to_index_map.items():
                if cidx == int(idx):
                    chunk_id = cid
                    break
            
            if chunk_id is None or chunk_id in seen_chunks:
                continue
            
            seen_chunks.add(chunk_id)
            
            try:
                chunk = Chunk.objects.select_related('document').get(id=chunk_id)
                doc = chunk.document
                
                # Apply RBAC filter
                if doc.id not in accessible_doc_ids:
                    continue
                
                # Apply score threshold
                if float(score) < min_score:
                    continue
                
                results.append({
                    'chunk_id': chunk_id,
                    'document_id': doc.id,
                    'filename': doc.filename,
                    'chunk_index': chunk.chunk_index,
                    'text': chunk.chunk_text,
                    'score': float(score),
                    'token_count': chunk.token_count,
                    'uploaded_by': doc.uploaded_by.username,
                })
                
                if len(results) >= top_k:
                    break
            except Chunk.DoesNotExist:
                continue
            except Exception as e:
                print(f"Error processing search result: {e}")
                continue
        
        return results
    
    def _get_accessible_documents(self, user, document_ids: Optional[List[int]] = None, task_id: Optional[int] = None) -> List[int]:
        """
        Get list of document IDs accessible to user based on RBAC and task filter.
        
        Rules:
        - Admins can access all documents
        - Regular users can access documents uploaded by admins (public) or themselves
        - Task filter further restricts to documents linked to the task
        
        Args:
            user: User object or None
            document_ids: Optional list of specific document IDs to filter
            task_id: Optional task ID to filter documents
        
        Returns:
            List of accessible document IDs
        """
        if user is None:
            # No user = no access
            return []
        
        from django.db.models import Q
        
        if user.role.role_name == 'admin':
            # Admins see all documents
            accessible = list(Document.objects.values_list('id', flat=True))
        else:
            # Regular users see:
            # 1. Documents they uploaded
            # 2. Documents uploaded by admins (public)
            admin_role = None
            try:
                admin_role = user.role.__class__.objects.get(role_name='admin')
            except:
                pass
            
            query = Q(uploaded_by=user)  # User's own documents
            if admin_role:
                query |= Q(uploaded_by__role=admin_role)  # Admin-uploaded documents
            
            accessible = list(Document.objects.filter(query).values_list('id', flat=True))
        
        # Further filter by provided document_ids
        if document_ids:
            accessible = list(set(accessible) & set(document_ids))
        
        # Filter by task if specified
        if task_id:
            try:
                from app.models import TaskDocument
                task_doc_ids = set(TaskDocument.objects.filter(
                    task_id=task_id
                ).values_list('document_id', flat=True))
                accessible = list(set(accessible) & task_doc_ids)
            except Exception as e:
                print(f"Error filtering by task: {e}")
        
        return accessible
    
    def rebuild_search_index(self):
        """Rebuild complete search index from all documents."""
        # Clear existing index
        self.embedding_service.reset_index()
        self.chunk_to_index_map = {}
        
        # Process all documents
        for document in Document.objects.all().order_by('id'):
            self.index_document(document.id, document.content_text or '')
        
        print(f"✓ Search index rebuilt: {len(self.chunk_to_index_map)} chunks indexed")
    
    def delete_document_index(self, document_id: int) -> int:
        """
        Remove document chunks from search index.
        
        Args:
            document_id: ID of document to remove
        
        Returns:
            Number of chunks removed
        """
        chunks = Chunk.objects.filter(document_id=document_id)
        chunk_ids = list(chunks.values_list('id', flat=True))
        
        # Remove from chunk map
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_to_index_map:
                del self.chunk_to_index_map[chunk_id]
        
        # Note: FAISS index rebuild is needed for complete cleanup
        # For now, we just remove metadata
        self._save_chunk_map()
        
        return len(chunk_ids)


# Global instance
search_service = SearchService()
