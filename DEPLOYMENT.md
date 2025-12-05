# Deployment Guide

This guide walks you through deploying Marites to Vercel.

## Prerequisites

- [Vercel account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/cli) installed: `npm install -g vercel`
- GitHub App created with proper permissions (see main README)
- Slack App created with proper permissions (see main README)

## Step 1: Prepare Your Environment

Make sure all your code is committed to git:

```bash
git add -A
git commit -m "Ready for deployment"
```

## Step 2: Create Vercel KV Database

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to "Storage" tab
3. Click "Create Database"
4. Select "KV" (Redis-compatible key-value store)
5. Choose a name (e.g., `marites-kv`)
6. Select the region closest to your users
7. Click "Create"

After creation, note down:
- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`

## Step 3: Login to Vercel CLI

```bash
vercel login
```

Follow the prompts to authenticate.

## Step 4: Deploy to Vercel

### Initial Deployment

```bash
cd /path/to/marites
vercel
```

This creates a preview deployment. Follow the prompts:
- Set up and deploy? **Y**
- Which scope? Choose your account/team
- Link to existing project? **N** (first time)
- What's your project's name? **marites** (or your preferred name)
- In which directory is your code located? **./** (press Enter)

### Production Deployment

Once you've verified the preview works, deploy to production:

```bash
vercel --prod
```

## Step 5: Configure Environment Variables

### Option A: Using Vercel Dashboard (Recommended)

1. Go to your project in [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to "Settings" → "Environment Variables"
3. Add each variable from the list below:

```bash
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_USERNAME=your_github_username

SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your_signing_secret
SLACK_USER_ID=U01234567890
SLACK_BOT_NAME=Marites

KV_REST_API_URL=https://your-kv-url.upstash.io
KV_REST_API_TOKEN=your_kv_token

APP_SECRET_KEY=generate_with_python_secrets
DEBUG=false
```

4. Make sure to select "Production", "Preview", and "Development" for each variable
5. Click "Save"

### Option B: Using Vercel CLI

```bash
vercel env add GITHUB_APP_ID
vercel env add GITHUB_PRIVATE_KEY
vercel env add GITHUB_WEBHOOK_SECRET
# ... add all other variables
```

## Step 6: Link KV Database to Project

1. In Vercel Dashboard, go to your project
2. Navigate to "Storage" tab
3. Click "Connect Database"
4. Select your KV database
5. Click "Connect"

This automatically adds the KV environment variables.

## Step 7: Redeploy with Environment Variables

After adding all environment variables:

```bash
vercel --prod
```

## Step 8: Configure Webhooks

### GitHub Webhook

1. Go to your GitHub App settings: `https://github.com/settings/apps/[your-app-name]`
2. Scroll to "Webhook"
3. Set Webhook URL to: `https://your-project.vercel.app/webhooks/github`
4. Set Webhook secret to match your `GITHUB_WEBHOOK_SECRET`
5. Ensure these events are selected:
   - Pull request review comment
   - Pull request review
6. Set webhook to "Active"
7. Save changes

### Slack Events

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Select your app
3. Navigate to "Event Subscriptions"
4. Enable Events
5. Set Request URL to: `https://your-project.vercel.app/webhooks/slack`
6. Wait for verification (should show "Verified ✓")
7. Subscribe to bot events:
   - `message.im` (Direct messages)
8. Save Changes
9. Reinstall your app to workspace if prompted

## Step 9: Test Your Deployment

### Test Health Endpoint

```bash
curl https://your-project.vercel.app/health
```

Should return:
```json
{
  "status": "healthy",
  "checks": {
    "github_configured": true,
    "slack_configured": true,
    "storage_configured": true
  }
}
```

### Test GitHub Webhook

1. Create a test PR on a repository your GitHub App has access to
2. Have someone add a review comment
3. Check if you receive a Slack DM

### Test Slack Thread Reply

1. Reply to a comment thread in Slack
2. Check if your reply appears on GitHub

## Troubleshooting

### Viewing Logs

```bash
vercel logs https://your-project.vercel.app
```

Or in Vercel Dashboard → Project → Logs

### Common Issues

