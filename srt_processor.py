"""
SRT subtitle file processing functions
"""

import re
from typing import List, Tuple


def parse_srt_file(file_content: str) -> List[Tuple[str, str, str]]:
    """
    Parse SRT subtitle file content and extract timestamps and text.
    
    Args:
        file_content (str): The content of the SRT file as a string
        
    Returns:
        List[Tuple[str, str, str]]: List of tuples containing (start_time, end_time, text)
        
    Example:
        >>> content = "1\\n00:00:01,000 --> 00:00:03,000\\nHello world\\n"
        >>> parse_srt_file(content)
        [('00:00:01,000', '00:00:03,000', 'Hello world')]
    """
    # Split content into blocks (separated by double newlines)
    blocks = re.split(r'\n\s*\n', file_content.strip())
    
    parsed_entries = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        
        if len(lines) < 3:
            continue  # Invalid block, skip
            
        # First line should be the sequence number
        try:
            sequence_num = int(lines[0])
        except ValueError:
            continue  # Skip if first line is not a number
            
        # Second line should contain timestamps
        timestamp_line = lines[1]
        timestamp_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
        timestamp_match = re.match(timestamp_pattern, timestamp_line)
        
        if not timestamp_match:
            continue  # Skip if timestamp format is invalid
            
        start_time = timestamp_match.group(1)
        end_time = timestamp_match.group(2)
        
        # Remaining lines are the subtitle text
        text_lines = lines[2:]
        text = ' '.join(text_lines).strip()
        
        if text:  # Only add non-empty text
            parsed_entries.append((start_time, end_time, text))
    
    return parsed_entries


def create_srt_output(translated_entries: List[Tuple[str, str, str]]) -> str:
    """
    Create SRT format output from translated subtitle entries.
    
    Args:
        translated_entries (List[Tuple[str, str, str]]): List of tuples containing 
                                                        (start_time, end_time, text)
        
    Returns:
        str: Complete SRT subtitle content as string
        
    Example:
        >>> entries = [('00:00:01,000', '00:00:03,000', 'Hello world')]
        >>> create_srt_output(entries)
        '1\\n00:00:01,000 --> 00:00:03,000\\nHello world\\n\\n'
    """
    srt_blocks = []
    
    for i, (start_time, end_time, text) in enumerate(translated_entries, 1):
        # Create each SRT block
        block = f"{i}\n{start_time} --> {end_time}\n{text}\n"
        srt_blocks.append(block)
    
    # Join all blocks with empty lines between them
    return '\n'.join(srt_blocks)


def validate_srt_content(file_content: str) -> bool:
    """
    Validate if the content appears to be a valid SRT file.
    
    Args:
        file_content (str): The content to validate
        
    Returns:
        bool: True if content appears to be valid SRT format
    """
    # Check for basic SRT patterns
    timestamp_pattern = r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
    
    # Look for at least one timestamp pattern
    if not re.search(timestamp_pattern, file_content):
        return False
    
    # Check if we can parse at least one entry
    try:
        entries = parse_srt_file(file_content)
        return len(entries) > 0
    except Exception:
        return False
