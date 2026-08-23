from datetime import datetime
from typing import Optional


def dt_to_text(dt: datetime) -> str:
    return dt.isoformat()


def text_to_dt(text: Optional[str]) -> Optional[datetime]:
    if text is None:
        return None
    return datetime.fromisoformat(text)
