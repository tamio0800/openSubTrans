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
你好世界

2
00:00:04,000 --> 00:00:06,000
こんにちは世界

3
00:00:07,000 --> 00:00:09,000
Héllo wörld! 🎬"""
        
        result = parse_srt_file(unicode_srt)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][2], '你好世界')
        self.assertEqual(result[1][2], 'こんにちは世界')
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
        mock_response.choices[0].message.content = "你好世界"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test individual translation
        texts = ["Hello world"]
        result = translate_with_openai(texts, "Chinese (Traditional)", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "你好世界")
        
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
        mock_response.choices[0].message.content = "你好世界"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = translate_with_openai(["", "Hello world", ""], "Chinese", "sk-test123")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], "你好世界")
        self.assertEqual(result[2], "")
    
    @patch('openai.OpenAI')
    def test_individual_translation(self, mock_openai):
        """Test individual translation (one text at a time)"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "你好世界"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        texts = ["Hello world"]
        result = translate_with_openai(texts, "Chinese", "sk-test123", "gpt-5-mini")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "你好世界")


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
            self.assertEqual(list(sig.parameters.keys()), ['text_list', 'target_language', 'api_key', 'model'])
            
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
