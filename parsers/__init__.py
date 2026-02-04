"""Cinema HTML parsers."""

from parsers.kika import parse as parse_kika
from parsers.mikro import parse as parse_mikro
from parsers.agrafka import parse as parse_agrafka
from parsers.paradox import parse as parse_paradox
from parsers.baranami import parse as parse_baranami
from parsers.kijow import parse as parse_kijow

PARSERS = {
    "kika": ("KIKA", parse_kika),
    "mikro": ("Mikro", parse_mikro),
    "agrafka": ("Agrafka", parse_agrafka),
    "paradox": ("Paradox", parse_paradox),
    "baranami": ("Barany", parse_baranami),
    "kijow": ("Kijów", parse_kijow),
}
