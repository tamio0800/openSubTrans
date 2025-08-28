#!/usr/bin/env python3
"""
Real-world test of GPT-5 translation functionality
This script uses actual OpenAI API to test translation
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srt_processor import parse_srt_file, create_srt_output, validate_srt_content
from translator import translate_with_openai, estimate_translation_cost


def test_real_translation():
    """Test actual translation with OpenAI API"""
    
    print("🧪 Testing Real OpenAI Translation")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('OPENAI_APIKEY')
    if not api_key:
        print("❌ No OPENAI_APIKEY environment variable found!")
        print("Please set it with: export OPENAI_APIKEY='your-api-key-here'")
        return False
    
    print(f"✅ API Key found: {api_key[:7]}...")
    
    # Load sample subtitle file
    try:
        with open('tests/sample_subtitle.srt', 'r', encoding='utf-8') as f:
            srt_content = f.read()
        print("✅ Sample subtitle file loaded")
    except FileNotFoundError:
        print("❌ Sample subtitle file not found at tests/sample_subtitle.srt")
        return False
    
    # Validate and parse SRT
    if not validate_srt_content(srt_content):
        print("❌ Invalid SRT format")
        return False
    
    parsed_entries = parse_srt_file(srt_content)
    print(f"✅ Parsed {len(parsed_entries)} subtitle entries")
    
    # Show original subtitles
    print("\n📄 Original Subtitles:")
    print("-" * 30)
    for i, (start, end, text) in enumerate(parsed_entries[:3], 1):
        print(f"{i}. {start} → {end}")
        print(f"   {text}")
    if len(parsed_entries) > 3:
        print(f"   ... and {len(parsed_entries) - 3} more entries")
    
    # Extract just the text for translation
    texts_to_translate = [entry[2] for entry in parsed_entries]
    
    # Test cost estimation first
    print("\n💰 Cost Estimation:")
    print("-" * 30)
    target_language = "Chinese (Traditional)"
    model = "gpt-5-mini"  # Use supported GPT-5 model
    cost_info = estimate_translation_cost(texts_to_translate, target_language, model)
    
    print(f"Total characters: {cost_info['total_characters']}")
    print(f"Estimated input tokens: {cost_info['estimated_input_tokens']}")
    print(f"Estimated output tokens: {cost_info['estimated_output_tokens']}")
    print(f"Estimated cost: ${cost_info['estimated_cost_usd']:.6f} USD")
    print(f"Model: {cost_info['model']}")
    
    # Ask for confirmation
    print(f"\n🤔 Proceed with translation to {target_language}?")
    print(f"   Estimated cost: ${cost_info['estimated_cost_usd']:.6f} USD")
    
    # For automated testing, we'll translate just the first 2 entries to minimize cost
    print("🚀 Proceeding with translation of first 2 entries (to minimize cost)...")
    test_texts = texts_to_translate[:2]
    
    try:
        print(f"\n⏳ Translating using {model}...")
        translated_texts = translate_with_openai(test_texts, target_language, api_key, model)
        
        print("✅ Translation completed!")
        
        # Show results
        print(f"\n🔄 Translation Results ({target_language}):")
        print("-" * 50)
        
        for i, (original, translated) in enumerate(zip(test_texts, translated_texts), 1):
            start, end, _ = parsed_entries[i-1]
            print(f"{i}. {start} → {end}")
            print(f"   Original:  {original}")
            print(f"   Translated: {translated}")
            print()
        
        # Create translated SRT for the test entries
        translated_entries = []
        for i, translated_text in enumerate(translated_texts):
            start, end, _ = parsed_entries[i]
            translated_entries.append((start, end, translated_text))
        
        # Add remaining entries as-is for completeness
        for i in range(len(translated_texts), len(parsed_entries)):
            translated_entries.append(parsed_entries[i])
        
        translated_srt = create_srt_output(translated_entries)
        
        # Save translated file
        output_filename = f"tests/translated_sample_{target_language.replace(' ', '_').replace('(', '').replace(')', '').lower()}.srt"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(translated_srt)
        
        print(f"💾 Translated SRT saved to: {output_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Translation failed: {str(e)}")
        return False


def test_different_languages():
    """Test translation to different languages with small samples"""
    
    print("\n\n🌍 Testing Multiple Languages")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_APIKEY')
    if not api_key:
        print("❌ No API key available")
        return False
    
    # Test with just one simple sentence to minimize cost
    test_text = ["Hello, welcome to our translation service!"]
    
    languages = [
        "Chinese (Traditional)",
        "Japanese", 
        "Korean",
        "Spanish"
    ]
    
    for lang in languages:
        try:
            print(f"\n🔄 Testing {lang}...")
            model = "gpt-5-mini"  # Use supported GPT-5 model
            cost_info = estimate_translation_cost(test_text, lang, model)
            print(f"   Estimated cost: ${cost_info['estimated_cost_usd']:.6f} USD (using {model})")
            
            translated = translate_with_openai(test_text, lang, api_key, model)
            print(f"   Original: {test_text[0]}")
            print(f"   {lang}: {translated[0]}")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
    
    return True


def main():
    """Run all real translation tests"""
    print("🚀 OpenSubTrans Real Translation Testing")
    print("=" * 60)
    print("This script will use actual OpenAI API calls")
    print("Make sure OPENAI_APIKEY environment variable is set")
    print("=" * 60)
    
    success = True
    
    # Test main translation functionality
    if not test_real_translation():
        success = False
    
    # Test multiple languages (comment out to save API costs)
    print("\n" + "="*60)
    print("🔄 Want to test multiple languages? (This will use more API calls)")
    print("Uncommenting the line below will test 4 different languages...")
    # if not test_different_languages():
    #     success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 All real translation tests completed successfully!")
        print("✅ The translation system is working with actual OpenAI API")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
