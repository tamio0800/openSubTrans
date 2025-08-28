# 🎬 OpenSubTrans

An intelligent movie and TV subtitle translation tool powered by OpenAI GPT-5, featuring smart context memory for consistent terminology translation.

## ✨ Features

- **🤖 AI-Powered Translation**: Uses OpenAI GPT-5 models for natural, colloquial translations
- **🧠 Smart Context Memory**: Automatically maintains consistent translation of character names, places, and proper nouns
- **⚡ Intelligent Batch Processing**: Processes subtitles in optimized batches for better dialogue coherence
- **📊 Real-time Progress**: Live progress tracking with detailed feedback
- **💰 Cost Estimation**: Transparent cost calculation before translation
- **🎛️ User-Friendly Interface**: Clean Streamlit web interface with intuitive controls
- **📁 SRT Support**: Full support for SRT subtitle format with validation

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (GPT-5 access required)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd openSubTrans
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Configure in the sidebar**
   - Enter your OpenAI API key
   - Select GPT-5 model (`gpt-5-mini` recommended for cost efficiency)
   - Enable/disable context memory (recommended: ON)

3. **Upload and translate**
   - Upload your SRT subtitle file
   - Choose target language
   - Review cost estimation
   - Click "Start Translation"
   - Download the translated file

## 🧠 Context Memory

OpenSubTrans features intelligent context memory that:

- **Automatically detects** proper nouns, character names, and places
- **Maintains consistency** across the entire subtitle file
- **Learns progressively** as it processes more content
- **Shows real-time summaries** of established terminology

### Example
```
Original: "John said hello to Mary in New York"
First batch: "John" → "約翰", "Mary" → "瑪麗", "New York" → "紐約"
Later batches: Automatically uses the same translations for consistency
```

## 🛠️ Development

### Running Tests

Run all tests:
```bash
./run_all_tests.sh
```

Run specific test categories:
```bash
# Core functionality tests only
python tests/test_all.py

# Real API tests (requires OPENAI_APIKEY)
export OPENAI_APIKEY='your-api-key'
python tests/test_real_translation.py
```

### Project Structure

```
openSubTrans/
├── app.py                 # Streamlit web interface
├── translator.py          # Core translation logic with GPT-5
├── context_manager.py     # Smart context memory system
├── srt_processor.py       # SRT file parsing and generation
├── prompts.py            # Translation prompt templates
├── tests/                # Comprehensive test suite (38 tests)
│   ├── test_all.py       # Main test suite
│   ├── test_real_translation.py  # Real API tests
│   └── sample_subtitle.srt       # Test data
├── requirements.txt      # Python dependencies
└── run_all_tests.sh     # Test runner script
```

## 🔧 Configuration

### Supported Models

- **gpt-5-mini**: Recommended for most use cases (cost-effective)
- **gpt-5**: Premium quality for critical translations

### Supported Languages

The application supports translation to any language supported by GPT-5, including:
- Chinese (Traditional/Simplified)
- Japanese
- Korean
- Spanish
- French
- German
- And many more...

### Environment Variables

```bash
# Optional: Set default API key
export OPENAI_APIKEY='your-api-key-here'
```

## 💡 Tips for Best Results

1. **Use Context Memory**: Keep it enabled for character-heavy content
2. **Batch Size**: The default 12-subtitle batches are optimized for dialogue coherence
3. **Cost Management**: Use `gpt-5-mini` for initial translations, `gpt-5` for final versions
4. **File Quality**: Ensure your SRT files are properly formatted before upload

## 🧪 Testing

The project includes comprehensive testing:

- **38 unit tests** covering all functionality
- **100% pass rate** with continuous integration
- **Real API tests** for end-to-end validation
- **Mock tests** for development without API costs

## 📊 Performance

- **Smart Batching**: ~12 subtitles per API call for efficiency
- **Context Awareness**: Automatic terminology consistency
- **Progress Tracking**: Real-time updates during translation
- **Error Handling**: Graceful fallbacks and error recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `./run_all_tests.sh`
4. Submit a pull request

## 📄 License

[Add your license information here]

## 🎯 Roadmap

- [ ] Support for additional subtitle formats (VTT, ASS)
- [ ] Bulk file processing
- [ ] Translation quality scoring
- [ ] Custom terminology dictionaries
- [ ] API rate limiting optimization

---

**Made with ❤️ for the subtitle translation community**