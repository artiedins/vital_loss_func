#!/usr/bin/env python3
# Vitality Loss Function — compute_loss.py
#
# loss = -log(composite/100). Lower is better. Zero is perfect.
# Down over time is good. Flat with aging is acceptable. Up is a signal.
#
# See AGENT.md for data preparation, key definitions, and interpretation.

import yaml, math
from pathlib import Path
from datetime import date

RESULTS_DIR = Path("dated_test_results")
SAMPLE_DIR = Path("sample_data")

DOMAIN_WEIGHTS = {
    "fitness": 0.25,
    "cardiovascular": 0.20,
    "metabolic": 0.20,
    "sleep": 0.12,
    "inflammation": 0.12,
    "renal": 0.06,
    "hormonal": 0.05,
}

# Used only when a key never appears in any dated results file.
# Represents a health-conscious but non-elite adult baseline.
DEFAULTS = {
    "vo2_max_ml_kg_min": 40.0,
    "grip_strength_kg": 46.0,
    "fev1_percent_predicted": 93.0,
    "heart_rate_recovery_bpm": 25.0,
    "almi_kg_m2": 8.1,
    "apoB_mg_dl": 80.0,
    "systolic_bp_mmHg": 122.0,
    "rdw_percent": 13.2,
    "resting_hr_bpm": 62.0,
    "hba1c_percent": 5.4,
    "fasting_glucose_mg_dl": None,  # null — only used when explicitly measured fasting
    "vat_cm2": 110.0,
    "triglycerides_mg_dl": 100.0,
    "hdl_c_mg_dl": 52.0,
    "sleep_regularity_index": 72.0,
    "sleep_duration_hours": 7.0,
    "hrv_ms": 40.0,
    "sleep_efficiency_percent": 82.0,
    "hs_crp_mg_l": 1.2,
    "homocysteine_umol_l": 9.0,
    "cystatin_c_mg_l": 0.90,
    "egfr_ml_min_1_73m2": 88.0,
    "albumin_g_dl": 4.1,
    "tsh_miu_l": 2.5,
    "free_t4_ng_dl": 1.1,
}

# Score = 100 at these values. Used for gradient computation.
# fasting_glucose excluded — its signal is captured through hba1c blend.
# Three fitness keys are sex-specific — see get_optimal().
OPTIMALS = {
    "vo2_max_ml_kg_min": 52.0,  # male; female = 42.0
    "grip_strength_kg": 52.0,  # male; female = 36.0
    "fev1_percent_predicted": 100.0,
    "heart_rate_recovery_bpm": 30.0,
    "almi_kg_m2": 8.7,  # male; female = 7.5
    "apoB_mg_dl": 55.0,
    "systolic_bp_mmHg": 115.0,
    "rdw_percent": 12.5,
    "resting_hr_bpm": 44.0,
    "hba1c_percent": 5.2,
    "vat_cm2": 80.0,
    "triglycerides_mg_dl": 70.0,
    "hdl_c_mg_dl": 72.0,
    "sleep_regularity_index": 90.0,
    "sleep_duration_hours": 7.2,
    "hrv_ms": 65.0,
    "sleep_efficiency_percent": 90.0,
    "hs_crp_mg_l": 0.3,
    "homocysteine_umol_l": 5.5,
    "cystatin_c_mg_l": 0.75,
    "egfr_ml_min_1_73m2": 95.0,
    "albumin_g_dl": 4.4,
    "tsh_miu_l": 2.4,
    "free_t4_ng_dl": 1.15,
}

# Female-specific thresholds for the three sex-differentiated fitness keys.
# Sources: ACSM/Cooper Institute/FRIEND database (VO2), EWGSOP2 + NAKO n=200K (grip),
#          EWGSOP2 / Tromsø Study (ALMI). Males unchanged.
FEMALE_THRESHOLDS = {
    "vo2_max_ml_kg_min": {"opt": 42.0, "poor": 19.0},
    "grip_strength_kg": {"opt": 36.0, "poor": 16.0},
    "almi_kg_m2": {"opt": 7.5, "poor": 5.5},
}

