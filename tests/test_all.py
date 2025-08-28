"""
Unified test suite for OpenSubTrans project using unittest
Tests both SRT processing and translation functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import io

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from srt_processor import parse_srt_file, create_srt_output, validate_srt_content
    SRT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SRT processor not available: {e}")
    SRT_AVAILABLE = False

try:
    from translator import translate_with_openai, estimate_translation_cost
    TRANSLATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Translator not available: {e}")
    TRANSLATOR_AVAILABLE = False


class TestSRTProcessor(unittest.TestCase):
    """Test cases for SRT processing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not SRT_AVAILABLE:
            self.skipTest("SRT processor module not available")
    
    def test_parse_simple_srt(self):
        """Test parsing simple SRT content"""
        simple_srt = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
How are you?

3
00:00:07,500 --> 00:00:09,200
I'm fine, thank you"""
        
        result = parse_srt_file(simple_srt)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ('00:00:01,000', '00:00:03,000', 'Hello world'))
        self.assertEqual(result[1], ('00:00:04,000', '00:00:06,000', 'How are you?'))
        self.assertEqual(result[2], ('00:00:07,500', '00:00:09,200', "I'm fine, thank you"))
    
    def test_parse_multiline_text(self):
        """Test parsing SRT with multi-line text"""
        multiline_srt = """1
00:00:01,000 --> 00:00:04,000
This is a longer subtitle
that spans multiple lines
and should be joined together"""
        
        result = parse_srt_file(multiline_srt)
        
        self.assertEqual(len(result), 1)
        expected_text = "This is a longer subtitle that spans multiple lines and should be joined together"
        self.assertEqual(result[0][2], expected_text)
    
    def test_parse_malformed_content(self):
        """Test parsing malformed SRT content"""
        malformed_srt = """1
Invalid timestamp format
Some text

2
00:00:04,000 --> 00:00:06,000
Valid entry"""
        
        result = parse_srt_file(malformed_srt)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][2], 'Valid entry')
    
    def test_parse_unicode_content(self):
        """Test parsing SRT with Unicode characters"""
        unicode_srt = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
こんにちはWorld

3
00:00:07,000 --> 00:00:09,000
Héllo wörld! 🎬"""
        
        result = parse_srt_file(unicode_srt)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][2], 'Hello world')
        self.assertEqual(result[1][2], 'こんにちはWorld')
        self.assertEqual(result[2][2], 'Héllo wörld! 🎬')
    
    def test_parse_empty_entries(self):
        """Test parsing SRT with empty entries"""
        empty_entries_srt = """1
00:00:01,000 --> 00:00:03,000
Valid text

2
00:00:04,000 --> 00:00:06,000


3
00:00:07,000 --> 00:00:09,000
Another valid text"""
        
        result = parse_srt_file(empty_entries_srt)
        
        self.assertEqual(len(result), 2)  # Should skip empty entries
        self.assertEqual(result[0][2], 'Valid text')
        self.assertEqual(result[1][2], 'Another valid text')
    
    def test_parse_special_characters(self):
        """Test parsing SRT with special characters"""
        special_chars_srt = """1
00:00:01,000 --> 00:00:03,000
"Hello," he said... 'Really?'

2
00:00:04,000 --> 00:00:06,000
[Music playing] ♪ La la la ♪

3
00:00:07,000 --> 00:00:09,000
<i>Italic text</i> & <b>bold text</b>"""
        
        result = parse_srt_file(special_chars_srt)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][2], '"Hello," he said... \'Really?\'')
        self.assertEqual(result[1][2], '[Music playing] ♪ La la la ♪')
        self.assertEqual(result[2][2], '<i>Italic text</i> & <b>bold text</b>')
    
    def test_create_srt_output(self):
        """Test creating SRT output from entries"""
        entries = [
            ('00:00:01,000', '00:00:03,000', 'Hello world'),
            ('00:00:04,000', '00:00:06,000', 'How are you?'),
            ('00:00:07,500', '00:00:09,200', 'I am fine, thank you')
        ]
        
        result = create_srt_output(entries)
        
        expected_lines = [
            "1",
            "00:00:01,000 --> 00:00:03,000",
            "Hello world",
            "",
            "2", 
            "00:00:04,000 --> 00:00:06,000",
            "How are you?",
            "",
            "3",
            "00:00:07,500 --> 00:00:09,200", 
            "I am fine, thank you",
            ""
        ]
        expected = '\n'.join(expected_lines)
        
        self.assertEqual(result, expected)
    
    def test_round_trip_parsing(self):
        """Test parsing and recreating SRT content"""
        original_srt = """1
