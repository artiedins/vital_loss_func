# Vitality Loss Function

## The idea

Most AI agents have stale medical training data, but they are strong at translating raw formats (PDFs, lab reports, wearable exports) into structured YAML and reasoning about gradients.

Instead of asking an agent what your bloodwork means from scratch, we encode current cohort and clinical evidence directly into a scalar loss function and let the agent handle format translation and gradient interpretation.

**Loss = -log(composite/100).** Lower is better. Zero is perfect.

The agent reads your raw health documents, maps them to a well-specified schema, runs the script, and returns a prioritized gradient table showing which inputs reduce loss most. The research lives in updateable Python code rather than frozen model weights.

Track the loss curve over months. Down is good. Flat with age is acceptable. Up is a signal.

---

## Quick start

```bash
git clone https://github.com/artiedins/vital_loss_func.git
cd vital_loss_func
pip install pyyaml
mkdir raw_test_results dated_test_results
python3 compute_loss.py   # runs on sample_data or defaults until you add data
```

---

## Using an AI agent

Drop raw health documents (lab PDFs, DEXA/CPET reports, wearable exports) into `raw_test_results/`. Then tell your agent:

> "Read `AGENTS.md` and follow the instructions."

The agent extracts biomarkers, writes dated YAML files to `dated_test_results/` (and `extra_test_results/` for infrequent panels), runs `compute_loss.py`, and interprets the gradient output.

---

## Repository structure

```text
vital_loss_func/
+-- compute_loss.py       # the loss function -- run this
+-- AGENTS.md             # key contract and interpretation guide for agents
+-- README.md             # this file
+-- .gitignore
+-- raw_test_results/     # gitignored -- drop raw documents here
+-- dated_test_results/   # gitignored -- annual and sub-annual YAML files
+-- extra_test_results/   # gitignored -- infrequent/once-per-lifetime YAML files
```

---

## Requirements

- Python 3.8+
- PyYAML: `pip install pyyaml`

---

## Notes

- All personal data directories (`raw_test_results/`, `dated_test_results/`, `extra_test_results/`) are gitignored. Nothing personal touches GitHub.
- Missing inputs fall back to sex-specific US adult (45 to 49) population medians and surface under `TEST THESE`.
- Tests on different dates go in separate files. The script merges using **strictly causal forward-fill** (`d <= target` only, never backfilling future measurements), so historical timeline entries remain immutable when new tests arrive.
- Include `sex: male|female` and `dob: YYYY-MM-DD` (or `birth_year: YYYY`) once in any dated YAML file to activate sex-specific scoring curves and exact-age CKD-EPI 2012 creatinine fallback.

---

## Domain structure and inputs

Seven domains (24 scored biomarkers), each scored 0 to 100 and weighted by mortality and functional-capacity evidence, plus 5 non-scored readouts.

**Fitness / Function: 25%** The only domain directly measuring physiological capacity rather than risk proxies.

- VO2 max (`vo2_max_ml_kg_min`, 35%): incremental lab CPET with metabolic cart; 100 at >=55 (male) / >=45 (female) mL/kg/min, 0 at <=22 / <=19.
- Countermovement jump height (`cmj_height_cm`, 22%): lower-body explosive power, locked to hands-on-hips (akimbo) protocol on a consistent device; 100 at >=46 (male) / >=34 (female) cm, 0 at <=20 / <=14.
- ALMI (`almi_kg_m2`, 18%): appendicular lean mass index from DEXA; 100 at >=9.5 (male) / >=7.5 (female), 0 at <=7.0 / <=5.5 (EWGSOP2 sarcopenia cutoffs).
- Grip strength (`grip_strength_kg`, 15%): dominant hand, calibrated dynamometer; 100 at >=52 (male) / >=36 (female) kg, 0 at <=28 / <=16.
- Heart rate recovery (`heart_rate_recovery_bpm`, 10%): 60-second passive stopped recovery drop after maximal effort (omit active walking cooldowns); 100 at >=30 bpm, 0 at <=10 bpm.

**Cardiovascular: 20%**

- ApoB (`apoB_mg_dl`, 40%): log-scale descending; 100 at <=60 mg/dL, 0 at >=150 mg/dL.
- Systolic BP (`systolic_bp_mmHg`, 30%): tiered scoring with 100 at <=115 mmHg, steps at 120, 130, and 140 mmHg.
- Resting HR (`resting_hr_bpm`, 20%): overnight sleep minimum; 100 at <=48 bpm, 0 at >=95 bpm.
- RDW (`rdw_percent`, 10%): U-shaped plateau; 100 in 12.0 to 13.1%.

**Metabolic: 20%**

- Visceral adipose tissue mass (`vat_mass_lbs`, 25%): raw DEXA CoreScan mass in lbs (log-scale descending; 100 at <=0.75 lb male / <=0.50 lb female, 0 at >=4.50 / >=3.50 lb). Auto-converts `vat_area_cm2` (`/ 44.0`) and legacy `vat_lbs_x313.7_cm2` (`/ 313.7`).
- HbA1c (`hba1c_percent`, 25%): U-shaped plateau; 100 in 5.0 to 5.4%.
- Triglycerides (`triglycerides_mg_dl`, 20%): fasting, log-scale descending; 100 at <=90 mg/dL, 0 at >=400 mg/dL.
- Fat Mass Index (`fmi_kg_m2`, 15%): DEXA total fat mass (kg) / height (m)^2; sex-specific U-shaped plateau (male 2.5 to 3.5, female 4.5 to 6.5 kg/m2) with a gentle low-end taper against excessive leanness.
- HDL-C (`hdl_c_mg_dl`, 15%): sex-specific U-shaped plateau (male 50 to 75, female 60 to 85 mg/dL).

