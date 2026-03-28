# CI/CD Integration

Crible can be integrated into continuous integration pipelines to automatically assess skill files on commits, pull requests, or scheduled runs.

## Quick Start

### Fail Build on Critical Findings

```bash
#!/bin/bash
# Run Crible assessment and fail if critical findings exist

crible assess skill.md --format json --no-review --output report.json

# Check if critical findings > 0
CRITICAL_COUNT=$(jq '.summary.by_severity.critical' report.json)

if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo "❌ Assessment failed: $CRITICAL_COUNT critical findings"
    exit 1
else
    echo "✅ Assessment passed: No critical findings"
    exit 0
fi
```

### Generate Report Artifact

```bash
# Generate human-readable report as build artifact
crible assess skill.md --no-review --output report.md

# Archive for later review
mkdir -p build/reports
mv report.md build/reports/
```

---

## GitHub Actions

### Example Workflow

`.github/workflows/skill-quality.yml`:

```yaml
name: Skill Quality Assessment

on:
  pull_request:
    paths:
      - 'skills/**/*.md'
  push:
    branches:
      - main

jobs:
  assess:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Crible
        run: |
          pip install git+https://github.com/fjag/crible.git

      - name: Run Crible Assessment
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for skill in skills/**/*.md; do
            echo "Assessing $skill..."
            crible assess "$skill" --format json --no-review --output "${skill%.md}_report.json"
          done

      - name: Check for Critical Findings
        run: |
          FAILED=0
          for report in skills/**/*_report.json; do
            CRITICAL=$(jq '.summary.by_severity.critical' "$report")
            if [ "$CRITICAL" -gt 0 ]; then
              echo "❌ $report: $CRITICAL critical findings"
              FAILED=1
            fi
          done

          if [ "$FAILED" -eq 1 ]; then
            exit 1
          fi

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: crible-reports
          path: skills/**/*_report.json
```

### Secrets Configuration

In your GitHub repository:
1. Go to **Settings → Secrets and variables → Actions**
2. Add secret: `ANTHROPIC_API_KEY`
3. Paste your API key

---

## GitLab CI

### Example Pipeline

`.gitlab-ci.yml`:

```yaml
stages:
  - quality

skill_assessment:
  stage: quality
  image: python:3.9
  before_script:
    - pip install git+https://github.com/fjag/crible.git
  script:
    - |
      for skill in skills/**/*.md; do
        echo "Assessing $skill..."
        crible assess "$skill" --format json --no-review --output "${skill%.md}_report.json"
      done
    - |
      FAILED=0
      for report in skills/**/*_report.json; do
        CRITICAL=$(jq '.summary.by_severity.critical' "$report")
        if [ "$CRITICAL" -gt 0 ]; then
          echo "❌ $report: $CRITICAL critical findings"
          FAILED=1
        fi
      done

      if [ "$FAILED" -eq 1 ]; then
        exit 1
      fi
  artifacts:
    when: always
    paths:
      - skills/**/*_report.json
    expire_in: 30 days
  only:
    changes:
      - skills/**/*.md
```

### Variables Configuration

In GitLab project:
1. Go to **Settings → CI/CD → Variables**
2. Add variable: `ANTHROPIC_API_KEY`
3. Mark as **Masked** and **Protected**

---

## Jenkins

### Jenkinsfile Example

```groovy
pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install git+https://github.com/fjag/crible.git'
            }
        }

        stage('Assess Skills') {
            steps {
                sh '''
                    for skill in skills/**/*.md; do
                        echo "Assessing $skill..."
                        crible assess "$skill" --format json --no-review --output "${skill%.md}_report.json"
                    done
                '''
            }
        }

        stage('Check Quality') {
            steps {
                script {
                    def failed = false

                    sh '''
                        for report in skills/**/*_report.json; do
                            CRITICAL=$(jq '.summary.by_severity.critical' "$report")
                            if [ "$CRITICAL" -gt 0 ]; then
                                echo "❌ $report: $CRITICAL critical findings"
                                exit 1
                            fi
                        done
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'skills/**/*_report.json', allowEmptyArchive: true
        }
    }
}
```

---

## Advanced Patterns

### Conditional Failure by Severity

```bash
# Fail on critical, warn on warnings, ignore info
CRITICAL=$(jq '.summary.by_severity.critical' report.json)
WARNINGS=$(jq '.summary.by_severity.warning' report.json)

if [ "$CRITICAL" -gt 0 ]; then
    echo "❌ Build failed: $CRITICAL critical findings"
    exit 1
elif [ "$WARNINGS" -gt 5 ]; then
    echo "⚠️ Build passed with warnings: $WARNINGS warnings (threshold: 5)"
    exit 0
else
    echo "✅ Build passed: No issues"
    exit 0
fi
```

### Layer-Specific Checks

```bash
# Only fail on Layer 1 (ambiguity) and Layer 3 (domain constraints)
LAYER1=$(jq '.summary.by_layer["1"]' report.json)
LAYER3=$(jq '.summary.by_layer["3"]' report.json)

if [ "$LAYER1" -gt 0 ] || [ "$LAYER3" -gt 0 ]; then
    echo "❌ Ambiguity or domain issues detected"
    exit 1
fi
```