TEST_METHODS = {
    "vo2_max_ml_kg_min": "Lab VO2 max test (treadmill or cycle ergometer, incremental protocol)",
    "grip_strength_kg": "Handheld dynamometer, dominant hand, best of 3 attempts",
    "fev1_percent_predicted": "Spirometry with GLI-2012 reference equations",
    "heart_rate_recovery_bpm": "HR at peak effort minus HR at exactly 60 seconds after stopping",
    "almi_kg_m2": "DEXA scan with body composition analysis",
    "apoB_mg_dl": "Blood panel — request ApoB specifically (not in all panels)",
    "systolic_bp_mmHg": "Validated BP cuff: seated, rested 5 min, average of 3",
    "rdw_percent": "CBC (complete blood count) — in most standard panels",
    "resting_hr_bpm": "Morning supine 5-min average before rising, before caffeine",
    "hba1c_percent": "Standard blood panel",
    "fasting_glucose_mg_dl": "Standard blood panel, 8+ hours fasted",
    "vat_cm2": "DEXA scan with visceral fat analysis (same scan as ALMI)",
    "triglycerides_mg_dl": "Standard blood panel, fasting preferred",
    "hdl_c_mg_dl": "Standard blood panel",
    "sleep_regularity_index": "Wearable (Oura, WHOOP, Garmin): 30-day rolling SRI",
    "sleep_duration_hours": "Wearable or sleep diary: 30-day average nightly sleep",
    "hrv_ms": "RMSSD: Polar H10 morning supine 5-min or Oura overnight average",
    "sleep_efficiency_percent": "Wearable: 30-day average (time asleep / time in bed × 100)",
    "hs_crp_mg_l": "Blood panel — request HIGH-SENSITIVITY CRP specifically",
    "homocysteine_umol_l": "Blood panel — request specifically",
    "cystatin_c_mg_l": "Blood panel — request specifically (not in standard panels)",
    "egfr_ml_min_1_73m2": "Calculated from creatinine + cystatin C (CKD-EPI 2021)",
    "albumin_g_dl": "Standard blood panel",
    "tsh_miu_l": "Standard blood panel (3rd-generation TSH)",
    "free_t4_ng_dl": "Blood panel — request FREE T4 specifically (not total T4)",
}

DOMAIN_COMPONENTS = {
    "fitness": [
        ("vo2_max_ml_kg_min", 0.35),
        ("grip_strength_kg", 0.25),
        ("fev1_percent_predicted", 0.20),
        ("heart_rate_recovery_bpm", 0.10),
        ("almi_kg_m2", 0.10),
    ],
    "cardiovascular": [
        ("apoB_mg_dl", 0.40),
        ("systolic_bp_mmHg", 0.30),
        ("rdw_percent", 0.15),
        ("resting_hr_bpm", 0.15),
    ],
    "metabolic": [
        ("vat_cm2", 0.35),
        ("hba1c_percent", 0.25),  # blends with fasting_glucose when available
        ("triglycerides_mg_dl", 0.20),
        ("hdl_c_mg_dl", 0.20),
    ],
    "sleep": [
        ("sleep_regularity_index", 0.35),
        ("sleep_duration_hours", 0.30),
        ("hrv_ms", 0.25),
        ("sleep_efficiency_percent", 0.10),
    ],
    "inflammation": [
        ("hs_crp_mg_l", 0.60),
        ("homocysteine_umol_l", 0.40),
    ],
    "renal": [
        ("cystatin_c_mg_l", 0.60),
        ("egfr_ml_min_1_73m2", 0.25),
        ("albumin_g_dl", 0.15),
    ],
    "hormonal": [
        ("tsh_miu_l", 0.60),
        ("free_t4_ng_dl", 0.40),
    ],
}


# ── scoring primitives ─────────────────────────────────────────────────────────


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def _la(v, poor, opt):  # linear ascending: higher = better
    return clamp(100.0 * (v - poor) / (opt - poor))


def _ld(v, opt, poor):  # linear descending: lower = better
    return clamp(100.0 * (poor - v) / (poor - opt))


def _logd(v, opt, poor):  # log descending: lower = better, right-skewed distribution
    lv = math.log(max(v, 0.001))
    return clamp(100.0 * (math.log(poor) - lv) / (math.log(poor) - math.log(opt)))


def get_optimal(key, sex):
    if sex == "female" and key in FEMALE_THRESHOLDS:
        return FEMALE_THRESHOLDS[key]["opt"]
    return OPTIMALS[key]


