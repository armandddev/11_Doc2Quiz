from dataclasses import asdict, dataclass


@dataclass
class Section:
    id: str
    title: str
    level: str | None
    text: str
    summary: str
    notion_ids: list[str] | None
    pages: list[int]

    def to_dict(self) -> dict:
        return asdict(self)