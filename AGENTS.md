# AGENTS.md: Vitality Loss Function

## What This Is

A scalar health loss function: `loss = -log(composite/100)`. Zero is perfect. Down over time is good. Flat with aging is acceptable. Up is a signal.

The composite is a weighted sum across seven physiological domains (24 scored biomarkers), plus 5 tracked readouts (recovery, bone guardrail, glycemic context, and supplement markers) that are printed and flagged when low without shifting composite weights. Domain weights reflect relative mortality and functional-capacity evidence from large cohort studies. The full scoring logic is in `compute_loss.py`.

**Your role:** You may be asked to do one or both of:

- **Section A:** Preprocess raw health documents into dated YAML files.
- **Section B:** Interpret computed output and advise the human.

---

## Workflow

### If you can execute code (e.g., coding agent, Claude Code, OpenClaw)

1. Read `AGENTS.md` (this file).
2. Optionally read `compute_loss.py` for exact scoring thresholds.
3. Read documents in `raw_test_results/`.
4. Write dated YAML files to `dated_test_results/` (and `extra_test_results/` for infrequent panels).
5. Run `python3 compute_loss.py`.
6. Interpret output and advise.

### If you cannot execute code (e.g., web interface)

1. Human uploads raw health documents to you.
2. You produce YAML content; human saves as `dated_test_results/results_YYYY_MM_DD.yaml`.
3. Human runs `python3 compute_loss.py`.
4. Human pastes full output back to you.
5. You interpret and advise.

---

## Section A: Creating Dated YAML Files

### Location and naming

Write annual or sub-annual test results to `dated_test_results/` and less frequent test results (multi-year or once-per-lifetime markers such as Lp(a), Cystatin C, NMR subfractions, Free T4/T3, and sex hormone panels) to `extra_test_results/`. Filename format in both directories is `results_YYYY_MM_DD.yaml` using the **test date**, not today's date. `compute_loss.py` loads and merges both directories by date.

Use one file per test date per directory. If a blood panel was drawn on March 1 and a DEXA scan was done on March 15, write two separate files. The script merges them using **strictly causal forward-fill**: for each target date, it uses the most recent measurement on or before that date (`d <= target`) and falls back to sex-specific population medians (`DEFAULTS`) for any biomarker not yet measured. Future measurements never backfill earlier dates, so historical timeline values stay immutable as new tests are added.

### Rules

- **Omit keys you cannot confidently extract.** Do not guess or estimate. A missing key falls back to a population median default and surfaces in `TEST THESE`, which is better than an invented number.
- If a document reports units different from the contract below, convert before writing.
- Add a YAML comment at the top of each file noting the source document(s) and relevant context (fasting status, lab name, device/protocol used for DEXA, CPET, CMJ, sleep, or HRV).
- Fasting status matters for glucose and triglycerides; always annotate it.
- For sleep and HRV values derived from a wearable, note the device and method in a comment and use a 30-day rolling average, not a single-night reading.

### Example file header

```yaml
# Blood panel: comprehensive metabolic + lipid + thyroid + hs-CRP + homocysteine
# Draw date: 2025-03-01. Fasting: yes (12 hours).
# Fitness and sleep keys are stored in separate dated files.

sex: male
dob: 1980-01-15
apoB_mg_dl: 68.0
hba1c_percent: 5.2
# ...
```

---

## The Key Contract

All keys, units, and scoring intent. Include only keys you can confidently derive.

### Global profile parameters

**sex** (`male` or `female`): Include this key in any one of your dated YAML files. It applies globally to the scoring session and does not need to be repeated in every file. If absent, the script defaults to `male`. Seven scoring curves differ by sex (`vo2_max_ml_kg_min`, `grip_strength_kg`, `cmj_height_cm`, `almi_kg_m2`, `vat_mass_lbs`, `fmi_kg_m2`, `hdl_c_mg_dl`), as do the creatinine-to-cystatin C fallback factor and sex-specific interaction cutoffs.