### Comparison with Baseline

```bash
# Compare current assessment with previous run
CURRENT_CRITICAL=$(jq '.summary.by_severity.critical' report.json)
BASELINE_CRITICAL=$(jq '.summary.by_severity.critical' baseline_report.json)

if [ "$CURRENT_CRITICAL" -gt "$BASELINE_CRITICAL" ]; then
    echo "❌ Quality regression: critical findings increased from $BASELINE_CRITICAL to $CURRENT_CRITICAL"
    exit 1
fi
```

### Cost Control

```bash
# Use Haiku model for cost-effective CI runs
crible assess skill.md --model haiku --no-review --format json
```

### Batch Processing with Parallelization

```bash
# Parallel assessment using GNU parallel
find skills/ -name "*.md" | parallel -j4 \
    'crible assess {} --format json --no-review --output {.}_report.json'
```

---

## Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook: Assess changed skill files

CHANGED_SKILLS=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$')

if [ -z "$CHANGED_SKILLS" ]; then
    exit 0
fi

echo "Running Crible assessment on changed skills..."

for skill in $CHANGED_SKILLS; do
    crible assess "$skill" --format json --no-review --output /tmp/report.json

    CRITICAL=$(jq '.summary.by_severity.critical' /tmp/report.json)

    if [ "$CRITICAL" -gt 0 ]; then
        echo "❌ $skill has $CRITICAL critical findings. Commit blocked."
        echo "Run: crible assess $skill (to review interactively)"
        exit 1
    fi
done

echo "✅ All skill files passed quality checks"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Cost Management in CI/CD

### Track Token Usage

```bash
# Aggregate token costs across all assessments
jq -s 'map(.execution_metadata.total_tokens) | add' skills/**/*_report.json

# Estimate total cost (Sonnet: $3 per 1M input tokens, $15 per 1M output tokens)
# Approximation: average $6 per 1M tokens
TOTAL_TOKENS=$(jq -s 'map(.execution_metadata.total_tokens) | add' skills/**/*_report.json)
COST=$(echo "scale=4; $TOTAL_TOKENS / 1000000 * 6" | bc)
echo "Estimated cost: \$$COST"
```

### Set Budget Limits

```bash
# Fail if token usage exceeds budget
MAX_TOKENS=50000  # ~$0.30 budget
TOTAL_TOKENS=$(jq -s 'map(.execution_metadata.total_tokens) | add' skills/**/*_report.json)

if [ "$TOTAL_TOKENS" -gt "$MAX_TOKENS" ]; then
    echo "⚠️ Token budget exceeded: $TOTAL_TOKENS / $MAX_TOKENS"
    exit 1
fi
```

---

## Notifications

### Slack Integration

```bash
# Send results to Slack
CRITICAL=$(jq '.summary.by_severity.critical' report.json)
WARNINGS=$(jq '.summary.by_severity.warning' report.json)

if [ "$CRITICAL" -gt 0 ]; then
    MESSAGE="❌ Skill assessment failed: $CRITICAL critical, $WARNINGS warnings"
    COLOR="danger"
else
    MESSAGE="✅ Skill assessment passed: $WARNINGS warnings"
    COLOR="good"
fi

curl -X POST -H 'Content-type: application/json' \
    --data "{\"attachments\":[{\"color\":\"$COLOR\",\"text\":\"$MESSAGE\"}]}" \
    $SLACK_WEBHOOK_URL
```

### Email Reports

```bash
# Email summary
SUMMARY=$(jq -r '.summary | to_entries | map("\(.key): \(.value)") | join(", ")' report.json)

echo "$SUMMARY" | mail -s "Crible Assessment Results" team@example.com
```

---

## Best Practices

1. **Run on Pull Requests:** Catch quality issues before merging
2. **Use `--no-review` flag:** Skip interactive mode in CI
3. **Archive JSON reports:** Enable historical analysis
4. **Set reasonable thresholds:** Don't block on every warning
5. **Use Haiku for cost control:** Save Sonnet for manual reviews
6. **Track token usage:** Monitor API costs over time
7. **Combine with other checks:** Linting, testing, manual review
8. **Schedule periodic runs:** Re-assess skills as Crible improves

---

## Troubleshooting

### API Rate Limits

```bash
# Add retry logic
for i in {1..3}; do
    crible assess skill.md --no-review --format json && break
    echo "Retrying in 5 seconds..."
    sleep 5
done
```

### Timeout Handling

```bash
# Set timeout for long-running assessments
timeout 5m crible assess skill.md --no-review --format json || echo "Assessment timed out"
```

### Missing API Key

```bash
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not set"
    exit 1
fi
```

---

## See Also

- [Output Examples](OUTPUTS.md) - Report format details
- [Usage Examples](USAGE_EXAMPLE.md) - Interactive usage patterns
- JSON Schema documentation (coming soon)
