"""Document chunking service for semantic search."""

import re
from typing import List, Tuple

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class ChunkingService:
    """Service for splitting documents into overlapping chunks."""
    
    # Configurable chunking parameters
    CHUNK_SIZE_TOKENS = 400  # Target chunk size in tokens
    OVERLAP_TOKENS = 75      # Number of tokens to overlap between chunks
    MIN_CHUNK_TOKENS = 50    # Minimum tokens per chunk to avoid too-small chunks
    
    def __init__(self):
        """Initialize tokenizer for accurate token counting."""
        self.tokenizer = None
        self._init_tokenizer()
    
    def _init_tokenizer(self):
        """Initialize tiktoken tokenizer for GPT models."""
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self.tokenizer = None
        
        if self.tokenizer is None and not TIKTOKEN_AVAILABLE:
            print("Warning: tiktoken not installed. Using approximate token counting.")
    
    def count_tokens(self, text: str) -> int:
        """Count approximate number of tokens in text."""
        if self.tokenizer is not None:
            return len(self.tokenizer.encode(text))
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return max(1, len(text) // 4)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        # Simple sentence splitting (can be improved with spaCy for production)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_sentence_boundary(self, text: str, target_tokens: int) -> int:
        """Find a good sentence boundary near target token count."""
        sentences = self._split_into_sentences(text)
        if not sentences:
            return len(text)
        
        accumulated_length = 0
        accumulated_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If we've exceeded target, use previous position
            if accumulated_tokens + sentence_tokens > target_tokens:
                return accumulated_length
            
            accumulated_length += len(sentence) + 1  # +1 for space
            accumulated_tokens += sentence_tokens
        
        return len(text)
    
    def chunk_document(self, text: str) -> List[dict]:
        """
        Split document into overlapping chunks.
        
        Args:
            text: Full document text
        
        Returns:
            List of dicts with 'text' and 'token_count' keys
        """
        if not text or not text.strip():
            return []
        
        chunks_data = []
        remaining_text = text.strip()
        overlap_text = ""  # Overlap from previous chunk
        chunk_index = 0
        
        while remaining_text:
            # Combine overlap with new content
            working_text = overlap_text + remaining_text
            working_tokens = self.count_tokens(working_text)
            
            # If entire text fits, use it as final chunk
            if working_tokens <= self.CHUNK_SIZE_TOKENS:
                if self.count_tokens(working_text.strip()) >= self.MIN_CHUNK_TOKENS:
                    chunks_data.append({
                        'text': working_text.strip(),
                        'token_count': self.count_tokens(working_text.strip()),
                        'index': chunk_index,
                    })
                    chunk_index += 1
                break
            
            # Find sentence boundary near target token count
            target_length = self._find_sentence_boundary(
                working_text, 
                self.CHUNK_SIZE_TOKENS
            )
            
            # Use at least CHUNK_SIZE_TOKENS worth if possible
            if target_length < len(overlap_text) + 100:  # Prevent too-small chunks
                target_length = min(
                    len(working_text),
                    len(overlap_text) + int(len(remaining_text) * 0.5)
                )
            
            chunk_text = working_text[:target_length].rstrip()
            
            if not chunk_text.strip():
                # Fallback: take a fixed-size slice if boundary detection fails
                chunk_text = working_text[:min(1000, len(working_text))]
            
            chunk_text = chunk_text.strip()
            chunk_tokens = self.count_tokens(chunk_text)
            
            if chunk_tokens >= self.MIN_CHUNK_TOKENS:
                chunks_data.append({
                    'text': chunk_text,
                    'token_count': chunk_tokens,
                    'index': chunk_index,
                })
                chunk_index += 1
            
            # Calculate overlap for next chunk
            overlap_boundary = max(
                len(chunk_text) - sum(
                    len(s) + 1
                    for s in self._split_into_sentences(chunk_text)[-2:]
                ),
                len(chunk_text) // 2,
            )
            overlap_text = chunk_text[overlap_boundary:].strip()
            remaining_text = working_text[target_length:].strip()
        
        return chunks_data
    
    def chunk_documents_batch(self, documents: List[Tuple[int, str]]) -> List[dict]:
        """
        Chunk multiple documents efficiently.
        
        Args:
            documents: List of (document_id, text) tuples
        
        Returns:
            List of dicts with 'document_id', 'chunk_index', 'text', 'token_count'
        """
        all_chunks = []
        
        for doc_id, text in documents:
            chunks = self.chunk_document(text)
            for chunk_data in chunks:
                all_chunks.append({
                    'document_id': doc_id,
                    'chunk_index': chunk_data['index'],
                    'text': chunk_data['text'],
                    'token_count': chunk_data['token_count'],
                })
        
        return all_chunks


# Global instance
chunking_service = ChunkingService()
