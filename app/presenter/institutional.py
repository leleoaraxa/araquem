from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.utils.filecache import load_yaml_cached

POLICY_PATH = "data/policies/institutional.yaml"


def load_institutional_policy() -> Dict[str, Any]:
    # load_yaml_cached já faz cache por mtime; manter leitura simples aqui evita reload no hot path.
    return load_yaml_cached(POLICY_PATH)


def _get_intent_prefix(policy: Dict[str, Any]) -> str:
    apply_when = policy.get("apply_when") if isinstance(policy, dict) else {}
    intent_prefix = (
        apply_when.get("intent_prefix")
        if isinstance(apply_when, dict)
        else "institutional_"
    )
    if not isinstance(intent_prefix, str) or not intent_prefix.strip():
        return "institutional_"
    return intent_prefix


def is_institutional_intent(intent: str) -> bool:
    policy = load_institutional_policy()
    intent_prefix = _get_intent_prefix(policy if isinstance(policy, dict) else {})
    return bool(isinstance(intent, str) and intent.startswith(intent_prefix))


def _truncate_text(text: str, max_chars: int) -> str:
    if not isinstance(text, str):
        return ""
    if not isinstance(max_chars, int) or max_chars <= 0:
        return text.strip()
    return text.strip()[:max_chars]


def compose_institutional_answer(
    *, baseline_answer: str, intent: str
) -> Optional[str]:
    policy = load_institutional_policy()
    intent_prefix = _get_intent_prefix(policy if isinstance(policy, dict) else {})

    if not isinstance(intent, str) or not intent.startswith(intent_prefix):
        return None

    paths = policy.get("paths") if isinstance(policy, dict) else {}
    response_contract_path = (
        paths.get("response_contract") if isinstance(paths, dict) else None
    )
    intent_map_path = paths.get("intent_map") if isinstance(paths, dict) else None
    concepts_path = paths.get("concepts") if isinstance(paths, dict) else None

    if isinstance(response_contract_path, str) and response_contract_path.strip():
        contract = load_yaml_cached(str(response_contract_path))
    else:
        contract = None

    safe_fallback_text = _render_safe_fallback(contract)
    safe_fallback_text = (
        safe_fallback_text
        or "Não consegui completar a resposta institucional agora."
    )

    if not all(
        isinstance(path, str) and path.strip()
        for path in (response_contract_path, intent_map_path, concepts_path)
    ):
        return safe_fallback_text

    intent_map = load_yaml_cached(str(intent_map_path))
    concepts = load_yaml_cached(str(concepts_path))

    if not contract or not intent_map or not concepts:
        return safe_fallback_text

    layers_cfg = contract.get("response_layers") if isinstance(contract, dict) else {}
    layer_1_cfg = layers_cfg.get("layer_1_direct") if isinstance(layers_cfg, dict) else {}
    layer_2_cfg = (
        layers_cfg.get("layer_2_enrichment") if isinstance(layers_cfg, dict) else {}
    )
    layer_3_cfg = layers_cfg.get("layer_3_concept") if isinstance(layers_cfg, dict) else {}

    layer_1_constraints = (
        layer_1_cfg.get("constraints") if isinstance(layer_1_cfg, dict) else {}
    )
    layer_2_constraints = (
        layer_2_cfg.get("constraints") if isinstance(layer_2_cfg, dict) else {}
    )
    layer_3_constraints = (
        layer_3_cfg.get("constraints") if isinstance(layer_3_cfg, dict) else {}
    )

    max_layer_1_chars = layer_1_constraints.get("max_chars", 280)
    max_bullets = layer_2_constraints.get("max_bullets", 4)
    max_chars_per_bullet = layer_2_constraints.get("max_chars_per_bullet", 140)
    max_layer_3_chars = layer_3_constraints.get("max_chars", 350)

    composition = contract.get("composition") if isinstance(contract, dict) else {}
    presentation = composition.get("presentation") if isinstance(composition, dict) else {}
    headings = presentation.get("headings") if isinstance(presentation, dict) else {}
    layer_2_title = headings.get("layer_2_default_title") or "Complemento útil"
    layer_3_title = headings.get("layer_3_default_title") or "Conceito"

    intent_entries = intent_map.get("intent_map") if isinstance(intent_map, dict) else None
    intent_entry = None
    if isinstance(intent_entries, list):
        for item in intent_entries:
            if isinstance(item, dict) and item.get("intent_id") == intent:
                intent_entry = item
                break

    intent_map_fallback = (
        intent_map.get("fallback") if isinstance(intent_map, dict) else {}
    )
    concept_ref = None
    bullets: List[str] = []
    if isinstance(intent_entry, dict):
        concept_ref = intent_entry.get("concept_ref")
        enrichment = intent_entry.get("enrichment")
        if isinstance(enrichment, dict):
            items = enrichment.get("bullets")
            if isinstance(items, list):
                bullets = [item for item in items if isinstance(item, str)]

    if not isinstance(concept_ref, str) or not concept_ref.strip():
        fallback_ref = (
            intent_map_fallback.get("concept_ref")
            if isinstance(intent_map_fallback, dict)
            else None
        )
        if isinstance(fallback_ref, str) and fallback_ref.strip():
            concept_ref = fallback_ref
        else:
            return safe_fallback_text

    concept_entries = concepts.get("concepts") if isinstance(concepts, dict) else []
    concept_text = ""
    if isinstance(concept_entries, list):
        for item in concept_entries:
            if isinstance(item, dict) and item.get("id") == concept_ref:
                concept_text = str(item.get("description") or "")
                break
    if not concept_text:
        return safe_fallback_text

    layer_1_text = _truncate_text(baseline_answer, int(max_layer_1_chars))
    layer_3_text = _truncate_text(concept_text, int(max_layer_3_chars))
    if not layer_1_text and not layer_3_text and not bullets:
        return safe_fallback_text

    composed_sections: List[str] = []
    if layer_1_text:
        composed_sections.append(layer_1_text)

    if bullets:
        limited_bullets: List[str] = []
        for bullet in bullets[: int(max_bullets)]:
            trimmed = _truncate_text(bullet, int(max_chars_per_bullet))
            if trimmed:
                limited_bullets.append(f"- {trimmed}")
        if limited_bullets:
            composed_sections.append(f"{layer_2_title}\n" + "\n".join(limited_bullets))

    if layer_3_text:
        composed_sections.append(f"{layer_3_title}\n{layer_3_text}")

    if not composed_sections:
        return safe_fallback_text

    return "\n\n".join(composed_sections)


