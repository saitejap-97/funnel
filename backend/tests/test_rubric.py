"""Rubric aggregation is deterministic pure math."""
from funnel.rubric import aggregate


def test_aggregate_weighted_sum():
    scores = [
        {"criterion": "skills_match", "score_0_10": 10,
         "evidence": "e", "confidence": 1},
        {"criterion": "experience_relevance", "score_0_10": 5,
         "evidence": "", "confidence": 0.5},
        {"criterion": "education_fit", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
        {"criterion": "impact_signals", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
        {"criterion": "growth_trajectory", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
    ]
    total, breakdown = aggregate(scores)
    assert total == round((10 * 0.35 + 5 * 0.30) * 10, 1) == 50.0
    assert len(breakdown) == 5


def test_aggregate_clamps_and_ignores_unknown():
    total, breakdown = aggregate(
        [
            {"criterion": "skills_match", "score_0_10": 99},
            {"criterion": "nope", "score_0_10": 10},
        ]
    )
    assert total == 35.0  # 10 clamped * 0.35 * 10
    assert [b["criterion"] for b in breakdown] == ["skills_match"]


def _every_object_node(schema):
    """Yield every {'type': 'object'} node in a JSON schema tree."""
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            yield schema
        for value in schema.values():
            yield from _every_object_node(value)
    elif isinstance(schema, list):
        for item in schema:
            yield from _every_object_node(item)


def test_schemas_are_strict_mode_compatible():
    """OpenAI strict structured outputs reject schemas where an object node
    lacks additionalProperties:false, `required` misses a property key, or
    `type` is a union — each was a live-API 400, not a unit failure."""
    from funnel.rubric import profile_json_schema, rank_json_schema

    def check(node, path="root"):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, path
                props = set(node.get("properties", {}))
                req = node.get("required", [])
                assert set(req) >= props, f"{path}: required misses {props - set(req)}"
            t = node.get("type")
            if t is not None:
                assert isinstance(t, str), f"{path}: union type {t}"
            for key, value in node.items():
                check(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                check(item, f"{path}[{i}]")

    for schema_fn in (profile_json_schema, rank_json_schema):
        nodes = list(_every_object_node(schema_fn()))
        assert nodes, f"{schema_fn.__name__} has no object nodes?"
        check(schema_fn())
