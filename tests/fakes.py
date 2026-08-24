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
    """Der einzige Seam. Liefert vorbereitete Antworten statt echter Netzwerkaufrufe.

    Führt außerdem Buch darüber, wie viele Modelle gleichzeitig „im Flug“ sind
    (`max_gleichzeitige_modelle`) und ob jemals zwei Calls desselben Modells gleichzeitig
    liefen (`wiederholung_ueberlappung`) — damit Tests die geforderte Ausführungsordnung
    (parallel über Modelle, seriell über Wiederholungen) über HTTP beobachten können, ohne
    Produktionscode direkt anzusprechen.
    """

    def __init__(self) -> None:
        self._warteschlangen: Dict[str, List[VorbereiteteAntwort]] = {}
        self._standard = VorbereiteteAntwort()
        self.aufrufe: List[str] = []
        self.verwendete_api_keys: List[str] = []
        self._aktive_modelle: set = set()
        self.max_gleichzeitige_modelle = 0
        self.wiederholung_ueberlappung = False
        self._lock = threading.Lock()

    def antworte_mit(self, modell: str, antwort: VorbereiteteAntwort) -> None:
        self._warteschlangen.setdefault(modell, []).append(antwort)

    def setze_standard(self, antwort: VorbereiteteAntwort) -> None:
        self._standard = antwort

    def run(self, request: ModelRequest) -> ModelResult:
        modell = request.model
        self._markiere_aktiv(modell)
        try:
            with self._lock:
                self.aufrufe.append(modell)
                self.verwendete_api_keys.append(request.api_key)
            antwort = self._naechste_antwort(modell)
            if antwort.verzoegerung_s:
                time.sleep(antwort.verzoegerung_s)
            if antwort.fehler:
                raise ModelGatewayError(antwort.fehler, json.dumps({"model": modell}))
            return _zu_model_result(request, antwort)
        finally:
            self._markiere_inaktiv(modell)

    def _naechste_antwort(self, modell: str) -> VorbereiteteAntwort:
        with self._lock:
            warteschlange = self._warteschlangen.get(modell)
            if warteschlange:
                return warteschlange.pop(0)
            return self._standard

    def _markiere_aktiv(self, modell: str) -> None:
        with self._lock:
            if modell in self._aktive_modelle:
                self.wiederholung_ueberlappung = True
            self._aktive_modelle.add(modell)
            self.max_gleichzeitige_modelle = max(
                self.max_gleichzeitige_modelle, len(self._aktive_modelle)
            )

    def _markiere_inaktiv(self, modell: str) -> None:
        with self._lock:
            self._aktive_modelle.discard(modell)


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
