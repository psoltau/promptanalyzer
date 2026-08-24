import json
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.application.ports import ModelGatewayError, ModelRequest, ModelResult
from app.domain.models import Modell


@dataclass
class VorbereiteteAntwort:
    incomplete_grund: Optional[str] = None
    input_tokens: int = 10
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    output_tokens: int = 5
    total_tokens: int = 15
    web_search_calls: int = 0
    antwort_text: str = "Hallo, das ist die Antwort."
    fehler: Optional[str] = None
    verzoegerung_s: float = 0.0


class FakeModelGateway:
    """Der einzige Seam. Liefert vorbereitete Antworten statt echter Netzwerkaufrufe."""

    def __init__(self) -> None:
        self._warteschlangen: Dict[str, List[VorbereiteteAntwort]] = {}
        self._standard = VorbereiteteAntwort()
        self.aufrufe: List[str] = []
        self.verwendete_api_keys: List[str] = []
        self._lock = threading.Lock()

    def antworte_mit(self, modell: str, antwort: VorbereiteteAntwort) -> None:
        self._warteschlangen.setdefault(modell, []).append(antwort)

    def setze_standard(self, antwort: VorbereiteteAntwort) -> None:
        self._standard = antwort

    def run(self, request: ModelRequest) -> ModelResult:
        with self._lock:
            self.aufrufe.append(request.model)
            self.verwendete_api_keys.append(request.api_key)
        antwort = self._naechste_antwort(request.model)
        if antwort.verzoegerung_s:
            time.sleep(antwort.verzoegerung_s)
        if antwort.fehler:
            raise ModelGatewayError(antwort.fehler, json.dumps({"model": request.model}))
        return _zu_model_result(request, antwort)

    def _naechste_antwort(self, modell: str) -> VorbereiteteAntwort:
        with self._lock:
            warteschlange = self._warteschlangen.get(modell)
            if warteschlange:
                return warteschlange.pop(0)
            return self._standard


@dataclass
class FakeModellRepository:
    """In-memory-Register für Use-Case-Tests, kein SQLite beteiligt."""

    _speicher: Dict[str, Modell] = field(default_factory=dict)

    def add(self, modell: Modell) -> None:
        self._speicher[modell.name] = modell

    def get(self, name: str) -> Optional[Modell]:
        return self._speicher.get(name)

    def list(self) -> List[Modell]:
        return list(self._speicher.values())

    def update(self, modell: Modell) -> None:
        self._speicher[modell.name] = modell

    def delete(self, name: str) -> None:
        self._speicher.pop(name, None)


def _zu_model_result(request: ModelRequest, antwort: VorbereiteteAntwort) -> ModelResult:
    status = "incomplete" if antwort.incomplete_grund else "completed"
    return ModelResult(
        incomplete_grund=antwort.incomplete_grund,
        input_tokens=antwort.input_tokens,
        cached_input_tokens=antwort.cached_input_tokens,
        reasoning_tokens=antwort.reasoning_tokens,
        output_tokens=antwort.output_tokens,
        total_tokens=antwort.total_tokens,
        web_search_calls=antwort.web_search_calls,
        antwort_text=antwort.antwort_text,
        request_json=json.dumps({"model": request.model, "input": request.user_prompt}),
        response_json=json.dumps({"status": status}),
    )
