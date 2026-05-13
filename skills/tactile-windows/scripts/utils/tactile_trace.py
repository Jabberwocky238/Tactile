from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
TRACE_KIND = "tactile_trace"
VERIFICATION_STATUSES = {"passed", "failed", "planned", "skipped", "unknown"}
ACTION_SOURCES = {"ax", "uia", "ocr", "profile_region", "visual", "coordinate", "unknown"}
TEXT_KEYS = {"text", "message", "body", "query", "value"}


def clean_text(value: Any, *, limit: int = 180) -> str | None:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    if len(compact) > limit:
        return compact[: limit - 1] + "..."
    return compact


def source_name(value: Any) -> str:
    source = str(value or "").strip().lower()
    if source in {"direct_ax", "ax_action", "ax"}:
        return "ax"
    if source in {"uia", "uia_coordinate_click", "uia_action"}:
        return "uia"
    if source in {"ocr", "ocrline", "ocr_coordinate"}:
        return "ocr"
    if source in {"profile", "profile_region", "profileregion"}:
        return "profile_region"
    if source in {"visual", "visual_coordinate"}:
        return "visual"
    if source in {"coordinate", "coordinates", "virtual_region", "virtualregion"}:
        return "coordinate"
    return "unknown"


def sanitize_action(action: Any) -> dict[str, Any]:
    if not isinstance(action, dict):
        return {}
    result: dict[str, Any] = {}
    for key in (
        "type",
        "element_id",
        "key",
        "keys",
        "seconds",
        "deltaY",
        "deltaX",
        "delta_y",
        "delta_x",
        "source",
        "method",
    ):
        if key in action:
            result[key] = action[key]
    for key in ("x", "y"):
        if key in action:
            result[key] = action[key]
    for key, value in action.items():
        if key in TEXT_KEYS and isinstance(value, str):
            result[f"{key}_length"] = len(value)
    if "text_length" in action:
        result["text_length"] = action.get("text_length")
    return result


def observation_summary(step: dict[str, Any], *, platform: str) -> dict[str, Any]:
    sources = step.get("observation_sources")
    if isinstance(sources, dict):
        visual = sources.get("visual_observation") if isinstance(sources.get("visual_observation"), dict) else {}
        return {
            "platform": platform,
            "ax_elements": int(sources.get("ax_elements") or 0),
            "ocr_lines": int(sources.get("ocr_lines") or 0),
            "profile_regions": int(sources.get("profile_regions") or 0),
            "screenshot": bool(sources.get("screenshot_path")),
            "visual_enabled": bool(visual.get("enabled")),
            "visual_attached": bool(visual.get("image_attached_to_planner")),
        }
    return {
        "platform": platform,
        "uia_view": step.get("uia_view"),
        "accessibility_hint": step.get("accessibility_hint"),
        "element_count_sent_to_llm": step.get("element_count_sent_to_llm"),
        "traversal_stats": step.get("traversal_stats") if isinstance(step.get("traversal_stats"), dict) else {},
    }


