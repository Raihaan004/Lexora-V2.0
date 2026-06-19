from typing import List

class ChunkerService:
    """Service to handle document chunking recursively preserving sentence context."""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Delimiters tried in order of preference to preserve text structure
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        Main interface to partition document text into overlapping segments.
        
        Args:
            text: Clean extracted text string.
            
        Returns:
            chunks: List of structured text strings.
        """
        if not text or not text.strip():
            return []
        return self._recursive_split(text.strip(), self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Recursively splits text until chunks fit within chunk_size constraints."""
        if not separators:
            # If no separators left, hard split on character size with overlap
            chunks = []
            start = 0
            while start < len(text):
                chunks.append(text[start:start + self.chunk_size])
                start += self.chunk_size - self.chunk_overlap
                # Exit if the remaining string is too small to split
                if len(text) - start <= self.chunk_overlap:
                    break
            return chunks

        separator = separators[0]
        next_separators = separators[1:]
        
        # Split text by separator
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)
            
        final_splits = []
        for s in splits:
            if not s:
                continue
            if len(s) <= self.chunk_size:
                final_splits.append(s)
            else:
                # Recursively split the long segment
                final_splits.extend(self._recursive_split(s, next_separators))
                
        # Merge individual splits to form chunks that approach chunk_size
        return self._merge_splits(final_splits, separator)

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """Combines split blocks while keeping sizes <= chunk_size and adding overlaps."""
        chunks = []
        current_chunk = []
        current_len = 0
        
        for s in splits:
            s_len = len(s)
            # If a single split block exceeds chunk_size, output it directly
            if s_len > self.chunk_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                chunks.append(s)
                continue
                
            separator_len = len(separator) if current_len > 0 else 0
            if current_len + separator_len + s_len <= self.chunk_size:
                current_chunk.append(s)
                current_len += separator_len + s_len
            else:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                
                # Rollback current list to form the overlap for the next chunk
                overlap_chunk = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    item_sep_len = len(separator) if overlap_len > 0 else 0
                    if overlap_len + item_sep_len + len(item) <= self.chunk_overlap:
                        overlap_chunk.insert(0, item)
                        overlap_len += item_sep_len + len(item)
                    else:
                        break
                
                current_chunk = overlap_chunk + [s]
                current_len = overlap_len + (len(separator) if overlap_len > 0 else 0) + s_len
                
        if current_chunk:
            chunks.append(separator.join(current_chunk))
            
        # Clean double spaces or empty string elements from returned list
        return [c.strip() for c in chunks if c.strip()]

chunker_service = ChunkerService()
