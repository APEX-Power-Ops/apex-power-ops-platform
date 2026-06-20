from dataclasses import dataclass, field


@dataclass
class ResolvedResource:
    resource_type: str
    title: str
    source: str               # "curated" | "section_match"
    reference: dict = field(default_factory=dict)   # {kind, id?/url?/section?, slug?, summary?}
    is_primary: bool = False
    is_mandatory: bool = False
    cert_level: str | None = None
    score: float = 0.0
    why: str = ""
