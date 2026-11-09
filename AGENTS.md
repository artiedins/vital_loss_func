# AGENTS.md -- Vitality Loss Function

## What This Is

A scalar health loss function: `loss = -log(composite/100)`. Zero is perfect. Down over time is
good. Flat is acceptable. Up is a signal.

The composite is a weighted sum across seven physiological domains, scoring each biomarker against
research-derived optimal thresholds. Domain weights reflect relative mortality and
functional-capacity evidence from large cohort studies. The full scoring logic is in
`compute_loss.py`.

**Your role:** You may be asked to do one or both of:

- **Section A** -- Preprocess raw health documents into dated YAML files
- **Section B** -- Interpret computed output and advise the human

---

## Workflow

### If you can execute code (e.g., coding agent, Claude Code, OpenClaw):

1. Read `AGENTS.md` (this file)
1. Optionally read `compute_loss.py` for exact scoring thresholds
1. Read documents in `raw_test_results/`
1. Write dated YAML files to `dated_test_results/`
1. Run `python compute_loss.py`
1. Interpret output and advise

### If you cannot execute code (e.g., web interface):

1. Human uploads raw health documents to you
1. You produce YAML content -> human saves as `dated_test_results/results_YYYY_MM_DD.yaml`
1. Human runs `python compute_loss.py`
1. Human pastes full output back to you
1. You interpret and advise

---

## Section A: Creating Dated YAML Files

### Location and naming

Write annual or sub-annual test results to `dated_test_results/` and less frequent test results
(multi-year or once-per-lifetime markers such as Lp(a), Cystatin C, NMR subfractions, Free T4/T3,
and sex hormone panels) to `extra_test_results/`. Filename format in both directories:
`results_YYYY_MM_DD.yaml` using the **test date**, not today's date. Both `compute_loss.py` and
`compute_loss_v2.py` load and merge both directories by date.