**dob** (`YYYY-MM-DD`, or `birth_year: YYYY`): Include in any one dated YAML file. Used to calculate exact age on each test date when inverting CKD-EPI 2012 from creatinine eGFR if Cystatin C has not yet been measured. If absent, the fallback assumes age 45.

```yaml
sex: female
dob: 1980-05-14
```

---

### Fitness / Function (domain weight: 25%)

**vo2_max_ml_kg_min** (mL/kg/min, within-domain weight: 35%): Maximum oxygen uptake from an incremental lab CPET protocol (treadmill or cycle ergometer) with a metabolic cart. Do not use formula estimates from resting HR or submaximal step tests (roughly +-15% error). Confirm maximal effort via peak RER >= 1.10 or a clear VO2 plateau before accepting the value. Linear ascending: 100 at >=55.0 (male) or >=45.0 (female), 0 at <=22.0 (male) or <=19.0 (female). The 55/45 targets build an aging reserve (given ~10%/decade physiological decline) so elite cardiovascular capacity holds into later decades. Sources: Mandsager et al., JAMA Netw Open 2018; Kokkinos et al., JACC 2022; FRIEND database, Mayo Clin Proc 2015.

**cmj_height_cm** (cm, within-domain weight: 22%): Countermovement jump height, capturing lower-body explosive power (rate of force development and type II fast-twitch fiber recruitment). Lower-body power declines roughly twice as fast with age as isometric strength or lean mass and governs reactive balance, acceleration, and jumping ability. Measure when fresh after a standardized warm-up using an optical/laser contact timer (e.g., OVR Jump), force plate, or validated contact mat; take the best of 3 to 5 maximal attempts.

**Protocol lock:** Always use **hands-on-hips (akimbo)** and record the same device across sessions. Free-arm swing adds ~15 to 20% via upper-body momentum, and cross-device offsets between force plates, optical timers, and phone apps can exceed 5 cm. Do not mix arm-swing and akimbo values or compare across different devices. Linear ascending: 100 at >=46.0 cm (male) or >=34.0 cm (female), 0 at <=20.0 cm (male) or <=14.0 cm (female).

**almi_kg_m2** (kg/m2, within-domain weight: 18%): Appendicular Lean Mass Index from DEXA: `(arms lean + legs lean in kg) / (height in meters)^2`. Linear ascending: 100 at >=9.5 (male) or >=7.5 (female), 0 at <=7.0 (male) or <=5.5 (female). The male lower bound (7.0) and female lower bound (5.5) match the EWGSOP2 sarcopenia cutoffs. Sources: Cruz-Jentoft et al., Age Ageing 2019; Tromso Study 2015-16.

**grip_strength_kg** (kg, within-domain weight: 15%): Dominant hand, best of 3 attempts with a calibrated handheld dynamometer (Jamar or equivalent). Linear ascending: 100 at >=52.0 kg (male) or >=36.0 kg (female), 0 at <=28.0 kg (male) or <=16.0 kg (female). Sources: Cruz-Jentoft et al., Age Ageing 2019; Thorand et al., Age Ageing 2023.

**heart_rate_recovery_bpm** (bpm, within-domain weight: 10%): HR at peak effort minus HR exactly 60 seconds after stopping exercise, measured with a chest HR strap (not optical wrist). Linear ascending: 100 at >=30 bpm, 0 at <=10 bpm.

**Protocol lock:** Valid only for **passive stopped recovery** (standing still or seated immediately after peak effort) following a near-maximal test (VO2 max CPET, maximal ramp test, or all-out interval finish). Do **not** record HRR from submaximal/Zone 2 workouts or from **active walking/jogging cooldowns** (e.g., 2.0 mph treadmill walk), which suppress the 60-second HR drop (often down to 10 to 18 bpm) and do not match the stopped-recovery mortality norms. If the test used an active cooldown or was submaximal, omit this key and note the reason in a YAML comment.

