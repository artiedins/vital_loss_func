# Vitality Loss Function

A research-grounded biological vitality tracker built as a scalar loss function.

**Loss = −log(composite/100).** Lower is better. Zero is perfect.  
Track it over time. Down is good. Flat with age is acceptable. Up is a signal.

The scoring encodes current literature across seven physiological domains: fitness, cardiovascular, metabolic, sleep/recovery, inflammation, renal/organ, and hormonal. Domain weights and biomarker thresholds reflect relative mortality and functional-capacity evidence, not population averages. See `AGENT.md` for the full scientific rationale.

---

## Quick Start

```bash
git clone <repo>
cd vital_loss_func
pip install pyyaml

# Add your own raw health data in any format, just dump in this directory:
mkdir raw_test_results

# Tell your agent "Read `AGENT.md` and follow the instructions.", agent will populate:
mkdir dated_test_results

# Then run
python compute_loss.py

# cut and paste output into agent for analysis and actions for improving health/vitality and reducing mortality

```

---

## Using an AI Agent

Tell your agent: **"Read `AGENT.md` and follow the instructions."**

Your agent will:
1. Read your raw health documents from `raw_test_results/`
2. Create formatted `dated_test_results/results_YYYY_MM_DD.yaml` files
3. Run `compute_loss.py` (if it can execute code) or guide you to run it
4. Interpret the output and suggest next steps

If you're using a web-based AI interface, follow the manual workflow in `AGENT.md`.

---

## Repository Structure

```
vitality-loss-function/
├── compute_loss.py          # the loss function — run this
├── AGENT.md                 # instructions for AI agents (and curious humans)
├── README.md                # this file
├── dated_test_results/      # your personal data — gitignored
└── raw_test_results/        # raw documents — gitignored
```

---

## Requirements

- Python 3.8+
- PyYAML: `pip install pyyaml`

---

## Notes

- `dated_test_results/` and `raw_test_results/` are gitignored. Your data stays local.
- Missing keys use population-based defaults. The loss curve improves (in relevance) as you replace defaults with real measurements.
- Tests taken on different dates (blood panel vs DEXA vs fitness) go in separate files. The script handles merging automatically using nearest-in-time values.
- The function is intentionally stable. It should not change unless substantive new research warrants it.
