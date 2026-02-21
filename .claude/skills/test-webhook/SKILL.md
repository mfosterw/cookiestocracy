---
name: test-webhook
description: Set up smee to forward GitHub webhooks to local Django for manual testing
disable-model-invocation: true
argument-hint: https://smee.io/2ckdUNpB3Qt0UvE7
---

## Task
Start a smee webhook proxy to forward GitHub webhook events to the local Django server for manual testing.

## Prerequisites
- `smee` CLI installed (`npm install -g smee-client`)
- Docker containers running (`just up`)
- A smee channel URL from https://smee.io or a personal one
- A GitHub webhook configured on your fork pointing to the smee URL, with the `GITHUB_WEBHOOK_SECRET` matching your `.envs/.local/.django` file

## Steps

1. Parse the smee URL from `$ARGUMENTS`
2. Verify containers are running with `just up`
3. Start smee in the background:
   ```
   smee --url <SMEE_URL> --path /hooks/github/ --port 8000
   ```
4. Confirm smee connects successfully
5. Inform the user they are ready to test by creating or updating pull requests on their GitHub fork

## Configuration reference
- Webhook path: `/hooks/github/`
- Local port: `8000` (Docker maps this to the Django container)
- Webhook secret env var: `GITHUB_WEBHOOK_SECRET` in `.envs/.local/.django`
- Django setting: `WEBISCITE_GITHUB_WEBHOOK_SECRET` in `config/settings/base.py`
- Webhook handler: `democrasite/webiscite/webhooks.py` — `GithubWebhookView`
- Supported events: `pull_request` (opened, reopened, closed, ready_for_review), `push`, `ping`

## Troubleshooting
- If webhook returns 403: check that `GITHUB_WEBHOOK_SECRET` matches the secret configured on the GitHub webhook
- If webhook returns 400: check the `x-github-event` and `x-hub-signature-256` headers are present
- If smee doesn't connect: verify the smee URL is correct and the channel exists
- Check Django logs with `docker compose -f docker-compose.local.yml logs django -f` for webhook processing errors
