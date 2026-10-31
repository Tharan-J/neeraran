"""
Agent 5: Prioritizer
Ranks open operational cases using a transparent, multi-criteria mathematical formula.
Shows every term's score contribution (never a black box).
Terms: loss_rate, population_affected, vulnerable_weight, urgency, crew_readiness.

CRITICAL MANDATE (Requirement 5):
Separates citizen complaint administrative priority from sensor-confirmed leak scores.
"""

import time
from typing import Dict, List, Any, Tuple
from apps.api.agents.models import Case, AgentTrace
from apps.api.agents.prompts import SYSTEM_PROMPT_PRIORITIZER
from apps.api.ai.gemini_client import gemini_client

DEFAULT_WEIGHTS = {
    "loss_rate": 0.30,
    "population": 0.20,
    "vulnerability": 0.25,
    "urgency": 0.15,
    "crew_availability": 0.10
}

VULNERABLE_BLOCKS = ["BLK-HSTL-A", "BLK-HSTL-B", "BLK-HSTL-C", "BLK-HLTH", "BLK-CRECHE"]

BLOCK_POPULATIONS = {
    "BLK-HSTL-A": 650,
    "BLK-HSTL-B": 600,
    "BLK-HSTL-C": 750,
    "BLK-MESS": 2000,
    "BLK-HLTH": 80,
    "BLK-CRECHE": 45,
    "BLK-ACAD-1": 1200,
    "BLK-ACAD-2": 1000,
    "BLK-LIB": 400,
    "CAMPUS": 5000
}

class PrioritizerAgent:
    def __init__(self, weights: Dict[str, float] = None):
        self.name = "Prioritizer"
        self.system_prompt = SYSTEM_PROMPT_PRIORITIZER
        self.weights = weights or DEFAULT_WEIGHTS.copy()

    def set_weights(self, new_weights: Dict[str, float]):
        self.weights.update(new_weights)

    def calculate_score(self, case: Case) -> Dict[str, Any]:
        """Calculates transparent score breakdown for a case."""
        loc = case.location

        # 1. Loss rate term (0-100 normalized)
        loss_term = min(100.0, (case.loss_rate_kl_day / 80.0) * 100.0)

        # 2. Population term
        pop = BLOCK_POPULATIONS.get(loc, 300)
        pop_term = min(100.0, (pop / 1500.0) * 100.0)

        # 3. Vulnerability term (Hostels, Healthcare, Crèche get top priority)
        is_vuln = any(v in loc for v in VULNERABLE_BLOCKS)
        vuln_term = 100.0 if is_vuln else 25.0

        # 4. Urgency term based on physical case severity
        if case.case_type == "leak":
            urgency_term = 90.0
        elif case.case_type == "shortage":
            urgency_term = 95.0
        elif case.case_type == "sensor_fault":
            urgency_term = 40.0
        elif case.case_type == "unconfirmed_complaint":
            urgency_term = 70.0  # High citizen attention, distinct from physical leak
        else:
            urgency_term = 20.0

        # 5. Crew availability
        crew_term = 85.0

        total_score = (
            self.weights["loss_rate"] * loss_term +
            self.weights["population"] * pop_term +
            self.weights["vulnerability"] * vuln_term +
            self.weights["urgency"] * urgency_term +
            self.weights["crew_availability"] * crew_term
        )

        breakdown = {
            "total_score": round(total_score, 1),
            "terms": {
                "loss_rate": {"value": case.loss_rate_kl_day, "unit": "kL/d", "score": round(loss_term, 1), "weight": self.weights["loss_rate"], "contribution": round(self.weights["loss_rate"] * loss_term, 1)},
                "population": {"value": pop, "unit": "people", "score": round(pop_term, 1), "weight": self.weights["population"], "contribution": round(self.weights["population"] * pop_term, 1)},
                "vulnerability": {"value": "vulnerable" if is_vuln else "standard", "score": round(vuln_term, 1), "weight": self.weights["vulnerability"], "contribution": round(self.weights["vulnerability"] * vuln_term, 1)},
                "urgency": {"value": case.case_type, "score": round(urgency_term, 1), "weight": self.weights["urgency"], "contribution": round(self.weights["urgency"] * urgency_term, 1)},
                "crew_availability": {"value": "ready", "score": round(crew_term, 1), "weight": self.weights["crew_availability"], "contribution": round(self.weights["crew_availability"] * crew_term, 1)},
            }
        }
        return breakdown

    def run(self, cases: List[Case]) -> Tuple[List[Case], AgentTrace]:
        t0 = time.perf_counter()

        breakdowns = {}
        for c in cases:
            b = self.calculate_score(c)
            c.priority_score = b["total_score"]
            breakdowns[c.id] = b

        ranked_cases = sorted(cases, key=lambda x: x.priority_score, reverse=True)

        # Reasoning note
        summary_note = f"Ranked {len(cases)} cases using multi-criteria weighted formula."
        if gemini_client.is_available() and ranked_cases:
            top_case = ranked_cases[0]
            prompt = f"""Prioritizer Agent ranking summary:
Top ranked case: {top_case.id} at {top_case.location} (score: {top_case.priority_score})
Case type: {top_case.case_type}, Loss rate: {top_case.loss_rate_kl_day} kL/d
Score terms: {breakdowns[top_case.id]['terms']}

Provide a 1-sentence engineering justification for why this case was prioritized first."""
            res = gemini_client.generate_for_agent(
                agent_name=self.name,
                prompt=prompt,
                system_instruction=self.system_prompt,
                incident_id=top_case.id
            )
            if res.get("success") and res.get("text"):
                summary_note = res["text"].strip()

        execution_ms = (time.perf_counter() - t0) * 1000.0
        trace = AgentTrace(
            agent_name=self.name,
            started_at=time.strftime("%H:%M:%S"),
            ended_at=time.strftime("%H:%M:%S"),
            execution_time_ms=round(execution_ms, 2),
            status="success",
            inputs={"cases_count": len(cases), "weights": self.weights},
            outputs={"ranked_case_ids": [c.id for c in ranked_cases], "score_breakdowns": breakdowns},
            notes=summary_note
        )

        return ranked_cases, trace
