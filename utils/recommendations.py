from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationBundle:
    strengths: List[str]
    improvements: List[str]
    actions: List[str]
    focus_areas: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strengths": self.strengths,
            "improvements": self.improvements,
            "actions": self.actions,
            "focus_areas": self.focus_areas,
        }


def _top_keywords(keywords: List[Dict[str, Any]], sentiment: str, limit: int = 6) -> List[str]:
    filtered = [k.get("keyword") for k in (keywords or []) if k.get("sentiment_category") == sentiment]
    filtered = [k for k in filtered if k]
    return filtered[:limit]


def generate_recommendations(
    *,
    positive_pct: float,
    negative_pct: float,
    neutral_pct: float,
    avg_instructional: float,
    avg_personal_social: float,
    keywords: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate human-readable recommendations from evaluation aggregates.

    Inputs are based on admin/reports.html data:
    - sentiment percentages
    - average rating breakdown (A=instructional, B=personal/social)
    - top keywords summary (list of {keyword, frequency, sentiment_category})
    """

    keywords = keywords or []
    top_negative = _top_keywords(keywords, "negative", limit=6)
    top_neutral = _top_keywords(keywords, "neutral", limit=6)
    top_positive = _top_keywords(keywords, "positive", limit=6)

    # Heuristics: thresholds tuned for 1..5 star style ratings and pct sentiment.
    sentiment_strength = "strong" if positive_pct >= 60 else "mixed"
    sentiment_risk = "high" if negative_pct >= 30 else "medium" if negative_pct >= 20 else "low"

    strengths: List[str] = []
    improvements: List[str] = []
    actions: List[str] = []
    focus_areas: List[str] = []

    # Strengths derived from A/B
    if avg_instructional >= 4:
        strengths.append("Instructional delivery is consistently strong (A: Instructional Skills).")
        focus_areas.append("Instructional Skills")
    elif avg_instructional >= 3:
        strengths.append("Instructional delivery is generally solid; small enhancements can boost clarity and pacing.")
        focus_areas.append("Instructional Skills")

    if avg_personal_social >= 4:
        strengths.append("Interpersonal approach and classroom rapport are highly rated (B: Personal & Social Qualities).")
        focus_areas.append("Personal & Social Qualities")
    elif avg_personal_social >= 3:
        strengths.append("Rapport and approach are acceptable; consistency in availability and communication can improve outcomes.")
        focus_areas.append("Personal & Social Qualities")

    # Sentiment-driven improvements
    if sentiment_risk in {"high", "medium"}:
        improvements.append(
            f"Overall feedback shows higher negativity ({negative_pct:.1f}% negative). Focus on the main concern themes to reduce recurring dissatisfaction."
        )
        if top_negative:
            improvements.append("Recurring negative themes include: " + ", ".join(top_negative[:3]) + ".")
    else:
        improvements.append(
            "Feedback is mostly positive; focus on refining areas that produce neutral responses and occasional negatives."
        )
        if top_neutral:
            improvements.append("Neutral themes that may need clarification or consistency: " + ", ".join(top_neutral[:3]) + ".")

    # Keyword-grounded focus
    if top_negative:
        focus_areas.append("Address negative keyword themes")
    elif top_neutral:
        focus_areas.append("Clarify neutral keyword themes")

    # Action plans: map to likely questionnaire items/skills, without overfitting.
    if avg_instructional < 3.5:
        actions.extend(
            [
                "Start each module with a clear syllabus/learning objectives and how grading works; revisit them after exams.",
                "Improve lesson clarity with short, structured explanations and examples tied to assessment tasks.",
                "Use a time-boxed lesson plan (start/end on time) to ensure the whole period is used effectively.",
            ]
        )
        if top_negative:
            actions.append("For the top negative themes, add targeted examples/practice exercises and check understanding mid-session.")
    else:
        actions.extend(
            [
                "Maintain the current instructional strengths while refining pacing and increasing opportunities for participation.",
                "Add quick formative checks (e.g., 3-question quizzes) to catch confusion earlier.",
            ]
        )

    if avg_personal_social < 3.5:
        actions.extend(
            [
                "Increase student availability for consultation (set office hours and communicate them clearly).",
                "Strengthen respectful communication: actively welcome questions and respond constructively.",
                "Use inclusive participation strategies (pair work, think-pair-share) to improve engagement.",
            ]
        )
        if top_negative:
            actions.append("Where negatives relate to classroom interaction, standardize response approaches to student concerns.")
    else:
        actions.extend(
            [
                "Keep building rapport and ensure consistency in approachable communication across sessions.",
                "Encourage continued student feedback and close the loop on recurring concerns.",
            ]
        )

    # Add sentiment-summary specific bullets
    actions.append(
        "Measure impact next semester by tracking the same sentiment percentages and verifying whether keyword frequency for negative themes decreases."
    )

    # If positive is strong, add “keep doing” plus “still improve” nuance.
    if sentiment_strength == "strong" and top_positive:
        strengths.append("Students also highlight positive strengths such as: " + ", ".join(top_positive[:3]) + ".")
        actions.insert(0, "Continue reinforcing the practices that lead to positive feedback and share them in internal teaching best-practice sessions.")

    # Final shaping: dedupe & cap sizes
    def _dedupe_cap(items: List[str], cap: int) -> List[str]:
        seen = set()
        out = []
        for x in items:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
            if len(out) >= cap:
                break
        return out

    return RecommendationBundle(
        strengths=_dedupe_cap(strengths, 4),
        improvements=_dedupe_cap(improvements, 4),
        actions=_dedupe_cap(actions, 6),
        focus_areas=_dedupe_cap(focus_areas, 5),
    ).to_dict()

