# Marites

**Gossip! Your code review messenger**

A production-ready Python application that forwards GitHub PR review comments to Slack and enables bi-directional communication.

## Features

- 🔔 **Real-time Notifications**: Get notified in Slack when reviewers comment on your PRs
- 💬 **Two-way Communication**: Reply to comments directly from Slack threads
- 🔗 **Smart Links**: Direct links to GitHub comments and Cursor editor
- 📝 **Code Context**: Automatic code summary around commented lines
- 🚀 **Serverless**: Deploys to Vercel with zero configuration
- 👥 **Multi-User Support**: Team members can opt-in via Slack commands

## Multi-User Support

PR Marites supports multiple users in the same organization! Team members can register themselves:

1. **Find Marites** in Slack Apps
2. **Open a DM** with the bot
3. **Send:** `register your_github_username`
4. **Done!** You'll receive notifications when someone comments on your PRs

**Available Commands:**
- `register <github_username>` - Start receiving PR notifications
- `unregister` - Stop receiving notifications
- `status` - Check your registration status
- `help` - Show available commands

## Prerequisites

1. **GitHub App**: Create a GitHub App with the following permissions:
   - Repository permissions:
     - Pull requests: Read & Write
     - Contents: Read
   - Subscribe to events:
     - Pull request review comment
     - Pull request review

2. **Slack App**: Create a Slack App with:
   - Bot Token Scopes:
     - `chat:write`
     - `users:read`
     - `channels:history`
     - `im:write`
     - `im:history`
   - Event Subscriptions:
     - `message.im`
   - Enable Socket Mode (for local development) or use Request URL for webhooks

3. **Vercel Account**: For deployment

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd marites
```

2. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create a .env file with the variables listed in the Environment Variables section below
# OR configure them in your Vercel project settings
```

4. Deploy to Vercel:
```bash
vercel --prod
```

5. Configure webhooks:
   - **GitHub**: Set webhook URL to `https://your-app.vercel.app/webhooks/github`
   - **Slack**: Set request URL to `https://your-app.vercel.app/webhooks/slack`

## Environment Variables

Copy and configure these variables in your Vercel project settings or local `.env` file:

```bash
# GitHub Configuration
# Create a GitHub App at https://github.com/settings/apps
GITHUB_APP_ID=your_github_app_id_here
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nYour private key here\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here

# Slack Configuration
# Create a Slack App at https://api.slack.com/apps
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your_slack_signing_secret_here
SLACK_BOT_NAME=Marites

# Vercel KV Storage
# Create a KV database in your Vercel project settings
KV_REST_API_URL=https://your-kv-instance.upstash.io
KV_REST_API_TOKEN=your_kv_api_token_here

# Application Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
APP_SECRET_KEY=your_app_secret_key_here

# Optional: Enable debug logging
DEBUG=false
```

### GitHub Configuration

- `GITHUB_APP_ID`: Your GitHub App ID
- `GITHUB_PRIVATE_KEY`: Private key for GitHub App authentication
- `GITHUB_WEBHOOK_SECRET`: Secret for webhook verification

### Slack Configuration

- `SLACK_BOT_TOKEN`: Bot User OAuth Token (starts with `xoxb-`)
- `SLACK_SIGNING_SECRET`: For verifying Slack requests
- `SLACK_BOT_NAME`: Display name for the bot (optional, defaults to "Marites")

**Note:** Users don't need to be pre-configured! They register themselves via Slack DM.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   GitHub    │ ───────>│   Vercel     │ ───────>│    Slack    │
│  (Webhook)  │         │  (Serverless)│         │    (Bot)    │
└─────────────┘         └──────────────┘         └─────────────┘
                              │  ▲
                              │  │
                              ▼  │
                        ┌──────────────┐
                        │  Vercel KV   │
                        │  (Storage)   │
                        └──────────────┘
```

## How It Works

1. **Comment Detection**: GitHub webhook fires when a review comment is created
2. **Comment Forwarding**: App checks if the PR author matches `GITHUB_USERNAME`
3. **Slack Notification**: Bot sends a DM with:
   - Direct link to the comment
   - Code context (5 lines before/after)
   - Cursor link for quick editing
4. **Reply Handling**: User replies in Slack thread
5. **GitHub Update**: App posts reply back to GitHub as a comment

## Development

Run locally with:

```bash
vercel dev
```

Use ngrok for webhook testing:

```bash
ngrok http 3000
```

## License

MIT