def action_snapshots(step: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots = step.get("action_elements")
    return [item for item in snapshots if isinstance(item, dict)] if isinstance(snapshots, list) else []


def snapshot_for_action(step: dict[str, Any], action: dict[str, Any]) -> dict[str, Any] | None:
    snapshots = action_snapshots(step)
    element_id = action.get("element_id")
    if element_id is not None:
        for snapshot in snapshots:
            if snapshot.get("element_id") == element_id:
                return snapshot
    if "x" not in action or "y" not in action:
        return None
    try:
        x = round(float(action["x"]), 1)
        y = round(float(action["y"]), 1)
    except (TypeError, ValueError):
        return None
    for snapshot in snapshots:
        center = snapshot.get("center")
        if not isinstance(center, dict):
            continue
        try:
            if round(float(center.get("x")), 1) == x and round(float(center.get("y")), 1) == y:
                return snapshot
        except (TypeError, ValueError):
            continue
    return None


def infer_action_source(result: dict[str, Any] | None, step: dict[str, Any], action: dict[str, Any]) -> str:
    mode = str((result or {}).get("mode") or "").lower()
    if mode == "direct_ax":
        return "ax"
    if "uia" in mode:
        return "uia"
    explicit_source = source_name(action.get("source"))
    if explicit_source != "unknown":
        return explicit_source
    snapshot = snapshot_for_action(step, action)
    if snapshot is not None:
        snapshot_source = source_name(snapshot.get("source"))
        if snapshot_source != "unknown":
            return snapshot_source
        if snapshot.get("direct_ax"):
            return "ax"
    if mode in {"coordinate", "keyboard", "paste", "clipboard_paste", "unicode_stream"}:
        return "coordinate"
    return "unknown"


def coordinate_source(result: dict[str, Any] | None, step: dict[str, Any], action: dict[str, Any]) -> str | None:
    mode = str((result or {}).get("mode") or "").lower()
    has_point = isinstance((result or {}).get("point"), dict) or ("x" in action and "y" in action)
    if not has_point and mode not in {"coordinate", "uia_coordinate_click"}:
        return None
    source = infer_action_source(result, step, action)
    return source if source in ACTION_SOURCES else "unknown"


def planned_action_summary(step: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    sanitized = sanitize_action(action)
    source = infer_action_source(None, step, action)
    sanitized["source_summary"] = source
    coordinate = coordinate_source(None, step, action)
    if coordinate is not None:
        sanitized["coordinate_source"] = coordinate
    return sanitized


def execution_summary(step: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    action = result.get("action") if isinstance(result, dict) else {}
    action = action if isinstance(action, dict) else {}
    source = infer_action_source(result, step, action)
    summary: dict[str, Any] = {
        "ok": result.get("ok"),
        "mode": result.get("mode"),
        "action": sanitize_action(action),
        "source_summary": source,
    }
    coordinate = coordinate_source(result, step, action)
    if coordinate is not None:
        summary["coordinate_source"] = coordinate
    for key in ("point", "fallback_from", "fallback_reason", "input_method", "skipped", "activation"):
        if key in result:
            summary[key] = result.get(key)
    return summary


def compact_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, (bool, int, float)) or value is None:
            evidence[key] = value
        elif isinstance(value, str) and key in {"status", "reason", "kind", "mode", "confidence"}:
            evidence[key] = clean_text(value, limit=180)
        elif isinstance(value, list):
            evidence[f"{key}_count"] = len(value)
        elif isinstance(value, dict):
            evidence[f"{key}_present"] = True
    return evidence


def verification_status(payload: dict[str, Any]) -> str:
    raw_status = str(payload.get("status") or "").strip().lower()
    if raw_status in VERIFICATION_STATUSES:
        return raw_status
    if isinstance(payload.get("expected_text_visible"), bool):
        return "passed" if payload.get("expected_text_visible") else "failed"
    if isinstance(payload.get("matched"), bool):
        return "passed" if payload.get("matched") else "failed"
    if isinstance(payload.get("confirmed"), bool):
        return "passed" if payload.get("confirmed") else "failed"
    if isinstance(payload.get("covered"), bool):
        if payload.get("covered"):
            return "planned"
        return "failed" if payload.get("required") else "skipped"
    return "unknown"


def add_verification(
    verifications: list[dict[str, Any]],
    seen: set[int],
    *,
    name: str,
    source: str,
    payload: Any,
) -> None:
    if not isinstance(payload, dict):
        return
    identity = id(payload)
    if identity in seen:
        return
    seen.add(identity)
    verifications.append(
        {
            "name": name,
            "source": source,
            "status": verification_status(payload),
            "evidence": compact_evidence(payload),
        }
    )


def extract_verifications(step: dict[str, Any]) -> list[dict[str, Any]]:
    verifications: list[dict[str, Any]] = []
    seen: set[int] = set()
    for key in ("verification", "post_input_verification", "title_verification", "draft_verification", "post_send_verification"):
        add_verification(verifications, seen, name=key, source="step", payload=step.get(key))
    for index, result in enumerate(step.get("execution_results") or [], start=1):
        if not isinstance(result, dict):
            continue
        for key in ("verification", "post_input_verification", "title_verification", "draft_verification", "post_send_verification"):
            add_verification(verifications, seen, name=key, source=f"execution[{index}]", payload=result.get(key))
        diagnostics = result.get("input_diagnostics")
        if isinstance(diagnostics, dict):
            add_verification(
                verifications,
                seen,
                name="post_input_verification",
                source=f"execution[{index}].input_diagnostics",
                payload=diagnostics.get("post_input_verification"),
            )
    return verifications


def step_trace(step: dict[str, Any], *, platform: str) -> dict[str, Any]:
    plan = step.get("plan") if isinstance(step.get("plan"), dict) else {}
    actions = [item for item in plan.get("actions") or [] if isinstance(item, dict)]
    executions = [item for item in step.get("execution_results") or [] if isinstance(item, dict)]
    return {
        "step": step.get("step"),
        "target": step.get("target") if isinstance(step.get("target"), dict) else {},
        "observation": observation_summary(step, platform=platform),
        "plan": {
            "status": plan.get("status"),
            "summary": clean_text(plan.get("summary"), limit=300),
            "actions": [planned_action_summary(step, action) for action in actions],
        },
        "execution": [execution_summary(step, result) for result in executions],
        "verifications": extract_verifications(step),
    }


def metric_action_sources(trace_step: dict[str, Any]) -> list[str]:
    executions = trace_step.get("execution") or []
    if executions:
        return [str(item.get("source_summary") or "unknown") for item in executions if isinstance(item, dict)]
    actions = ((trace_step.get("plan") or {}).get("actions") or [])
    return [str(item.get("source_summary") or "unknown") for item in actions if isinstance(item, dict)]


def build_metrics(trace_steps: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = {
        "step_count": len(trace_steps),
        "action_count": 0,
        "execution_count": 0,
        "ax_action_count": 0,
        "uia_action_count": 0,
        "ocr_action_count": 0,
        "visual_action_count": 0,
        "profile_region_action_count": 0,
        "coordinate_action_count": 0,
        "fallback_count": 0,
        "verification_count": 0,
        "passed_verification_count": 0,
        "failed_verification_count": 0,
        "planned_verification_count": 0,
        "skipped_verification_count": 0,
        "unknown_verification_count": 0,
    }
    for trace_step in trace_steps:
        actions = ((trace_step.get("plan") or {}).get("actions") or [])
        executions = trace_step.get("execution") or []
        metrics["action_count"] += len(actions)
        metrics["execution_count"] += len(executions)
        for source in metric_action_sources(trace_step):
            if source == "ax":
                metrics["ax_action_count"] += 1
            elif source == "uia":
                metrics["uia_action_count"] += 1
            elif source == "ocr":
                metrics["ocr_action_count"] += 1
                metrics["coordinate_action_count"] += 1
            elif source == "profile_region":
                metrics["profile_region_action_count"] += 1
                metrics["coordinate_action_count"] += 1
            elif source == "visual":
                metrics["visual_action_count"] += 1
                metrics["coordinate_action_count"] += 1
            elif source == "coordinate":
                metrics["coordinate_action_count"] += 1
        for item in executions:
            if isinstance(item, dict) and (item.get("fallback_from") or item.get("fallback_reason")):
                metrics["fallback_count"] += 1
        for verification in trace_step.get("verifications") or []:
            if not isinstance(verification, dict):
                continue
            metrics["verification_count"] += 1
            status = str(verification.get("status") or "unknown")
            key = f"{status}_verification_count"
            if key in metrics:
                metrics[key] += 1
            else:
                metrics["unknown_verification_count"] += 1
    return metrics


def outcome_from_run_log(run_log: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    status = str(run_log.get("final_status") or "unknown")
    failed = int(metrics.get("failed_verification_count") or 0)
    passed = int(metrics.get("passed_verification_count") or 0)
    planned = int(metrics.get("planned_verification_count") or 0)
    unknown = int(metrics.get("unknown_verification_count") or 0)
    if failed:
        verification_status_value = "failed"
        verified = False
    elif passed and not unknown:
        verification_status_value = "passed"
        verified = True
    elif planned:
        verification_status_value = "planned"
        verified = False
    else:
        verification_status_value = "unknown"
        verified = False
    failure_reason = clean_text(run_log.get("failure_reason") or run_log.get("reason"))
    if failure_reason is None and status in {"blocked", "max_steps_reached"}:
        failure_reason = status
    return {
        "status": status,
        "verified": verified,
        "verification_status": verification_status_value,
        "failure_reason": failure_reason,
    }


def build_trace(run_log: dict[str, Any], *, platform: str) -> dict[str, Any]:
    steps = [step_trace(step, platform=platform) for step in run_log.get("steps") or [] if isinstance(step, dict)]
    metrics = build_metrics(steps)
    trace = {
        "schema_version": SCHEMA_VERSION,
        "kind": TRACE_KIND,
        "platform": platform,
        "target": run_log.get("target") if isinstance(run_log.get("target"), dict) else {},
        "task": {
            "source": "workflow",
            "instruction": clean_text(run_log.get("instruction"), limit=500),
        },
        "steps": steps,
        "outcome": outcome_from_run_log(run_log, metrics),
        "metrics": metrics,
    }
    return trace


def trace_summary(trace: Any) -> dict[str, Any] | None:
    if not isinstance(trace, dict):
        return None
    metrics = trace.get("metrics") if isinstance(trace.get("metrics"), dict) else {}
    outcome = trace.get("outcome") if isinstance(trace.get("outcome"), dict) else {}
    failed: list[dict[str, Any]] = []
    for step in trace.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for verification in step.get("verifications") or []:
            if isinstance(verification, dict) and verification.get("status") == "failed":
                failed.append(
                    {
                        "step": step.get("step"),
                        "name": verification.get("name"),
                        "source": verification.get("source"),
                        "evidence": verification.get("evidence"),
                    }
                )
    return {
        "schema_version": trace.get("schema_version"),
        "platform": trace.get("platform"),
        "final_status": outcome.get("status"),
        "verified": outcome.get("verified"),
        "step_count": metrics.get("step_count", len(trace.get("steps") or [])),
        "metrics": metrics,
        "failed_verifications": failed,
    }
