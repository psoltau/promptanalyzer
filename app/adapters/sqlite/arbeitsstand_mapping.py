import json
import sqlite3
from typing import Any, Dict

from app.domain.models import Arbeitsstand

ARBEITSSTAND_SPALTEN = (
    "system_prompt, user_prompt, tools_json, modelle, max_output_tokens, "
    "reasoning_effort, web_suche, search_context_size, wiederholungen"
)


def arbeitsstand_row_to_domain(row: sqlite3.Row) -> Arbeitsstand:
    return Arbeitsstand(
        system_prompt=row["system_prompt"],
        user_prompt=row["user_prompt"],
        tools_json=row["tools_json"],
        modelle=tuple(json.loads(row["modelle"])),
        max_output_tokens=row["max_output_tokens"],
        reasoning_effort=row["reasoning_effort"],
        web_suche=bool(row["web_suche"]),
        search_context_size=row["search_context_size"],
        wiederholungen=row["wiederholungen"],
    )


def arbeitsstand_to_params(arbeitsstand: Arbeitsstand) -> Dict[str, Any]:
    return {
        "system_prompt": arbeitsstand.system_prompt,
        "user_prompt": arbeitsstand.user_prompt,
        "tools_json": arbeitsstand.tools_json,
        "modelle": json.dumps(list(arbeitsstand.modelle)),
        "max_output_tokens": arbeitsstand.max_output_tokens,
        "reasoning_effort": arbeitsstand.reasoning_effort,
        "web_suche": int(arbeitsstand.web_suche),
        "search_context_size": arbeitsstand.search_context_size,
        "wiederholungen": arbeitsstand.wiederholungen,
    }
