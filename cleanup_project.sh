#!/bin/bash

# Project Cleanup Script
# Version: 2.26.0
# Автоматическая очистка и организация проекта

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🧹 PROJECT CLEANUP & ORGANIZATION                          ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
DELETED=0
ARCHIVED=0
MOVED=0

echo "📊 Creating directory structure..."

# Create docs structure
mkdir -p docs/{archive/{releases,deployments,ci-fixes,refactoring,testing},guides/{setup,development,ocr},releases,architecture}

echo -e "${GREEN}✓${NC} Directory structure created"
echo ""

#==============================================================================
# Priority 1: Archive old Release Notes
#==============================================================================
echo "📦 Priority 1: Archiving old release notes..."

if ls RELEASE_NOTES_v1.*.md 1> /dev/null 2>&1; then
    mv RELEASE_NOTES_v1.*.md docs/archive/releases/ 2>/dev/null || true
    COUNT=$(ls docs/archive/releases/RELEASE_NOTES_v1.*.md 2>/dev/null | wc -l)
    ARCHIVED=$((ARCHIVED + COUNT))
    echo -e "  ${GREEN}✓${NC} Archived $COUNT v1.x release notes"
fi

if ls RELEASE_NOTES_v2.[0-9].md 1> /dev/null 2>&1; then
    mv RELEASE_NOTES_v2.[0-9].md docs/archive/releases/ 2>/dev/null || true
    COUNT=$(ls docs/archive/releases/RELEASE_NOTES_v2.[0-9].md 2>/dev/null | wc -l)
    ARCHIVED=$((ARCHIVED + COUNT))
    echo -e "  ${GREEN}✓${NC} Archived $COUNT v2.0-2.9 release notes"
fi

for version in 10 11 12 13 14 15; do
    if [ -f "RELEASE_NOTES_v2.${version}.md" ]; then
        mv "RELEASE_NOTES_v2.${version}.md" docs/archive/releases/
        ARCHIVED=$((ARCHIVED + 1))
    fi
done

