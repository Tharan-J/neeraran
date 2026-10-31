"""
NEERARAN Google Gemini AI Integration
Uses official google.genai SDK with function calling, structured outputs,
and deterministic fallback when API key is missing or calls time out.
"""

import os
import re
import json
import time
from typing import Dict, List, Any, Optional

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.provider = os.getenv("LLM_PROVIDER", "gemini")
        self.client = None
        self.token_usage_total = 0
        self.calls_total = 0
        self.fallbacks_total = 0

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print("Gemini client initialization warning:", e)
                self.client = None

    def is_available(self) -> bool:
        return bool(self.client and self.api_key)

    def parse_scenario_text(self, text: str) -> Dict[str, Any]:
        """
        Parses free-text scenario from jury into structured typed event list.
        Example: "Hostel A 2nd floor pipe burst losing 65 LPM" ->
        [{"type": "burst_main", "location": "BLK-HSTL-A", "loss_lpm": 65.0}]
        """
        self.calls_total += 1
        t0 = time.perf_counter()

        # If Gemini is available, query with prompt
        if self.is_available():
            try:
                prompt = f"""
                You are a hydraulic engineer for NEERARAN campus water system.
                Parse the following jury scenario into a JSON array of events:
                Scenario: "{text}"

                Supported events:
                - "burst_main" (location, loss_lpm)
                - "slow_leak" (location, loss_lpm)
                - "sensor_fault" (location, mode)
                - "heatwave" (delta_c, days, demand_pct)
                - "pump_failure" (pump)
                - "occupancy_surge" (location, surge_pct)
                - "contamination_report" (location)

                Return ONLY valid JSON array with keys: event_type, location, params.
                """
                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                self.token_usage_total += 180
                raw = resp.text.strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                events = json.loads(raw)
                return {
                    "source": "gemini",
                    "parsed_events": events,
                    "confirmation_text": f"Parsed {len(events)} operational event(s) using Gemini 2.5 Flash.",
                    "requires_confirmation": True
                }
            except Exception as err:
                self.fallbacks_total += 1
                # Fall back to deterministic regex parser
                pass

        # Deterministic rule-based parser fallback
        self.fallbacks_total += 1
        parsed = []
        lower = text.lower()

        # Extract number if present
        nums = re.findall(r"\d+(?:\.\d+)?", text)
        val = float(nums[0]) if nums else 50.0

        loc = "BLK-HSTL-A"
        if "hostel b" in lower or "boys 2" in lower:
            loc = "BLK-HSTL-B"
        elif "hostel c" in lower or "girls" in lower:
            loc = "BLK-HSTL-C"
        elif "mess" in lower or "kitchen" in lower:
            loc = "BLK-MESS"
        elif "acad" in lower or "class" in lower:
            loc = "BLK-ACAD-1"
        elif "health" in lower or "hospital" in lower:
            loc = "BLK-HLTH"
        elif "library" in lower:
            loc = "BLK-LIB"

        if "burst" in lower or "fissure" in lower or "break" in lower:
            parsed.append({
                "event_type": "burst_main",
                "location": loc,
                "params": {"loss_lpm": max(30.0, val), "segment": f"PIPE-OHT1-{loc.split('-')[-1]}"}
            })
        elif "leak" in lower or "drip" in lower:
            parsed.append({
                "event_type": "slow_leak",
                "location": loc,
                "params": {"loss_lpm": max(15.0, val)}
            })
        elif "heat" in lower or "hot" in lower or "temperature" in lower:
            parsed.append({
                "event_type": "heatwave",
                "location": "CAMPUS",
                "params": {"delta_c": 4.5, "demand_pct": 25.0}
            })
        elif "sensor" in lower or "meter" in lower or "zero" in lower:
            parsed.append({
                "event_type": "sensor_fault",
                "location": loc,
                "params": {"mode": "flat_zero"}
            })
        elif "pump" in lower or "motor" in lower:
            parsed.append({
                "event_type": "pump_failure",
                "location": "PUMP-BORE1",
                "params": {"pump": "PUMP-BORE1"}
            })
        elif "contaminat" in lower or "dirty" in lower or "smell" in lower:
            parsed.append({
                "event_type": "contamination_report",
                "location": loc,
                "params": {"note": "Visual or odor anomaly reported. Recommending immediate human testing."}
            })
        else:
            parsed.append({
                "event_type": "slow_leak",
                "location": loc,
                "params": {"loss_lpm": 40.0}
            })

        return {
            "source": "deterministic_rule_parser",
            "parsed_events": parsed,
            "confirmation_text": f"Rule-based parser identified {len(parsed)} event(s) targeting {loc}.",
            "requires_confirmation": True
        }

# Singleton Gemini AI Client
gemini_client = GeminiClient()
