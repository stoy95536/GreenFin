from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

required = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    ".gitignore",
    ".env.example",
    "docs/PRODUCT_SPEC.md",
    "docs/ARCHITECTURE.md",
    "docs/DOMAIN_MODEL.md",
    "docs/RULES.md",
    "docs/API_SPEC.md",
    "docs/DEMO_SCENARIO.md",
    "docs/DEVELOPMENT_PLAN.md",
    "docs/CURRENT_STAGE.md",
    "docs/DECISIONS.md",
    "logs/templates/AI_CHANGE_LOG_TEMPLATE.txt",
    "logs/templates/TEST_RESULT_TEMPLATE.txt",
]

missing = [p for p in required if not (ROOT / p).exists()]

if missing:
    print("Repository validation FAILED.")
    for p in missing:
        print(f"MISSING: {p}")
    sys.exit(1)

agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
required_phrases = [
    "Build → Test → Verify → Record → Continue",
    "AI Modification Trace Policy",
    "Stage Gate Policy",
    "Evidence First, Rule Driven, Explainable by Design",
]

bad = [x for x in required_phrases if x not in agents]
if bad:
    print("Repository validation FAILED.")
    for x in bad:
        print(f"AGENTS.md missing required phrase: {x}")
    sys.exit(1)

print("Repository validation PASS.")
print(f"Checked {len(required)} required files.")
print("AGENTS.md governance rules detected.")
