#!/bin/bash

# Script to close dangerous and obsolete Dependabot PRs
# Date: 2025-10-24
# Reason: Major updates that can break the application

echo "🔧 Closing Dependabot PRs..."
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not installed"
    echo "Install: https://cli.github.com/"
    echo ""
    echo "Alternative: Close PRs manually at:"
    echo "https://github.com/newwdead/CRM/pulls"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI ready"
echo ""

# Dangerous PRs to close
echo "📋 Closing 6 dangerous PRs..."
echo ""

# PR #5 - Python 3.14
echo "Closing #5 (Python 3.11→3.14)..."
gh pr close 5 --repo newwdead/CRM --comment "❌ Skipping Python 3.14 update.

**Reason:** Python 3.14 is too new and potentially unstable.

**Current:** Python 3.11 (LTS) ✅  
**Decision:** Staying on 3.11 for stability.

**When to revisit:** When Python 3.14 reaches stable LTS status.

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #5" || echo "  ⚠️  Already closed or error"

# PR #1 - Node 25
echo "Closing #1 (Node 20→25)..."
gh pr close 1 --repo newwdead/CRM --comment "❌ Skipping Node 25 update.

**Reason:** Node 25 is experimental/preview.

**Current:** Node 20 (LTS) ✅  
**Decision:** Staying on Node 20 LTS for stability.

**When to revisit:** When Node 25 reaches LTS status.

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #1" || echo "  ⚠️  Already closed or error"

# PR #17 - Redis 7
echo "Closing #17 (Redis 5→7)..."
gh pr close 17 --repo newwdead/CRM --comment "⏳ Postponing Redis 7.0 update.

**Reason:** Major version with significant API changes.

**Current:** Redis 5.2.0 (stable) ✅  
**Decision:** Postpone until dedicated testing sprint.

**Requirements for merge:**
- Full integration testing
- Performance benchmarking
- Migration guide review

**Timeline:** Next major release (v6.0.0)

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #17" || echo "  ⚠️  Already closed or error"

# PR #16 - pytest-asyncio
echo "Closing #16 (pytest-asyncio 0.24→1.2)..."
gh pr close 16 --repo newwdead/CRM --comment "⏳ Postponing pytest-asyncio 1.2 update.

**Reason:** Major version with breaking test changes.

**Current:** pytest-asyncio 0.24.0 (stable) ✅  
**Decision:** Postpone until dedicated testing sprint.

**Requirements for merge:**
- Review all async tests
- Update test fixtures
- Ensure 100% test pass rate

**Timeline:** Next major release (v6.0.0)

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #16" || echo "  ⚠️  Already closed or error"

# PR #12 - bcrypt
echo "Closing #12 (bcrypt 4→5)..."
gh pr close 12 --repo newwdead/CRM --comment "⏳ Postponing bcrypt 5.0 update.

**Reason:** Security-critical package requires thorough audit.

**Current:** bcrypt 4.2.0 (stable & secure) ✅  
**Decision:** Postpone until security audit.

**Requirements for merge:**
- Security audit
- Password hash compatibility testing
- Auth flow verification
- Penetration testing

**Timeline:** With dedicated security sprint

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #12" || echo "  ⚠️  Already closed or error"

# PR #9 - react-router-dom
echo "Closing #9 (react-router-dom 6→7)..."
gh pr close 9 --repo newwdead/CRM --comment "⏳ Postponing react-router-dom 7 update.

**Reason:** Major version with significant routing API changes.

**Current:** react-router-dom 6.26.2 (stable) ✅  
**Decision:** Postpone until dedicated refactoring sprint.

**Requirements for merge:**
- Review all routing code
- Test all navigation flows
- Update all route components
- Verify lazy loading

**Timeline:** Next major release (v6.0.0)

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #9" || echo "  ⚠️  Already closed or error"

echo ""
echo "📋 Closing 3 obsolete PRs (already updated in workflows)..."
echo ""

# PR #14 - actions/setup-python
echo "Closing #14 (actions/setup-python)..."
gh pr close 14 --repo newwdead/CRM --comment "✅ Already updated in workflows.

**Status:** Workflows already use \`actions/setup-python@v5\` (latest stable).

**File:** \`.github/workflows/ci.yml\`, \`ci-cd.yml\`, \`security.yml\`

**No action needed:** This PR is redundant.

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #14" || echo "  ⚠️  Already closed or error"

# PR #11 - actions/checkout
echo "Closing #11 (actions/checkout)..."
gh pr close 11 --repo newwdead/CRM --comment "✅ Already updated in workflows.

**Status:** Workflows already use \`actions/checkout@v4\` (latest stable).

**File:** All workflow files in \`.github/workflows/\`

**No action needed:** This PR is redundant.

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #11" || echo "  ⚠️  Already closed or error"

# PR #10 - github/codeql-action
echo "Closing #10 (github/codeql-action)..."
gh pr close 10 --repo newwdead/CRM --comment "✅ Already updated in workflows.

**Status:** Workflows already use \`github/codeql-action@v3\` (latest stable).

**File:** \`.github/workflows/codeql.yml\`

**No action needed:** This PR is redundant.

Закрыто автоматически скриптом." 2>/dev/null && echo "  ✅ Closed #10" || echo "  ⚠️  Already closed or error"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ ГОТОВО!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Закрыто PRs:"
echo "  🔴 Опасные: #1, #5, #9, #12, #16, #17 (6)"
echo "  ✅ Устаревшие: #10, #11, #14 (3)"
echo ""
echo "Осталось для review:"
echo "  🟡 #2 (celery 5.4→5.5)"
echo "  🟡 #6 (react-hotkeys-hook 4→5)"
echo "  🟡 #7 (react-markdown 9→10)"
echo "  🟡 #8 (framer-motion 11→12)"
echo "  🟡 #15 (httpx 0.27→0.28)"
echo ""
echo "Проверьте: https://github.com/newwdead/CRM/pulls"
echo ""
echo "На русском! 🇷🇺"
