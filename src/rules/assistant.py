"""
Intelligent Quality Assistant for PharmaSPC Intelligence.

Rule-based recommendation engine that translates SPC rule violations
into plain-language findings, probable causes, and investigation steps.

No external AI API required — all logic is deterministic and rule-based.
"""

from typing import Dict, List


def generate_recommendations(rule_results: Dict) -> List[Dict]:
    """
    Generate human-readable recommendations based on detected SPC rules.

    For each detected rule violation, produces a structured finding
    with: title, severity, finding description, probable causes,
    and recommended investigation steps.

    Args:
        rule_results: Output from rule_engine.run_all_rules().

    Returns:
        List of recommendation dictionaries. Empty list if no rules detected.
        Each dict contains:
            - 'title' (str): Short name of the finding.
            - 'severity' (str): 'critical', 'warning', or 'info'.
            - 'finding' (str): Plain-language description of what was detected.
            - 'probable_causes' (list of str): Likely root causes.
            - 'investigation_steps' (list of str): Ordered actions to take.
    """
    recommendations = []

    # --- Rule 1: Control Limit Violation ---
    r1 = rule_results.get("rule1", {})
    if r1.get("detected"):
        violation_count = len(r1["violations"])
        points_text = ", ".join(str(v) for v in r1["violations"][:5])
        if len(r1["violations"]) > 5:
            points_text += f" ... (+{len(r1['violations']) - 5} more)"

        recommendations.append({
            "title": "Control Limit Violation",
            "severity": "critical",
            "finding": (
                f"{violation_count} measurement(s) found outside the 3-sigma "
                f"control limits (sample(s): {points_text}). "
                f"This is a strong signal of a special cause — "
                f"the process is not in statistical control."
            ),
            "probable_causes": [
                "Sudden equipment malfunction or miscalibration",
                "Incorrect raw material batch used",
                "Operator error or change in procedure",
                "Measurement system error (gauge, scale)",
                "Environmental disturbance (temperature, humidity spike)",
            ],
            "investigation_steps": [
                "Immediately review the samples at the flagged positions",
                "Check equipment calibration status and recent maintenance logs",
                "Review operator records and any shift changes at that time",
                "Inspect raw material batch documentation",
                "Verify measurement system (re-measure flagged samples)",
                "Initiate NCR (Non-Conformance Report) if product is affected",
            ],
        })

    # --- Rule 2: Trend Detection ---
    r2 = rule_results.get("rule2", {})
    if r2.get("detected"):
        direction = r2["direction"]
        start = r2["start_index"]
        end = r2["end_index"]
        length = end - start + 1

        recommendations.append({
            "title": f"Process Trend Detected ({direction.capitalize()})",
            "severity": "warning",
            "finding": (
                f"A continuous {direction} trend was detected across "
                f"{length} consecutive samples (samples {start} to {end}). "
                f"This pattern suggests a gradual process drift — "
                f"the process mean is slowly moving in one direction."
            ),
            "probable_causes": [
                "Gradual equipment wear (punch wear, die wear)",
                "Raw material property drift across a batch",
                "Temperature or environmental gradual change",
                "Operator fatigue or gradual process adjustment",
                "Lubricant or coating depletion over time",
            ],
            "investigation_steps": [
                f"Review process parameters recorded during samples {start}–{end}",
                "Check equipment wear indicators and schedule maintenance if needed",
                "Compare raw material properties at start vs end of the trend",
                "Review environmental monitoring data (temperature, humidity)",
                "Assess whether operator adjustments were made during this period",
                "Consider process adjustment if trend continues beyond control limits",
            ],
        })

    # --- Rule 3: Process Shift ---
    r3 = rule_results.get("rule3", {})
    if r3.get("detected"):
        direction = r3["direction"]
        start = r3["start_index"]
        end = r3["end_index"]
        length = end - start + 1

        recommendations.append({
            "title": f"Process Shift Detected ({direction.replace('_', ' ').title()})",
            "severity": "warning",
            "finding": (
                f"{length} consecutive samples were found {direction} "
                f"(samples {start} to {end}). "
                f"This sustained shift indicates the process average "
                f"has moved to a new level — a step change has occurred."
            ),
            "probable_causes": [
                "Deliberate or accidental change in machine settings",
                "New raw material batch with different properties",
                "Equipment replacement or part swap",
                "Change in operator or operating procedure",
                "Process parameter adjustment without documentation",
            ],
            "investigation_steps": [
                "Identify any events or changes recorded at or before sample " + str(start),
                "Review machine settings before and after the shift point",
                "Check if a new raw material batch was introduced",
                "Compare operator shift records at the time of the shift",
                "Review change control records for any recent modifications",
                "Update process baseline if the shift represents a valid improvement",
            ],
        })

    # --- No violations ---
    if not recommendations:
        recommendations.append({
            "title": "Process In Control",
            "severity": "info",
            "finding": (
                "No SPC rule violations were detected. "
                "The process appears to be stable and in statistical control."
            ),
            "probable_causes": [],
            "investigation_steps": [
                "Continue routine monitoring",
                "Maintain current process settings",
                "Schedule next periodic capability review",
            ],
        })

    return recommendations