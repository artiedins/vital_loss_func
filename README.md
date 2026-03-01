# Vitality Loss Function

## The idea

Most AI agents have stale medical training data. But they're excellent at translating formats — PDFs, lab reports, wearable exports — into structured YAML. And they understand loss functions.

So instead of asking an agent "what does my bloodwork mean," we encoded the latest research directly into a scalar loss function, then let the agent do what it's actually good at: format translation and gradient interpretation.

**Loss = −log(composite/100).** Lower is better. Zero is perfect.

The agent reads your raw health documents, maps them to a well-specified schema, runs the script, and gets back a prioritized gradient table — exactly which inputs, if improved, would reduce the loss most. It doesn't need to know the underlying medicine. The research is already baked into the function. The agent just needs to help you descend the gradient.

This works with any capable LLM. Even models with outdated medical knowledge can translate a lab PDF into YAML and interpret "move this value toward the target to reduce loss." The research injection happens at design time, not inference time.

Track the loss curve over months. Down is good. Flat with age is acceptable. Up is a signal.

---

## Quick start

```bash
git clone https://github.com/artiedins/vital_loss_func.git
cd vital_loss_func
pip install pyyaml
mkdir raw_test_results dated_test_results
python compute_loss.py   # runs on defaults until you add data
```

---

## Using an AI agent

Drop your raw health documents (lab PDFs, wearable exports, test reports, any format) into `raw_test_results/`. Then tell your agent:

> "Read `AGENT.md` and follow the instructions."

The agent will extract biomarkers, write dated YAML files to `dated_test_results/`, run the script, and interpret the gradient output. If your agent can execute code, this is a single session. If you're using a web interface, `AGENT.md` walks through the manual steps.

---

## Repository structure

```
vital_loss_func/
├── compute_loss.py       # the loss function — run this
├── AGENT.md              # instructions for AI agents (and curious humans)
├── README.md             # this file
├── .gitignore
├── raw_test_results/     # gitignored — drop raw documents here
└── dated_test_results/   # gitignored — agent writes YAML here
```

---

## Requirements

- Python 3.8+
- PyYAML: `pip install pyyaml`

---

## Notes

- Both data directories are gitignored. Nothing personal touches GitHub.
- Missing inputs fall back to population-based defaults. Loss curve relevance improves as real measurements replace defaults.
- Tests on different dates go in separate files. The script merges automatically using nearest-in-time values per key.
- The function is intentionally stable. It should not change unless substantive new research warrants updating it.

---

## Domain structure and inputs

For clinicians and technically-minded readers. Seven domains, each scored 0–100 and weighted by evidence for mortality and functional-capacity outcomes.

**Fitness / Function — 25%**
The only domain measuring actual physiological capacity rather than risk proxies. Weighted highest accordingly.
- VO2 max (mL/kg/min) — maximal oxygen uptake, incremental lab protocol
- Grip strength (kg) — dominant hand, calibrated dynamometer
- FEV1 % predicted — spirometry, GLI-2012 reference equations
- Heart rate recovery (bpm) — 1-minute post-maximal-effort drop
- ALMI (kg/m²) — appendicular lean mass index from DEXA

**Cardiovascular — 20%**
- ApoB (mg/dL) — preferred over LDL-C; captures atherogenic particle burden directly
- Systolic BP (mmHg) — tiered scoring with thresholds at 120 and 130
- RDW (%) — red cell distribution width; U-shaped mortality relationship
- Resting HR (bpm) — morning supine, before caffeine

**Metabolic — 20%**
- VAT (cm²) — visceral adipose tissue from DEXA; more metabolically relevant than total body fat
- HbA1c (%) — U-shaped scoring; values below 5.0% mildly penalized
- Fasting glucose (mg/dL) — optional; blends 70/30 with HbA1c when present
- Triglycerides (mg/dL) — fasting preferred
- HDL-C (mg/dL)

**Sleep / Recovery — 12%**
- Sleep Regularity Index (0–100) — consistency of sleep/wake timing; 30-day rolling
- Sleep duration (hours) — asymmetric U-shape; right tail penalty shallower than left
- HRV RMSSD (ms) — morning supine or overnight average; absolute thresholds (declines naturally with age by design)
- Sleep efficiency (%) — time asleep / time in bed

**Inflammation — 12%**
- hs-CRP (mg/L) — high-sensitivity required; standard CRP insufficient for optimization
- Homocysteine (μmol/L) — fasting; must be requested specifically

**Renal / Organ — 6%**
- Cystatin C (mg/L) — stronger predictor than creatinine; must be requested specifically
- eGFR (mL/min/1.73m²) — CKD-EPI 2021 combined equation preferred
- Albumin (g/dL)

**Hormonal — 5%**
- TSH (mIU/L) — optimal window 1.9–2.9 mIU/L; standard clinical range too broad for vitality optimization
- Free T4 (ng/dL) — free fraction required; total T4 not equivalent

Skewed biomarkers (ApoB, VAT, triglycerides, hs-CRP, homocysteine, cystatin C) are log-transformed before scoring. Four multiplicative interaction penalties apply when co-occurring risk conditions are detected (metabolic syndrome cluster, inflammation plus atherogenic lipids, elevated RDW, poor fitness with high CVD risk).

---

## Key references

A few of the less obvious design decisions are backed by recent large-cohort findings worth verifying directly.

- Mandsager et al. — *Association of Cardiorespiratory Fitness With Long-term Mortality Among Adults* — JAMA Network Open 2018. The VO2 max mortality curves that justify the 25% domain weight. https://pubmed.ncbi.nlm.nih.gov/30646252/
- Xu et al. (Thyroid Studies Collaboration) — *Thyroid function and mortality in older adults* — Lancet Diabetes & Endocrinology 2023, n=134,000+. The basis for the 1.9–2.9 mIU/L optimal TSH window rather than standard clinical range. https://pubmed.ncbi.nlm.nih.gov/37696273/
- Windred, Cain, Phillips et al. — *Sleep regularity is a stronger predictor of mortality risk than sleep duration* — Sleep 2024, UK Biobank n=88,975. Nonlinear mortality association with sleep/wake timing consistency, independent of duration and cardiovascular risk factors. https://pubmed.ncbi.nlm.nih.gov/37738616/
- Yang et al. — *Development and validation of a blood biomarker score for mortality prediction* — Journal of Translational Medicine 2023. Cystatin C as the strongest single blood predictor; basis for its 60% within-domain weight. https://translational-medicine.biomedcentral.com/articles/10.1186/s12967-023-04334-w
- Sniderman et al. — *The superiority of apolipoprotein B over low-density lipoprotein cholesterol* — JAMA Cardiology 2019. The ApoB over LDL-C preference; ApoB-LDL discordance and cardiovascular risk. https://pubmed.ncbi.nlm.nih.gov/31642874/
- O'Toole CK et al. (MULTI study, Columbia University) — *Sleep chart of biological aging clocks across organs and omics* — medRxiv preprint August 2025. Optimal sleep window 6.4–7.8h across 23 clocks and 17 organ systems; basis for the asymmetric sleep duration scoring curve. Note: preprint, peer review pending. https://www.medrxiv.org/content/10.1101/2025.08.08.25333313v1
- Chen et al. — *OMICmAge: An integrative multi-omics approach to quantify biological age* — Nature Aging 2026. Empirical validation that multi-domain integration outperforms single-modal clocks; supports the seven-domain architecture. https://www.nature.com/articles/s43587-026-01073-7

---

## Citation

If this project informs your work, a mention would be appreciated:

Dins, A. (2026). *Vitality Loss Function*. GitHub. https://github.com/artiedins/vital_loss_func
