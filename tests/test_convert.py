"""Conversions SDR de bout en bout sur des images fabriquées (le programme relit et contrôle chaque sortie lui-même)."""
import numpy as np
import pillow_heif
import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from conftest import convert, make_rgb

ALL = ("jpg", "heic", "jxl", "avif")


def names(out):
    return sorted(p.name for p in out.iterdir())


def test_jpeg_to_default_formats(lossy, jpeg_file):
    out, r = convert(lossy, jpeg_file)
    assert r["err"] is None and r["source"] == "jpeg" and r["kind"] == "SDR" and not r["degraded"]
    assert names(out) == ["avif", "heic", "jxl"]
    for ext in ("heic", "jxl", "avif"):
        assert (out / ext / f"photo.{ext}").stat().st_size > 0


def test_heic_to_default_formats(lossy, heic_file):
    out, r = convert(lossy, heic_file)
    assert r["err"] is None and r["source"] == "heic" and r["kind"] == "SDR"
    assert names(out) == ["avif", "jpg", "jxl"]


def test_lossless_jxl_pixels_equal_decoded_source(lossless, heic_file):
    pillow_jxl = pytest.importorskip("pillow_jxl")
    out, r = convert(lossless, heic_file, ("jxl",))
    assert r["err"] is None
    a = np.array(Image.open(heic_file).convert("RGB"))
    b = np.array(Image.open(out / "jxl" / "photo.jxl").convert("RGB"))
    assert a.shape == b.shape and np.array_equal(a, b)


def test_heic_to_heic_pixels_close_to_decoded_source(lossless, heic_file):
    out, r = convert(lossless, heic_file, ("heic",))
    assert r["err"] is None and r["details"][0].startswith("heic")
    a = np.array(Image.open(heic_file).convert("RGB")).astype(int)
    b = np.array(Image.open(out / "heic" / "photo.heic").convert("RGB")).astype(int)
    assert a.shape == b.shape and np.abs(a - b).max() <= 2


@pytest.mark.parametrize("preset", ["Lossless", "Lossy"])
def test_jpeg_to_jpg_keeps_icc_and_orientation_one(preset, jpeg_file, lossy, lossless):
    module = lossless if preset == "Lossless" else lossy
    icc = Image.open(jpeg_file).info.get("icc_profile")
    out, r = convert(module, jpeg_file, ("jpg",))
    assert r["err"] is None
    got = Image.open(out / "jpg" / "photo.jpg")
    assert got.size == (320, 240) and got.info.get("icc_profile") == icc
    assert module._exif_orientation(got.info.get("exif")) == 1


def test_all_four_formats_at_once(lossy, jpeg_file):
    out, r = convert(lossy, jpeg_file, ALL)
    assert r["err"] is None and names(out) == ["avif", "heic", "jpg", "jxl"]


def test_output_never_replaces_the_source(lossy, tmp_path):
    (tmp_path / "jpg").mkdir()
    src = tmp_path / "jpg" / "same.jpg"
    make_rgb().save(src, "JPEG", quality=90)
    before = src.read_bytes()
    out, r = convert(lossy, src, ("jpg", "jxl"), out=tmp_path)
    assert r["err"] and "fichier source" in r["err"]
    assert src.read_bytes() == before and (tmp_path / "jxl" / "same.jxl").exists()


def test_file_type_comes_from_content_not_extension(lossy, tmp_path):
    src = tmp_path / "misnamed.heic"           # un JPEG qui porte une extension .heic
    make_rgb().save(src, "JPEG", quality=90)
    out, r = convert(lossy, src, ("jxl",))
    assert r["err"] is None and r["source"] == "jpeg"


def test_corrupt_file_is_reported_not_raised(lossy, tmp_path):
    src = tmp_path / "broken.jpg"
    src.write_bytes(b"\xff\xd8\xff\xe0not really a jpeg")
    out, r = convert(lossy, src, ("jxl",))
    assert r["err"]


def test_truncated_jpeg_is_refused(lossy, tmp_path):
    src = tmp_path / "cut.jpg"
    make_rgb().save(src, "JPEG", quality=90)
    src.write_bytes(src.read_bytes()[:-3000])
    out, r = convert(lossy, src, ("jxl",))
    assert r["err"] and not (out / "jxl").exists()


def test_exif_with_nan_rational_is_copied_without_false_alarm(lossy, tmp_path):
    """GPSImgDirection 0/0 (appareils Pixel) : NaN != NaN ne doit pas faire conclure à un EXIF altéré."""
    exif = Image.Exif()
    exif[0x010F] = "Test"
    gps = exif.get_ifd(0x8825)
    gps[17] = IFDRational(0, 0)
    gps[16] = "T"
    src = tmp_path / "gps_nan.jpg"
    make_rgb().save(src, "JPEG", quality=92, exif=exif.tobytes())
    value = Image.open(src).getexif().get_ifd(0x8825).get(17)
    assert value is not None and value != value                       # le rationnel 0/0 est bien lu comme NaN
    out, r = convert(lossy, src, ALL)
    assert r["err"] is None and names(out) == ["avif", "heic", "jpg", "jxl"]
    strip = lambda b: b[6:] if b[:6] == b"Exif\x00\x00" else b
    assert strip(Image.open(out / "jpg" / "gps_nan.jpg").info["exif"]) == strip(Image.open(src).info["exif"])


def test_real_exif_difference_is_still_detected(lossy):
    exif = Image.Exif(); exif[0x010F] = "Test"
    gps = exif.get_ifd(0x8825); gps[17] = IFDRational(0, 0); gps[16] = "T"
    other = Image.Exif(); other[0x010F] = "Test"
    gps2 = other.get_ifd(0x8825); gps2[17] = IFDRational(0, 0); gps2[16] = "M"
    with pytest.raises(ValueError, match="altéré"):
        lossy._check_exif(exif.tobytes(), other.tobytes())
