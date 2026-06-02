# Modeling Policy

## Purpose
Define a clear boundary between configuration models and runtime domain/result payloads.

## Policy
- Use **Pydantic** only for configuration and environment parsing.
  - Current location: `src/paper_marker/config.py`.
- Use **dataclasses** for runtime domain models and result payloads.
  - Current location: `src/paper_marker/core/models.py`.
- Keep serialization explicit through `to_json_dict()` on dataclass payload roots.

## Rationale
- Configuration benefits from Pydantic validation and env alias support.
- Runtime conversion payloads are internal and performance-friendly as dataclasses.
- This split keeps contracts simple while preserving strict config parsing.

## Enforcement
- New runtime payload structures should be added as dataclasses unless there is a clear external schema requirement.
- If an external API contract requires strict schema validation, introduce targeted Pydantic DTOs at interface boundaries rather than replacing domain dataclasses wholesale.
