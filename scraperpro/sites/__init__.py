from .princetontec import PrincetonTecScraper
from .crispi import CrispiScraper
from .oakleysi import OakleySIScraper

REGISTRY = {
    "princetontec": PrincetonTecScraper,
    "crispi": CrispiScraper,
    "oakleysi": OakleySIScraper,
}
