import unicodedata

def normalize_string(string):
    """
    Normalize string
    - Remove diacritics
    - Remove leading and trailing spaces
    - NFKC normalization
    - To lowercase
    - Retain characters with category L (letters)
    """

    normalized = unicodedata.normalize('NFKD', string)
    normalized = normalized.strip()
    normalized = unicodedata.normalize('NFKC', normalized)
    normalized = normalized.lower()
    normalized = ''.join([char for char in normalized if unicodedata.category(char).startswith('L')])
    return normalized

class StrNorm:

    def __init__(self, string) -> None:
        self.value = string
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(normalize_string(self.value))

    def __eq__(self, __value: object) -> bool:
        if (__value == None):
            return False
        
        if (isinstance(__value, str)):
            return normalize_string(__value) == normalize_string(self.value)
        
        if (isinstance(__value, StrNorm)):
            return normalize_string(__value.value) == normalize_string(self.value)
        
        return False
