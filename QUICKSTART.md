# Quick Start Guide

Get your PR Marites up and running in 10 minutes!

## Step 1: Clone and Setup (2 min)

```bash
git clone <your-repo-url>
cd marites
```

## Step 2: Create GitHub App (3 min)

1. Go to https://github.com/settings/apps/new
2. Fill in:
   - **Name:** Marites
   - **Homepage URL:** https://github.com/yourusername
   - **Webhook URL:** https://your-app.vercel.app/webhooks/github (temp placeholder)
   - **Webhook secret:** Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
3. Set permissions:
   - Repository permissions:
     - **Pull requests:** Read & Write
     - **Contents:** Read
4. Subscribe to events:
   - ✅ Pull request review comment
   - ✅ Pull request review
5. Click "Create GitHub App"
6. Note your **App ID**
7. Click "Generate a private key" and download the `.pem` file

## Step 3: Create Slack App (3 min)

1. Go to https://api.slack.com/apps/new
2. Choose "From scratch"
3. Name: **Marites**
4. Pick your workspace
5. Go to **OAuth & Permissions**:
   - Add Bot Token Scopes:
     - `chat:write`
     - `users:read`
     - `im:write`
     - `im:history`
   - Click "Install to Workspace"
   - Copy the **Bot User OAuth Token** (starts with `xoxb-`)
6. Go to **Basic Information**:
   - Copy **Signing Secret**
7. Get your Slack User ID:
   - In Slack, click your profile → "Copy member ID"

## Step 4: Deploy to Vercel (2 min)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

Note your deployment URL: `https://your-project.vercel.app`

## Step 5: Configure Environment Variables (3 min)

In [Vercel Dashboard](https://vercel.com/dashboard):

1. Go to your project → Settings → Environment Variables
2. Add these variables (copy from the output of your GitHub/Slack app creation):

```bash
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...your key here...
-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret_from_step2

SLACK_BOT_TOKEN=xoxb-your-token-from-step3
SLACK_SIGNING_SECRET=your_signing_secret_from_step3
SLACK_BOT_NAME=Marites

APP_SECRET_KEY=run_python_secrets_to_generate
DEBUG=false
```

**Note:** Users don't need to be pre-configured! They register themselves via Slack.

3. Save all variables

## Step 6: Setup KV Database (2 min)

1. In Vercel Dashboard → Storage → Create Database
2. Select **KV** → Name it `marites-kv`
3. Create and link to your project
4. The `KV_REST_API_URL` and `KV_REST_API_TOKEN` are automatically added

## Step 7: Update Webhook URLs (1 min)

### GitHub:
1. Go to https://github.com/settings/apps/[your-app-name]
2. Update Webhook URL to: `https://your-project.vercel.app/webhooks/github`
3. Save

### Slack:
1. Go to https://api.slack.com/apps → Your App → Event Subscriptions
2. Enable Events
3. Set Request URL to: `https://your-project.vercel.app/webhooks/slack`
4. Save (wait for "Verified ✓")

## Step 8: Redeploy (1 min)

After adding environment variables:

```bash
vercel --prod
```

## Step 9: Test! (1 min)

```bash
# Test health
curl https://your-project.vercel.app/health

# Should return:
# {"status":"healthy","checks":{"github_configured":true,"slack_configured":true,"storage_configured":true}}
```

## Step 10: Register Users! (1 min)

1. **Find Marites** in Slack Apps
2. **Open a DM** with the bot
3. **Send:** `register your_github_username`
4. **You'll get:** ✅ Confirmation message
5. **Share with team:** Tell teammates to do the same!

## Step 11: Try it out! (1 min)

1. Create a PR in a repo your GitHub App has access to (you must be the author)
2. Have someone add a review comment on your PR
3. You should receive a Slack DM! 🎉
4. Reply in the Slack thread
5. Your reply should appear on GitHub! 🚀

---

## Troubleshooting

**Not receiving Slack messages?**
- Send `status` to PR Marites to check if you're registered
- Make sure you registered with the correct GitHub username
- Ensure the PR is authored by you

**GitHub API errors?**
- Verify GitHub App is installed on the repository
- Check `GITHUB_PRIVATE_KEY` includes line breaks
- Ensure App ID is correct

**Webhook verification failed?**
- Check secrets match exactly
- Redeploy after adding environment variables

**Still stuck?**
- Check Vercel logs: `vercel logs`
- See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed troubleshooting

---

## What's Next?

- **Reactions:** Add GitHub reactions to Slack
- **Notifications:** Get notified on PR approvals/changes requested
- **Analytics:** Track response times and engagement
- **Team Management:** Add admin commands for user management

See [README.md](./README.md) for full documentation.

---

**Total Time:** ~15 minutes to get your PR Marites gossiping!

