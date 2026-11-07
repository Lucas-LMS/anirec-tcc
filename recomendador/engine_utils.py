"""Small shared text normalization without importing the recommendation engine."""
import unicodedata
def normalize_name(value):return unicodedata.normalize('NFKC',str(value)).lower().strip()
