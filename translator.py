"""
OpenAI translation module for subtitle translation using GPT-5
"""

import openai
import time
from typing import List, Dict, Optional, Tuple
import logging


def translate_with_openai(text_list: List[str], target_language: str, api_key: str, model: str = "gpt-5-mini") -> List[str]:
    """
    Translate a list of texts using GPT-5 Responses API
    
    Args:
        text_list (List[str]): List of text strings to translate
        target_language (str): Target language for translation
        api_key (str): OpenAI API key
        model (str): GPT-5 model to use (default: gpt-5-mini)
        
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
        
        # Individual translation for fastest results
        all_translations = []
        
        for i, text in enumerate(non_empty_texts):
            try:
                # Create individual translation request
                translated_text = _translate_single(client, text, target_language, model)
                all_translations.append(translated_text)
                
                # Very small delay to avoid overwhelming the API
                if i < len(non_empty_texts) - 1:
                    time.sleep(0.05)
                    
            except Exception as e:
                logging.error(f"Failed to translate text '{text}': {str(e)}")
                # Use original text if translation fails
                all_translations.append(text)
        
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
        # Use Chat Completions API with GPT-5 compatible parameters
        api_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional subtitle translator. Return only the translation, nothing else."
                },
                {
                    "role": "user", 
                    "content": f"Translate this subtitle to {target_language}: {text}"
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