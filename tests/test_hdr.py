"""JPEG Ultra HDR (image SDR + carte de gain + métadonnées ISO 21496-1 / XMP) fabriqué ici, converti dans les quatre formats.
Le cas HEIC HDR d'un iPhone demande un vrai fichier : voir test_real_iphone_hdr (variable HJC_TEST_HEIC_HDR)."""
import io
import os
import re
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
from PIL import Image

from conftest import convert, make_ultrahdr

ALL = ("jpg", "heic", "jxl", "avif")


def names(out):
    return sorted(p.name for p in out.iterdir())


@pytest.fixture
def hdr_file(lossy, tmp_path):
    path = tmp_path / "uhdr.jpg"
    make_ultrahdr(lossy, path)
    return path


def test_synthetic_file_is_recognised_as_ultra_hdr(lossy, hdr_file):
    primary, gain = lossy._split_ultrahdr(hdr_file.read_bytes())
    assert gain is not None
    assert lossy.jpeg_hdr_source(primary, gain, 1)["meta"]["gain_max"] == pytest.approx(2.0)


def test_ultra_hdr_to_all_formats_keeps_hdr(lossy, hdr_file):
    out, r = convert(lossy, hdr_file, ALL)
    assert r["err"] is None and r["kind"] == "HDR" and not r["degraded"]
    assert sorted(r["hdr"]) == ["avif", "heic", "jpg", "jxl"]
    assert names(out) == ["avif", "heic", "jpg", "jxl"]


def test_avif_hdr_is_10_bit_pq_rec2020(lossy, hdr_file):
    out, r = convert(lossy, hdr_file, ("avif",))
    assert r["err"] is None and r["hdr"] == ["avif"]
    assert lossy._avif_colr((out / "avif" / "uhdr.avif").read_bytes()) == ((9, 16, 9), True)      # primaires, transfert, matrice ; plage complète


def test_heic_hdr_is_10_bit_pq_rec2020(lossy, hdr_file):
    out, r = convert(lossy, hdr_file, ("heic",))
    assert r["err"] is None and r["hdr"] == ["heic"]
    heif = pillow_heif.open_heif(str(out / "heic" / "uhdr.heic"), convert_hdr_to_8bit=False)[0]
    nclx = heif.info.get("nclx_profile") or {}
    assert heif.info.get("bit_depth") == 10
    assert tuple(nclx.get(k) for k in ("color_primaries", "transfer_characteristics", "matrix_coefficients", "full_range_flag")) == (9, 16, 9, 1)


def test_ultra_hdr_to_jpg_keeps_the_gain_map_and_metadata(lossy, hdr_file):
    out, r = convert(lossy, hdr_file, ("jpg",))
    assert r["err"] is None and r["hdr"] == ["jpg"]
    data = (out / "jpg" / "uhdr.jpg").read_bytes()
    primary, gain = lossy._split_ultrahdr(data)
    assert gain is not None
    src_primary, src_gain = lossy._split_ultrahdr(hdr_file.read_bytes())
    want = lossy.jpeg_hdr_source(src_primary, src_gain, 1)["meta"]
    got = lossy.jpeg_hdr_source(primary, gain, 1)["meta"]
    assert max(abs(got[k] - want[k]) for k in want) <= 2e-6


def test_hdr_off_gives_sdr_without_error(tmp_path, hdr_file):
    from conftest import load_program
    module = load_program("Lossy", HDR=False)
    out, r = convert(module, hdr_file, ("jxl", "avif"))
    assert r["err"] is None and r["hdr"] == [] and not r["degraded"]


def _segments_without(module, data, predicate):
    out = bytearray(data[:2])
    for marker, start, end in module._segments(data):
        if not predicate(marker, data[start:end]):
            out += data[start - 4:end]
    return bytes(out) + data[max(end for _, _, end in module._segments(data)):]


def test_xmp_only_source_gets_a_fabricated_iso_payload(lossy, hdr_file, tmp_path):
    """Source sans métadonnées ISO ni MPF (XMP hdrgm seul) : l'ISO de la sortie est fabriqué, relu, et égal au XMP à 2e-6 près."""
    primary, gain = lossy._split_ultrahdr(hdr_file.read_bytes())
    is_iso = lambda m, body: m == 0xE2 and body[:len(lossy.ISO_NS)] == lossy.ISO_NS
    is_mpf = lambda m, body: m == 0xE2 and body[:4] == b"MPF\x00"
    new_gain = _segments_without(lossy, gain, is_iso)
    new_primary = _segments_without(lossy, primary, lambda m, b: is_iso(m, b) or is_mpf(m, b))
    new_primary = re.sub(rb'Item:Length="\d+"', b'Item:Length="%d"' % len(new_gain), new_primary)
    xmp_only = tmp_path / "xmp_only.jpg"
    xmp_only.write_bytes(new_primary + new_gain)
    p2, g2 = lossy._split_ultrahdr(xmp_only.read_bytes())
    assert g2 is not None
    xmp_meta = lossy.jpeg_hdr_source(p2, g2, 1)["meta"]
    out, r = convert(lossy, xmp_only, ("jpg",))
    assert r["err"] is None and r["hdr"] == ["jpg"]
    data = (out / "jpg" / "xmp_only.jpg").read_bytes()
    _, out_gain = lossy._split_ultrahdr(data)
    payloads = [out_gain[s + len(lossy.ISO_NS):e] for m, s, e in lossy._segments(out_gain)
                if m == 0xE2 and out_gain[s:s + len(lossy.ISO_NS)] == lossy.ISO_NS]
    iso_meta = lossy._parse_iso(b"\x00" + max(payloads, key=len))
    assert max(abs(iso_meta[k] - xmp_meta[k]) for k in xmp_meta) <= 2e-6


def test_metadata_drift_is_detected(lossy, hdr_file):
    raw = hdr_file.read_bytes()
    with Image.open(io.BytesIO(raw)) as im:
        im.load()
        c, _ = lossy._prepare_jpeg(raw, im, [])
    good = lossy.build_hdr_jpeg(c.hs, c.im, c.exif, c.icc)
    lossy._check_hdr_meta(good, c)                      # sans dérive : aucune exception
    c.hs["meta"]["gain_max"] += 0.01
    with pytest.raises(ValueError, match="différentes"):
        lossy._check_hdr_meta(good, c)


@pytest.mark.skipif(not os.environ.get("HJC_TEST_HEIC_HDR"), reason="HJC_TEST_HEIC_HDR : chemin d'un HEIC HDR d'iPhone (non fourni)")
def test_real_iphone_hdr(lossless):
    """Optionnel : un vrai HEIC HDR d'iPhone (image SDR + carte de gain Apple + item tmap), fourni par l'utilisateur."""
    src = Path(os.environ["HJC_TEST_HEIC_HDR"])
    out, r = convert(lossless, src, ALL if os.environ.get("HJC_TEST_ALL") else ("avif", "jxl", "heic"))
    assert r["err"] is None and r["kind"] == "HDR" and not r["degraded"]
