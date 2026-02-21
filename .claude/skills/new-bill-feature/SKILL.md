---
name: new-bill-feature
description: Guide for adding a new feature to the Bill/voting system in webiscite
disable-model-invocation: true
argument-hint: "[description of the feature]"
---

## Task
Implement a new feature for the Bill/voting system: $ARGUMENTS

## Checklist of files to consider

The Bill system spans these files. Review each to determine if it needs changes:

**Models & Logic:**
- `democrasite/webiscite/models.py` — Bill, Vote, PullRequest models (fields, `vote()`, `submit()`, `_check_approval()`, Status choices)
- `democrasite/webiscite/managers.py` — `BillManager.create_from_github()`, queryset annotations (yes_percent, no_percent, user_vote)
- `democrasite/webiscite/constitution.py` — `is_constitutional()`, `update_constitution()` for protected file ranges
- `democrasite/webiscite/tasks.py` — `submit_bill()` Celery task (approval check → GitHub merge → constitution update)
- `democrasite/webiscite/webhooks.py` — `PullRequestHandler` (opened/reopened/closed) and HMAC-validated `GithubWebhookView`

**Views & API:**
- `democrasite/webiscite/views.py` — BillListView, BillDetailView, BillUpdateView, vote_view (AJAX POST)
- `democrasite/webiscite/api/views.py` — BillViewSet (list/retrieve/update + vote action), IsAuthorOrReadOnly permission
- `democrasite/webiscite/api/serializers.py` — BillSerializer, PullRequestSerializer
- `democrasite/webiscite/urls.py` — Template view URL patterns
- `config/api_router.py` — DRF router registration

**Templates & Frontend:**
- `democrasite/templates/webiscite/bill_list.html` — Card grid of bills
- `democrasite/templates/webiscite/bill_detail.html` — Single bill page
- `democrasite/templates/webiscite/snippets/vote.html` — Vote progress bar + yes/no buttons
- `democrasite/templates/webiscite/bill_form.html` — Edit form (name, description)
- `democrasite/static/js/vote.js` — AJAX vote handler, DOM updates for counts and progress bar

**Tests (mirror each area above):**
- `democrasite/webiscite/tests/test_models.py`
- `democrasite/webiscite/tests/test_views.py`
- `democrasite/webiscite/tests/test_tasks.py`
- `democrasite/webiscite/tests/test_webhooks.py`
- `democrasite/webiscite/tests/test_constitution.py`
- `democrasite/webiscite/tests/test_templates.py`
- `democrasite/webiscite/tests/factories.py` — PullRequestFactory, BillFactory, TaskFactory

**Config & Admin:**
- `democrasite/webiscite/admin.py` — SimpleHistoryAdmin for Bill, PullRequest
- `democrasite/webiscite/context_processors.py` — Exposes `github_repo` to templates
- `config/settings/base.py` — WEBISCITE_* settings (quorum, majority thresholds, voting period, GitHub token/repo)

## Key patterns to follow
- Bill status choices: DRAFT, OPEN, APPROVED, REJECTED, FAILED, CLOSED
- Votes are M2M through Vote model with unique constraint on (bill, user)
- Bill.vote() toggles existing votes; raises ClosedBillVoteError if bill not OPEN
- Constitutional bills need WEBISCITE_SUPERMAJORITY (66.67%), normal need WEBISCITE_NORMAL_MAJORITY (50%)
- Each Bill has a OneToOne PeriodicTask for scheduled submission
- Managers annotate querysets with vote percentages and user vote status
- API vote endpoint expects {"support": true/false}, template vote_view expects POST with "vote" field
- django-simple-history tracks Bill and Vote changes automatically
- PullRequest has a `draft` boolean field tracking GitHub's draft state
- Draft bills (from draft PRs) cannot be voted on or submitted; they transition to OPEN via Bill.publish() when the PR is marked ready for review
- The `unique_active_pull_request` constraint prevents duplicate bills for the same PR in both `open` and `draft` statuses
- PullRequest.close() closes both open and draft bills
- The submit PeriodicTask is created disabled for draft bills; Bill.publish() enables it and resets last_run_at so the voting period starts from publication
- GitHub's `ready_for_review` webhook action triggers PullRequestHandler.ready_for_review(), which updates the PR and publishes the draft bill

## Steps
1. Read the relevant files from the checklist above
2. Plan the changes needed across all layers (model → serializer → view → template → test)
3. If adding a model field, create a migration with `just manage makemigrations`
4. Implement changes
5. Update or add factories in factories.py for any new model fields
6. Write tests covering the new functionality
7. Run `just run pytest democrasite/webiscite/tests/` to verify
8. Run `just lint` to check style
9. Update documentation:
   - Update the "Key patterns to follow" section in this skill file (`.claude/skills/new-bill-feature/SKILL.md`) with the new feature's patterns
   - Update `docs/webiscite.rst` if the feature changes the pull request processing pipeline or bill lifecycle
   - If files were created or deleted, run `just run make -C docs apidocs` to regenerate API docs