def score_key(key, value, sex="male"):
    if value is None:
        return None
    v = float(value)

    # fitness — three keys are sex-specific
    if key == "vo2_max_ml_kg_min":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 22.0, 52.0)
    if key == "grip_strength_kg":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 28.0, 52.0)
    if key == "almi_kg_m2":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 7.0, 8.7)

    # fitness — sex-neutral
    if key == "fev1_percent_predicted":
        return _la(v, 60.0, 100.0)
    if key == "heart_rate_recovery_bpm":
        return _la(v, 10.0, 30.0)

    # cardiovascular
    if key == "apoB_mg_dl":
        return _logd(v, 60.0, 150.0)
    if key == "systolic_bp_mmHg":
        if v < 120:
            return 100.0
        if v < 130:
            return 85.0
        if v < 140:
            return 65.0
        return clamp(65.0 - (v - 140.0) * 65.0 / 40.0)
    if key == "rdw_percent":
        if 12.0 <= v <= 13.1:
            return 100.0
        if v < 12.0:
            return _la(v, 10.5, 12.0)
        return _ld(v, 13.1, 16.5)
    if key == "resting_hr_bpm":
        return _ld(v, 48.0, 95.0)

    # metabolic
    if key == "hba1c_percent":
        if 5.0 <= v <= 5.4:
            return 100.0
        if v < 5.0:
            return clamp(70.0 + (v - 4.4) * 30.0 / 0.6)
        if v <= 5.7:
            return clamp(100.0 - (v - 5.4) * 25.0 / 0.3)
        if v <= 6.5:
            return clamp(75.0 - (v - 5.7) * 50.0 / 0.8)
        return clamp(25.0 - (v - 6.5) * 25.0 / 1.5)
    if key == "fasting_glucose_mg_dl":
        return _ld(v, 85.0, 110.0)
    if key == "vat_cm2":
        return _logd(v, 100.0, 300.0)
    if key == "triglycerides_mg_dl":
        return _logd(v, 90.0, 400.0)
    if key == "hdl_c_mg_dl":
        return _la(v, 30.0, 65.0)

    # sleep
    if key == "sleep_regularity_index":
        return _la(v, 45.0, 85.0)
    if key == "sleep_duration_hours":
        if 6.5 <= v <= 8.0:
            return 100.0
        if v < 6.5:
            return clamp(100.0 - (6.5 - v) * 100.0 / 2.0)
        return clamp(100.0 - (v - 8.0) * 30.0 / 1.5)  # shallow right tail: athletes recover longer
    if key == "hrv_ms":
        return _la(v, 18.0, 60.0)
    if key == "sleep_efficiency_percent":
        return _la(v, 65.0, 87.0)

    # inflammation
    if key == "hs_crp_mg_l":
        return _logd(v, 0.5, 15.0)
    if key == "homocysteine_umol_l":
        return _logd(v, 6.5, 25.0)

    # renal
    if key == "cystatin_c_mg_l":
        return _logd(v, 0.85, 2.0)
    if key == "egfr_ml_min_1_73m2":
        return _la(v, 30.0, 90.0)
    if key == "albumin_g_dl":
        return _la(v, 3.0, 4.2)

    # hormonal
    if key == "tsh_miu_l":
        if 1.9 <= v <= 2.9:
            return 100.0
        if v < 1.9:
            return clamp(70.0 + (v - 0.5) * 30.0 / 1.4)
        return clamp(100.0 - (v - 2.9) * 30.0 / 2.1)
    if key == "free_t4_ng_dl":
        if 0.9 <= v <= 1.4:
            return 100.0
        if v < 0.9:
            return _la(v, 0.5, 0.9)
        return _ld(v, 1.4, 2.0)

    return None


# ── composite and loss ─────────────────────────────────────────────────────────


def domain_score(domain, values, sex):
    ws, wt = 0.0, 0.0
    for key, w in DOMAIN_COMPONENTS[domain]:
        if key == "hba1c_percent" and domain == "metabolic":
            s1 = score_key("hba1c_percent", values.get("hba1c_percent"), sex)
            fg = values.get("fasting_glucose_mg_dl")
            if fg is not None and s1 is not None:
                s2 = score_key("fasting_glucose_mg_dl", fg, sex)
                cs = 0.70 * s1 + 0.30 * (s2 if s2 is not None else s1)
            else:
                cs = s1
        else:
            cs = score_key(key, values.get(key), sex)
        if cs is not None:
            ws += w * cs
            wt += w
    return (ws / wt) if wt > 0 else 50.0


def composite_score(values, sex):
    return sum(DOMAIN_WEIGHTS[d] * domain_score(d, values, sex) for d in DOMAIN_WEIGHTS)


