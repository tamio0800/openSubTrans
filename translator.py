"""
OpenAI translation module for subtitle translation using GPT-5
"""

import openai
import time
import logging
from typing import List, Dict, Optional, Tuple
from prompts import SubtitlePrompts
from context_manager import ContextManager


def translate_with_openai(text_list: List[str], target_language: str, api_key: str, model: str = "gpt-5-mini", progress_callback=None, context_manager: ContextManager = None) -> List[str]:
    """
    Translate a list of texts using smart batch processing for better consistency
    
    This function automatically groups texts into batches of ~12 for improved dialogue
    coherence and efficiency, while maintaining proper nouns consistency.
    
    Args:
        text_list (List[str]): List of text strings to translate
        target_language (str): Target language for translation
        api_key (str): OpenAI API key
        model (str): GPT-5 model to use (default: gpt-5-mini)
        progress_callback (callable, optional): Function to call with progress updates (0.0 to 1.0)
        context_manager (ContextManager, optional): Context manager for terminology consistency
        
    Returns:
        List[str]: List of translated texts in the same order as input
        
    Raises:
        ValueError: If inputs are invalid
        OpenAI API exceptions: For API-related errors
    """
    
    # Input validation
    # Validate model is one of the supported GPT-5 models
    supported_models = ['gpt-5', 'gpt-5-mini']
    if model not in supported_models:
        raise ValueError(f"Only these GPT-5 models are supported: {supported_models}. Got: {model}")
    
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")
    
    if not target_language or not target_language.strip():
        raise ValueError("Target language cannot be empty")
    
    if not isinstance(text_list, list):
        raise ValueError("text_list must be a list")
    
    if not text_list:
        return []
    
    # Filter out empty strings but keep track of original positions
    non_empty_texts = []
    text_positions = []
    
    for i, text in enumerate(text_list):
        if text and text.strip():
            non_empty_texts.append(text.strip())
            text_positions.append(i)
    
    # If no non-empty texts, return list of empty strings
    if not non_empty_texts:
        return [""] * len(text_list)
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Smart batch translation for better consistency and efficiency
        all_translations = []
        batch_size = 12  # Optimal batch size for dialogue coherence
        
        # Get established terms for context-aware translation
        established_terms = {}
        if context_manager:
            established_terms = context_manager.get_established_terms()
        
        # Process texts in batches
        for i in range(0, len(non_empty_texts), batch_size):
            batch_texts = non_empty_texts[i:i + batch_size]
            
            try:
                # Translate the batch with context awareness
                batch_translations = _translate_batch(client, batch_texts, target_language, model, established_terms)
                all_translations.extend(batch_translations)
                
                # Update context manager with new translations if available
                if context_manager and batch_translations:
                    new_terms = context_manager.extract_terms_from_translation_pair(batch_texts, batch_translations)
                    if new_terms:
                        context_manager.update_terms(new_terms)
                        # Update established terms for next batch
                        established_terms.update(new_terms)
                
                # Update progress
                if progress_callback:
                    progress = min(1.0, (i + batch_size) / len(non_empty_texts))
                    progress_callback(progress)
                
                # Brief pause between batches to respect API limits
                if i + batch_size < len(non_empty_texts):
                    time.sleep(0.2)
                    
            except Exception as e:
                logging.error(f"Batch translation failed for batch starting at {i}: {str(e)}")
                # Fallback to individual translation for this batch
                for j, text in enumerate(batch_texts):
                    try:
                        translated_text = _translate_single(client, text, target_language, model)
                        all_translations.append(translated_text)
                    except Exception as single_e:
                        logging.error(f"Failed to translate text '{text}': {str(single_e)}")
                        all_translations.append(text)  # Use original text if all fails
                    
                    # Update progress even in fallback mode
                    if progress_callback:
                        current_completed = i + j + 1
                        progress = min(1.0, current_completed / len(non_empty_texts))
                        progress_callback(progress)
        
        # Reconstruct the full result list
        result = [""] * len(text_list)
        for i, translation in enumerate(all_translations):
            original_position = text_positions[i]
            result[original_position] = translation
        
        return result
        
    except openai.AuthenticationError as e:
        raise openai.AuthenticationError(f"Invalid API key: {str(e)}")
    except openai.RateLimitError as e:
        raise openai.RateLimitError(f"Rate limit exceeded: {str(e)}")
    except openai.APIError as e:
        raise openai.APIError(f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during translation: {str(e)}")


def _translate_single(client: openai.OpenAI, text: str, target_language: str, model: str) -> str:
    """
    Translate a single text using GPT-5 Responses API
    
    Args:
        client: OpenAI client instance
        text: Single text to translate
        target_language: Target language
        model: GPT-5 model to use
        
    Returns:
        Translated text
    """
    
    try:
        # Get prompts from centralized prompt manager
        prompts = SubtitlePrompts.get_single_translation_prompt(target_language)
        system_prompt = prompts["system"]
        user_prompt = prompts["user_template"].format(target_language=target_language, text=text)
        
        # Use Chat Completions API with GPT-5 compatible parameters
        api_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
            # GPT-5 models use default parameters only
        }
        
        # Make API call using Chat Completions API
        response = client.chat.completions.create(**api_params)
        
        # Parse response from Chat Completions API
        translated_content = response.choices[0].message.content.strip()
        
        # Return the translation or original text if empty
        return translated_content if translated_content else text
        
    except Exception as e:
        logging.error(f"Single translation failed: {str(e)}")
        return text  # Return original if translation fails