#### 1. Webhook Verification Failed

**Symptoms:** GitHub/Slack webhooks return 401 Unauthorized

**Solutions:**
- Verify `GITHUB_WEBHOOK_SECRET` and `SLACK_SIGNING_SECRET` match exactly
- Ensure environment variables are deployed (redeploy after adding them)

#### 2. GitHub API Authentication Failed

**Symptoms:** 401 errors when posting comments

**Solutions:**
- Verify `GITHUB_APP_ID` is correct
- Ensure `GITHUB_PRIVATE_KEY` includes `\n` for line breaks (or use Vercel's multi-line support)
- Check your GitHub App has correct permissions:
  - Pull requests: Read & Write
  - Contents: Read

#### 3. Slack Messages Not Sending

**Symptoms:** Comments not appearing in Slack

**Solutions:**
- Verify `SLACK_BOT_TOKEN` starts with `xoxb-`
- Check bot has correct OAuth scopes:
  - `chat:write`
  - `users:read`
  - `im:write`
  - `im:history`
- Verify `SLACK_USER_ID` is correct (find it via Slack profile → "Copy member ID")

#### 4. KV Storage Errors

**Symptoms:** 500 errors mentioning KV or storage

**Solutions:**
- Verify KV database is linked to project in Vercel Dashboard
- Check `KV_REST_API_URL` and `KV_REST_API_TOKEN` are correct
- Ensure KV database is in the same region as your deployment (for best performance)

#### 5. "Already Processed" Messages

**Symptoms:** Webhooks return 200 but nothing happens

**Solutions:**
- Check Vercel logs to see if event was already processed
- KV store caches processed events for 24 hours to prevent duplicates
- If testing repeatedly, you may need to clear the KV store or wait 24 hours

### Debug Mode

Enable debug logging by setting:

```bash
DEBUG=true
```

Then redeploy:

```bash
vercel --prod
```

View verbose logs:

```bash
vercel logs --follow
```

### Manual Testing

You can test webhooks locally using `vercel dev`:

```bash
vercel dev
```

Then use ngrok to expose your local server:

```bash
ngrok http 3000
```

Update your GitHub/Slack webhook URLs to the ngrok URL.

## Updating the Application

### Deploy Updates

```bash
git add -A
git commit -m "Your update message"
git push  # If you have a remote
vercel --prod
```

### Environment Variable Updates

If you only changed environment variables:

```bash
vercel env pull  # Download current variables
# Edit .env.local
vercel env add VARIABLE_NAME  # Add new variable
vercel --prod  # Redeploy
```

## Monitoring

### Vercel Analytics

Enable analytics in your Vercel project settings to monitor:
- Request volume
- Response times
- Error rates

### Custom Monitoring

Consider adding monitoring tools:
- [Sentry](https://sentry.io) for error tracking
- [LogDNA](https://logdna.com) for log aggregation
- [Datadog](https://datadoghq.com) for metrics

## Costs

- **Vercel Hobby Plan:** Free tier includes:
  - 100GB bandwidth
  - Serverless function executions
  - KV: 3,000 requests/day

- **Vercel Pro Plan:** $20/month includes:
  - 1TB bandwidth
  - Unlimited serverless executions
  - KV: 50,000 requests/day

Most personal/small team usage fits within the free tier.

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Rotate secrets regularly** - Update webhook secrets and tokens periodically
3. **Use environment variables** - Never hardcode credentials
4. **Enable Vercel firewall** - Available in Pro plan
5. **Monitor logs** - Watch for suspicious webhook attempts
6. **Restrict GitHub App permissions** - Only grant necessary permissions

## Support

If you encounter issues:

1. Check the logs: `vercel logs`
2. Verify environment variables are set correctly
3. Test endpoints manually with curl
4. Review [Vercel documentation](https://vercel.com/docs)
5. Check [GitHub Apps documentation](https://docs.github.com/en/apps)
6. Review [Slack API documentation](https://api.slack.com/docs)

## Rollback

If a deployment breaks something:

```bash
vercel rollback
```

Or in Vercel Dashboard → Project → Deployments → Click "..." → Promote to Production

