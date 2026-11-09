#!/usr/bin/env python3
# Vitality Loss Function -- compute_loss.py
#
# loss = -log(composite/100). Lower is better. Zero is perfect.
# Down over time is good. Flat with aging is acceptable. Up is a signal.
#
# See AGENTS.md for data preparation, key definitions, and interpretation.

# Code style:
# - No type hinting
# - No doc strings
# - No triple quoted multi-line strings
# - No comments with repeated characters for visual page breaks like # ---
# - No non-ascii characters
# - No command line argument processing
# - No global variables unless making them local increases complexity
# - Yes strategic inline comments enhancing rapid code comprehension by real humans
# - Yes if __name__ == "__main__": main()

import yaml, math
from pathlib import Path
from datetime import date

RESULTS_DIR = Path("dated_test_results")
EXTRA_RESULTS_DIR = Path("extra_test_results")
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

DEFAULTS = {
    "vo2_max_ml_kg_min": 49.1,
    "grip_strength_kg": 46.0,
    "cmj_height_cm": 35.0,
    "heart_rate_recovery_bpm": 29.0,
    "almi_kg_m2": 8.7,
    "apoB_mg_dl": 82.0,
    "systolic_bp_mmHg": 112.0,
    "rdw_percent": 11.8,
    "resting_hr_bpm": 52.0,
    "hba1c_percent": 5.3,
    "glucose_mg_dl": 89.0,
    "vat_lbs_x313.7_cm2": 50.0,
    "triglycerides_mg_dl": 54.0,
    "hdl_c_mg_dl": 63.0,
    "sleep_regularity_index": 83.0,
    "sleep_duration_hours": 7.0,
    "hrv_ms": 35.0,
    "hs_crp_mg_l": 0.2,
    "homocysteine_umol_l": 11.0,
    "omega3_1.47x_epa_dha_index_percent": 5.44,
    "cystatin_c_mg_l": 0.85,
    "uacr_mg_g": 10.0,
    "egfr_cr_ml_min_1_73m2": 83.0,
    "albumin_g_dl": 4.7,
    "tsh_miu_l": 2.0,
    "free_t4_ng_dl": 1.4,
    "methylmalonic_acid_nmol_l": 221.0,
    "magnesium_rbc_mg_dl": 4.5,
}

# OPTIMALS are fixed absolute standards, not age-graded. Aspirational capability
# targets are flagged in METRIC_META so rankings distinguish benchmarks from gaps.
OPTIMALS = {
    "vo2_max_ml_kg_min": 52.0,
    "grip_strength_kg": 52.0,
    "cmj_height_cm": 45.0,
    "heart_rate_recovery_bpm": 30.0,
    "almi_kg_m2": 9.5,
    "apoB_mg_dl": 60.0,
    "systolic_bp_mmHg": 112.0,
    "rdw_percent": 12.5,
    "resting_hr_bpm": 44.0,
    "hba1c_percent": 5.2,
    "glucose_mg_dl": 90.0,
    "vat_lbs_x313.7_cm2": 80.0,
    "triglycerides_mg_dl": 70.0,
    "hdl_c_mg_dl": 60.0,
    "sleep_regularity_index": 90.0,
    "sleep_duration_hours": 7.2,
    "hrv_ms": 45.0,
    "hs_crp_mg_l": 0.3,
    "homocysteine_umol_l": 8.5,
    "omega3_1.47x_epa_dha_index_percent": 8.0,
    "cystatin_c_mg_l": 0.75,
    "uacr_mg_g": 5.0,
    "albumin_g_dl": 4.4,
    "tsh_miu_l": 2.4,
    "free_t4_ng_dl": 1.15,
    "methylmalonic_acid_nmol_l": 120.0,
    "magnesium_rbc_mg_dl": 5.8,
}

FEMALE_THRESHOLDS = {
    "vo2_max_ml_kg_min": {"opt": 42.0, "poor": 19.0},
    "grip_strength_kg": {"opt": 36.0, "poor": 16.0},
    "cmj_height_cm": {"opt": 32.0, "poor": 14.0},
    "almi_kg_m2": {"opt": 7.5, "poor": 5.5},
    "hdl_c_mg_dl": {"opt": 70.0, "poor": 35.0},
}