---

### Cardiovascular (domain weight: 20%)

**apoB_mg_dl** (mg/dL, within-domain weight: 40%): Apolipoprotein B by NMR or immunonephelometry. Must be requested specifically. Log-scale descending: 100 at <=60 mg/dL, 0 at >=150 mg/dL. Linear and nonlinear Mendelian randomization in UK Biobank (n=347,797; JAMA Netw Open 2024, PMID 38241044; J Lipid Res 2024, PMID 38458338) show a monotonic causal effect of ApoB on CAD, CVD mortality, and all-cause mortality with no lower J-curve. Untreated NHANES population-percentile equivalents map LDL-C 70 mg/dL to ApoB 58 mg/dL and LDL-C 100 mg/dL to ApoB 79 mg/dL (Cole, Sniderman et al., J Clin Lipidol 2026, PMID 42844100).

**systolic_bp_mmHg** (mmHg, within-domain weight: 30%): Seated, rested 5 minutes, validated automated cuff, average of 3 readings spaced 1 minute apart. Tiered scoring: 100 at <=115, 92 for (115, 120), 85 for [120, 130), 65 for [130, 140), declining linearly to 0 at 180.

**resting_hr_bpm** (bpm, within-domain weight: 20%): Overnight minimum from a validated wearable capturing true cardiac minimum during sleep. Linear descending: 100 at <=48 bpm, 0 at >=95 bpm.

**rdw_percent** (%, within-domain weight: 10%): Red cell distribution width from CBC. U-shaped plateau: 100 in 12.0 to 13.1%, declining to 0 at <=10.5% or >=16.5%.

---

### Metabolic (domain weight: 20%)

**vat_mass_lbs** (lbs, within-domain weight: 25%): Visceral adipose tissue mass directly in pounds from DEXA CoreScan (or converted from grams via `g / 453.592`). Log-scale descending: 100 at <=0.75 lb (male) or <=0.50 lb (female), 0 at >=4.50 lb (male) or >=3.50 lb (female). GE Lunar iDXA metabolic-syndrome cutoffs sit at 1,369 g (3.02 lb) in men and 1,082 g (2.39 lb) in women (Bestaoui et al., 2025, PMID 40924743). If CoreScan reads `0.00` to `0.15 lbs` in a very lean person, record the printed value directly (it is at or below the ~60 g scanner precision floor and scores 100); do not fabricate an estimated value.

*Legacy/area compatibility:* If a DEXA report prints only VAT area in cm2, enter `vat_area_cm2` and `compute_loss.py` converts via `vat_area_cm2 / 44.0` (~11 cm android slab: `453.592 / 0.94 / 11`). Legacy `vat_lbs_x313.7_cm2` files are automatically undone via `/ 313.7` to recover raw lbs.

**hba1c_percent** (%, within-domain weight: 25%): NGSP-standardized HbA1c. U-shaped plateau: 100 in 5.0 to 5.4% (mortality nadir ~5.38%, JCEM 2019, n=15,869), mildly penalized below 5.0% (70 at 4.4%), tapering to 75 at 5.7%, 25 at 6.5%, and 0 at 8.0%.

**triglycerides_mg_dl** (mg/dL, within-domain weight: 20%): Fasting preferred (8+ hours). Log-scale descending: 100 at <=90 mg/dL, 0 at >=400 mg/dL.

**fmi_kg_m2** (kg/m2, within-domain weight: 15%): Fat Mass Index from DEXA: `total fat mass (kg) / (height in meters)^2`. Captures subcutaneous and total adiposity that VAT misses when VAT is near zero, while remaining independent of lean mass. U-shaped plateau: male 100 in 2.5 to 3.5 kg/m2 (tapers to 50 at 1.5 kg/m2 to guard against excessive leanness/RED-S, and linearly to 0 at 9.0 kg/m2); female 100 in 4.5 to 6.5 kg/m2 (50 at 3.0 kg/m2, 0 at 13.0 kg/m2). Sources: Kelly et al., PLoS ONE 2009; NHANES DXA reference distributions.

