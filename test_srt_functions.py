"""
Test examples for SRT processing functions
"""

from srt_processor import parse_srt_file, create_srt_output, validate_srt_content


def test_parse_srt_file():
    """Test the parse_srt_file function with various examples"""
    
    print("🧪 Testing parse_srt_file function")
    print("=" * 50)
    
    # Test case 1: Simple SRT content
    print("\n1. Testing simple SRT content:")
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
    print(f"Input entries: 3")
    print(f"Parsed entries: {len(result)}")
    for i, (start, end, text) in enumerate(result, 1):
        print(f"  {i}. {start} -> {end}: '{text}'")
    
    # Test case 2: Multi-line text
    print("\n2. Testing multi-line text:")
    multiline_srt = """1
00:00:01,000 --> 00:00:04,000
This is a longer subtitle
that spans multiple lines
and should be joined together"""
    
    result = parse_srt_file(multiline_srt)
    print(f"Parsed: '{result[0][2]}'")
    
    # Test case 3: Empty or malformed content
    print("\n3. Testing malformed content:")
    malformed_srt = """1
Invalid timestamp format
Some text

2
00:00:04,000 --> 00:00:06,000
Valid entry"""
    
    result = parse_srt_file(malformed_srt)
    print(f"Parsed entries from malformed input: {len(result)}")
    if result:
        print(f"Valid entry: '{result[0][2]}'")


def test_create_srt_output():
    """Test the create_srt_output function"""
    
    print("\n\n🧪 Testing create_srt_output function")
    print("=" * 50)
    
    # Test case 1: Simple entries
    print("\n1. Testing simple entries:")
    entries = [
        ('00:00:01,000', '00:00:03,000', 'Hello world'),
        ('00:00:04,000', '00:00:06,000', 'How are you?'),
        ('00:00:07,500', '00:00:09,200', 'I am fine, thank you')
    ]
    
    result = create_srt_output(entries)
    print("Generated SRT content:")
    print("-" * 30)
    print(result)
    print("-" * 30)
    
    # Test case 2: Round-trip test (parse then create)
    print("\n2. Testing round-trip (parse -> create):")
    original_srt = """1
00:00:01,000 --> 00:00:03,000
Original text

2
00:00:04,000 --> 00:00:06,000
Another line"""
    
    parsed = parse_srt_file(original_srt)
    recreated = create_srt_output(parsed)
    
    print("Original:")
    print(original_srt)
    print("\nRecreated:")
    print(recreated)


def test_edge_cases():
    """Test edge cases and special scenarios"""
    
    print("\n\n🧪 Testing edge cases")
    print("=" * 50)
    
    # Test case 1: Unicode and Chinese characters
    print("\n1. Testing Unicode/Chinese characters:")
    chinese_srt = """1
00:00:01,000 --> 00:00:03,000
你好世界

2
00:00:04,000 --> 00:00:06,000
こんにちは世界

3
00:00:07,000 --> 00:00:09,000
Héllo wörld! 🎬"""
    
    result = parse_srt_file(chinese_srt)
    print(f"Parsed {len(result)} entries with Unicode characters:")
    for i, (start, end, text) in enumerate(result, 1):
        print(f"  {i}. '{text}'")
    
    # Test case 2: Empty subtitle entries
    print("\n2. Testing empty subtitle entries:")
    empty_entries_srt = """1
00:00:01,000 --> 00:00:03,000
Valid text

2
00:00:04,000 --> 00:00:06,000


3
00:00:07,000 --> 00:00:09,000
Another valid text"""
    
    result = parse_srt_file(empty_entries_srt)
    print(f"Parsed {len(result)} entries (should skip empty ones)")
    for i, (start, end, text) in enumerate(result, 1):
        print(f"  {i}. '{text}'")
    
    # Test case 3: Very long subtitle text
    print("\n3. Testing very long subtitle text:")
    long_text = "This is a very long subtitle that might appear in documentaries or educational content where detailed explanations are provided within the subtitle track itself."
    long_srt = f"""1
00:00:01,000 --> 00:00:05,000
{long_text}"""
    
    result = parse_srt_file(long_srt)
    print(f"Long text length: {len(result[0][2])} characters")
    print(f"Text preview: '{result[0][2][:50]}...'")
    
    # Test case 4: Special characters and punctuation
    print("\n4. Testing special characters:")
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
    print(f"Parsed {len(result)} entries with special characters:")
    for i, (start, end, text) in enumerate(result, 1):
        print(f"  {i}. '{text}'")
    
    # Test case 5: Boundary time values
    print("\n5. Testing boundary time values:")
    boundary_srt = """1
00:00:00,000 --> 00:00:01,001
Start of video

2
23:59:58,500 --> 23:59:59,999
End of video"""
    
    result = parse_srt_file(boundary_srt)
    print(f"Boundary times parsed correctly: {len(result)} entries")
    for i, (start, end, text) in enumerate(result, 1):
        print(f"  {i}. {start} -> {end}: '{text}'")


def test_validate_srt_content():
    """Test the validate_srt_content function"""
    
    print("\n\n🧪 Testing validate_srt_content function")
    print("=" * 50)
    
    test_cases = [
        ("Valid SRT", """1
00:00:01,000 --> 00:00:03,000
Hello world""", True),
        
        ("Invalid - no timestamps", """1
Some text without timestamps""", False),
        
        ("Invalid - wrong timestamp format", """1
00:01 --> 00:03
Text""", False),
        
        ("Empty content", "", False),
        
        ("Valid with multiple entries", """1
00:00:01,000 --> 00:00:03,000
First line

2
00:00:04,000 --> 00:00:06,000
Second line""", True)
    ]
    
    for name, content, expected in test_cases:
        result = validate_srt_content(content)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} {name}: {result} (expected: {expected})")


def run_all_tests():
    """Run all test functions"""
    print("🚀 Running SRT Function Tests")
    print("=" * 60)
    
    try:
        test_parse_srt_file()
        test_create_srt_output()
        test_edge_cases()
        test_validate_srt_content()
        
        print("\n\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    run_all_tests()