def _render_safe_fallback(contract: Dict[str, Any]) -> Optional[str]:
    if not isinstance(contract, dict):
        return None

    compliance = contract.get("compliance") if isinstance(contract, dict) else {}
    safe_fallback = compliance.get("safe_fallback") if isinstance(compliance, dict) else {}
    response = safe_fallback.get("response") if isinstance(safe_fallback, dict) else {}

    if not isinstance(response, dict):
        return None

    layer_1_text = response.get("layer_1_direct")
    layer_2_data = response.get("layer_2_enrichment")
    layer_3_text = response.get("layer_3_concept")

    layers_cfg = contract.get("response_layers") if isinstance(contract, dict) else {}
    layer_1_cfg = layers_cfg.get("layer_1_direct") if isinstance(layers_cfg, dict) else {}
    layer_2_cfg = (
        layers_cfg.get("layer_2_enrichment") if isinstance(layers_cfg, dict) else {}
    )
    layer_3_cfg = layers_cfg.get("layer_3_concept") if isinstance(layers_cfg, dict) else {}

    layer_1_constraints = (
        layer_1_cfg.get("constraints") if isinstance(layer_1_cfg, dict) else {}
    )
    layer_2_constraints = (
        layer_2_cfg.get("constraints") if isinstance(layer_2_cfg, dict) else {}
    )
    layer_3_constraints = (
        layer_3_cfg.get("constraints") if isinstance(layer_3_cfg, dict) else {}
    )

    max_layer_1_chars = layer_1_constraints.get("max_chars", 280)
    max_bullets = layer_2_constraints.get("max_bullets", 4)
    max_chars_per_bullet = layer_2_constraints.get("max_chars_per_bullet", 140)
    max_layer_3_chars = layer_3_constraints.get("max_chars", 350)

    composition = contract.get("composition") if isinstance(contract, dict) else {}
    presentation = composition.get("presentation") if isinstance(composition, dict) else {}
    headings = presentation.get("headings") if isinstance(presentation, dict) else {}
    layer_2_title_default = headings.get("layer_2_default_title") or "Complemento útil"
    layer_3_title_default = headings.get("layer_3_default_title") or "Conceito"

    composed_sections: List[str] = []

    if isinstance(layer_1_text, str) and layer_1_text.strip():
        trimmed = _truncate_text(layer_1_text, int(max_layer_1_chars))
        if trimmed:
            composed_sections.append(trimmed)

    if isinstance(layer_2_data, dict):
        items = layer_2_data.get("items")
        title = layer_2_data.get("title") or layer_2_title_default
        bullets: List[str] = []
        if isinstance(items, list):
            for bullet in items[: int(max_bullets)]:
                if not isinstance(bullet, str):
                    continue
                trimmed = _truncate_text(bullet, int(max_chars_per_bullet))
                if trimmed:
                    bullets.append(f"- {trimmed}")
        if bullets:
            composed_sections.append(f"{title}\n" + "\n".join(bullets))

    if isinstance(layer_3_text, str) and layer_3_text.strip():
        trimmed = _truncate_text(layer_3_text, int(max_layer_3_chars))
        if trimmed:
            composed_sections.append(f"{layer_3_title_default}\n{trimmed}")

    if not composed_sections:
        return None

    return "\n\n".join(composed_sections)
