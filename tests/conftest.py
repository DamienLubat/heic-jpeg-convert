"""Fixtures des tests : tout est fabriqué ici, aucune photo réelle n'est nécessaire (ni fournie)."""
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
from PIL import Image

pillow_heif.register_heif_opener()
ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "heic_jpeg_convert.py"


def load_program(preset="Lossy", **overrides):
    """Charge le programme comme module, avec le préréglage voulu (réglage FIDELITE) et des surcharges de réglages."""
    text = PROGRAM.read_text(encoding="utf-8")
    text = re.sub(r'^FIDELITE = "[A-Za-z]+"(\s+#)', rf'FIDELITE = "{preset}"\1', text, count=1, flags=re.M)
    path = Path(tempfile.mkdtemp()) / "hjc.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"hjc_{preset}_{abs(hash(str(overrides)))}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, value in overrides.items():
        setattr(module, key, value)
    return module


def make_rgb(width=320, height=240, seed=1):
    """Dégradé + bruit, déterministe."""
    rng = np.random.default_rng(seed)
    x = np.broadcast_to(np.linspace(0, 255, width)[None, :, None], (height, width, 1))
    y = np.broadcast_to(np.linspace(0, 255, height)[:, None, None], (height, width, 1))
    base = np.concatenate([x, y, (x + y) / 2], axis=2) + rng.normal(0, 6, (height, width, 3))
    return Image.fromarray(np.clip(base, 0, 255).astype("uint8"))


def make_ultrahdr(module, path, size=(320, 240), orientation=1):
    """JPEG « Ultra HDR » synthétique (image SDR + carte de gain monocanal + métadonnées ISO / XMP), écrit par le programme."""
    im = make_rgb(*size, seed=2)
    gain = Image.fromarray(np.clip(np.linspace(0, 255, size[0] // 2)[None, :] * np.ones((size[1] // 2, 1)), 0, 255).astype("uint8"), "L")
    meta = dict(base_headroom=0.0, alt_headroom=2.0, gain_min=0.0, gain_max=2.0, gamma=1.0, base_offset=1 / 64, alt_offset=1 / 64)
    exif = Image.Exif()
    exif[0x010F] = "Test"
    if orientation != 1:
        exif[274] = orientation
    data = module.build_hdr_jpeg(dict(payload=None, meta=meta, gain=gain), im, exif.tobytes(), None)
    Path(path).write_bytes(data)
    return meta


@pytest.fixture(scope="session")
def lossy():
    return load_program("Lossy")


@pytest.fixture(scope="session")
def lossless():
    return load_program("Lossless")


@pytest.fixture
def jpeg_file(tmp_path):
    path = tmp_path / "photo.jpg"
    make_rgb().save(path, "JPEG", quality=90)
    return path


@pytest.fixture
def heic_file(tmp_path):
    path = tmp_path / "photo.heic"
    make_rgb(seed=3).save(path, "HEIF", quality=70)
    return path


def convert(module, src, wanted=None, out=None):
    """Convertit un fichier ; renvoie (dossier de sortie, dict du résultat)."""
    out = Path(out or tempfile.mkdtemp())
    job = (Path(src), out, Path(src).stem) + ((wanted,) if wanted is not None else ())
    name, err, kind, done, notes, degraded, details, label = module.convert(job)
    return out, dict(err=err, kind=kind, hdr=done, notes=notes, degraded=degraded, details=details, source=label)
