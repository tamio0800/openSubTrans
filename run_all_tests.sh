#!/bin/bash

echo "🚀 OpenSubTrans - 執行所有測試"
echo "============================================================"

# 激活虛擬環境
source env/bin/activate

echo "📊 執行核心功能測試..."
cd tests
python test_all.py

echo ""
echo "💰 執行定價測試..."
python test_new_pricing.py

echo ""
echo "🌐 檢查實際翻譯測試..."
if [ -z "$OPENAI_APIKEY" ]; then
    echo "⚠️  OPENAI_APIKEY 未設定，跳過實際翻譯測試"
    echo "   如需測試，請執行：export OPENAI_APIKEY='your-key'"
else
    echo "🔄 執行實際翻譯測試..."
    python test_real_translation.py
fi

echo ""
echo "✅ 所有測試執行完畢！"
