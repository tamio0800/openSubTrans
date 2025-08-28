"""
Context Memory Manager for Subtitle Translation

Manages terminology consistency across translation batches to ensure
proper nouns, character names, and places are translated consistently.
"""

import re
from typing import Dict, List, Tuple
from collections import Counter


class ContextManager:
    """
    Manages translation context and terminology consistency across batches
    """
    
    def __init__(self):
        """Initialize the context manager"""
        self.established_terms: Dict[str, str] = {}  # original -> translation
        self.term_confidence: Dict[str, int] = {}    # original -> confidence_score
        self.batch_history: List[Dict[str, str]] = []  # history of batch terms
        
    def extract_potential_terms(self, texts: List[str]) -> List[str]:
        """
        Extract potential proper nouns and important terms from text list
        
        Args:
            texts: List of subtitle texts
            
        Returns:
            List of potential terms (proper nouns, names, places)
        """
        potential_terms = set()
        
        for text in texts:
            # Extract capitalized words (potential proper nouns)
            capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]{1,}(?:\s+[A-Z][a-zA-Z]*)*\b', text)
            
            for word in capitalized_words:
                # Filter out common sentence starters and short words
                if len(word) >= 2 and not self._is_common_word(word):
                    potential_terms.add(word.strip())
        
        # Count frequency to identify most important terms
        term_counter = Counter()
        for text in texts:
            for term in potential_terms:
                if term in text:
                    term_counter[term] += 1
        
        # Return terms that appear more than once or are likely names
        important_terms = []
        for term, count in term_counter.items():
            if count > 1 or self._is_likely_proper_noun(term):
                important_terms.append(term)
        
        return sorted(important_terms)
    
    def _is_common_word(self, word: str) -> bool:
        """Check if word is a common English word that shouldn't be treated as proper noun"""
        common_words = {
            'I', 'The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 
            'Who', 'Why', 'How', 'Yes', 'No', 'Ok', 'Okay', 'Well', 'So', 'But',
            'And', 'Or', 'If', 'Then', 'Now', 'Here', 'There', 'Come', 'Go',
            'Get', 'Take', 'Give', 'Make', 'Let', 'See', 'Look', 'Good', 'Bad'
        }
        return word in common_words
    
    def _is_likely_proper_noun(self, word: str) -> bool:
        """Check if word is likely a proper noun based on patterns"""
        # Check for name-like patterns
        name_patterns = [
            r'^[A-Z][a-z]+$',  # Simple names like "John", "Mary"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Full names like "John Smith"
            r'^Dr\.|^Mr\.|^Mrs\.|^Ms\.', # Titles
        ]
        
        for pattern in name_patterns:
            if re.match(pattern, word):
                return True
        
        # Check if it contains multiple capital letters (like place names)
        capital_count = sum(1 for c in word if c.isupper())
        if capital_count >= 2 and len(word) >= 4:
            return True
            
        return False
    
    def extract_terms_from_translation_pair(self, original_texts: List[str], translated_texts: List[str]) -> Dict[str, str]:
        """
        Extract term mappings from original and translated text pairs
        
        Args:
            original_texts: Original subtitle texts
            translated_texts: Translated subtitle texts
            
        Returns:
            Dictionary mapping original terms to their translations
        """
        if len(original_texts) != len(translated_texts):
            return {}
        
        potential_terms = self.extract_potential_terms(original_texts)
        term_mappings = {}
        
        for original_term in potential_terms:
            # Find which subtitle contains this term
            for i, original_text in enumerate(original_texts):
                if original_term in original_text:
                    translated_text = translated_texts[i]
                    
                    # Simple heuristic: look for the most frequent non-English characters
                    # This is a simplified approach - could be enhanced with NLP
                    translated_candidates = self._extract_translated_candidates(translated_text)
                    
                    if translated_candidates:
                        # Take the first candidate that looks like a proper noun translation
                        for candidate in translated_candidates:
                            if self._is_valid_translation_candidate(candidate):
                                term_mappings[original_term] = candidate
                                break
                    break
        
        return term_mappings
    
    def _extract_translated_candidates(self, translated_text: str) -> List[str]:
        """Extract potential translated proper nouns from translated text"""
        # Look for sequences of non-ASCII characters (likely translated names)
        candidates = []
        
        # Pattern for Chinese/Japanese/Korean characters
        asian_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+'
        asian_matches = re.findall(asian_pattern, translated_text)
        candidates.extend(asian_matches)
        
        # Pattern for other non-ASCII characters (European names, etc.)
        other_pattern = r'[^\x00-\x7f]+'
        other_matches = re.findall(other_pattern, translated_text)
        candidates.extend(other_matches)
        
        # Also look for capitalized words that might be transliterated names
        cap_pattern = r'\b[A-Z][a-zA-Z]{1,}\b'
        cap_matches = re.findall(cap_pattern, translated_text)
        candidates.extend(cap_matches)
        
        return list(set(candidates))  # Remove duplicates
    
    def _is_valid_translation_candidate(self, candidate: str) -> bool:
        """Check if candidate is a valid translation of a proper noun"""
        # Basic validation - length and character types
        if len(candidate) < 1 or len(candidate) > 20:
            return False
        
        # Should not be just punctuation or numbers
        if re.match(r'^[^\w]+$', candidate):
            return False
            
        return True
    
    def update_terms(self, new_terms: Dict[str, str]) -> None:
        """
        Update the established terms with new translations
        
        Args:
            new_terms: Dictionary of original -> translation mappings
        """
        for original, translation in new_terms.items():
            if original in self.established_terms:
                # If we already have this term, increase confidence
                self.term_confidence[original] = self.term_confidence.get(original, 0) + 1
            else:
                # New term
                self.established_terms[original] = translation
                self.term_confidence[original] = 1
        
        # Store batch history
        if new_terms:
            self.batch_history.append(new_terms.copy())
    
    def get_established_terms(self, min_confidence: int = 1) -> Dict[str, str]:
        """
        Get established terms with at least the specified confidence level
        
        Args:
            min_confidence: Minimum confidence score to include term
            
        Returns:
            Dictionary of established term mappings
        """
        return {
            original: translation 
            for original, translation in self.established_terms.items()
            if self.term_confidence.get(original, 0) >= min_confidence
        }
    
    def get_context_summary(self) -> Dict:
        """Get a summary of the current context state"""
        return {
            'total_terms': len(self.established_terms),
            'high_confidence_terms': len(self.get_established_terms(min_confidence=2)),
            'batches_processed': len(self.batch_history),
            'established_terms': self.established_terms.copy()
        }
    
    def reset_context(self) -> None:
        """Reset the context manager to initial state"""
        self.established_terms.clear()
        self.term_confidence.clear()
        self.batch_history.clear()


# Utility functions for easy access
def create_context_manager() -> ContextManager:
    """Create a new context manager instance"""
    return ContextManager()


def extract_terms_from_subtitles(subtitles: List[str]) -> List[str]:
    """
    Quick utility to extract potential terms from subtitles
    
    Args:
        subtitles: List of subtitle texts
        
    Returns:
        List of potential proper nouns and terms
    """
    manager = ContextManager()
    return manager.extract_potential_terms(subtitles)