# Readout keys are tracked for workout recovery and supplement dosing without
# shifting composite weights. Non-actionable/settled labs are omitted to keep
# context light and tight for LLM workout and medication/supplement planning.
READOUT_KEYS = {
    "hrv_ms",
    "glucose_mg_dl",
    "methylmalonic_acid_nmol_l",
    "magnesium_rbc_mg_dl",
}

METRIC_META = {
    "vo2_max_ml_kg_min": {"klass": "capability", "intervention": "1-2 month VO2max interval block (e.g. 4x4 min at 90-95% HRmax)", "aspirational": True},
    "grip_strength_kg": {"klass": "capability", "intervention": "heavy carries, dead hangs, pulling resistance", "aspirational": True},
    "cmj_height_cm": {"klass": "capability", "intervention": "CMJ plyometrics + explosive resistance training", "aspirational": True},
    "almi_kg_m2": {"klass": "capability", "intervention": "hypertrophy resistance training + protein + 5g creatine", "aspirational": False},
    "heart_rate_recovery_bpm": {"klass": "autonomic", "intervention": "LT1 jogging volume (sub-LT1 aerobic base)", "aspirational": False},
    "resting_hr_bpm": {"klass": "autonomic", "intervention": "LT1 jogging volume (sub-LT1 aerobic base)", "aspirational": False},
    "apoB_mg_dl": {"klass": "disease", "intervention": "ezetimibe 10mg + psyllium 10g + low saturated fat", "aspirational": False},
    "systolic_bp_mmHg": {"klass": "disease", "intervention": "LT1 aerobic base + sodium/potassium balance", "aspirational": False},
    "rdw_percent": {"klass": "disease", "intervention": "B12 / methylation + iron sufficiency", "aspirational": False},
    "vat_lbs_x313.7_cm2": {"klass": "cardiometabolic", "intervention": "energy balance + LT1 jogging volume", "aspirational": False},
    "hba1c_percent": {"klass": "cardiometabolic", "intervention": "diet quality, post-meal walks, LT1 + resistance volume", "aspirational": False},
    "triglycerides_mg_dl": {"klass": "cardiometabolic", "intervention": "carb/alcohol moderation, omega-3, LT1 volume", "aspirational": False},
    "hdl_c_mg_dl": {"klass": "cardiometabolic", "intervention": "aerobic activity", "aspirational": False},
    "glucose_mg_dl": {"klass": "cardiometabolic", "intervention": "diet quality, post-meal movement", "aspirational": False},
    "sleep_regularity_index": {"klass": "sleep", "intervention": "consistent sleep/wake timing", "aspirational": False},
    "sleep_duration_hours": {"klass": "sleep", "intervention": "protect the sleep opportunity window", "aspirational": False},
    "hs_crp_mg_l": {"klass": "disease", "intervention": "aerobic base, body composition, omega-3", "aspirational": False},
    "homocysteine_umol_l": {"klass": "disease", "intervention": "B12 500-1000mcg/day (+/- methylfolate; target band 7-10 umol/L)", "aspirational": False},
    "omega3_1.47x_epa_dha_index_percent": {"klass": "disease", "intervention": "2 pills/day rTG fish oil (~2g EPA+DHA, e.g. Sports Research AlaskaOmega)", "aspirational": False},
    "cystatin_c_mg_l": {"klass": "renal", "intervention": None, "aspirational": False},
    "uacr_mg_g": {"klass": "renal", "intervention": None, "aspirational": False},
    "albumin_g_dl": {"klass": "renal", "intervention": None, "aspirational": False},
    "tsh_miu_l": {"klass": "hormonal", "intervention": None, "aspirational": False},
    "free_t4_ng_dl": {"klass": "hormonal", "intervention": None, "aspirational": False},
    "hrv_ms": {"klass": "autonomic", "intervention": "autonomic recovery readout -- pace HIIT/CMJ vs LT1 load", "aspirational": False},
    "methylmalonic_acid_nmol_l": {"klass": "supplement", "intervention": "vitamin B12 500-1000 mcg/day (target <150 nmol/L)", "aspirational": False},
    "magnesium_rbc_mg_dl": {"klass": "supplement", "intervention": "magnesium glycinate 200-400 mg elemental/day (target 5.5-6.5 mg/dL)", "aspirational": False},
}

