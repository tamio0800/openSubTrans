"""
Subtitle Translation Prompts Module

Centralized management of all translation prompts for consistency and maintainability.
"""

from typing import Dict, Any


class SubtitlePrompts:
    """Manages all subtitle translation prompts"""
    
    @staticmethod
    def get_base_system_rules(target_language: str) -> str:
        """
        Get the core translation rules that apply to all translation tasks
        
        Args:
            target_language: Target language for translation
            
        Returns:
            Core system prompt rules
        """
        return f"""Transform movie subtitles into {target_language} that sounds like locals naturally speaking.

ESSENTIAL RULES:
1. Use everyday speech patterns - how people really talk
2. Match the speaker's personality (casual/formal/young/old)
3. Keep names and places consistent throughout
4. Sound natural when spoken aloud
5. Use colloquial expressions native speakers actually use

AVOID: Textbook language, overly formal phrases, awkward literal translations

Make it sound so natural that {target_language} speakers would think it was originally written in their language."""

    @staticmethod
    def get_single_translation_prompt(target_language: str) -> Dict[str, str]:
        """
        Get prompts for single subtitle translation
        
        Args:
            target_language: Target language for translation
            
        Returns:
            Dictionary with 'system' and 'user_template' prompts
        """
        system_prompt = SubtitlePrompts.get_base_system_rules(target_language)
        system_prompt += "\n\nReturn ONLY the translation - no explanations."
        
        user_template = "Translate this movie subtitle to {target_language}:\n\n{text}"
        
        return {
            "system": system_prompt,
            "user_template": user_template
        }
    
    @staticmethod
    def get_batch_translation_prompt(target_language: str) -> Dict[str, str]:
        """
        Get prompts for batch subtitle translation
        
        Args:
            target_language: Target language for translation
            
        Returns:
            Dictionary with 'system' and 'user_template' prompts
        """
        system_prompt = SubtitlePrompts.get_base_system_rules(target_language)
        
        # Add batch-specific instructions
        batch_instructions = """

BATCH PROCESSING RULES:
- Maintain dialogue flow and consistency across all subtitles
- Keep character personalities consistent throughout the batch
- Preserve context and relationships between consecutive subtitles

FORMAT REQUIREMENTS:
- Return each translation on a separate line with the same numbering (1. 2. 3. etc.)
- Maintain the exact numbering format provided in the input"""
        
        system_prompt += batch_instructions
        
        user_template = "Translate these consecutive movie subtitles to {target_language}:\n\n{batch_content}"
        
        return {
            "system": system_prompt,
            "user_template": user_template
        }
    
    @staticmethod
    def get_context_aware_batch_prompt(target_language: str, established_terms: Dict[str, str] = None) -> Dict[str, str]:
        """
        Get prompts for context-aware batch translation (for Step 3)
        
        Args:
            target_language: Target language for translation
            established_terms: Dictionary of previously established term translations
            
        Returns:
            Dictionary with 'system' and 'user_template' prompts
        """
        system_prompt = SubtitlePrompts.get_base_system_rules(target_language)
        
        # Add context-aware instructions
        context_instructions = """

CONTEXT-AWARE TRANSLATION:
- Maintain dialogue flow and consistency across all subtitles
- Keep character personalities consistent throughout the batch
- Preserve context and relationships between consecutive subtitles"""
        
        # Add established terms if provided
        if established_terms:
            terms_list = [f"- {original} → {translation}" for original, translation in established_terms.items()]
            context_instructions += f"""

ESTABLISHED TRANSLATIONS (use these exact translations):
{chr(10).join(terms_list)}"""
        
        context_instructions += """

FORMAT REQUIREMENTS:
- Return each translation on a separate line with the same numbering (1. 2. 3. etc.)
- Maintain the exact numbering format provided in the input"""
        
        system_prompt += context_instructions
        
        user_template = "Translate these consecutive movie subtitles to {target_language}, maintaining consistency with previously established terms:\n\n{batch_content}"
        
        return {
            "system": system_prompt,
            "user_template": user_template
        }


# Convenience functions for backward compatibility
def get_single_prompt(target_language: str) -> Dict[str, str]:
    """Get single translation prompt"""
    return SubtitlePrompts.get_single_translation_prompt(target_language)


def get_batch_prompt(target_language: str) -> Dict[str, str]:
    """Get batch translation prompt"""
    return SubtitlePrompts.get_batch_translation_prompt(target_language)


def get_context_prompt(target_language: str, established_terms: Dict[str, str] = None) -> Dict[str, str]:
    """Get context-aware batch translation prompt"""
    return SubtitlePrompts.get_context_aware_batch_prompt(target_language, established_terms)