**Sleep / Recovery: 12%**

- Sleep Regularity Index (`sleep_regularity_index`, 55%): 30-day rolling sleep/wake timing consistency; 100 at >=85, 0 at <=45.
- Sleep duration (`sleep_duration_hours`, 45%): asymmetric U-shape; 100 in 6.5 to 8.0 hours, steeper left penalty than right.

**Inflammation: 12%**

- hs-CRP (`hs_crp_mg_l`, 45%): high-sensitivity assay, log-scale descending; 100 at <=0.5 mg/L, 0 at >=15.0 mg/L.
- Homocysteine (`homocysteine_umol_l`, 30%): fasting, U-shaped plateau; 100 in 7.0 to 10.0 umol/L.
- Omega-3 Index (`omega3_1.47x_epa_dha_index_percent`, 25%): RBC-membrane EPA+DHA equivalent (`1.47 * (EPA + DHA)` from whole blood, excluding DPA); 100 at >=8.0%, 0 at <=4.0%.

**Renal / Organ: 6%**

- Cystatin C (`cystatin_c_mg_l`, 60%): log-scale descending; 100 at <=0.85 mg/L, 0 at >=2.0 mg/L (falls back to exact-age, sex-adjusted CKD-EPI 2012 inversion of `egfr_cr_ml_min_1_73m2` until measured directly).
- Urine Albumin-to-Creatinine Ratio (`uacr_mg_g`, 25%): log-scale descending; 100 at <=5.0 mg/g, 0 at >=150 mg/g.
- Serum albumin (`albumin_g_dl`, 15%): linear ascending; 100 at >=4.2 g/dL, 0 at <=3.0 g/dL.

**Hormonal: 5%**

- TSH (`tsh_miu_l`, 60%): optimal plateau 1.9 to 2.9 mIU/L.
- Free T4 (`free_t4_ng_dl`, 40%): optimal plateau 0.9 to 1.4 ng/dL.

**Tracked Readouts (not scored in composite, flagged when <60):**

- Bone mineral density T-score (`bmd_t_score`), fasting glucose (`glucose_mg_dl`), HRV RMSSD (`hrv_ms`), RBC magnesium (`magnesium_rbc_mg_dl`), and methylmalonic acid (`methylmalonic_acid_nmol_l`).

Skewed biomarkers (`apoB_mg_dl`, `vat_mass_lbs`, `triglycerides_mg_dl`, `hs_crp_mg_l`, `cystatin_c_mg_l`, `uacr_mg_g`) are log-transformed before scoring. Four multiplicative interaction penalties apply when co-occurring risk conditions are detected (metabolic syndrome cluster, inflammation plus atherogenic lipids, elevated RDW, poor fitness with high CVD risk).

---

## Key references

- Mandsager et al. *Association of Cardiorespiratory Fitness With Long-term Mortality Among Adults.* JAMA Network Open 2018. https://pubmed.ncbi.nlm.nih.gov/30646252/
- Kokkinos et al. *Cardiorespiratory Fitness and Mortality Risk Across the Spectra of Age, Race, and Sex.* JACC 2022. https://pubmed.ncbi.nlm.nih.gov/35926933/
- Sniderman et al. *The superiority of apolipoprotein B over low-density lipoprotein cholesterol.* JAMA Cardiology 2019. https://pubmed.ncbi.nlm.nih.gov/31642874/
- Cole, Dufresne, Toth, Langlois, Thanassoulis, Sniderman. *ApoB Population-Percentile Equivalents of LDL-C Thresholds.* Journal of Clinical Lipidology 2026. https://pubmed.ncbi.nlm.nih.gov/42844100/
- Bestaoui et al. *GE Lunar iDXA Visceral Adipose Tissue Cutoffs for Metabolic Syndrome.* 2025. https://pubmed.ncbi.nlm.nih.gov/40924743/
- Kelly, Wilson, Heymsfield. *Dual Energy X-Ray Absorptiometry Body Composition Reference Values from NHANES.* PLoS ONE 2009. https://pubmed.ncbi.nlm.nih.gov/19753111/
- Xu et al. (Thyroid Studies Collaboration). *Thyroid function and mortality in older adults.* Lancet Diabetes & Endocrinology 2023. https://pubmed.ncbi.nlm.nih.gov/37696273/
- Windred, Cain, Phillips et al. *Sleep regularity is a stronger predictor of mortality risk than sleep duration.* Sleep 2024, UK Biobank n=88,975. https://pubmed.ncbi.nlm.nih.gov/37738616/
- Yang et al. *Development and validation of a blood biomarker score for mortality prediction.* Journal of Translational Medicine 2023. https://translational-medicine.biomedcentral.com/articles/10.1186/s12967-023-04334-w
- Harris and Von Schacky. *The Omega-3 Index: a new risk factor for death from coronary heart disease?* Prev Med 2004 (and Stark et al., Prostaglandins 2016 for the 1.47x whole-blood conversion). https://pubmed.ncbi.nlm.nih.gov/15208005/
- Chen et al. *OMICmAge: An integrative multi-omics approach to quantify biological age.* Nature Aging 2026. https://www.nature.com/articles/s43587-026-01073-7

---

## Citation

If this project informs your work, a mention would be appreciated:

Dins, A. (2026). *Vitality Loss Function*. GitHub. https://github.com/artiedins/vital_loss_func