DOMAIN_COMPONENTS = {
    "fitness": [
        ("vo2_max_ml_kg_min", 0.30),
        ("grip_strength_kg", 0.20),
        ("cmj_height_cm", 0.20),
        ("almi_kg_m2", 0.15),
        ("heart_rate_recovery_bpm", 0.15),
    ],
    "cardiovascular": [
        ("apoB_mg_dl", 0.40),
        ("systolic_bp_mmHg", 0.30),
        ("resting_hr_bpm", 0.20),
        ("rdw_percent", 0.10),
    ],
    "metabolic": [
        ("vat_lbs_x313.7_cm2", 0.35),
        ("hba1c_percent", 0.25),
        ("triglycerides_mg_dl", 0.20),
        ("hdl_c_mg_dl", 0.20),
    ],
    "sleep": [
        ("sleep_regularity_index", 0.55),
        ("sleep_duration_hours", 0.45),
    ],
    "inflammation": [
        ("hs_crp_mg_l", 0.45),
        ("homocysteine_umol_l", 0.30),
        ("omega3_1.47x_epa_dha_index_percent", 0.25),
    ],
    "renal": [
        ("cystatin_c_mg_l", 0.60),
        ("uacr_mg_g", 0.25),
        ("albumin_g_dl", 0.15),
    ],
    "hormonal": [
        ("tsh_miu_l", 0.60),
        ("free_t4_ng_dl", 0.40),
    ],
}


# scoring primitives


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def _la(v, poor, opt):
    # linear ascending: poor -> 0, opt -> 100
    return clamp(100.0 * (v - poor) / (opt - poor))


def _ld(v, opt, poor):
    # linear descending: opt -> 100, poor -> 0
    return clamp(100.0 * (poor - v) / (poor - opt))


def _logd(v, opt, poor):
    # log-scale descending: used for skewed biomarkers (ApoB, VAT, uACR, etc.)
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

    if key == "vo2_max_ml_kg_min":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 22.0, 52.0)
    if key == "grip_strength_kg":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 28.0, 52.0)
    if key == "cmj_height_cm":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 20.0, 45.0)
    if key == "almi_kg_m2":
        if sex == "female":
            return _la(v, FEMALE_THRESHOLDS[key]["poor"], FEMALE_THRESHOLDS[key]["opt"])
        return _la(v, 7.0, 9.5)

    if key == "heart_rate_recovery_bpm":
        return _la(v, 10.0, 30.0)

    if key == "apoB_mg_dl":
        return _logd(v, 60.0, 150.0)
    if key == "systolic_bp_mmHg":
        if v < 115:
            return 100.0
        if v < 120:
            return 92.0
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
    if key == "glucose_mg_dl":
        return _ld(v, 90.0, 125.0)
    if key == "vat_lbs_x313.7_cm2":
        return _logd(v, 100.0, 300.0)
    if key == "triglycerides_mg_dl":
        return _logd(v, 90.0, 400.0)
    if key == "hdl_c_mg_dl":
        lo, hi, poor_lo, poor_hi = (60.0, 85.0, 35.0, 120.0) if sex == "female" else (50.0, 75.0, 30.0, 110.0)
        if lo <= v <= hi:
            return 100.0
        if v < lo:
            return _la(v, poor_lo, lo)
        return _ld(v, hi, poor_hi)

    if key == "sleep_regularity_index":
        return _la(v, 45.0, 85.0)
    if key == "sleep_duration_hours":
        if 6.5 <= v <= 8.0:
            return 100.0
        if v < 6.5:
            return clamp(100.0 - (6.5 - v) * 100.0 / 2.0)
        return clamp(100.0 - (v - 8.0) * 30.0 / 1.5)
    if key == "hrv_ms":
        return _la(v, 20.0, 48.0)

    if key == "hs_crp_mg_l":
        return _logd(v, 0.5, 15.0)
    if key == "homocysteine_umol_l":
        # U-shaped mortality band: 7.0-10.0 umol/L plateau
        if 7.0 <= v <= 10.0:
            return 100.0
        if v < 7.0:
            return clamp(100.0 - (7.0 - v) * 12.0)
        return clamp(100.0 - (v - 10.0) * 15.0)
    if key == "omega3_1.47x_epa_dha_index_percent":
        return _la(v, 4.0, 8.0)

    if key == "cystatin_c_mg_l":
        return _logd(v, 0.85, 2.0)
    if key == "uacr_mg_g":
        # KDIGO endothelial barrier axis: <=5 mg/g optimal, >=30 mg/g microalbuminuria
        return _logd(v, 5.0, 150.0)
    if key == "albumin_g_dl":
        return _la(v, 3.0, 4.2)

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

    # readout-only supplement curves (used for display and LOW flagging, never in composite)
    if key == "methylmalonic_acid_nmol_l":
        return _ld(v, 150.0, 300.0)
    if key == "magnesium_rbc_mg_dl":
        if 5.5 <= v <= 6.5:
            return 100.0
        if v < 5.5:
            return _la(v, 4.0, 5.5)
        return _ld(v, 6.5, 8.0)

    return None


