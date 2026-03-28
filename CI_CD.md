# CI/CD Integration

Integrate Crible into your CI/CD pipeline to automatically assess skill files on commits or pull requests.

## Quick Example: Fail on Critical Findings

```bash
#!/bin/bash
# Run assessment and fail if critical findings exist

crible assess skill.md --format json --no-review --output report.json

CRITICAL=$(jq '.summary.by_severity.critical' report.json)

if [ "$CRITICAL" -gt 0 ]; then
    echo "❌ $CRITICAL critical findings detected"
    exit 1
fi
```

---

## GitHub Actions

`.github/workflows/skill-quality.yml`:

```yaml
name: Skill Quality Check

on:
  pull_request:
    paths:
      - 'skills/**/*.md'

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Crible
        run: pip install git+https://github.com/fjag/crible.git

      - name: Assess Skills
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for skill in skills/**/*.md; do
            crible assess "$skill" --format json --no-review --output "${skill%.md}_report.json"
          done

      - name: Check Results
        run: |
          for report in skills/**/*_report.json; do
            CRITICAL=$(jq '.summary.by_severity.critical' "$report")
            [ "$CRITICAL" -gt 0 ] && echo "❌ $report has $CRITICAL critical findings" && exit 1
          done

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: crible-reports
          path: skills/**/*_report.json
```

**Setup:** Add `ANTHROPIC_API_KEY` to repository secrets (Settings → Secrets and variables → Actions)

---

## GitLab CI

`.gitlab-ci.yml`:

```yaml
skill_quality:
  stage: test
  image: python:3.9
  before_script:
    - pip install git+https://github.com/fjag/crible.git
  script:
    - |
      for skill in skills/**/*.md; do
        crible assess "$skill" --format json --no-review --output "${skill%.md}_report.json"
      done
    - |
      for report in skills/**/*_report.json; do
        CRITICAL=$(jq '.summary.by_severity.critical' "$report")
        [ "$CRITICAL" -gt 0 ] && echo "❌ Critical findings in $report" && exit 1
      done
  artifacts:
    when: always
    paths:
      - skills/**/*_report.json
    expire_in: 30 days
  only:
    changes:
      - skills/**/*.md
```

**Setup:** Add `ANTHROPIC_API_KEY` as masked CI/CD variable (Settings → CI/CD → Variables)

---

## Advanced Patterns

### Conditional Failure by Severity

```bash
# Fail on critical, warn on high warning count
CRITICAL=$(jq '.summary.by_severity.critical' report.json)
WARNINGS=$(jq '.summary.by_severity.warning' report.json)

if [ "$CRITICAL" -gt 0 ]; then
    echo "❌ Build failed: $CRITICAL critical findings"
    exit 1
elif [ "$WARNINGS" -gt 5 ]; then
    echo "⚠️ Warning: $WARNINGS warnings exceed threshold"
    # exit 0 to pass, or exit 1 to fail
fi
```

### Cost Control

```bash
# Use Haiku model for cost-effective CI runs
crible assess skill.md --model haiku --no-review --format json

# Skip expensive Layer 2 if not needed
crible assess skill.md --skip-layer 2 --no-review --format json
```

### Pre-commit Hook

`.git/hooks/pre-commit`:

```bash
#!/bin/bash
CHANGED_SKILLS=$(git diff --cached --name-only | grep '\.md$')

for skill in $CHANGED_SKILLS; do
    crible assess "$skill" --format json --no-review --output /tmp/report.json
    CRITICAL=$(jq '.summary.by_severity.critical' /tmp/report.json)
    if [ "$CRITICAL" -gt 0 ]; then
        echo "❌ $skill has critical findings. Run: crible assess $skill"
        exit 1
    fi
done
```

Make executable: `chmod +x .git/hooks/pre-commit`

---

## See Also

- [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md) - Interactive usage patterns
- [OUTPUTS.md](OUTPUTS.md) - Report format details