def interaction_modifier(values):
    mods = []
    v = values
    if v.get("hba1c_percent", 5.0) > 5.7 and v.get("triglycerides_mg_dl", 100) > 150 and v.get("hdl_c_mg_dl", 60) < 40:
        mods.append(("metabolic_syndrome_cluster", 0.94))
    if v.get("hs_crp_mg_l", 0.5) > 3.0 and v.get("apoB_mg_dl", 70) > 90:
        mods.append(("inflammation_plus_lipids", 0.97))
    if v.get("rdw_percent", 13) > 14.0:
        mods.append(("elevated_rdw", 0.96))
    poor_fit = v.get("vo2_max_ml_kg_min", 50) < 35 or v.get("grip_strength_kg", 50) < 40
    high_cvd = v.get("apoB_mg_dl", 70) > 90 or v.get("systolic_bp_mmHg", 120) > 140
    if poor_fit and high_cvd:
        mods.append(("poor_fitness_high_cvd", 0.93))
    product = 1.0
    for _, m in mods:
        product *= m
    return product, mods


def compute_loss(values, sex):
    comp = composite_score(values, sex)
    mod, mods = interaction_modifier(values)
    adjusted = clamp(comp * mod, lo=0.5, hi=100.0)
    return -math.log(adjusted / 100.0), adjusted, mods


# ── data loading and nearest-neighbor fill ─────────────────────────────────────


def load_dated_files():
    src = RESULTS_DIR
    using_sample = False
    if not RESULTS_DIR.exists() or not any(RESULTS_DIR.glob("*.yaml")):
        src = SAMPLE_DIR
        using_sample = True

    files = []
    raw_paths = sorted(src.glob("*.yaml"))

    for f in raw_paths:
        try:
            stem = f.stem.replace("results_", "")
            parts = stem.replace("-", "_").split("_")
            dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
            with open(f) as fp:
                raw = yaml.safe_load(fp) or {}
            data = {}
            for k, val in raw.items():
                if k not in DEFAULTS:
                    continue
                if val is None:
                    data[k] = None
                else:
                    try:
                        data[k] = float(val)
                    except (TypeError, ValueError):
                        pass
            files.append((dt, data))
        except Exception as e:
            print(f"# Skipping {f.name}: {e}")

    return sorted(files, key=lambda x: x[0]), using_sample, raw_paths


def load_sex(raw_paths):
    # Read sex from any YAML file that specifies it; default to male.
    for f in raw_paths:
        with open(f) as fp:
            raw = yaml.safe_load(fp) or {}
        if raw.get("sex") in ("male", "female"):
            return raw["sex"]
    return "male"


def fill_for_date(target, dated_files):
    # for each key, use the measurement nearest in time; fall back to default if never measured
    result = dict(DEFAULTS)
    for key in DEFAULTS:
        best_dist, best_val = float("inf"), None
        for d, vals in dated_files:
            if key in vals and vals[key] is not None:
                dist = abs((target - d).days)
                if dist < best_dist:
                    best_dist, best_val = dist, vals[key]
        if best_val is not None:
            result[key] = best_val
    return result


def measured_keys_ever(dated_files):
    seen = set()
    for _, vals in dated_files:
        for k, v in vals.items():
            if v is not None and k in DEFAULTS:
                seen.add(k)
    return seen


def key_source(key, target, dated_files):
    best_dist, best_date = float("inf"), None
    for d, vals in dated_files:
        if key in vals and vals[key] is not None:
            dist = abs((target - d).days)
            if dist < best_dist:
                best_dist, best_date = dist, d
    return f"measured:{best_date}" if best_date else "DEFAULT"


# ── gradient analysis ──────────────────────────────────────────────────────────


def compute_gradients(values, current_loss, measured, sex):
    results = []
    for key in OPTIMALS:
        opt = get_optimal(key, sex)
        test = dict(values)
        test[key] = opt
        new_loss, _, _ = compute_loss(test, sex)
        delta = current_loss - new_loss
        if delta > 0.001:
            sc = score_key(key, values.get(key), sex)
            src = "measured" if key in measured else "DEFAULT"
            results.append((key, values.get(key), opt, sc, delta, src))
    return sorted(results, key=lambda x: -x[4])


# ── output ─────────────────────────────────────────────────────────────────────