# composite and loss


def domain_score(domain, values, sex):
    ws, wt = 0.0, 0.0
    for key, w in DOMAIN_COMPONENTS[domain]:
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


# derived and fallback keys


def derive_computed_keys(values, measured):
    # silent creatinine fallback: when cystatin_c_mg_l has never been measured
    # but creatinine eGFR is present, invert CKD-EPI 2012 so the filtration
    # slot scores from actual bloodwork with a display flag.
    if "cystatin_c_mg_l" not in measured and "egfr_cr_ml_min_1_73m2" in measured:
        egfr = max(15.0, min(140.0, float(values["egfr_cr_ml_min_1_73m2"])))
        base = 133.0 * (0.996**47)
        exp = -0.499 if egfr >= base else -1.328
        values["cystatin_c_mg_l"] = round(0.8 * ((egfr / base) ** (1.0 / exp)), 2)
        values["_cys_from_creatinine"] = True
    return values


def _parse_yaml_into(f, by_date, source_tag):
    try:
        stem = f.stem.replace("results_", "")
        parts = stem.replace("-", "_").split("_")
        dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
        with open(f) as fp:
            raw = yaml.safe_load(fp) or {}
        if "omega3_1.47x_epa_dha_index_percent" not in raw and raw.get("epa_percent_weight") is not None and raw.get("dha_percent_weight") is not None:
            raw["omega3_1.47x_epa_dha_index_percent"] = round(1.47 * (float(raw["epa_percent_weight"]) + float(raw["dha_percent_weight"])), 2)
        if "uacr_mg_g" not in raw:
            if raw.get("urine_albumin_creatinine_ratio_mg_g") is not None:
                raw["uacr_mg_g"] = float(raw["urine_albumin_creatinine_ratio_mg_g"])
            elif raw.get("urine_microalbumin_mg_dl") is not None:
                if raw.get("urine_creatinine_mg_dl") not in (None, 0, 0.0):
                    raw["uacr_mg_g"] = round(1000.0 * float(raw["urine_microalbumin_mg_dl"]) / float(raw["urine_creatinine_mg_dl"]), 2)
                else:
                    # 1 mg/dL spot urine microalbumin ~ 10 mg/g uACR at 100 mg/dL urine creatinine
                    raw["uacr_mg_g"] = round(float(raw["urine_microalbumin_mg_dl"]) * 10.0, 2)
        data = by_date.setdefault(dt, {})
        tags = data.setdefault("_sources", {})
        for k, val in raw.items():
            if k not in DEFAULTS:
                continue
            if val is None:
                data[k] = None
            else:
                try:
                    data[k] = float(val)
                    tags[k] = source_tag
                except (TypeError, ValueError):
                    pass
    except Exception as e:
        print(f"# Skipping {f.name}: {e}")


# data loading and causal forward-fill


