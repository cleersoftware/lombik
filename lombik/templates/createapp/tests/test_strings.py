from application.strings import plural, singularize, to_camel, to_snake


def test_to_snake():
    assert to_snake("Hello World") == "hello_world"
    assert to_snake("Hello-World") == "hello_world"
    assert to_snake("  Hello World  ") == "hello_world"


def test_to_camel():
    assert to_camel("hello_world") == "HelloWorld"
    assert to_camel("hello-world") == "HelloWorld"


def test_plural_regular():
    assert plural("plan") == "plans"
    assert plural("cat") == "cats"


def test_plural_y_to_ies():
    assert plural("city") == "cities"
    assert plural("company") == "companies"


def test_plural_sibilants():
    assert plural("bus") == "buses"
    assert plural("box") == "boxes"
    assert plural("church") == "churches"


def test_plural_irregular():
    assert plural("person") == "people"
    assert plural("child") == "children"
    assert plural("sheep") == "sheep"


def test_singularize():
    assert singularize("plans") == "plan"
    assert singularize("cities") == "city"
    assert singularize("people") == "person"


def test_roundtrip():
    for word in ("plan", "city", "bus", "child", "person"):
        assert singularize(plural(word)) == word
