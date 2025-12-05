#!/bin/bash

echo "🐟 Starting Marites in development mode..."
echo ""

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your configuration."
    echo "See README.md for required environment variables."
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    echo "❌ Error: Vercel CLI not found!"
    echo "Install it with: npm install -g vercel"
    exit 1
fi

echo "✅ Environment file found"
echo "✅ Vercel CLI installed"
echo ""
echo "📝 Starting Vercel development server..."
echo "   The server will be available at http://localhost:3000"
echo ""
echo "🔗 Webhook endpoints:"
echo "   • GitHub: http://localhost:3000/webhooks/github"
echo "   • Slack:  http://localhost:3000/webhooks/slack"
echo "   • Health: http://localhost:3000/health"
echo ""
echo "💡 Tip: Use ngrok to expose your local server for webhook testing:"
echo "   ngrok http 3000"
echo ""

vercel dev