def load_dated_files():
    src = RESULTS_DIR
    using_sample = False
    if not RESULTS_DIR.exists() or not any(RESULTS_DIR.glob("*.yaml")):
        src = SAMPLE_DIR
        using_sample = True

    by_date = {}
    raw_paths = sorted(src.glob("*.yaml"))
    for f in raw_paths:
        _parse_yaml_into(f, by_date, "measured")

    if not using_sample and EXTRA_RESULTS_DIR.exists():
        extra_paths = sorted(EXTRA_RESULTS_DIR.glob("*.yaml"))
        for f in extra_paths:
            _parse_yaml_into(f, by_date, "extra")
        raw_paths = raw_paths + extra_paths

    files = sorted(by_date.items(), key=lambda x: x[0])
    return files, using_sample, raw_paths


def load_sex(raw_paths):
    for f in raw_paths:
        with open(f) as fp:
            raw = yaml.safe_load(fp) or {}
        if raw.get("sex") in ("male", "female"):
            return raw["sex"]
    return "male"


def _select_date_for_key(key, target, dated_files):
    # causal forward-fill: prefer most recent measurement on or before target (d <= target);
    # fall back to earliest future measurement only before a biomarker's first draw.
    past_dist, past_date, past_val, past_tag = float("inf"), None, None, "measured"
    fut_dist, fut_date, fut_val, fut_tag = float("inf"), None, None, "measured"
    for d, vals in dated_files:
        if key in vals and vals[key] is not None:
            diff = (target - d).days
            tag = vals.get("_sources", {}).get(key, "measured")
            if diff >= 0 and diff < past_dist:
                past_dist, past_date, past_val, past_tag = diff, d, vals[key], tag
            elif diff < 0 and (-diff) < fut_dist:
                fut_dist, fut_date, fut_val, fut_tag = -diff, d, vals[key], tag
    if past_date is not None:
        return past_date, past_val, past_tag
    return fut_date, fut_val, fut_tag


def fill_for_date(target, dated_files):
    result = dict(DEFAULTS)
    for key in DEFAULTS:
        _, val, _ = _select_date_for_key(key, target, dated_files)
        if val is not None:
            result[key] = val
    return result


def measured_keys_ever(dated_files):
    seen = set()
    for _, vals in dated_files:
        for k, v in vals.items():
            if v is not None and k in DEFAULTS:
                seen.add(k)
    return seen


def key_source(key, target, dated_files):
    d, _, tag = _select_date_for_key(key, target, dated_files)
    if d is None and key == "cystatin_c_mg_l":
        d, _, tag = _select_date_for_key("egfr_cr_ml_min_1_73m2", target, dated_files)
    return f"{tag}:{d}" if d else "DEFAULT"


# gradient analysis


def compute_gradients(values, current_loss, measured, sex):
    results = []
    for key in OPTIMALS:
        if key in READOUT_KEYS:
            continue
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


def find_cliff(deltas, max_rank=8, threshold=0.35):
    n = min(len(deltas), max_rank)
    if n < 2:
        return len(deltas), 0.0
    best_drop, best_cut = -1.0, n
    for i in range(1, n):
        if deltas[i - 1] <= 0:
            continue
        drop = (deltas[i - 1] - deltas[i]) / deltas[i - 1]
        if drop >= threshold:
            return i, drop
        if drop > best_drop:
            best_drop, best_cut = drop, i
    return best_cut, best_drop


def intervention_for(key):
    meta = METRIC_META.get(key)
    return meta["intervention"] if meta else None


def is_aspirational(key):
    meta = METRIC_META.get(key)
    return bool(meta and meta.get("aspirational"))


# output


