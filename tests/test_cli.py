"""Ligne de commande, en sous-processus (le clavier est simulé par un pseudo-terminal sous Linux/macOS)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from conftest import PROGRAM, make_rgb

pty = pytest.importorskip("pty") if os.name != "nt" else None


def folder(tmp_path, *names):
    d = tmp_path / "src"
    d.mkdir()
    small = make_rgb()
    for n in names:
        if n.endswith(".heic"):
            small.save(d / n, "HEIF", quality=70)
        else:
            small.save(d / n, "JPEG", quality=90)
    return d


def cli(args, answers=None, timeout=600):
    """(code retour, sortie). answers : touches tapées (pty) ; None : pas de clavier (entrée = /dev/null)."""
    cmd = [sys.executable, str(PROGRAM), *map(str, args)]
    if answers is None:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    master, slave = pty.openpty()
    p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.close(slave)
    for a in answers:
        os.write(master, a.encode())
    out = p.communicate(timeout=timeout)[0].decode("utf-8", "replace")
    os.close(master)
    return p.returncode, out


def listing(d, sub):
    path = d / "converti" / sub
    return sorted(x.name for x in path.iterdir()) if path.exists() else []


def test_help():
    rc, out = cli(["--aide"])
    assert rc == 0 and "Usage" in out and "--formats" in out


def test_unknown_format_is_refused_before_any_work(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d, "-f", "png"])
    assert rc == 2 and "inconnu" in out and not (d / "converti").exists()


def test_missing_source_folder(tmp_path):
    rc, out = cli([tmp_path / "absent"])
    assert rc == 2 and "introuvable" in out


def test_single_format(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d, "--formats=jxl"])
    assert rc == 0 and sorted(x.name for x in (d / "converti").iterdir()) == ["jxl"]
    assert listing(d, "jxl") == ["a.jxl", "b.jxl"]


def test_defaults_ask_nothing(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d])
    assert rc == 0 and "[o/N]" not in out
    assert listing(d, "jpg") == ["a.jpg"] and listing(d, "heic") == ["b.heic"]
    assert listing(d, "jxl") == ["a.jxl", "b.jxl"] and listing(d, "avif") == ["a.avif", "b.avif"]


def test_same_format_without_keyboard_or_yes_is_skipped_with_exit_1(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d, "-f", "heic"])
    assert rc == 1 and listing(d, "heic") == ["b.heic"] and "IGNORÉES" in out


def test_same_format_with_yes(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d, "-f", "heic", "-y"])
    assert rc == 0 and listing(d, "heic") == ["a.heic", "b.heic"]


@pytest.mark.skipif(os.name == "nt", reason="pty indisponible sous Windows")
def test_same_format_confirmation_defaults_to_no(tmp_path):
    d = folder(tmp_path, "a.heic", "b.jpg")
    rc, out = cli([d, "-f", "heic,jpg"], ["oui\n", "\n"])        # oui pour HEIC -> HEIC, Entrée (= non) pour JPEG -> JPG
    assert rc == 0 and listing(d, "heic") == ["a.heic", "b.heic"] and listing(d, "jpg") == ["a.jpg"]


@pytest.mark.skipif(os.name == "nt", reason="pty indisponible sous Windows")
def test_closed_input_is_not_a_refusal(tmp_path):
    d = folder(tmp_path, "only.heic")
    rc, out = cli([d, "-f", "heic"], ["\x04"])                    # Ctrl+D
    assert rc == 1 and "Rien à convertir" in out


def test_source_is_never_overwritten(tmp_path):
    d = tmp_path / "jpg"
    d.mkdir()
    make_rgb().save(d / "s.jpg", "JPEG", quality=90)
    before = (d / "s.jpg").read_bytes()
    rc, out = cli([d, tmp_path, "-f", "jpg", "-y"])
    assert rc == 1 and (d / "s.jpg").read_bytes() == before and "fichier source" in out


def test_formats_setting_in_the_program(tmp_path):
    text = PROGRAM.read_text(encoding="utf-8")
    patched = tmp_path / "patched.py"
    patched.write_text(text.replace('FORMATS_SORTIE = "auto"', 'FORMATS_SORTIE = "avif"', 1), encoding="utf-8")
    d = folder(tmp_path, "s.heic")
    p = subprocess.run([sys.executable, str(patched), str(d)], stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
    assert p.returncode == 0 and sorted(x.name for x in (d / "converti").iterdir()) == ["avif"]
