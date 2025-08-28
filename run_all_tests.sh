#!/bin/bash

echo "🚀 OpenSubTrans - Running All Tests"
echo "============================================================"

# Activate virtual environment
source env/bin/activate

echo "📊 Running core functionality tests..."
cd tests
python test_all.py

echo ""
echo "🌐 Checking real translation tests..."
if [ -z "$OPENAI_APIKEY" ]; then
    echo "⚠️  OPENAI_APIKEY not set, skipping real translation tests"
    echo "   To test, run: export OPENAI_APIKEY='your-key'"
else
    echo "🔄 Running real translation tests..."
    python test_real_translation.py
fi

echo ""
echo "✅ All tests completed!"
