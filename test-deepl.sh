#!/bin/bash
# Test DeepL API Translation

echo "🧪 Testing DeepL API..."
echo ""
echo "Enter your DeepL API Key (from https://www.deepl.com/en/your-account/keys):"
read -r DEEPL_API_KEY

if [ -z "$DEEPL_API_KEY" ]; then
    echo "❌ No API key provided"
    exit 1
fi

echo ""
echo "Testing translation: 'Mushroom soup with buckwheat' → German"
echo ""

curl -X POST 'https://api-free.deepl.com/v2/translate' \
    --data-urlencode "auth_key=$DEEPL_API_KEY" \
    --data-urlencode "text=Mushroom soup with buckwheat" \
    --data 'source_lang=EN' \
    --data 'target_lang=DE' \
    | python3 -m json.tool

echo ""
echo ""
echo "If you see a translation above, DeepL is working! ✅"
echo ""
echo "To use it with the app, set the environment variable:"
echo "export DEEPL_API_KEY='$DEEPL_API_KEY'"
