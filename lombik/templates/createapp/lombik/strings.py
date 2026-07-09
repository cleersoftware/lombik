from lombik.constants import IRREGULAR

def plural(word: str) -> str:
    if not word:
        return word

    lower = word.lower()

    # Preserve capitalization
    if lower in IRREGULAR:
        result = IRREGULAR[lower]
        if word.istitle():
            return result.capitalize()
        if word.isupper():
            return result.upper()
        return result

    # city -> cities
    if (
        lower.endswith("y")
        and len(lower) > 1
        and lower[-2] not in "aeiou"
    ):
        return word[:-1] + "ies"

    # bus -> buses, church -> churches, box -> boxes
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"

    # default -o rule
    if lower.endswith("o"):
        return word + "s"

    # default
    return word + "s"