def main():
    dated_files, using_sample, raw_paths = load_dated_files()
    sex = load_sex(raw_paths)

    if not dated_files:
        print("# No data files found.")
        print("# Add results_YYYY_MM_DD.yaml files to dated_test_results/")
        print("# See AGENT.md for format and key definitions.")
        return

    if using_sample:
        print("# Using sample_data/ for demonstration — add files to dated_test_results/ for real results")

    measured = measured_keys_ever(dated_files)

    # compute loss for every dated file
    timeline = []
    for dt, _ in dated_files:
        vals = fill_for_date(dt, dated_files)
        loss, comp, mods = compute_loss(vals, sex)
        timeline.append((dt, loss, comp, mods, vals))

    # primary output: one line per date, machine-readable
    for dt, loss, _, _, _ in timeline:
        print(f"{dt.strftime('%Y_%m_%d')} {loss:.4f}")

    print()
    print("---")
    print()

    latest_dt, latest_loss, latest_comp, latest_mods, latest_vals = timeline[-1]

    # data coverage
    scoreable = [k for k in DEFAULTS if k != "fasting_glucose_mg_dl"]
    never = [k for k in scoreable if k not in measured]
    print(f"DATA COVERAGE  (as of {latest_dt}  sex={sex})")
    print(f"  measured : {len(measured)} / {len(scoreable)}")
    if never:
        print(f"  defaults : {', '.join(never)}")
    print()

    # latest values per domain
    print(f"LATEST VALUES  composite={latest_comp:.1f}/100  loss={latest_loss:.4f}")
    print(f"  {'key':<32} {'value':>8}  {'score':>6}  source")
    print(f"  {'─'*32} {'─'*8}  {'─'*6}  {'─'*22}")
    for domain, components in DOMAIN_COMPONENTS.items():
        print(f"  [{domain}  weight={DOMAIN_WEIGHTS[domain]:.0%}]")
        for key, _ in components:
            val = latest_vals.get(key)
            sc = score_key(key, val, sex)
            src = key_source(key, latest_dt, dated_files)
            vs = f"{val:.2f}" if isinstance(val, (int, float)) and val is not None else "—"
            ss = f"{sc:.1f}" if sc is not None else "—"
            flag = "  ← LOW" if sc is not None and sc < 60 else ""
            print(f"  {key:<32} {vs:>8}  {ss:>6}  {src}{flag}")
    print()

    # interaction penalties
    if latest_mods:
        print("INTERACTION PENALTIES")
        for name, val in latest_mods:
            print(f"  ✗ {name}: {(1 - val) * 100:.0f}% composite reduction")
    else:
        print("INTERACTION PENALTIES  none active")
    print()

    # gradient table
    grads = compute_gradients(latest_vals, latest_loss, measured, sex)
    print("GRADIENT ANALYSIS  (loss reduction if key reaches optimal)")
    print(f"  {'#':<3} {'key':<32} {'current':>8} {'optimal':>8} {'score':>6} {'Δloss':>7}  source")
    print(f"  {'─'*3} {'─'*32} {'─'*8} {'─'*8} {'─'*6} {'─'*7}  {'─'*10}")
    for i, (key, cur, opt, sc, delta, src) in enumerate(grads[:15], 1):
        cs = f"{cur:.2f}" if cur is not None else "—"
        ss = f"{sc:.1f}" if sc is not None else "—"
        print(f"  {i:<3} {key:<32} {cs:>8} {opt:>8.2f} {ss:>6} {delta:>7.4f}  {src}")
    print()

    # priority targets split by source
    default_grads = [(k, c, o, s, d) for k, c, o, s, d, src in grads if src == "DEFAULT"]
    measured_grads = [(k, c, o, s, d) for k, c, o, s, d, src in grads if src != "DEFAULT"]

    print("PRIORITY TARGETS")
    if default_grads:
        print("  A. GET THESE TESTS  (high-gradient keys on defaults — real values may move loss significantly)")
        for key, cur, opt, sc, delta in default_grads[:5]:
            method = TEST_METHODS.get(key, "see AGENT.md")
            print(f"     Δloss={delta:.4f}  {key:<32}  {method}")
    if measured_grads:
        print()
        print("  B. INTERVENTION TARGETS  (measured, suboptimal — these are your gradient descent steps)")
        for key, cur, opt, sc, delta in measured_grads[:5]:
            cs = f"{cur:.2f}" if cur is not None else "?"
            print(f"     Δloss={delta:.4f}  {key:<32}  current={cs}  target={opt:.2f}  score={sc:.1f}/100")

    print()
    print("---")
    print("Paste this output to an AI agent alongside AGENT.md Section B for interpretation.")


if __name__ == "__main__":
    main()
