"""
NEERARAN Google Gemini AI Integration
Uses official google.genai SDK with function calling, structured outputs,
live token tracking, and deterministic fallback when API key is missing or calls time out.
Model: gemini-3.5-flash-lite
Official Paid Tier Pricing: Input $0.30/1M tokens, Output $2.50/1M tokens
"""

import os
import re
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from apps.api.db.database import (
    SessionLocal, GeminiRequest, AgentTokenUsage, ModelPricingConfig
)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
DEFAULT_INPUT_PRICE_PER_M = 0.30
DEFAULT_OUTPUT_PRICE_PER_M = 2.50

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = DEFAULT_MODEL
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

    def _get_pricing(self, db) -> tuple:
        cfg = db.query(ModelPricingConfig).filter(
            ModelPricingConfig.model_name == self.model_name,
            ModelPricingConfig.is_active == True
        ).first()
        if cfg:
            return cfg.input_price_per_million, cfg.output_price_per_million
        return DEFAULT_INPUT_PRICE_PER_M, DEFAULT_OUTPUT_PRICE_PER_M

    def _persist_usage(
        self,
        agent_name: str,
        incident_id: Optional[str],
        input_tokens: int,
        output_tokens: int,
        thinking_tokens: int,
        cached_tokens: int,
        latency_ms: float,
        status: str,
        error_msg: Optional[str] = None
    ) -> float:
        total_tokens = input_tokens + output_tokens + thinking_tokens
        self.token_usage_total += total_tokens
        self.calls_total += 1
        cost_usd = 0.0

        try:
            with SessionLocal() as db:
                in_price, out_price = self._get_pricing(db)
                cost_usd = (input_tokens / 1_000_000.0 * in_price) + ((output_tokens + thinking_tokens) / 1_000_000.0 * out_price)

                req_rec = GeminiRequest(
                    id=f"GREQ-{uuid.uuid4().hex[:10]}",
                    request_id=f"REQ-{uuid.uuid4().hex[:8]}",
                    agent_name=agent_name,
                    agent_run_id=f"RUN-{int(time.time())}",
                    incident_id=incident_id,
                    model=self.model_name,
                    start_time=datetime.utcnow(),
                    completion_time=datetime.utcnow(),
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    thinking_tokens=thinking_tokens,
                    cached_tokens=cached_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=cost_usd,
                    status=status,
                    error_message=error_msg
                )
                db.add(req_rec)

                # Update or create AgentTokenUsage
                usage = db.query(AgentTokenUsage).filter(AgentTokenUsage.agent_name == agent_name).first()
                if not usage:
                    usage = AgentTokenUsage(
                        id=agent_name,
                        agent_name=agent_name,
                        total_requests=1,
                        total_input_tokens=input_tokens,
                        total_output_tokens=output_tokens,
                        total_thinking_tokens=thinking_tokens,
                        total_tokens=total_tokens,
                        total_cost_usd=cost_usd,
                        updated_at=datetime.utcnow()
                    )
                    db.add(usage)
                else:
                    usage.total_requests += 1
                    usage.total_input_tokens += input_tokens
                    usage.total_output_tokens += output_tokens
                    usage.total_thinking_tokens += thinking_tokens
                    usage.total_tokens += total_tokens
                    usage.total_cost_usd += cost_usd
                    usage.updated_at = datetime.utcnow()

                db.commit()
        except Exception as e:
            print(f"Error persisting token usage: {e}")

        return cost_usd

    def generate_for_agent(
        self,
        agent_name: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Token-optimized concise prompt execution with gemini-3.5-flash-lite.
        """
        t0 = time.perf_counter()
        if not self.is_available():
            return {"success": False, "source": "unavailable", "text": ""}

        try:
            full_contents = []
            if system_instruction:
                full_contents.append(f"INSTRUCTION: {system_instruction.strip()}\n")
            full_contents.append(prompt.strip())

            resp = self.client.models.generate_content(
                model=self.model_name,
                contents="\n".join(full_contents)
            )
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0

            u = getattr(resp, "usage_metadata", None)
            inp = getattr(u, "prompt_token_count", 0) or len(prompt) // 4
            out = getattr(u, "candidates_token_count", 0) or len(resp.text) // 4
            thk = getattr(u, "thoughts_token_count", 0) or 0
            cch = getattr(u, "cached_content_token_count", 0) or 0

            cost = self._persist_usage(
                agent_name=agent_name,
                incident_id=incident_id,
                input_tokens=inp,
                output_tokens=out,
                thinking_tokens=thk,
                cached_tokens=cch,
                latency_ms=latency_ms,
                status="success"
            )

            return {
                "success": True,
                "source": "gemini",
                "model": self.model_name,
                "text": resp.text.strip(),
                "usage": {
                    "prompt_tokens": inp,
                    "candidates_tokens": out,
                    "thoughts_tokens": thk,
                    "cached_tokens": cch,
                    "total_tokens": inp + out + thk,
                    "cost_usd": cost,
                    "latency_ms": round(latency_ms, 1)
                }
            }
        except Exception as err:
            self.fallbacks_total += 1
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0
            self._persist_usage(
                agent_name=agent_name,
                incident_id=incident_id,
                input_tokens=len(prompt) // 4,
                output_tokens=0,
                thinking_tokens=0,
                cached_tokens=0,
                latency_ms=latency_ms,
                status="failed",
                error_msg=str(err)
            )
            return {"success": False, "source": "error", "error": str(err)}

    def parse_scenario_text(self, text: str) -> Dict[str, Any]:
        """
        Parses free-text scenario from jury into structured typed event list.
        Example: "Hostel A 2nd floor pipe burst losing 65 LPM" ->
        [{"type": "burst_main", "location": "BLK-HSTL-A", "loss_lpm": 65.0}]
        """
        t0 = time.perf_counter()
        agent_name = "ScenarioParser"

        if self.is_available():
            try:
                # Token-optimized concise prompt (no redundant essay)
                prompt = f"""You are a hydraulic engineer for NEERARAN campus water network.
Parse this scenario into a JSON array:
"{text}"

Allowed event_type: burst_main, slow_leak, sensor_fault, heatwave, pump_failure, occupancy_surge, contamination_report.
Format:
[
  {{"event_type": "burst_main", "location": "BLK-HSTL-A", "params": {{"loss_lpm": 65.0}}}}
]
Return ONLY raw JSON."""
                resp = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                t1 = time.perf_counter()
                latency_ms = (t1 - t0) * 1000.0

                u = getattr(resp, "usage_metadata", None)
                inp = getattr(u, "prompt_token_count", 0) or 80
                out = getattr(u, "candidates_token_count", 0) or 45
                thk = getattr(u, "thoughts_token_count", 0) or 0
                cch = getattr(u, "cached_content_token_count", 0) or 0

                cost = self._persist_usage(
                    agent_name=agent_name,
                    incident_id=None,
                    input_tokens=inp,
                    output_tokens=out,
                    thinking_tokens=thk,
                    cached_tokens=cch,
                    latency_ms=latency_ms,
                    status="success"
                )

                raw = resp.text.strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                events = json.loads(raw)
                return {
                    "source": "gemini",
                    "model": self.model_name,
                    "parsed_events": events,
                    "confirmation_text": f"Parsed {len(events)} operational event(s) using {self.model_name}.",
                    "token_usage": {
                        "prompt_tokens": inp,
                        "candidates_tokens": out,
                        "thoughts_tokens": thk,
                        "cached_tokens": cch,
                        "total_tokens": inp + out + thk,
                        "cost_usd": cost,
                        "latency_ms": round(latency_ms, 1)
                    },
                    "requires_confirmation": True
                }
            except Exception as err:
                self.fallbacks_total += 1
                t1 = time.perf_counter()
                latency_ms = (t1 - t0) * 1000.0
                self._persist_usage(
                    agent_name=agent_name,
                    incident_id=None,
                    input_tokens=80,
                    output_tokens=0,
                    thinking_tokens=0,
                    cached_tokens=0,
                    latency_ms=latency_ms,
                    status="fallback",
                    error_msg=str(err)
                )

        # Deterministic rule-based parser fallback
        self.fallbacks_total += 1
        parsed = []
        lower = text.lower()

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
            "model": "rule_engine",
            "parsed_events": parsed,
            "confirmation_text": f"Rule-based parser identified {len(parsed)} event(s) targeting {loc}.",
            "requires_confirmation": True
        }

# Singleton Gemini AI Client
gemini_client = GeminiClient()