**hdl_c_mg_dl** (mg/dL, within-domain weight: 15%): Standard lipid panel. Sex-specific U-shaped plateau reflecting the observed J-curve at extreme HDL-C (>80 to 100 mg/dL): male 100 in 50 to 75 mg/dL (0 at <=30 or >=110); female 100 in 60 to 85 mg/dL (0 at <=35 or >=120).

---

### Sleep / Recovery (domain weight: 12%)

Requires a validated wearable for best accuracy. Missing keys fall back to population defaults.

**sleep_regularity_index** (0 to 100, within-domain weight: 55%): Consistency of sleep/wake timing over a 30-day rolling average. Linear ascending: 100 at >=85, 0 at <=45. Source: Windred et al., Sleep 2024 (UK Biobank, n=88,975).

**sleep_duration_hours** (hours, within-domain weight: 45%): Average nightly time asleep (not time in bed), 30-day rolling average. Asymmetric U-shape: 100 in 6.5 to 8.0 hours, steep left penalty (0 at 4.5 h), shallower right penalty (70 at 9.5 h).

---

### Inflammation (domain weight: 12%)

**hs_crp_mg_l** (mg/L, within-domain weight: 45%): High-sensitivity CRP (standard CRP has a ~3 to 5 mg/L floor and cannot be used). Avoid testing within 2 weeks of illness, injury, vaccination, or unusually hard exercise. Log-scale descending: 100 at <=0.5 mg/L, 0 at >=15.0 mg/L.

**homocysteine_umol_l** (umol/L, within-domain weight: 30%): Fasting, requested specifically. U-shaped mortality plateau: 100 in 7.0 to 10.0 umol/L, tapering down below 7.0 (-12 pts per umol/L) and above 10.0 (-15 pts per umol/L).

**omega3_1.47x_epa_dha_index_percent** (% RBC-membrane equivalent, within-domain weight: 25%): Omega-3 Index expressed as RBC-membrane EPA+DHA equivalent. Linear ascending: 100 at >=8.0%, 0 at <=4.0%. If your lab reports whole-blood EPA % and DHA % by weight, `compute_loss.py` automatically computes `1.47 * (epa_percent_weight + dha_percent_weight)` (excluding DPA; Stark et al., Prostaglandins 2016; Harris and Von Schacky, Prev Med 2004).

---

### Renal / Organ (domain weight: 6%)

Stages kidney and vascular endothelial health across two orthogonal KDIGO axes: glomerular filtration (`cystatin_c_mg_l`) and glomerular barrier integrity (`uacr_mg_g`), plus serum albumin (`albumin_g_dl`).

**cystatin_c_mg_l** (mg/L, within-domain weight: 60%): Unaffected by muscle mass or creatine supplementation; strongest single blood predictor of mortality (Yang et al., J Transl Med 2023). Log-scale descending: 100 at <=0.85 mg/L, 0 at >=2.0 mg/L.

**uacr_mg_g** (mg/g, within-domain weight: 25%): Urine albumin-to-creatinine ratio. If entered as `urine_albumin_creatinine_ratio_mg_g`, the script aliases it directly; if entered as spot `urine_microalbumin_mg_dl` (with optional `urine_creatinine_mg_dl`), the script converts using `1000 * microalbumin / urine_creatinine` or `10 * microalbumin` at an assumed 100 mg/dL urine creatinine. Log-scale descending: 100 at <=5.0 mg/g, 47.3 at 30 mg/g, 0 at >=150 mg/g.

