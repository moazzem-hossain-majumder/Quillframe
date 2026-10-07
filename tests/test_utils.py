import pytest

from quillframe.utils import extract_json, slugify


def test_extract_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_fenced_json():
    assert extract_json('Here you go:\n```json\n{"a": [1, 2]}\n```\nEnjoy!') == {"a": [1, 2]}


def test_extract_json_surrounded_by_prose():
    assert extract_json('Sure! {"a": {"b": 2}} Hope that helps.') == {"a": {"b": 2}}


def test_extract_json_with_braces_inside_strings():
    assert extract_json('noise {"a": "curly } brace \\" quote"} noise') == {"a": 'curly } brace " quote'}


@pytest.mark.parametrize("bad", ["no json here", '{"unclosed": 1', ""])
def test_extract_json_failures(bad):
    with pytest.raises(ValueError):
        extract_json(bad)


def test_slugify():
    assert slugify("A Dhaka studio's NEW film!") == "a-dhaka-studio-s-new-film"
    assert slugify("   ") == "campaign"
    assert slugify("বাংলা") == "campaign"
    assert len(slugify("x" * 200)) <= 40
