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
    """Generate score-based recommendations with commendation for strong performance.

    Inputs are based on admin/reports.html data:
    - sentiment percentages
    - average rating breakdown (A=instructional, B=personal/social)
    - top keywords summary (list of {keyword, frequency, sentiment_category})
    """

    keywords = keywords or []
    top_negative = _top_keywords(keywords, "negative", limit=6)
    top_neutral = _top_keywords(keywords, "neutral", limit=6)
    top_positive = _top_keywords(keywords, "positive", limit=6)

    strengths: List[str] = []
    improvements: List[str] = []
    actions: List[str] = []
    focus_areas: List[str] = []

    overall_score = round((avg_instructional + avg_personal_social) / 2, 2)

    item_labels = {
        "is_1": "Explains course objectives, requirements, and grading system",
        "is_2": "Provides course outline/study guide",
        "is_3": "Is prepared and organized for classes",
        "is_4": "Exhibits mastery of subject matter",
        "is_5": "Explains the lesson clearly",
        "is_6": "Speaks clearly and fluently",
        "is_7": "Uses effective teaching strategies",
        "is_8": "Uses instructional aids effectively",
        "is_9": "Provides opportunities for student participation",
        "is_10": "Discusses up-to-date information related to the subject",
        "is_11": "Makes classroom activities interesting",
        "is_12": "Guides students to accomplish learning goals",
        "is_13": "Encourages participation and critical thinking",
        "is_14": "Welcomes student questions",
        "is_15": "Gives and checks relevant assignments/projects",
        "is_16": "Starts and ends classes on time",
        "is_17": "Maintains classroom discipline",
        "is_18": "Uses the whole class period effectively",
        "ps_1": "Respects students' dignity and worth",
        "ps_2": "Shows care and concern for students",
        "ps_3": "Promotes smooth student-teacher relationships",
        "ps_4": "Is open-minded and approachable",
        "ps_5": "Commands student respect",
        "ps_6": "Shows healthy humor and cheerfulness",
        "ps_7": "Dresses appropriately",
        "ps_8": "Has a well-modulated voice",
        "ps_9": "Is available for student consultation and assistance",
    }

    def _score_band(score: float) -> str:
        if score >= 4.5:
            return "excellent"
        if score >= 4.0:
            return "very_good"
        if score >= 3.0:
            return "good"
        return "needs_support"

    instructional_band = _score_band(avg_instructional)
    social_band = _score_band(avg_personal_social)
    overall_band = _score_band(overall_score)

    # Score-based recommendation for Instructional Skills (always provide one)
    if instructional_band == "excellent":
        strengths.append(
            f"Excellent instructional performance (A: {avg_instructional:.2f}/5). Commendation: your lesson clarity, structure, and delivery are outstanding."
        )
        improvements.append(
            "Continue leading by example in instructional practices and document your high-impact methods for mentoring and peer sharing."
        )
        actions.append(
            "Sustain advanced instructional strategies (clear objectives, active checks for understanding, aligned assessments) and share best practices with colleagues."
        )
        focus_areas.append("Sustain instructional excellence")
    elif instructional_band == "very_good":
        strengths.append(
            f"Very strong instructional performance (A: {avg_instructional:.2f}/5). Students recognize effective teaching and clear facilitation."
        )
        improvements.append(
            "Refine pacing and provide more differentiated examples to move instructional performance from very good to excellent."
        )
        actions.append(
            "Introduce short diagnostic checks and targeted reinforcement for difficult topics to further improve instructional consistency."
        )
        focus_areas.append("Instructional refinement")
    elif instructional_band == "good":
        strengths.append(
            f"Solid instructional foundation (A: {avg_instructional:.2f}/5). Core teaching expectations are generally being met."
        )
        improvements.append(
            "Strengthen lesson organization and clarity to reduce confusion and improve consistency in student understanding."
        )
        actions.append(
            "Use structured lesson flow (objective → explanation → guided practice → recap) and provide clearer links between discussions and assessments."
        )
        focus_areas.append("Instructional consistency")
    else:
        strengths.append(
            f"Instructional baseline identified (A: {avg_instructional:.2f}/5), creating a clear starting point for focused coaching and support."
        )
        improvements.append(
            "Prioritize instructional support: improve clarity, pacing, and content organization to raise learning effectiveness."
        )
        actions.append(
            "Apply an instructional recovery plan: explicit lesson objectives, step-by-step examples, frequent comprehension checks, and regular feedback loops."
        )
        focus_areas.append("Instructional recovery priorities")

    # Score-based recommendation for Personal & Social Qualities (always provide one)
    if social_band == "excellent":
        strengths.append(
            f"Excellent interpersonal performance (B: {avg_personal_social:.2f}/5). Commendation: students highly value your professionalism, empathy, and rapport."
        )
        improvements.append(
            "Maintain this strong student-centered approach and continue modeling respectful, inclusive classroom interaction."
        )
        actions.append(
            "Preserve current communication strengths and continue proactive consultation and constructive feedback practices."
        )
        focus_areas.append("Sustain interpersonal excellence")
    elif social_band == "very_good":
        strengths.append(
            f"Very good personal/social performance (B: {avg_personal_social:.2f}/5), with positive student rapport and communication."
        )
        improvements.append(
            "Increase consistency in availability and follow-through to elevate interpersonal impact to an excellent level."
        )
        actions.append(
            "Set and communicate consistent consultation windows and reinforce inclusive participation techniques each session."
        )
        focus_areas.append("Interpersonal consistency")
    elif social_band == "good":
        strengths.append(
            f"Adequate personal/social performance (B: {avg_personal_social:.2f}/5) with room for stronger student engagement."
        )
        improvements.append(
            "Improve approachability, responsiveness, and classroom interaction quality to strengthen trust and engagement."
        )
        actions.append(
            "Adopt active listening prompts, structured Q&A routines, and clearer response timelines to student concerns."
        )
        focus_areas.append("Student engagement and communication")
    else:
        strengths.append(
            f"Personal/social baseline identified (B: {avg_personal_social:.2f}/5), enabling targeted improvements in classroom climate."
        )
        improvements.append(
            "Focus on rebuilding classroom rapport through respectful communication, responsiveness, and supportive student interaction."
        )
        actions.append(
            "Implement a social-support plan: weekly consultation schedule, explicit communication norms, and consistent acknowledgement of student questions."
        )
        focus_areas.append("Rapport rebuilding and support")

    # Overall score-based commendation/appreciation
    if overall_band in {"excellent", "very_good"}:
        strengths.append(
            f"Instructor appreciation: overall score is {overall_score:.2f}/5. This reflects strong teaching performance and meaningful student impact—well done."
        )
        actions.insert(
            0,
            "Recognize and sustain high performance through continued reflective practice and sharing effective methods with the department.",
        )
    elif overall_band == "good":
        improvements.append(
            f"Overall score is {overall_score:.2f}/5. Performance is stable, and targeted improvements can raise outcomes to a higher tier."
        )
    else:
        improvements.append(
            f"Overall score is {overall_score:.2f}/5. A focused improvement cycle is recommended to raise instructional quality and student experience."
        )

    # Item-level recommendations from keyword signals (by item code in keyword text, e.g., "A1", "B3")
    low_item_hints = {
        "is_1": "Begin each term with a concise grading and expectations orientation, then revisit it before major assessments.",
        "is_2": "Provide a clear weekly course guide and keep it updated in an accessible channel.",
        "is_3": "Prepare lesson materials ahead of class and sequence activities to avoid downtime.",
        "is_4": "Strengthen content mastery with updated references and cross-topic examples.",
        "is_5": "Use simpler explanations with worked examples and concept checks after each segment.",
        "is_6": "Improve voice projection, diction, and pacing so instructions are consistently understood.",
        "is_7": "Vary teaching strategies (discussion, demonstration, guided practice) based on lesson goals.",
        "is_8": "Use visual/interactive instructional aids aligned with the topic and assessment tasks.",
        "is_9": "Increase structured participation opportunities (think-pair-share, short responses, group tasks).",
        "is_10": "Integrate recent, relevant examples and current developments into discussions.",
        "is_11": "Include engaging activity blocks to maintain attention and reinforce key concepts.",
        "is_12": "Set explicit learning targets per session and monitor progress toward each target.",
        "is_13": "Use prompts that require reasoning and evidence to stimulate critical thinking.",
        "is_14": "Actively invite questions and respond in a way that encourages further inquiry.",
        "is_15": "Design relevant assignments and provide timely, actionable feedback on outputs.",
        "is_16": "Follow a strict time plan to start and end sessions consistently on schedule.",
        "is_17": "Apply clear behavior expectations and consistent classroom management routines.",
        "is_18": "Optimize class flow so most of the period is spent on meaningful learning tasks.",
        "ps_1": "Model respectful language and actions that affirm student dignity in all interactions.",
        "ps_2": "Demonstrate care through supportive check-ins and responsiveness to student needs.",
        "ps_3": "Build stronger relationships through positive communication and collaborative norms.",
        "ps_4": "Increase approachability by inviting consultation and maintaining a non-judgmental tone.",
        "ps_5": "Strengthen professional presence through consistent fairness and accountability.",
        "ps_6": "Use appropriate humor and positive tone to create a healthy classroom atmosphere.",
        "ps_7": "Maintain professional appearance standards consistently across sessions.",
        "ps_8": "Practice voice modulation for clarity, emphasis, and student engagement.",
        "ps_9": "Set regular consultation hours and communicate clear support channels to students.",
    }

    code_map = {}
    for i in range(1, 19):
        code_map[f"a{i}"] = f"is_{i}"
        code_map[f"is_{i}"] = f"is_{i}"
    for i in range(1, 10):
        code_map[f"b{i}"] = f"ps_{i}"
        code_map[f"ps_{i}"] = f"ps_{i}"

    item_flags: Dict[str, int] = {}
    for k in keywords:
        word = str(k.get("keyword", "")).strip().lower()
        if not word:
            continue
        mapped = code_map.get(word)
        if not mapped:
            continue
        if str(k.get("sentiment_category", "")).lower() == "negative":
            item_flags[mapped] = item_flags.get(mapped, 0) + int(k.get("frequency", 1) or 1)

    if item_flags:
        improvements.append("Item-based improvement recommendations were generated for low/negative-scored indicators:")
        for item_key, _count in sorted(item_flags.items(), key=lambda x: x[1], reverse=True)[:6]:
            label = item_labels.get(item_key, item_key)
            hint = low_item_hints.get(item_key, "Apply targeted coaching and monitoring for this item.")
            actions.append(f"{label}: {hint}")
            focus_areas.append(f"Improve item {item_key.upper()}")

    # Sentiment-context recommendations
    if negative_pct >= 30:
        improvements.append(
            f"Sentiment risk is high ({negative_pct:.1f}% negative). Prioritize recurring concerns to reduce dissatisfaction in the next cycle."
        )
        if top_negative:
            improvements.append("Top negative themes to address: " + ", ".join(top_negative[:3]) + ".")
        actions.append(
            "Create a short-term intervention plan for the top negative themes and review progress after each assessment period."
        )
        focus_areas.append("High negative-sentiment mitigation")
    elif negative_pct >= 20:
        improvements.append(
            f"Sentiment risk is moderate ({negative_pct:.1f}% negative). Address repeated concern patterns before they escalate."
        )
        if top_negative:
            improvements.append("Recurring concern themes: " + ", ".join(top_negative[:3]) + ".")
        actions.append(
            "Track moderate-risk concerns monthly and apply targeted classroom adjustments for recurring issues."
        )
        focus_areas.append("Moderate sentiment risk control")
    else:
        strengths.append(
            f"Sentiment outlook is favorable ({positive_pct:.1f}% positive, {negative_pct:.1f}% negative), indicating generally positive student perception."
        )
        if top_positive:
            strengths.append("Frequently praised areas include: " + ", ".join(top_positive[:3]) + ".")
        if top_neutral:
            improvements.append("Neutral themes to refine for stronger impact: " + ", ".join(top_neutral[:3]) + ".")
        actions.append(
            "Maintain successful practices and fine-tune neutral areas to convert more feedback into positive sentiment."
        )
        focus_areas.append("Positive sentiment sustainability")

    actions.append(
        "Reassess the same score and sentiment indicators next semester to confirm improvements and sustain strong performance."
    )

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
        strengths=_dedupe_cap(strengths, 6),
        improvements=_dedupe_cap(improvements, 6),
        actions=_dedupe_cap(actions, 8),
        focus_areas=_dedupe_cap(focus_areas, 6),
    ).to_dict()