**egfr_cr_ml_min_1_73m2** (mL/min/1.73m2, fallback input only): Creatinine-based eGFR from standard blood panels. On dates where `cystatin_c_mg_l` has not yet been measured, `compute_loss.py` inverts CKD-EPI 2012 using exact age (`dob`) and `sex` (0.932 factor for females) to populate the filtration slot and flags the creatinine source in output.

**albumin_g_dl** (g/dL, within-domain weight: 15%): Serum albumin. Linear ascending: 100 at >=4.2 g/dL, 0 at <=3.0 g/dL.

---

### Hormonal (domain weight: 5%)

**tsh_miu_l** (mIU/L, within-domain weight: 60%): 3rd-generation TSH. Optimal plateau 1.9 to 2.9 mIU/L (Xu et al., Lancet Diabetes Endocrinol 2023, n=134K+), tapering to 70 at 0.5 and 70 at 5.0.

**free_t4_ng_dl** (ng/dL, within-domain weight: 40%): Free T4 (total T4 is not equivalent). Optimal plateau 0.9 to 1.4 ng/dL, linear to 0 at <=0.5 or >=2.0.

---

### Readout Keys (tracked and flagged when <60, not scored in composite)

These 5 keys appear under `READOUTS` and print an action note when they fall below score 60 (`LOW`), without adding noise or double-counting to the composite loss:

- **bmd_t_score** (SD): Total-body or clinical hip/spine DEXA T-score. Linear ascending: 100 at >=0.0, 60 at -1.0 (WHO osteopenia boundary, flags `LOW` below -1.0), 0 at <=-2.5 (WHO osteoporosis).
- **glucose_mg_dl** (mg/dL): Fasting glucose readout paired alongside HbA1c. Linear descending: 100 at <=90 mg/dL, 0 at >=125 mg/dL.
- **hrv_ms** (ms, RMSSD): Autonomic recovery readout (morning supine 5-min chest strap or 30-day wearable overnight average). Linear ascending: 100 at >=48 ms, 0 at <=20 ms. Declines naturally with age (~0.5 to 1 ms/year); use sudden drops or low baselines to pace high-intensity/plyometric load vs easy aerobic work.
- **magnesium_rbc_mg_dl** (mg/dL): RBC magnesium supplement readout. U-shaped plateau: 100 in 5.5 to 6.5 mg/dL, 0 at <=4.0 or >=8.0.
- **methylmalonic_acid_nmol_l** (nmol/L): Functional B12 status readout. Linear descending: 100 at <=150 nmol/L, 0 at >=300 nmol/L.

---

### Interaction Penalties

Multiplicative reductions applied to the composite when co-occurring risk conditions are present:

| Condition | Trigger | Reduction |
|---|---|---|
| Metabolic syndrome cluster | HbA1c >5.7 AND triglycerides >150 AND HDL <40 (male) or <50 (female) | 6% |
| Inflammation + atherogenic lipids | hs-CRP >3.0 AND ApoB >90 | 3% |
| Elevated RDW | RDW >14.0% | 4% |
| Poor fitness + high CVD risk | (VO2 <35 male / <28 female OR grip <40 male / <24 female) AND (ApoB >90 OR SBP >140) | 7% |

---

## Section B: Interpreting Output

### Output structure

Lines matching `YYYY_MM_DD NNNN.NNNN` are the primary loss curve. Everything after `---` is analysis (coverage, latest domain values, readouts, interaction penalties, gradient ranking, and priority tiers).

### The loss value

`loss = -log(composite/100)`. At composite=100, loss=0.0000. At composite=90, loss=0.1054. At composite=70, loss=0.3567. Improvements from low scores register larger loss drops than equal point gains near 100.

**What the trend means:**

- Loss decreasing over time: interventions are working, or new tests confirm values better than population defaults.
- Loss flat over a year: maintaining position despite aging.
- Loss increasing: real physiological decline, or previously unmeasured poor values revealed by new tests. Because fill is strictly causal, past timeline entries never shift retroactively when new tests arrive.

