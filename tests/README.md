# OpenSubTrans Test Suite

This directory contains all test files and test data for the OpenSubTrans project.

## Test Files Overview

### 🧪 Unit Tests
- **`test_all.py`** - Comprehensive unittest suite
  - SRT processing functionality tests
  - Translation module tests  
  - Cost estimation tests
  - Module import validation

### 🌐 Real API Tests
- **`test_real_translation.py`** - Actual OpenAI API translation testing
  - Uses real OpenAI API key
  - Tests complete translation workflow
  - Generates actual translation results

## Test Data

### 📄 Subtitle Files
- **`sample_subtitle.srt`** - Sample English subtitle file for testing

## How to Run Tests

### Run Unit Tests
```bash
cd tests
python test_all.py
```

### Run Real Translation Tests (Requires API Key)
```bash
# Set environment variable
export OPENAI_APIKEY=your_api_key_here

cd tests
python test_real_translation.py
```

### Run All Tests (Automated)
```bash
# From project root
./run_all_tests.sh
```

## Notes

- Real translation tests use actual OpenAI API and will incur costs
- Ensure tests are run within the virtual environment
- Only GPT-5 models are supported: gpt-5, gpt-5-mini
- Generated translation files are ignored by git (.gitignore)

## Test Coverage

- ✅ SRT file parsing and validation
- ✅ Translation function mocking
- ✅ Cost estimation accuracy
- ✅ Error handling and edge cases
- ✅ Model validation and API integration