if [ $ARCHIVED -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Total archived: $ARCHIVED files"
fi
echo ""

#==============================================================================
# Priority 2: Delete CI Fixes
#==============================================================================
echo "🗑️  Priority 2: Removing CI fix reports..."

CI_FILES=(
    "CI_ALL_FIXES_v2.15.md"
    "CI_ERRORS_FIXED_SUMMARY.md"
    "CI_ERRORS_FIX_v2.15.1_FINAL.md"
    "CI_FIXES_COMPLETE.md"
    "CI_FIXES_FINAL.md"
    "CI_FIX_REPORT.md"
    "GITHUB_ACTIONS_ANALYSIS.md"
    "GITHUB_ACTIONS_IMPROVEMENTS_SUMMARY.md"
    "WORKFLOWS_PROBLEMS_AND_FIXES.md"
)

for file in "${CI_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        DELETED=$((DELETED + 1))
        echo -e "  ${RED}✗${NC} Deleted $file"
    fi
done
echo ""

#==============================================================================
# Priority 3: Archive old Deployment Success
#==============================================================================
echo "📦 Priority 3: Archiving old deployment logs..."

DEPLOY_FILES=(
    "DEPLOYMENT_v2.7_SUCCESS.md"
    "DEPLOYMENT_v2.13_SUCCESS.md"
    "DEPLOYMENT_v2.14_SUCCESS.md"
)

for file in "${DEPLOY_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/deployments/
        ARCHIVED=$((ARCHIVED + 1))
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done
echo ""

#==============================================================================
# Priority 4: Delete Summary/Session files
#==============================================================================
echo "🗑️  Priority 4: Removing summary files..."

SUMMARY_FILES=(
    "SESSION_SUMMARY.md"
    "SUMMARY_v2.21.3.md"
    "PROJECT_KNOWLEDGE_SUMMARY.md"
    "CLEANUP_SUMMARY.md"
    "FINAL_SUMMARY_v2.16.md"
)

for file in "${SUMMARY_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        DELETED=$((DELETED + 1))
        echo -e "  ${RED}✗${NC} Deleted $file"
    fi
done
echo ""

#==============================================================================
# Priority 5: Delete Legacy/Old files
#==============================================================================
echo "🗑️  Priority 5: Removing legacy files..."

LEGACY_FILES=(
    "LEGACY_FILES_REPORT.md"
    "GIT_CLEANUP_SUCCESS.md"
    "GIT_STRUCTURE_ANALYSIS.md"
    "PLAN_v2.4.md"
    "OPTIMIZATION_REPORT.md"
    "OPTIMIZATION_SUMMARY.md"
    "QUICK_START_OPTIMIZATION.md"
    "FRONTEND_REFACTORING_PLAN.md"
    "FRONTEND_REFACTORING_STATUS.md"
    "REFACTORING_SUMMARY_v2.16.md"
    "RELEASE_COMPLETE_v2.16.md"
    "CELERY_FIX_LOG.md"
    "COMPREHENSIVE_CHECK_v2.16.md"
)

for file in "${LEGACY_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        DELETED=$((DELETED + 1))
        echo -e "  ${RED}✗${NC} Deleted $file"
    fi
done
echo ""

#==============================================================================
# Priority 6: Archive old Test Reports
#==============================================================================
echo "📦 Priority 6: Archiving old test reports..."

TEST_FILES=(
    "TEST_REPORT_v2.4.md"
    "TEST_RESULTS_MANUAL_v2.4.md"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/testing/
        ARCHIVED=$((ARCHIVED + 1))
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done
echo ""

#==============================================================================
# Priority 7: Delete old Shell Scripts
#==============================================================================
echo "🗑️  Priority 7: Removing old shell scripts..."

OLD_SCRIPTS=(
    "DEPLOY_v2.16.sh"
    "DEPLOY_v2.17.sh"
    "DEPLOY_v2.18.sh"
    "DEPLOY_v2.20.sh"
    "TEST_v2.21.sh"
    "FULL_TEST_v2.21.1.sh"
)

for file in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        DELETED=$((DELETED + 1))
        echo -e "  ${RED}✗${NC} Deleted $file"
    fi
done
echo ""

#==============================================================================
# Priority 8: Organize Setup Guides
#==============================================================================
echo "📚 Priority 8: Organizing setup guides..."

SETUP_GUIDES=(
    "AUTH_SETUP.md"
    "TELEGRAM_SETUP.md"
    "TELEGRAM_CONFIGURATION.md"
    "WHATSAPP_SETUP.md"
    "SSL_SETUP.md"
    "SSL_SETUP_QUICK.md"
    "DOMAIN_SSL_SETUP.md"
    "MONITORING_SETUP.md"
    "PRODUCTION_DEPLOYMENT.md"
)

for file in "${SETUP_GUIDES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/setup/
        MOVED=$((MOVED + 1))
        echo -e "  ${YELLOW}→${NC} Moved $file to docs/guides/setup/"
    fi
done
echo ""

#==============================================================================
# Priority 9: Organize Development Guides
#==============================================================================
echo "📚 Priority 9: Organizing development guides..."

DEV_GUIDES=(
    "ROUTER_GUIDE.md"
    "SERVICE_LAYER_GUIDE.md"
    "SYSTEM_SETTINGS_GUIDE.md"
    "NAVIGATION_QUICK_START.md"
    "GITHUB_WORKFLOWS_GUIDE.md"
    "GITHUB_RELEASE.md"
    "WORKFLOWS_EXPLAINED_RU.md"
    "CONTRIBUTING.md"
)

for file in "${DEV_GUIDES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/development/
        MOVED=$((MOVED + 1))
        echo -e "  ${YELLOW}→${NC} Moved $file to docs/guides/development/"
    fi
done
echo ""

#==============================================================================
# Priority 10: Organize OCR Guides
#==============================================================================
echo "📚 Priority 10: Organizing OCR guides..."

OCR_GUIDES=(
    "OCR_PROVIDERS.md"
    "OCR_TRAINING_GUIDE.md"
    "OCR_TRAINING_HOW_IT_WORKS.md"
    "OCR_TRAINING_SETUP.md"
    "OCR_MULTISELECT_GUIDE.md"
    "OCR_ENHANCEMENTS_v2.6.md"
    "OCR_IMPROVEMENTS_v2.6_FINAL.md"
    "OCR_EDITOR_FIX.md"
)

for file in "${OCR_GUIDES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/ocr/
        MOVED=$((MOVED + 1))
        echo -e "  ${YELLOW}→${NC} Moved $file to docs/guides/ocr/"
    fi
done
echo ""

#==============================================================================
# Priority 11: Organize Architecture Docs
#==============================================================================
echo "📚 Priority 11: Organizing architecture docs..."

ARCH_DOCS=(
    "ARCHITECTURE.md"
    "ARCHITECTURE_AUDIT_v2.16.md"
    "TECHNICAL_DEBT.md"
    "PROJECT_OPTIMIZATION_PLAN_v2.21.3.md"
    "CURSOR_OPTIMIZATION.md"
)

for file in "${ARCH_DOCS[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/architecture/
        MOVED=$((MOVED + 1))
        echo -e "  ${YELLOW}→${NC} Moved $file to docs/architecture/"
    fi
done
echo ""

#==============================================================================
# Priority 12: Organize Release Notes
#==============================================================================
echo "📚 Priority 12: Organizing recent release notes..."

RELEASE_NOTES=(
    "RELEASE_NOTES_v2.20.md"
    "RELEASE_NOTES_v2.21.md"
    "RELEASE_NOTES_v2.21.7.md"
    "RELEASE_NOTES_v2.21.8.md"
    "RELEASE_NOTES_v2.17.md"
    "RELEASE_NOTES_v2.17_RU.md"
    "RELEASE_NOTES_v2.18.md"
)

for file in "${RELEASE_NOTES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/releases/
        MOVED=$((MOVED + 1))
        echo -e "  ${YELLOW}→${NC} Moved $file to docs/releases/"
    fi
done
echo ""

#==============================================================================
# Summary
#==============================================================================
echo "═══════════════════════════════════════════════════════════════"
echo "📊 CLEANUP SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${RED}✗${NC} Deleted:  $DELETED files"
echo -e "  ${GREEN}✓${NC} Archived: $ARCHIVED files"
echo -e "  ${YELLOW}→${NC} Moved:    $MOVED files"
echo ""
echo -e "  ${GREEN}Total cleaned: $((DELETED + ARCHIVED + MOVED)) files${NC}"
echo ""

# Count remaining files in root
REMAINING=$(find . -maxdepth 1 -type f -name "*.md" ! -name "README.md" ! -name "README.ru.md" | wc -l)
echo -e "  📄 Markdown files remaining in root: $REMAINING"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review docs/ structure"
echo "  2. Update references in remaining files"
echo "  3. Commit changes: git add . && git commit -m 'chore: cleanup and organize documentation'"
echo ""