def _translate_batch(client: openai.OpenAI, texts: List[str], target_language: str, model: str, established_terms: Dict[str, str] = None) -> List[str]:
    """
    Translate multiple texts in a single batch for better consistency
    
    Args:
        client: OpenAI client instance
        texts: List of texts to translate
        target_language: Target language
        model: GPT-5 model to use
        established_terms: Dictionary of previously established term translations
        
    Returns:
        List of translated texts in the same order as input
    """
    
    try:
        # Create numbered batch for clear parsing
        numbered_texts = []
        for i, text in enumerate(texts, 1):
            numbered_texts.append(f"{i}. {text}")
        
        batch_content = "\n".join(numbered_texts)
        
        # Get prompts from centralized prompt manager (context-aware if terms available)
        if established_terms:
            prompts = SubtitlePrompts.get_context_aware_batch_prompt(target_language, established_terms)
        else:
            prompts = SubtitlePrompts.get_batch_translation_prompt(target_language)
        
        system_prompt = prompts["system"]
        user_prompt = prompts["user_template"].format(target_language=target_language, batch_content=batch_content)
        
        # Make batch API call
        api_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
        }
        
        response = client.chat.completions.create(**api_params)
        translated_content = response.choices[0].message.content.strip()
        
        # Parse the numbered response
        translations = _parse_batch_response(translated_content, len(texts))
        
        return translations
        
    except Exception as e:
        logging.error(f"Batch translation failed: {str(e)}")
        raise e


def _parse_batch_response(response_text: str, expected_count: int) -> List[str]:
    """
    Parse batch response from the API - handles both numbered and simple formats
    
    Args:
        response_text: The response from the API
        expected_count: Number of translations expected
        
    Returns:
        List of parsed translations
    """
    
    response_text = response_text.strip()
    
    # Handle single translation case (for backward compatibility with tests)
    if expected_count == 1:
        # If it's just a single response without numbering, return it as-is
        lines = response_text.split('\n')
        if len(lines) == 1 or not any(line.strip().startswith(('1.', '1)')) for line in lines):
            return [response_text]
    
    # Handle numbered batch format
    lines = response_text.split('\n')
    translations = []
    
    for i in range(1, expected_count + 1):
        found = False
        for line in lines:
            line = line.strip()
            # Look for numbered format like "1. translation" or "1) translation"
            if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                # Extract the translation part after the number and separator
                if '.' in line:
                    translation = line.split('.', 1)[1].strip()
                else:
                    translation = line.split(')', 1)[1].strip()
                translations.append(translation)
                found = True
                break
        
        if not found:
            # If numbered format not found, try line-by-line approach
            if i <= len(lines):
                line = lines[i-1].strip()
                # Remove any leading numbers if present
                if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                    if '.' in line:
                        translation = line.split('.', 1)[1].strip()
                    else:
                        translation = line.split(')', 1)[1].strip()
                    translations.append(translation)
                else:
                    translations.append(line)
                found = True
        
        if not found:
            translations.append(f"Translation {i} not found")
    
    # Ensure we have the right number of translations
    while len(translations) < expected_count:
        translations.append(f"Missing translation {len(translations) + 1}")
    
    return translations[:expected_count]


def translate_with_context_memory(text_list: List[str], target_language: str, api_key: str, model: str = "gpt-5-mini", progress_callback=None) -> Tuple[List[str], ContextManager]:
    """
    Convenience function for translation with automatic context memory management
    
    Args:
        text_list: List of texts to translate
        target_language: Target language for translation
        api_key: OpenAI API key
        model: GPT-5 model to use
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (translated_texts, context_manager)
    """
    context_manager = ContextManager()
    translated_texts = translate_with_openai(
        text_list, target_language, api_key, model, 
        progress_callback, context_manager
    )
    return translated_texts, context_manager


def estimate_translation_cost(text_list: List[str], target_language: str, model: str = "gpt-5-mini") -> Dict[str, any]:
    """
    Estimate the cost of translating given texts
    
    Args:
        text_list: List of texts to translate
        target_language: Target language
        model: GPT-5 model to use
        
    Returns:
        Dictionary with cost estimation details
    """
    
    if not text_list:
        return {
            "total_characters": 0,
            "estimated_input_tokens": 0,
            "estimated_output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "total_texts": 0,
            "model": model
        }
    
    # Calculate total characters for non-empty texts
    total_chars = sum(len(text) for text in text_list if text and text.strip())
    
    if total_chars == 0:
        return {
            "total_characters": 0,
            "estimated_input_tokens": 0,
            "estimated_output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "total_texts": 0,
            "model": model
        }
    
    # Rough estimation: 1 token ≈ 4 characters for English, 3 for others
    char_per_token = 4 if "english" in target_language.lower() else 3
    estimated_input_tokens = max(1, total_chars // char_per_token)
    estimated_output_tokens = estimated_input_tokens  # Assume similar length output
    
    # Get pricing for supported GPT-5 models (Updated January 2025)
    # Prices are per 1K tokens (converted from per million tokens)
    pricing_map = {
        "gpt-5": {"input": 0.00125, "output": 0.01},        # $1.25/$10.00 per million
        "gpt-5-mini": {"input": 0.00025, "output": 0.002},  # $0.25/$2.00 per million
    }
    
    # Get pricing for the specified model
    pricing = pricing_map.get(model, pricing_map["gpt-5-mini"])  # Default to mini if not found
    
    # Calculate costs (prices are per 1K tokens)
    input_cost = (estimated_input_tokens / 1000) * pricing["input"]
    output_cost = (estimated_output_tokens / 1000) * pricing["output"]
    total_cost = input_cost + output_cost
    
    # Ensure minimum cost for display purposes
    total_cost = max(total_cost, 0.000001)
    
    return {
        "total_characters": total_chars,
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_cost_usd": total_cost,
        "total_texts": len([t for t in text_list if t and t.strip()]),
        "model": model
    }