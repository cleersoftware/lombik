from lombik.constants import IRREGULAR


def to_snake(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def to_camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_"))


def singularize(word: str) -> str:
    if not word:
        return word

    lower = word.lower()

    for singular, pluralized in IRREGULAR.items():
        if lower == pluralized:
            if word.istitle():
                return singular.capitalize()
            if word.isupper():
                return singular.upper()
            return singular

    if lower.endswith("ies") and len(lower) > 3:
        return word[:-3] + "y"
    if lower.endswith(("sses", "shes", "ches", "xes", "zes")):
        return word[:-2]
    if lower.endswith("s") and not lower.endswith("ss"):
        return word[:-1]
    return word


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