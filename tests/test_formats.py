"""Choix des formats de sortie et arguments de la ligne de commande (sans toucher à une image)."""
import pytest


def test_parse_formats_basic(lossy):
    assert lossy.parse_formats("heic,jxl") == (("heic", "jxl"), [])


def test_parse_formats_canonical_order_case_and_spaces(lossy):
    assert lossy.parse_formats("AVIF  jpg") == (("jpg", "avif"), [])


def test_parse_formats_aliases_and_separators(lossy):
    assert lossy.parse_formats(".heif; JPEG + jfif")[0] == ("jpg", "heic")


def test_avi_is_read_as_avif_with_a_notice(lossy):
    selected, notices = lossy.parse_formats("avi")
    assert selected == ("avif",) and notices


@pytest.mark.parametrize("value", ["auto", "", None])
def test_auto(lossy, value):
    assert lossy.parse_formats(value)[0] is None


@pytest.mark.parametrize("bad, fragment", [("png", "inconnu"), ("heic,gif", "gif"), ("auto,heic", "auto")])
def test_invalid_format(lossy, bad, fragment):
    with pytest.raises(ValueError, match=fragment):
        lossy.parse_formats(bad)


def test_default_plans(lossy):
    assert lossy.plan_outputs("heic", None) == ("jpg", "jxl", "avif")
    assert lossy.plan_outputs("jpeg", None) == ("heic", "jxl", "avif")
    assert lossy.SAME_FORMAT == {"heic": "heic", "jpeg": "jpg"}


def test_argv(lossy):
    pa = lossy._parse_argv
    assert pa(["d", "o", "-f", "heic,jxl", "-y"]) == ("d", "o", "heic,jxl", True, False)
    assert pa(["-fheic"])[2] == "heic" and pa(["--formats=jxl"])[2] == "jxl"
    assert pa(["--oui"])[3] and pa(["--aide"])[4]
    assert pa(["-f", "heic", "-f", "jxl"])[2] == "heic,jxl"
    assert pa(["--", "-d"])[0] == "-d"


@pytest.mark.parametrize("argv", [["-f"], ["-f", "-y"], ["-x"], ["a", "b", "c"]])
def test_argv_errors(lossy, argv):
    with pytest.raises(ValueError):
        lossy._parse_argv(argv)