def main():
    dated_files, using_sample, raw_paths = load_dated_files()
    sex = load_sex(raw_paths)

    if not dated_files:
        print("# No data files found.")
        print("# Add results_YYYY_MM_DD.yaml files to dated_test_results/")
        print("# See AGENTS.md for format and key definitions.")
        return

    if using_sample:
        print("# Using sample_data/ for demonstration -- add files to dated_test_results/ for real results")

    measured = measured_keys_ever(dated_files)

    timeline = []
    for dt, _ in dated_files:
        vals = fill_for_date(dt, dated_files)
        vals = derive_computed_keys(vals, measured)
        loss, comp, mods = compute_loss(vals, sex)
        timeline.append((dt, loss, comp, mods, vals))

    for dt, loss, _, _, _ in timeline:
        print(f"{dt.strftime('%Y_%m_%d')} {loss:.4f}")

    print()
    print("---")
    print()

    latest_dt, latest_loss, latest_comp, latest_mods, latest_vals = timeline[-1]

    non_scoreable = {"egfr_cr_ml_min_1_73m2"} | READOUT_KEYS
    scoreable = [k for k in DEFAULTS if k not in non_scoreable]
    measured_scoreable = [k for k in scoreable if k in measured or (k == "cystatin_c_mg_l" and "egfr_cr_ml_min_1_73m2" in measured)]
    never = [k for k in scoreable if k not in measured_scoreable]
    print(f"DATA COVERAGE  (as of {latest_dt}  sex={sex})")
    print(f"  measured : {len(measured_scoreable)} / {len(scoreable)}")
    if never:
        print(f"  defaults : {', '.join(never)}")
    print()

    print(f"LATEST VALUES  composite={latest_comp:.1f}/100  loss={latest_loss:.4f}")
    print(f"  {'key':<42} {'value':>8}  {'score':>6}  {'source'}")
    print(f"  {'-'*42} {'-'*8}  {'-'*6}  {'-'*22}")
    for domain, components in DOMAIN_COMPONENTS.items():
        print(f"  [{domain}  weight={DOMAIN_WEIGHTS[domain]:.0%}]")
        for key, _ in components:
            val = latest_vals.get(key)
            sc = score_key(key, val, sex)
            src = key_source(key, latest_dt, dated_files)
            vs = f"{val:.2f}" if isinstance(val, (int, float)) and val is not None else "-"
            ss = f"{sc:.1f}" if sc is not None else "-"
            flag = "  (LOW)" if sc is not None and sc < 60 else ""
            creat_note = "  (creatinine fallback; muscle/creatine bias possible)" if (key == "cystatin_c_mg_l" and latest_vals.get("_cys_from_creatinine")) else ""
            print(f"  {key:<42} {vs:>8}  {ss:>6}  {src}{flag}{creat_note}")
    print()

    print("READOUTS  (actionable recovery & supplement markers -- tracked, not scored in composite)")
    for key in sorted(READOUT_KEYS):
        val = latest_vals.get(key)
        sc = score_key(key, val, sex)
        src = key_source(key, latest_dt, dated_files)
        vs = f"{val:.2f}" if isinstance(val, (int, float)) and val is not None else "-"
        ss = f"{sc:.1f}" if sc is not None else "-"
        flag = "  (LOW)" if sc is not None and sc < 60 else ""
        intv = intervention_for(key)
        intv_s = f"  ->  {intv}" if (flag and intv) else ""
        print(f"  {key:<42} {vs:>8}  {ss:>6}  {src}{flag}{intv_s}")
    print()

    if latest_mods:
        print("INTERACTION PENALTIES")
        for name, val in latest_mods:
            print(f"  ACTIVE {name}: {(1 - val) * 100:.0f}% composite reduction")
    else:
        print("INTERACTION PENALTIES  none active")
    print()

    grads = compute_gradients(latest_vals, latest_loss, measured_scoreable, sex)
    print("GRADIENT ANALYSIS  (loss reduction if key reaches optimal)")
    print(f"  {'#':<3} {'key':<42} {'current':>8} {'optimal':>8} {'score':>6} {'delta_loss':>10}  source")
    print(f"  {'-'*3} {'-'*42} {'-'*8} {'-'*8} {'-'*6} {'-'*10}  {'-'*10}")
    for i, (key, cur, opt, sc, delta, src) in enumerate(grads[:15], 1):
        cs = f"{cur:.2f}" if cur is not None else "-"
        ss = f"{sc:.1f}" if sc is not None else "-"
        asp = "  *aspirational" if is_aspirational(key) else ""
        print(f"  {i:<3} {key:<42} {cs:>8} {opt:>8.2f} {ss:>6} {delta:>10.4f}  {src}{asp}")
    print()

    default_grads = [(k, c, o, s, d) for k, c, o, s, d, src in grads if src == "DEFAULT"]
    measured_grads = [(k, c, o, s, d) for k, c, o, s, d, src in grads if src != "DEFAULT"]

    m_deltas = [d for _, _, _, _, d in measured_grads]
    cut, drop = find_cliff(m_deltas)
    focus = measured_grads[:cut]
    focus_keys = set(k for k, _, _, _, _ in focus)
    delta_by_key = {k: d for (k, _, _, _, d) in measured_grads}

    keep_doing, next_tier, cut_loose = [], [], []
    considered, seen = [], set()
    for domain, comps in DOMAIN_COMPONENTS.items():
        for key, _ in comps:
            if key not in seen:
                seen.add(key)
                considered.append(key)
    for key, _, _, _, _ in measured_grads:
        if key not in seen:
            seen.add(key)
            considered.append(key)

    for key in considered:
        if key in focus_keys:
            continue
        if key_source(key, latest_dt, dated_files) == "DEFAULT":
            continue
        sc = score_key(key, latest_vals.get(key), sex)
        intv = intervention_for(key)
        d = delta_by_key.get(key, 0.0)
        if intv is None:
            cut_loose.append((key, sc))
        elif sc is not None and sc < 92 and d >= 0.005:
            next_tier.append((key, latest_vals.get(key), get_optimal(key, sex), sc, d))
        else:
            keep_doing.append((key, sc, intv))

    next_tier.sort(key=lambda x: -x[4])

    print("PRIORITY TARGETS")
    print(f"  FOCUS  (above the cliff -- a {drop*100:.0f}% drop in delta_loss falls after #{cut}; the short list worth new attention)")
    for key, cur, opt, sc, delta in focus:
        cs = f"{cur:.2f}" if cur is not None else "?"
        intv = intervention_for(key)
        intv_s = f"  ->  {intv}" if intv else ""
        print(f"     delta_loss={delta:.4f}  {key:<42}  current={cs}  target={opt:.2f}  score={sc:.1f}{intv_s}")

    if next_tier:
        print()
        print("  NEXT TIER  (below the cliff -- real but lower yield; revisit, do not crowd out the focus set)")
        for key, cur, opt, sc, delta in next_tier[:6]:
            cs = f"{cur:.2f}" if cur is not None else "?"
            intv = intervention_for(key)
            intv_s = f"  ->  {intv}" if intv else ""
            print(f"     delta_loss={delta:.4f}  {key:<42}  current={cs}  target={opt:.2f}  score={sc:.1f}{intv_s}")

    if default_grads:
        print()
        print("  TEST THESE  (running on DEFAULTS -- a real measurement may move loss; go get the number)")
        for key, cur, opt, sc, delta in default_grads[:5]:
            print(f"     delta_loss={delta:.4f}  {key}")

    if keep_doing:
        print()
        print("  KEEP DOING  (won, but the win is intervention-dependent -- stop adding, never stop maintaining)")
        for key, sc, intv in sorted(keep_doing, key=lambda x: -(x[1] if x[1] is not None else 0.0)):
            asp = "  *" if is_aspirational(key) else ""
            ss = f"{sc:.1f}" if sc is not None else "-"
            print(f"     score={ss:>5}  {key:<42}{asp}  <-  {intv}")

    if cut_loose:
        print()
        print("  CUT LOOSE  (no direct lever and/or fully maintained -- safe to ignore unless it drifts)")
        for key, sc in sorted(cut_loose, key=lambda x: -(x[1] if x[1] is not None else 0.0)):
            ss = f"{sc:.1f}" if sc is not None else "-"
            print(f"     score={ss:>5}  {key}")

    print()
    print("---")
    print("FOCUS = new effort.  KEEP DOING = sustain, do not stop.  CUT LOOSE = ignore unless trend turns.")
    print("Aspirational targets (*) are fixed standards/benchmarks; their gap is not necessarily closable.")
    print("Paste this output to an AI agent alongside AGENTS.md Section B for interpretation.")


if __name__ == "__main__":
    main()
