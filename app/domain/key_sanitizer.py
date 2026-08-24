import re
from typing import Optional

_KEY_MUSTER = re.compile(r"sk-[A-Za-z0-9_-]{3,}")
_ERSATZ = "[KEY_ENTFERNT]"


def bereinige(text: Optional[str]) -> Optional[str]:
    """Entfernt key-artige Zeichenketten aus Text, der geschrieben werden soll.

    Gürtel zum Hosenträger (SPEC.md, "Umgang mit dem Key"): der Key reist architektonisch
    nur im Header, aber ein Nutzer kann ihn auch versehentlich in einen Prompt tippen.
    """
    if text is None:
        return None
    return _KEY_MUSTER.sub(_ERSATZ, text)
