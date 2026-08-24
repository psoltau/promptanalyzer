class DomainError(Exception):
    """Base class for all domain errors. Mapped to HTTP responses in main.py."""


class ProfilNichtGefunden(DomainError):
    def __init__(self) -> None:
        super().__init__("Profil nicht gefunden")


class CallNichtGefunden(DomainError):
    def __init__(self) -> None:
        super().__init__("Call nicht gefunden")


class LaufNichtGefunden(DomainError):
    def __init__(self) -> None:
        super().__init__("Lauf nicht gefunden")


class NameLeer(DomainError):
    def __init__(self) -> None:
        super().__init__("Profilname ist leer")


class KeinModellGewaehlt(DomainError):
    def __init__(self) -> None:
        super().__init__("Arbeitsstand hat kein Modell ausgewählt")


class WiederholungenUngueltig(DomainError):
    def __init__(self) -> None:
        super().__init__("Wiederholungen muss mindestens 1 sein")


class ToolsJsonUngueltig(DomainError):
    def __init__(self) -> None:
        super().__init__("tools_json ist kein gültiges JSON")


class KeyFehlt(DomainError):
    def __init__(self) -> None:
        super().__init__("Kein API-Key im Header und keiner in der Umgebung")


class ModellNichtGefunden(DomainError):
    def __init__(self) -> None:
        super().__init__("Modell nicht gefunden")


class ModellNameVergeben(DomainError):
    def __init__(self) -> None:
        super().__init__("Modellname ist bereits vergeben")