One file per test date per directory. If a blood panel was drawn on March 1st and a DEXA scan was
done on March 15th, write two separate files. The script merges them using causal forward-fill
(most recent measurement on or before the target date, falling back to the earliest future
measurement only before a biomarker's first draw).

### Rules

- **Omit keys you cannot confidently extract.** Do not guess or estimate. A missing key falls back
  to a population default, which is better than a wrong value.
- If a document gives units different from the contract below, convert before writing.
- Add a YAML comment at the top of each file noting the source document(s) and any relevant context
  (fasting status, lab name, device used for sleep/HRV).
- Fasting status matters for glucose and triglycerides -- always annotate.
- For sleep and HRV values derived from a wearable, note the device and method in a comment and use
  a 30-day rolling average, not a single-night reading.

### Example file header

```yaml
# Blood panel -- comprehensive metabolic + lipid + thyroid + hs-CRP + homocysteine
# Draw date: 2025-03-01. Fasting: yes (12 hours).
# Fitness and sleep keys not in this file -- in separate dated files.

apoB_mg_dl: 68.0
hba1c_percent: 5.2
# ...
```

---

## The Key Contract

All keys, units, and scoring intent. Include only keys you can confidently derive.

### Global parameter

**sex** -- `male` or `female` Include this key in any one of your dated YAML files. It applies
globally to the entire scoring session -- you do not need to repeat it in every file. If absent, the
script defaults to `male`. Four fitness scoring curves differ by sex (VO2 max, grip strength, CMJ
height, ALMI); all other biomarker thresholds are sex-neutral.

```yaml
sex: female
```

---

### Fitness / Function (domain weight: 25%)

**vo2_max_ml_kg_min** -- mL/kg/min (within-domain weight: 30%) Maximum oxygen uptake. Must be from a
proper incremental lab protocol (Bruce, Balke, or cycle ergometer equivalent) with a metabolic cart.
Do not use formula estimates from resting HR or submaximal step tests -- these have +-15% error and
will corrupt this domain. Confirm maximal effort via peak RER >= 1.10 before accepting the value.
Score 100 at >=52 (male) or >=42 (female), 0 at \<=22 (male) or \<=19 (female). Sources: ACSM/Cooper
Institute normative data; FRIEND database, Mayo Clinic Proceedings 2015.

**grip_strength_kg** -- kg (within-domain weight: 20%) Dominant hand, best of 3 attempts with a
calibrated handheld dynamometer (Jamar or equivalent). Score 100 at >=52 kg (male) or >=36 kg
(female), 0 at \<=28 kg (male) or \<=16 kg (female). Female poor threshold is the EWGSOP2 sarcopenia
cutoff, validated in German National Cohort n=200,389. Sources: Cruz-Jentoft et al. Age Ageing 2019;
Thorand et al. Age Ageing 2023.

**cmj_height_cm** -- cm (within-domain weight: 20%) Countermovement jump height, capturing lower-body
explosive power (rate of force development and type II fast-twitch fiber recruitment). Lower-body
power declines roughly twice as fast with age (~3-3.5%/year after age 40) as isometric strength
(~1.5-2%/year) or lean mass (~1%/year), and is the primary determinant of reactive balance, slip
recovery, and agility in pickup sports. Measure when fresh after a standardized warm-up using an
optical/laser flight-time device (e.g., OVR Jump), force plate, or validated contact mat; take the
best of 3-5 maximal attempts. Keep arm protocol consistent across sessions (hands-on-hips akimbo
isolates lower-body extension; free-arm swing adds ~10-15% via shoulder/trunk momentum -- note the
protocol and device in a YAML comment). Score 100 at >=45 cm (male) or >=32 cm (female), 0 at \<=20
cm (male) or \<=14 cm (female).

**almi_kg_m2** -- kg/m2 (within-domain weight: 15%) Appendicular Lean Mass Index from DEXA: (arms +
legs lean mass in kg) / height in meters squared. Same DEXA scan as vat_lbs_x313.7_cm2. Score 100 at
\>=9.5 kg/m2 (male) or >=7.5 kg/m2 (female), 0 at \<=7.0 kg/m2 (male) or \<=5.5 kg/m2 (female). The
male optimal of 9.5 corresponds to the longevity 75th percentile; the EWGSOP2 sarcopenia cutoff is
7.0. Sources: Cruz-Jentoft et al. Age Ageing 2019; Tromso Study 2015-16.

**heart_rate_recovery_bpm** -- bpm (within-domain weight: 15%) HR at peak effort minus HR exactly 60
seconds after stopping exercise. Requires a chest HR monitor (not optical wrist) for accuracy. Score
100 at >=30 bpm drop, 0 at \<=10 bpm.

**Critical:** HRR is only valid when measured after a near-maximum effort -- the final minutes of a
VO2 max test, a hard interval session, or a dedicated ramp test. Do not extract HRR from Zone 2
workouts, easy runs, or resting sessions. A Zone 2 HR at end of workout minus HR one minute later
will produce a low number (often 8-15 bpm) that reflects the modest cardiovascular demand of the
session, not the autonomic recovery capacity this metric is designed to capture. If the raw data
does not contain a documented max-effort test, omit this key entirely rather than using a proxy
value.

---

### Cardiovascular (domain weight: 20%)

**apoB_mg_dl** -- mg/dL Apolipoprotein B. NMR or immunonephelometry. Must be requested specifically
-- not included in all standard lipid panels. Score uses log scale: 100 at \<=60 mg/dL, 0 at >=150
mg/dL. Linear and nonlinear Mendelian randomization in the UK Biobank (n=347,797; JAMA Netw Open
2024, PMID 38241044; J Lipid Res 2024, PMID 38458338) demonstrate a monotonically increasing causal
effect of ApoB on coronary artery disease, cardiovascular mortality, and all-cause mortality across
the entire concentration distribution with no lower threshold or J-curve; observational J-curves
below 70 mg/dL reflect reverse causation from frailty and chronic disease. The \<=60 mg/dL anchor
aligns with the untreated NHANES population-percentile equivalent of LDL-C 70 mg/dL (ApoB 58 mg/dL,
~5th-10th percentile; Sniderman et al., J Clin Lipidol 2026, PMID 42844100) and the PESA/FLOWPROMOTE
threshold below which subclinical coronary plaque progression arrests and regression predominates.

**systolic_bp_mmHg** -- mmHg Seated, rested for 5 minutes, validated automated cuff, average of 3
readings with 1-minute intervals. Do not use a single reading. Scoring is tiered: 100 if \<115, 92
if 115-119, 85 if 120-129, 65 if 130-139, declining to 0 at 180. Observational data show continuous
CVD risk reduction down to 115 mmHg; SPRINT validated the \<120 target in an RCT but did not
directly test \<115 vs \<120.

**rdw_percent** -- % Red cell distribution width from a CBC. U-shaped scoring: 100 in the 12.0-13.1%
range, declining to 0 at extremes (\<=10.5% or >=16.5%).

**resting_hr_bpm** -- bpm Overnight minimum from a validated wearable that captures true cardiac
minimum during sleep when sympathetic tone is lowest. Score 100 at \<=48 bpm, 0 at >=95 bpm.

---

### Metabolic (domain weight: 20%)

**hba1c_percent** -- % NGSP-standardized HbA1c. In standard panels. Optimal zone 5.0-5.4% (mortality
nadir at 5.38%, JCEM 2019, n=15,869). Values below 5.0% are mildly penalized -- in athletes this
often reflects faster red blood cell turnover rather than true glycemic benefit. Score 100 at
5.0-5.4%.

**glucose_mg_dl** -- mg/dL (optional) Fasting glucose. When present, blends with HbA1c (70/30) to
form the glycemic component. If absent, HbA1c alone covers glycemic control. Always include if the
blood draw was fasting. Score 100 at \<=85 mg/dL, optimal target 82 mg/dL (80-84 mg/dL is the
T2D-risk nadir from a 12.4M-person cohort study).

**vat_lbs_x313.7_cm2** -- cm2 (enter the converted value, not raw lbs) Visceral adipose tissue area
in cm2, derived from DEXA. Same scan as ALMI. More metabolically relevant than total body fat. Score
uses log scale: 100 at \<=100 cm2, 0 at >=300 cm2.

GE Lunar machines report VAT in lbs. Convert before entering:

```
cm2 = lbs * 313.7
```

The conversion factor 313.7 = 453.592 g/lb / 0.94 g/cm3 * 0.65 cm2/cm3, where 0.94 g/cm3 is visceral
adipose tissue density and 0.65 cm2/cm3 is the volume-to-area conversion for the L1-L4 measurement
region.

```yaml
# GE Lunar scan: VAT reported as 0.16 lbs
# 0.16 * 313.7 = 50.0
vat_lbs_x313.7_cm2: 50.0
```

If a GE Lunar CoreScan displays `0.00 lbs` in a very lean individual, this is a subtraction-floor
artifact (CoreScan models subcutaneous abdominal fat from lateral wall thickness and subtracts it
from total L1-L4 Android fat; when true VAT is below the ~0.3-0.5 lb noise floor, the subtraction
clips at zero). Estimate VAT from Android fat mass and A/G ratio (~0.15-0.25 lbs = 47-78 cm2,
centered at 50.0 cm2 for a lean insulin-sensitive male) and document the estimate in a YAML comment
rather than entering `0.0`.

If your DEXA machine reports VAT Area directly in cm2, enter that value unchanged -- the variable
name documents the conversion for GE Lunar users; the scoring function treats the stored value as
cm2 regardless of how it was derived. Note in a YAML comment which format your machine uses.

**triglycerides_mg_dl** -- mg/dL Fasting preferred (8+ hours). Score uses log scale: 100 at \<=90
mg/dL, 0 at >=400 mg/dL.

**hdl_c_mg_dl** -- mg/dL Standard lipid panel. Score 100 at >=65 mg/dL, 0 at \<=30 mg/dL.

---

### Sleep / Recovery (domain weight: 12%)

This domain requires a wearable for best accuracy. Missing keys fall back to defaults.

**sleep_regularity_index** -- 0-100 (within-domain weight: 40%) Consistency of sleep/wake timing.
Derivable from any wearable that tracks sleep/wake times over 7+ days. If the device does not report
SRI directly, it can be computed as the average daily overlap of sleep windows across consecutive
days. Use a 30-day rolling average. Score 100 at >=85, 0 at \<=45.

**sleep_duration_hours** -- hours (within-domain weight: 30%) Average nightly sleep duration (time
asleep, not time in bed). 30-day average. Score 100 at 6.5-8.0 hours. The penalty for sleeping less
than 6.5h is steep; the penalty for sleeping more than 8.0h is shallow (long sleep in active
individuals often reflects recovery need rather than pathology).

**hrv_ms** -- ms (RMSSD) (within-domain weight: 30%) Root mean square of successive differences in
R-R intervals. Two acceptable sources: (1) chest strap morning supine 5-minute protocol -- lie flat
before rising, no caffeine; (2) wearable overnight average. The morning supine protocol produces a
more controlled, reproducible number; overnight averages are convenient but blend readings across
sleep stages. Do not use HRV readings from during exercise or from optical wrist sensors during
activity. Note the source in a YAML comment. Score 100 at >=60 ms, 0 at \<=18 ms. **This value
declines naturally with age even in healthy individuals -- a declining hrv_ms over years is expected
biology, not failure.**

---

### Inflammation (domain weight: 12%)

**hs_crp_mg_l** -- mg/L (within-domain weight: 45%) HIGH-SENSITIVITY CRP -- must be requested
specifically. Standard CRP panels have a detection floor of ~3-5 mg/L and are useless for
optimization at low levels. Avoid testing within 2 weeks of illness, injury, vaccination, or intense
exercise. Score uses log scale: 100 at \<=0.5 mg/L, 0 at >=15 mg/L.

**homocysteine_umol_l** -- umol/L (within-domain weight: 30%) Fasting. Must be requested
specifically -- not in standard panels. Primary modulators are B12, B6, and folate. Score uses log
scale: 100 at \<=6.5 umol/L, 0 at >=25 umol/L.

**omega3_1.47x_epa_dha_index_percent** -- % RBC-membrane equivalent (within-domain weight: 25%) The
Omega-3 Index, expressed as RBC-membrane EPA+DHA equivalent. Many commercial omega-3 tests report
whole-blood values; you must convert before entering.

**How to derive this value from a whole-blood EPA+DHA result:**

1. Find the EPA % by weight and DHA % by weight values on the report
1. Add them together (do NOT include DPA -- it adds no incremental predictive power to the Index per
   founding Harris/Von Schacky studies and the Atherosclerosis 2017 10-cohort meta-analysis)
1. Multiply the sum by 1.47 (whole-blood to RBC-membrane conversion, Stark et al. Prostaglandins
   2016\)
1. Enter that result as `omega3_1.47x_epa_dha_index_percent`

Example: EPA 0.5% + DHA 3.1% = 3.6% whole-blood. 3.6 x 1.47 = 5.3. Enter 5.3.

Score 100 at >=8% RBC-equivalent (low-risk zone, Harris/Von Schacky 2004), 0 at \<=4%. Intervention:
EPA+DHA supplementation at 2-4g/day typically raises the index 2-3 points over 3-6 months. Retest at
3-month intervals when actively supplementing.

```yaml
# Whole-blood EPA+DHA: EPA 0.5, DHA 3.1, DPA 0.8 (DPA excluded)
# (0.5 + 3.1) * 1.47 = 5.3
omega3_1.47x_epa_dha_index_percent: 5.3
```

---

### Renal / Organ (domain weight: 6%)

The renal domain stages kidney and vascular endothelial health across two orthogonal KDIGO axes:
glomerular filtration (`cystatin_c_mg_l`) and glomerular barrier integrity (`uacr_mg_g`), alongside
serum albumin (`albumin_g_dl`).

**cystatin_c_mg_l** -- mg/L (within-domain weight: 60%) More stable than creatinine; unaffected by
muscle mass or creatine supplementation; strongest single blood predictor of mortality per Yang et
al. 2023. Score uses log scale: 100 at \<=0.85 mg/L, 0 at >=2.0 mg/L. Because CKD-EPI 2012
cystatin-C eGFR is a deterministic function of `cystatin_c_mg_l`, age, and sex, `egfr_ml_min_1_73m2`
is omitted from the domain so the same filtration measurement is not double-counted.

**uacr_mg_g** -- mg/g (within-domain weight: 25%) Urine albumin-to-creatinine ratio (or spot urine
microalbumin; if entered as `urine_microalbumin_mg_dl`, the script converts `1 mg/dL -> 10 mg/g` at
standard ~100 mg/dL urine creatinine). Captures glomerular endothelial barrier integrity and microvascular
health orthogonal to filtration rate. Score uses log scale: 100 at \<=5.0 mg/g, 47.3 at the 30 mg/g
clinical microalbuminuria cutoff, and 0 at >=150 mg/g.

**egfr_cr_ml_min_1_73m2** -- mL/min/1.73m2 (fallback input, not an independent scored slot)
Creatinine-only eGFR from standard blood panels. When `cystatin_c_mg_l` has never been measured, the
script inverts CKD-EPI 2012 to populate the filtration slot and flags the creatinine source in output.

**albumin_g_dl** -- g/dL (within-domain weight: 15%) Serum albumin. Standard panel. Score 100 at
\>=4.2 g/dL, 0 at \<=3.0 g/dL.

---

### Hormonal (domain weight: 5%)

**tsh_miu_l** -- mIU/L 3rd-generation TSH. Optimal range is 1.9-2.9 mIU/L per Lancet Diabetes
Endocrinology 2023 (n=134K UK Biobank participants). Standard clinical range (0.5-4.5) is too broad
for vitality optimization. Score 100 at 1.9-2.9.

**free_t4_ng_dl** -- ng/dL FREE T4 -- must be requested specifically. Total T4 is not equivalent.
Standard reference range 0.8-1.8 ng/dL. Score 100 at 0.9-1.4 ng/dL.

---

### Interaction Penalties

These are multiplicative reductions applied to the composite when co-occurring conditions produce
synergistic (non-additive) risk. The script computes and reports them automatically.

| Condition | Trigger | Reduction | |-----------|---------|-----------| | Metabolic syndrome cluster
| HbA1c >5.7 AND triglycerides >150 AND HDL \<40 | 6% | | Inflammation + atherogenic lipids | hs-CRP
\>3.0 AND ApoB >90 | 3% | | Elevated RDW | RDW >14% | 4% | | Poor fitness + high CVD risk | (VO2 \<35
OR grip \<40) AND (ApoB >90 OR SBP >140) | 7% |

---

## Section B: Interpreting Output

### Output structure

Lines matching `YYYY_MM_DD NNNN.NNNN` are the primary loss curve. Everything after `---` is
debug/analysis.

### The loss value

`loss = -log(composite/100)`. At composite=100, loss=0. At composite=87, loss~=0.14. At
composite=70, loss~=0.36. The scale is non-linear: improvements at the high end (e.g., 90->95) are
harder to achieve and register as smaller loss reductions than equivalent improvements at the low
end (e.g., 60->65). This is intentional.

**What the trend means:**

- Loss decreasing over time: interventions are working or tests are confirming better-than-default
  values
- Loss flat over a year: maintaining position -- acceptable if aging is expected to increase it
- Loss increasing: either real biological decline, or previously unknown poor values being revealed
  by new testing

### The gradient table

The gradient table shows how much the loss would drop if each key were brought to its optimal value.
This is the gradient vector for descending the loss function. It already accounts for domain weights
and within-domain component weights. The keys at the top of the table are where intervention has the
most leverage -- they are, literally, the direction of steepest descent.

**Two source types:**

- `DEFAULT`: This key has never been tested. The gradient reflects the difference between the
  population default and optimal. A high-gradient DEFAULT key means: test this first -- you may
  discover your actual value is better than the default (loss drops) or worse (loss rises, revealing
  a real problem). Either outcome is informative.
- `measured:YYYY-MM-DD`: Real data. A high-gradient measured key is a genuine intervention target.

### Advising the human

Use the gradient table as your primary guide. Address in this order:

1. **High-gradient DEFAULT keys** -- recommend testing. These are the keys most likely to move the
   loss.

1. **High-gradient measured keys** -- recommend interventions. Key levers by domain:

   - **fitness**: Zone 2 cardio (VO2 max, resting HR, HRR), high-intensity intervals (VO2 max
     ceiling), resistance training (ALMI, grip strength), plyometrics and explosive power work
     (CMJ height)
   - **cardiovascular**: ApoB responds to diet (reduce saturated fat, add soluble fiber) and
     lipid-lowering therapy (ezetimibe 10 mg lowers ApoB ~15-18%; low-dose statin + ezetimibe lowers
     ApoB ~40-50%), systolic BP responds to sodium reduction, exercise, sleep
   - **metabolic**: VAT responds to sustained caloric deficit + aerobic exercise; HDL responds to
     Zone 2 cardio and alcohol reduction; triglycerides respond to sugar/refined carb reduction
   - **sleep**: SRI responds to fixed wake time (most powerful lever); sleep duration responds to
     earlier bedtime; HRV responds to reduced alcohol, lower training load, and improved sleep
     quality
   - **inflammation**: hs-CRP responds to weight loss, sleep improvement, anti-inflammatory diet;
     homocysteine responds to methylated B12/B6/folate supplementation (confirm deficiency first);
     omega3 index responds to EPA+DHA supplementation (typically 2-4g/day raises the RBC-equivalent
     index 2-3 points over 3-6 months -- retest at 3 months when actively supplementing; note that
     EPA-only formulations such as icosapent ethyl show stronger cardiovascular event reduction in
     RCTs than combined EPA+DHA products, though both raise the index)
   - **renal**: cystatin C and eGFR -- flag any concerning values for clinical evaluation; when the
     output note says "creatinine source; muscle-mass upward bias possible," recommend upgrading to
     a cystatin C panel; hydration and avoiding nephrotoxic substances are the primary lifestyle
     levers
   - **hormonal**: TSH outside 1.9-2.9 warrants clinical evaluation; do not recommend self-directed
     thyroid intervention

1. **Active interaction penalties** -- these compound risk and should be addressed before marginal
   optimization of individual biomarkers. Metabolic syndrome cluster and poor fitness + high CVD are
   the highest-priority penalties.

### On defaults vs measurements

When many keys are on defaults, the loss value has wide uncertainty. A loss of 0.15 with 18/22 keys
measured is more reliable than 0.15 with 8/22. When advising, note how many keys are on defaults and
which domains they fall in. The sleep domain is commonly all-defaults for users without a wearable
-- flag this explicitly and note it affects the 12% sleep weight.

### Calibration note on HRV

HRV (hrv_ms) declines approximately 0.5-1 ms/year in healthy individuals regardless of fitness. A
gradual decline in this component over years is expected biology. Sudden drops (>10 ms over weeks)
are a signal worth noting. The score does not age-adjust HRV intentionally -- the loss function uses
absolute thresholds so the loss curve naturally rises with aging if nothing else changes, which is
the intended behavior.

### What this function cannot tell you

This loss function captures objectively measurable biomarkers. It does not capture sleep
architecture quality, cognitive function, bone mineral density, advanced inflammatory cytokines
(IL-6, TNF-alpha), lipoprotein particle size, or genetic risk factors. High scores on this function
are meaningful but not complete. Encourage clinical evaluation for any value flagged as LOW or any
interaction penalty that fires.