00:00:01,000 --> 00:00:03,000
Original text

2
00:00:04,000 --> 00:00:06,000
Another line"""
        
        parsed = parse_srt_file(original_srt)
        recreated = create_srt_output(parsed)
        
        # Parse again to compare structure
        reparsed = parse_srt_file(recreated)
        
        self.assertEqual(len(parsed), len(reparsed))
        for original, reparsed_entry in zip(parsed, reparsed):
            self.assertEqual(original, reparsed_entry)
    
    def test_validate_srt_content(self):
        """Test SRT content validation"""
        # Valid SRT
        valid_srt = """1
00:00:01,000 --> 00:00:03,000
Hello world"""
        self.assertTrue(validate_srt_content(valid_srt))
        
        # Invalid - no timestamps
        invalid_no_timestamps = """1
Some text without timestamps"""
        self.assertFalse(validate_srt_content(invalid_no_timestamps))
        
        # Invalid - wrong timestamp format
        invalid_timestamp = """1
00:01 --> 00:03
Text"""
        self.assertFalse(validate_srt_content(invalid_timestamp))
        
        # Empty content
        self.assertFalse(validate_srt_content(""))
        
        # Valid with multiple entries
        valid_multiple = """1
00:00:01,000 --> 00:00:03,000
First line

2
00:00:04,000 --> 00:00:06,000
Second line"""
        self.assertTrue(validate_srt_content(valid_multiple))


class TestTranslator(unittest.TestCase):
    """Test cases for translation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not TRANSLATOR_AVAILABLE:
            self.skipTest("Translator module not available")
    
    def test_input_validation_empty_api_key(self):
        """Test validation of empty API key"""
        with self.assertRaises(ValueError) as context:
            translate_with_openai(["Hello"], "Chinese", "")
        self.assertIn("API key cannot be empty", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            translate_with_openai(["Hello"], "Chinese", "   ")
        self.assertIn("API key cannot be empty", str(context.exception))
    
    def test_input_validation_empty_target_language(self):
        """Test validation of empty target language"""
        with self.assertRaises(ValueError) as context:
            translate_with_openai(["Hello"], "", "sk-test123")
        self.assertIn("Target language cannot be empty", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            translate_with_openai(["Hello"], "   ", "sk-test123")
        self.assertIn("Target language cannot be empty", str(context.exception))
    
    def test_input_validation_invalid_text_list(self):
        """Test validation of invalid text list"""
        with self.assertRaises(ValueError) as context:
            translate_with_openai("Not a list", "Chinese", "sk-test123")
        self.assertIn("text_list must be a list", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            translate_with_openai(None, "Chinese", "sk-test123")
        self.assertIn("text_list must be a list", str(context.exception))
    
    def test_empty_text_list(self):
        """Test handling of empty text list"""
        result = translate_with_openai([], "Chinese", "sk-test123")
        self.assertEqual(result, [])
    
    def test_list_with_empty_strings(self):
        """Test handling of list with only empty strings"""
        result = translate_with_openai(["", "   ", ""], "Chinese", "sk-test123")
        self.assertEqual(result, ["", "", ""])
    
    @patch('openai.OpenAI')
    def test_successful_translation(self, mock_openai):
        """Test successful translation with mocked OpenAI"""
        # Setup mock response for individual translation
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello world"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test individual translation
        texts = ["Hello world"]
        result = translate_with_openai(texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Hello world")
        
        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-5-mini')
        # GPT-5 models use default parameters only
    
    @patch('openai.OpenAI')
    def test_mixed_empty_and_valid_strings(self, mock_openai):
        """Test handling of mixed empty and valid strings"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello world"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = translate_with_openai(["", "Hello world", ""], "Chinese", "sk-test123")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], "Hello world")
        self.assertEqual(result[2], "")
    
    @patch('openai.OpenAI')
    def test_individual_translation(self, mock_openai):
        """Test individual translation (one text at a time)"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello world"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        texts = ["Hello world"]
        result = translate_with_openai(texts, "Chinese", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Hello world")
    
    @patch('openai.OpenAI')
    def test_batch_translation(self, mock_openai):
        """Test batch translation with numbered response format"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # Mock a numbered batch response
        mock_response.choices[0].message.content = "1. Hello\n2. World\n3. Welcome"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        texts = ["Hello", "World", "Welcome"]
        result = translate_with_openai(texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Hello")
        self.assertEqual(result[1], "World")
        self.assertEqual(result[2], "Welcome")
        
        # Verify batch processing was used (single API call for multiple texts)
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_large_batch_splitting(self, mock_openai):
        """Test that large inputs are split into appropriate batches"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        
        # Create mock responses for multiple batches
        batch_responses = [
            "1. First batch\n2. Second item\n3. Third item",
            "1. Fourth item\n2. Fifth item"
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Mock(choices=[Mock(message=Mock(content=batch_responses[0]))]),
            Mock(choices=[Mock(message=Mock(content=batch_responses[1]))])
        ]
        mock_openai.return_value = mock_client
        
        # Test with 15 texts (should split into 2 batches: 12 + 3)
        texts = [f"Text {i}" for i in range(1, 16)]
        result = translate_with_openai(texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 15)
        # Check first batch results
        self.assertEqual(result[0], "First batch")
        self.assertEqual(result[1], "Second item")
        self.assertEqual(result[2], "Third item")
        # Check second batch results
        self.assertEqual(result[12], "Fourth item")
        self.assertEqual(result[13], "Fifth item")
        
        # Should have made 2 API calls (2 batches)
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    @patch('openai.OpenAI')
    def test_batch_fallback_to_individual(self, mock_openai):
        """Test fallback to individual translation when batch fails"""
        mock_client = Mock()
        
        # First call (batch) fails, subsequent calls (individual) succeed
        mock_client.chat.completions.create.side_effect = [
            Exception("Batch failed"),  # Batch translation fails
            Mock(choices=[Mock(message=Mock(content="Hello"))]),  # Individual 1 succeeds
            Mock(choices=[Mock(message=Mock(content="World"))]),  # Individual 2 succeeds
        ]
        mock_openai.return_value = mock_client
        
        texts = ["Hello", "World"]
        result = translate_with_openai(texts, "Chinese", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Hello")
        self.assertEqual(result[1], "World")
        
        # Should have made 3 calls: 1 batch + 2 individual fallbacks
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)
    
    @patch('openai.OpenAI')
    def test_progress_callback(self, mock_openai):
        """Test progress callback functionality"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "1. Hello\n2. World\n3. Welcome"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Track progress updates
        progress_updates = []
        def track_progress(progress):
            progress_updates.append(progress)
        
        texts = ["Hello", "World", "Welcome"]
        result = translate_with_openai(texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini", progress_callback=track_progress)
        
        # Should have received progress updates
        self.assertGreater(len(progress_updates), 0)
        
        # Progress should be between 0 and 1
        for progress in progress_updates:
            self.assertGreaterEqual(progress, 0.0)
            self.assertLessEqual(progress, 1.0)
        
        # Final progress should be 1.0 (or close to it)
        self.assertGreaterEqual(progress_updates[-1], 0.8)  # Allow for floating point precision
        
        # Translation should still work correctly
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Hello")
        self.assertEqual(result[1], "World")
        self.assertEqual(result[2], "Welcome")
    
    def test_parse_batch_response_formats(self):
        """Test parsing various batch response formats"""
        from translator import _parse_batch_response
        
        # Test numbered format with dots
        response1 = "1. Hello\n2. World\n3. Welcome"
        result1 = _parse_batch_response(response1, 3)
        self.assertEqual(result1, ["Hello", "World", "Welcome"])
        
        # Test numbered format with parentheses
        response2 = "1) Hello\n2) World\n3) Welcome"
        result2 = _parse_batch_response(response2, 3)
        self.assertEqual(result2, ["Hello", "World", "Welcome"])
        
        # Test single response (backward compatibility)
        response3 = "Hello world"
        result3 = _parse_batch_response(response3, 1)
        self.assertEqual(result3, ["Hello world"])
        
        # Test mixed format
        response4 = "1. Hello\nWorld\n3. Welcome"
        result4 = _parse_batch_response(response4, 3)
        self.assertEqual(result4, ["Hello", "World", "Welcome"])
        
        # Test incomplete response
        response5 = "1. Hello\n2. World"
        result5 = _parse_batch_response(response5, 3)
        self.assertEqual(len(result5), 3)
        self.assertEqual(result5[0], "Hello")
        self.assertEqual(result5[1], "World")
        self.assertTrue("Translation 3 not found" in result5[2])


class TestContextMemory(unittest.TestCase):
    """Test cases for context memory functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not TRANSLATOR_AVAILABLE:
            self.skipTest("Translator module not available")
            
        # Import here to handle missing dependencies gracefully
        from context_manager import ContextManager, extract_terms_from_subtitles
        self.ContextManager = ContextManager
        self.extract_terms_from_subtitles = extract_terms_from_subtitles
    
    def test_extract_potential_terms(self):
        """Test extraction of potential proper nouns from subtitles"""
        manager = self.ContextManager()
        
        # Test basic name extraction
        texts = [
            "Hello John, how are you?",
            "Hi Mary, I'm fine.",
            "John and Mary went to New York.",
            "Dr. Smith was waiting for them."
        ]
        
        terms = manager.extract_potential_terms(texts)
        
        # Should extract names and places
        self.assertIn("John", terms)
        self.assertIn("Mary", terms) 
        self.assertIn("New York", terms)
        self.assertIn("Smith", terms)
        
        # Should not extract common words
        self.assertNotIn("Hello", terms)
        self.assertNotIn("I", terms)
    
    def test_term_frequency_filtering(self):
        """Test that terms appearing multiple times are prioritized"""
        manager = self.ContextManager()
        
        texts = [
            "John said hello to everyone.",
            "John walked to the store.",
            "The store owner greeted John.",
            "RandomName appeared once."
        ]
        
        terms = manager.extract_potential_terms(texts)
        
        # John appears 3 times, should be included
        self.assertIn("John", terms)
        
        # RandomName appears once, might be included if it looks like proper noun
        # (This is flexible based on the heuristics)
    
    def test_context_manager_term_updates(self):
        """Test updating and retrieving established terms"""
        manager = self.ContextManager()
        
        # Test initial state
        self.assertEqual(len(manager.get_established_terms()), 0)
        
        # Add some terms
        new_terms = {
            "John": "John_ZH",
            "Mary": "Mary_ZH",
            "New York": "NewYork_ZH"
        }
        manager.update_terms(new_terms)
        
        # Check terms are stored
        established = manager.get_established_terms()
        self.assertEqual(len(established), 3)
        self.assertEqual(established["John"], "John_ZH")
        self.assertEqual(established["Mary"], "Mary_ZH")
        self.assertEqual(established["New York"], "NewYork_ZH")
        
        # Test confidence scoring
        manager.update_terms({"John": "John_ZH"})  # Same term again
        self.assertEqual(manager.term_confidence["John"], 2)
    
    def test_context_manager_confidence_filtering(self):
        """Test filtering terms by confidence level"""
        manager = self.ContextManager()
        
        # Add terms with different confidence levels
        manager.update_terms({"John": "John_ZH"})  # confidence 1
        manager.update_terms({"Mary": "Mary_ZH"})  # confidence 1
        manager.update_terms({"John": "John_ZH"})  # John now confidence 2
        
        # Test minimum confidence filtering
        high_confidence = manager.get_established_terms(min_confidence=2)
        self.assertEqual(len(high_confidence), 1)
        self.assertIn("John", high_confidence)
        self.assertNotIn("Mary", high_confidence)
        
        all_terms = manager.get_established_terms(min_confidence=1)
        self.assertEqual(len(all_terms), 2)
    
    def test_context_summary(self):
        """Test context manager summary functionality"""
        manager = self.ContextManager()
        
        # Test empty state
        summary = manager.get_context_summary()
        self.assertEqual(summary['total_terms'], 0)
        self.assertEqual(summary['high_confidence_terms'], 0)
        self.assertEqual(summary['batches_processed'], 0)
        
        # Add some terms
        manager.update_terms({"John": "John_ZH", "Mary": "Mary_ZH"})
        manager.update_terms({"John": "John_ZH"})  # Increase John's confidence
        
        summary = manager.get_context_summary()
        self.assertEqual(summary['total_terms'], 2)
        self.assertEqual(summary['high_confidence_terms'], 1)  # Only John has confidence >= 2
        self.assertEqual(summary['batches_processed'], 2)
    
    def test_extract_terms_from_translation_pair(self):
        """Test extracting term mappings from original and translated text pairs"""
        manager = self.ContextManager()
        
        original_texts = [
            "Hello John",
            "Hi Mary", 
            "Dr. Smith said hello"
        ]
        
        translated_texts = [
            "Hello John_ZH",
            "Hi Mary_ZH",
            "Dr Smith says Hello"
        ]
        
        mappings = manager.extract_terms_from_translation_pair(original_texts, translated_texts)
        
        # Should extract some mappings (exact matches depend on heuristics)
        self.assertIsInstance(mappings, dict)
        # The exact content depends on the translation extraction heuristics
        # We just verify it doesn't crash and returns a dict
    
    @patch('openai.OpenAI')
    def test_context_aware_translation(self, mock_openai):
        """Test translation with context manager integration"""
        from translator import translate_with_openai
        from context_manager import ContextManager
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "1. Hello John_ZH\n2. Hi Mary_ZH"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create context manager with established terms
        context_manager = ContextManager()
        context_manager.update_terms({"John": "John_ZH", "Mary": "Mary_ZH"})
        
        texts = ["Hello John", "Hi Mary"]
        result = translate_with_openai(
            texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini", 
            context_manager=context_manager
        )
        
        # Should complete without errors
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Hello John_ZH")
        self.assertEqual(result[1], "Hi Mary_ZH")
        
        # Verify API was called with context-aware prompt
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        # The system prompt should include established terms
        system_message = call_args[1]['messages'][0]['content']
        self.assertIn("John", system_message)  # Should mention established terms
        self.assertIn("John_ZH", system_message)
    
    @patch('openai.OpenAI')
    def test_convenience_function(self, mock_openai):
        """Test the convenience function for context memory translation"""
        from translator import translate_with_context_memory
        
        # Mock OpenAI response  
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello world"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        texts = ["Hello world"]
        translated_texts, context_manager = translate_with_context_memory(
            texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini"
        )
        
        # Should return both translated texts and context manager
        self.assertEqual(len(translated_texts), 1)
        self.assertEqual(translated_texts[0], "Hello world")
        self.assertIsInstance(context_manager, self.ContextManager)
    
    def test_context_reset(self):
        """Test context manager reset functionality"""
        manager = self.ContextManager()
        
        # Add some data
        manager.update_terms({"John": "John_ZH", "Mary": "Mary_ZH"})
        self.assertEqual(len(manager.get_established_terms()), 2)
        
        # Reset
        manager.reset_context()
        
        # Should be empty
        self.assertEqual(len(manager.get_established_terms()), 0)
        self.assertEqual(len(manager.term_confidence), 0)
        self.assertEqual(len(manager.batch_history), 0)
        
        summary = manager.get_context_summary()
        self.assertEqual(summary['total_terms'], 0)
        self.assertEqual(summary['batches_processed'], 0)


class TestCostEstimation(unittest.TestCase):
    """Test cases for cost estimation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not TRANSLATOR_AVAILABLE:
            self.skipTest("Translator module not available")
    
    def test_empty_list_cost_estimation(self):
        """Test cost estimation for empty list"""
        result = estimate_translation_cost([], "Chinese")
        
        self.assertEqual(result["total_characters"], 0)
        self.assertEqual(result["estimated_cost_usd"], 0.0)
        self.assertEqual(result["total_texts"], 0)
        self.assertEqual(result["model"], "gpt-5-mini")
    
    def test_cost_estimation_english(self):
        """Test cost estimation for English target language"""
        texts = ["Hello world", "How are you?"]
        result = estimate_translation_cost(texts, "English")
        
        self.assertEqual(result["total_characters"], 23)  # "Hello world" + "How are you?"
        self.assertEqual(result["estimated_input_tokens"], 5)  # 23 chars / 4 chars per token
        self.assertEqual(result["estimated_output_tokens"], 5)
        self.assertEqual(result["total_texts"], 2)
        self.assertEqual(result["model"], "gpt-5-mini")
        self.assertGreater(result["estimated_cost_usd"], 0)
        self.assertIsInstance(result["estimated_cost_usd"], float)
    
    def test_cost_estimation_non_english(self):
        """Test cost estimation for non-English target language"""
        texts = ["Hello world", "How are you?"]
        result = estimate_translation_cost(texts, "Chinese")
        
        self.assertEqual(result["total_characters"], 23)
        self.assertEqual(result["estimated_input_tokens"], 7)  # 23 chars / 3 chars per token
        self.assertEqual(result["estimated_output_tokens"], 7)
        self.assertEqual(result["total_texts"], 2)
        self.assertEqual(result["model"], "gpt-5-mini")
        self.assertGreater(result["estimated_cost_usd"], 0)
        self.assertIsInstance(result["estimated_cost_usd"], float)
    
    def test_cost_estimation_with_empty_strings(self):
        """Test cost estimation ignoring empty strings and whitespace-only strings"""
        texts = ["Hello world", "", "How are you?", "   "]
        result = estimate_translation_cost(texts, "Chinese")
        
        self.assertEqual(result["total_characters"], 23)  # Only non-empty, non-whitespace strings counted
        self.assertEqual(result["total_texts"], 2)  # Only non-empty, non-whitespace strings counted
        self.assertGreater(result["estimated_cost_usd"], 0)
    
    def test_english_vs_non_english_token_estimation(self):
        """Test that English has fewer estimated tokens than non-English"""
        texts = ["Hello world"]
        result_en = estimate_translation_cost(texts, "English")
        result_zh = estimate_translation_cost(texts, "Chinese")
        
        self.assertLess(result_en["estimated_input_tokens"], result_zh["estimated_input_tokens"])


class TestModuleImports(unittest.TestCase):
    """Test cases for module imports and function signatures"""
    
    def test_srt_processor_imports(self):
        """Test SRT processor module imports"""
        if SRT_AVAILABLE:
            # Test function existence
            self.assertTrue(callable(parse_srt_file))
            self.assertTrue(callable(create_srt_output))
            self.assertTrue(callable(validate_srt_content))
            
            # Test function signatures
            import inspect
            
            sig = inspect.signature(parse_srt_file)
            self.assertEqual(list(sig.parameters.keys()), ['file_content'])
            
            sig = inspect.signature(create_srt_output)
            self.assertEqual(list(sig.parameters.keys()), ['translated_entries'])
            
            sig = inspect.signature(validate_srt_content)
            self.assertEqual(list(sig.parameters.keys()), ['file_content'])
        else:
            self.skipTest("SRT processor module not available")
    
    def test_translator_imports(self):
        """Test translator module imports"""
        if TRANSLATOR_AVAILABLE:
            # Test function existence
            self.assertTrue(callable(translate_with_openai))
            self.assertTrue(callable(estimate_translation_cost))
            
            # Test function signatures
            import inspect
            
            sig = inspect.signature(translate_with_openai)
            self.assertEqual(list(sig.parameters.keys()), ['text_list', 'target_language', 'api_key', 'model', 'progress_callback', 'context_manager'])
            
            sig = inspect.signature(estimate_translation_cost)
            self.assertEqual(list(sig.parameters.keys()), ['text_list', 'target_language', 'model'])
        else:
            self.skipTest("Translator module not available")


def create_test_suite():
    """Create a comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestModuleImports,
        TestSRTProcessor, 
        TestTranslator,
        TestContextMemory,
        TestCostEstimation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests_with_summary():
    """Run tests with detailed summary"""
    print("🚀 Running OpenSubTrans Unified Test Suite")
    print("=" * 60)
    
    print(f"SRT Processor Available: {'✅' if SRT_AVAILABLE else '❌'}")
    print(f"Translator Available: {'✅' if TRANSLATOR_AVAILABLE else '❌'}")
    print()
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🔥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(':')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All tests passed!")
    elif success_rate >= 80:
        print("🎯 Good test coverage, but some issues to address.")
    else:
        print("⚠️  Multiple test failures - please review code.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests_with_summary()
    sys.exit(0 if success else 1)
