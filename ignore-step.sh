#!/bin/bash

# ================================================================
# Vercel Deployment Filter
# Only deploy when FRONTEND files change
# ================================================================

echo "🔍 Checking what changed..."

# Get changed files
CHANGED_FILES=$(git diff --name-only HEAD^ HEAD 2>/dev/null || echo "")

# If git diff fails (first deployment), deploy anyway
if [ -z "$CHANGED_FILES" ]; then
  echo "✅ DEPLOYING: Initial deployment or can't detect changes"
  exit 1
fi

echo "Changed files:"
echo "$CHANGED_FILES"

# Backend files that Vercel should ignore
BACKEND_ONLY_PATTERN="^(app\.py|requirements\.txt|render\.yaml|Dockerfile|\.dockerignore|__pycache__|\.pytest_cache)"

# Filter to see if we have ANY non-backend changes
NON_BACKEND_CHANGES=$(echo "$CHANGED_FILES" | grep -vE "$BACKEND_ONLY_PATTERN")

if [ -z "$NON_BACKEND_CHANGES" ]; then
  echo "🛑 SKIPPING VERCEL: Only backend files changed"
  echo "   Backend files: $CHANGED_FILES"
  echo "   → HF Space will handle this deployment"
  echo "   → Saving Vercel deployment quota"
  exit 0
else
  echo "✅ DEPLOYING VERCEL: Frontend files changed:"
  echo "$NON_BACKEND_CHANGES"
  exit 1
fi