### The gradient table and priority tiers

The gradient table ranks every scored biomarker by `delta_loss` (the loss drop if that key moved from its current value to optimal). Every optimal in `OPTIMALS` sits on the exact 100-point edge (or plateau midpoint) of `score_key()`, so targets never overshoot.

`compute_loss.py` partitions keys into five operational buckets:

- **FOCUS:** Measured keys above the sharpest drop-off (`>=35%` cliff) in `delta_loss`. The short list worth new training, nutrition, or clinical effort.
- **NEXT TIER:** Measured keys below the cliff with `score < 92` and `delta_loss >= 0.005`. Real secondary levers; keep progressing without crowding out `FOCUS`.
- **TEST THESE:** Unmeasured keys currently on population `DEFAULTS` with `delta_loss > 0.001`. Test these before guessing interventions.
- **KEEP DOING:** High-scoring measured keys (`>=92` or small gradient) whose win depends on ongoing habits or therapy. Sustain them; do not add unnecessary extra volume.
- **CUT LOOSE:** High-scoring measured keys with no direct behavioral lever (renal/thyroid labs). Ignore unless a trend turns.

### Advising the human

Address items in this order:

1. **Active interaction penalties** and **LOW (`<60`) readout flags** (e.g., osteopenia `bmd_t_score < -1.0`, B12/magnesium deficiency, or suppressed HRV indicating recovery mismatch).
2. **`TEST THESE` default keys** with large `delta_loss` so real measurements replace population medians.
3. **`FOCUS` keys** first, then **`NEXT TIER`** keys, using domain-appropriate levers:
   - **Fitness:** Polarized endurance (1 to 2x/week VO2 max intervals such as 4x4 min at 90 to 95% HRmax, or low-impact incline/bike intervals when tendons are sensitive, layered on top of an easy sub-LT1 aerobic base); progressive lower-body strength plus maximal-intent plyometrics with gradual tendon load progression for CMJ; hypertrophy resistance training + protein + 5 g creatine for ALMI; heavy carries/dead hangs/pulling for grip.
   - **Cardiovascular:** ApoB responds to saturated fat reduction, soluble fiber (psyllium), and lipid-lowering therapy (ezetimibe 10 mg lowers ApoB ~15 to 18%; low-dose statin + ezetimibe lowers ApoB ~40 to 50%); systolic BP responds to aerobic volume, sodium/potassium balance, and sleep.
   - **Metabolic:** VAT and FMI respond to modest energy deficit, high protein, and consistent aerobic + resistance volume; triglycerides respond to refined-carb/alcohol reduction and omega-3; HDL responds to aerobic activity.
   - **Sleep:** Fixed wake time drives SRI; protecting the sleep opportunity window drives duration.
   - **Inflammation:** Aerobic base, lean body composition, and omega-3 (~2 to 4 g/day EPA+DHA) drive hs-CRP and the Omega-3 Index; B12/methylfolate lower elevated homocysteine toward the 7 to 10 umol/L plateau.
   - **Renal / Hormonal:** Flag out-of-range values for clinical evaluation. When Cystatin C shows a creatinine fallback note, recommend a direct Cystatin C blood test to remove muscle-mass and creatine confounding.

### On defaults vs measurements

Always check `DATA COVERAGE` (`measured : X / 24`). A loss of 0.15 with 24/24 measured carries far higher certainty than 0.15 with 10/24 measured. When the sleep domain is on defaults (no wearable), flag that it covers 12% of the composite.

### What this function cannot tell you

This loss function captures 24 scored biomarkers and 5 readouts, not every aspect of health. It does not capture sleep architecture, cognitive function, tendon/joint load tolerance, advanced inflammatory cytokines (IL-6, TNF-alpha), coronary artery calcium / CT angiography, or genetic risk (such as Lp(a)). Treat high scores as strong evidence within scope, not a substitute for clinical care or injury management.
