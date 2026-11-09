"""PNG en entrée et en sortie. Tous les PNG sont fabriqués ici (aucun fichier n'est fourni) ; les attendus sont calculés
par Pillow, numpy ou à la main, pas par le programme."""
import importlib.util
import io
import re
import struct
import zlib

import numpy as np
import pytest
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo

from conftest import PROGRAM, convert, load_program, make_rgb, make_ultrahdr

ALL = ("jpg", "heic", "jxl", "avif")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _has_png16():
    try:
        import imagecodecs
        return bool(imagecodecs.PNG.available)
    except Exception:
        return False


needs_png16 = pytest.mark.skipif(not _has_png16(), reason="imagecodecs avec son codec PNG indisponible")


# --- outils de fabrication et de lecture, indépendants du programme ----------------------------------------------------
def chunk(typ, payload):
    return struct.pack(">I", len(payload)) + typ + payload + struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)


def chunks_of(data):
    """[(type, données)] d'un PNG ; les CRC sont vérifiés."""
    assert data[:8] == PNG_SIGNATURE
    pos, out = 8, []
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        typ, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        assert zlib.crc32(typ + body) & 0xFFFFFFFF == struct.unpack(">I", data[pos + 8 + n:pos + 12 + n])[0]
        out.append((typ, body))
        pos += 12 + n
    return out


def with_chunks(png, *blocks):
    """PNG dont les blocs sont insérés juste après IHDR."""
    return png[:33] + b"".join(blocks) + png[33:]


def save_png(tmp_path, name, im, **kw):
    path = tmp_path / name
    im.save(path, "PNG", **kw)
    return path


def pixels(path):
    with Image.open(path) as im:
        im.load()
        return im.mode, np.array(im)


def names(out):
    return sorted(p.name for p in out.iterdir())


def rgba_image(width=160, height=120):
    im = make_rgb(width, height)
    ramp = np.broadcast_to(np.linspace(0, 255, width).astype("uint8")[None, :], (height, width)).copy()
    im.putalpha(Image.fromarray(ramp))
    return im


def u8(a16):
    """16 -> 8 bits, arrondi : calcul flottant indépendant de celui du programme (entier)."""
    return np.rint(a16.astype(np.float64) * 255 / 65535).astype(np.uint8)


# --- entrée PNG : formats de sortie ------------------------------------------------------------------------------------
def test_png_to_default_formats(lossy, tmp_path):
    src = save_png(tmp_path, "p.png", make_rgb())
    out, r = convert(lossy, src)
    assert r["err"] is None and r["source"] == "png" and r["kind"] == "SDR" and not r["degraded"] and not r["notes"]
    assert names(out) == ["avif", "heic", "jpg", "jxl"]               # jamais de png sans le demander


@pytest.mark.parametrize("preset", ["Lossless", "Lossy"])
def test_png_to_all_five_formats(preset, lossy, lossless, tmp_path):
    module = lossless if preset == "Lossless" else lossy
    src = save_png(tmp_path, "p.png", make_rgb())
    out, r = convert(module, src, ALL + ("png",))
    assert r["err"] is None and names(out) == ["avif", "heic", "jpg", "jxl", "png"]


def test_png_to_png_pixels_are_identical(lossy, lossless, tmp_path):
    src = save_png(tmp_path, "p.png", make_rgb())
    for module in (lossy, lossless):                                  # le préréglage ne change rien au PNG
        out, r = convert(module, src, ("png",))
        mode, got = pixels(out / "png" / "p.png")
        assert r["err"] is None and mode == "RGB" and np.array_equal(got, np.array(make_rgb()))
        assert r["details"][0].startswith("png") and "identiques" in r["details"][0]


def test_jpeg_and_heic_to_png_are_pixel_identical_to_the_decoded_source(lossy, jpeg_file, heic_file):
    for src in (jpeg_file, heic_file):
        out, r = convert(lossy, src, ("png",))
        mode, got = pixels(out / "png" / f"{src.stem}.png")
        assert r["err"] is None and mode == "RGB"
        with Image.open(src) as ref:
            assert np.array_equal(got, np.array(ref.convert("RGB")))


# --- entrée PNG : transparence ----------------------------------------------------------------------------------------
def test_alpha_is_kept_in_png_and_flattened_on_white_elsewhere(lossless, tmp_path):
    imagecodecs = pytest.importorskip("imagecodecs")
    src = save_png(tmp_path, "a.png", rgba_image())
    out, r = convert(lossless, src, ("png", "jpg", "jxl"))
    assert r["err"] is None
    ref = np.array(rgba_image())
    mode, got = pixels(out / "png" / "a.png")
    assert mode == "RGBA" and np.array_equal(got, ref)                # alpha gardé tel quel
    assert r["degraded"] and any("transparence aplatie" in n and "jpg, jxl" in n for n in r["notes"])
    alpha = ref[..., 3:4] / 255.0
    expected = np.rint(ref[..., :3] * alpha + 255 * (1 - alpha)).astype(int)         # fond blanc, calcul numpy
    with Image.open(out / "jpg" / "a.jpg") as im:
        assert np.abs(np.array(im.convert("RGB")).astype(int) - expected).max() <= 8     # JPEG q100 : quelques niveaux
    jxl = imagecodecs.jpegxl_decode((out / "jxl" / "a.jxl").read_bytes())[..., :3].astype(int)
    assert np.abs(jxl - expected).max() <= 1


def test_png_only_output_of_a_transparent_png_is_not_degraded(lossless, tmp_path):
    src = save_png(tmp_path, "a.png", rgba_image())
    out, r = convert(lossless, src, ("png",))
    assert r["err"] is None and not r["degraded"] and not r["notes"]


def test_flatten_colour_is_the_png_fond_setting(tmp_path):
    imagecodecs = pytest.importorskip("imagecodecs")
    black = load_program("Lossless", PNG_FOND=(0, 0, 0))
    src = save_png(tmp_path, "a.png", rgba_image())
    out, r = convert(black, src, ("jxl",))
    assert r["err"] is None and "(0, 0, 0)" in " ".join(r["notes"])
    ref = np.array(rgba_image())
    got = imagecodecs.jpegxl_decode((out / "jxl" / "a.jxl").read_bytes())[..., :3].astype(int)
    expected = np.rint(ref[..., :3] * (ref[..., 3:4] / 255.0)).astype(int)
    assert np.abs(got - expected).max() <= 1


def test_fully_opaque_alpha_is_ignored_silently(lossless, tmp_path):
    im = make_rgb()
    im.putalpha(Image.new("L", im.size, 255))
    src = save_png(tmp_path, "o.png", im)
    out, r = convert(lossless, src, ("png", "jxl"))
    assert r["err"] is None and not r["degraded"] and not r["notes"]
    assert pixels(out / "png" / "o.png")[0] == "RGB"


def _modes(tmp_path):
    base = make_rgb(96, 64)
    key = tuple(int(v) for v in np.array(base)[0, 0])
    gray = base.convert("L")
    la = gray.convert("LA")
    la.putalpha(Image.fromarray(np.broadcast_to(np.linspace(0, 255, 96).astype("uint8")[None, :], (64, 96)).copy()))
    return {
        "palette": save_png(tmp_path, "palette.png", base.quantize(32)),
        "palette_trns": save_png(tmp_path, "palette_trns.png", base.quantize(32), transparency=0),
        "palette_alpha": save_png(tmp_path, "palette_alpha.png", base.quantize(32),
                                  transparency=bytes(np.linspace(0, 255, 32).astype("uint8"))),      # un alpha par couleur
        "gray": save_png(tmp_path, "gray.png", gray),
        "gray_trns": save_png(tmp_path, "gray_trns.png", gray, transparency=int(gray.getpixel((0, 0)))),
        "gray_alpha": save_png(tmp_path, "gray_alpha.png", la),
        "one_bit": save_png(tmp_path, "one_bit.png", gray.convert("1")),
        "rgb_trns": save_png(tmp_path, "rgb_trns.png", base, transparency=key),
    }


@pytest.mark.filterwarnings("error::UserWarning")                     # aucun avertissement de Pillow sur ces types de PNG
@pytest.mark.parametrize("kind", ["palette", "palette_trns", "palette_alpha", "gray", "gray_trns", "gray_alpha", "one_bit", "rgb_trns"])
def test_every_png_colour_type(kind, lossless, tmp_path):
    src = _modes(tmp_path)[kind]
    with Image.open(src) as ref:
        ref.load()
        expected = np.array(ref.convert("RGBA"))                      # interprétation de Pillow (tRNS comprise)
    transparent = expected[..., 3].min() < 255
    out, r = convert(lossless, src, ("png", "jxl"))
    assert r["err"] is None
    mode, got = pixels(out / "png" / f"{kind}.png")
    assert mode == ("RGBA" if transparent else "RGB")
    assert np.array_equal(got, expected if transparent else expected[..., :3])
    assert r["degraded"] == transparent                               # signalé seulement si une vraie transparence est aplatie en jxl


# --- entrée PNG : 16 bits ---------------------------------------------------------------------------------------------
def _rng16(shape, seed=5):
    return np.random.default_rng(seed).integers(0, 65536, shape, dtype=np.uint16)


@needs_png16
@pytest.mark.parametrize("channels, mode_out", [(1, "RGB"), (2, "RGBA"), (3, "RGB"), (4, "RGBA")])
def test_16_bit_png_is_rounded_to_8_bits_and_flagged(channels, mode_out, lossless, tmp_path):
    import imagecodecs
    a = _rng16((48, 64, channels))
    if channels in (2, 4):
        a[..., -1] = np.linspace(0, 65535, 64).astype(np.uint16)[None, :]          # une vraie transparence
    src = tmp_path / "s16.png"
    src.write_bytes(imagecodecs.png_encode(np.ascontiguousarray(a[..., 0] if channels == 1 else a)))
    out, r = convert(lossless, src, ("png",))
    assert r["err"] is None and r["degraded"] and any("16 bits" in n for n in r["notes"])
    mode, got = pixels(out / "png" / "s16.png")
    assert mode == mode_out
    e = u8(a)
    if channels == 1:
        assert all(np.array_equal(got[..., k], e[..., 0]) for k in range(3))
    elif channels == 2:
        assert all(np.array_equal(got[..., k], e[..., 0]) for k in range(3)) and np.array_equal(got[..., 3], e[..., 1])
    else:
        assert np.array_equal(got, e)


def adam7_png16(arr):
    """PNG RVB 16 bits ENTRELACÉ (Adam7), fabriqué à la main : (y0, x0, pas y, pas x) de chacune des 7 passes."""
    h, w, _ = arr.shape
    raw = b""
    for y0, x0, dy, dx in ((0, 0, 8, 8), (0, 4, 8, 8), (4, 0, 8, 4), (0, 2, 4, 4), (2, 0, 4, 2), (0, 1, 2, 2), (1, 0, 2, 1)):
        sub = arr[y0::dy, x0::dx]
        if sub.shape[0] and sub.shape[1]:
            raw += b"".join(b"\x00" + row.astype(">u2").tobytes() for row in sub)
    return (PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 2, 0, 0, 1))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@needs_png16
@pytest.mark.parametrize("size", [(1, 1), (7, 5), (13, 1), (31, 17)])
def test_interlaced_16_bit_png(size, lossless, tmp_path):
    w, h = size
    a = _rng16((h, w, 3), seed=w * 100 + h)
    data = adam7_png16(a)
    with Image.open(io.BytesIO(data)) as check:                        # le fichier fabriqué est valide : Pillow le lit (en 8 bits)
        check.load()
        assert np.abs(np.array(check).astype(int) - (a >> 8).astype(int)).max() <= 1
    src = tmp_path / "i16.png"
    src.write_bytes(data)
    out, r = convert(lossless, src, ("png",))
    assert r["err"] is None
    assert np.array_equal(pixels(out / "png" / "i16.png")[1], u8(a))


@needs_png16
def test_16_bit_png_with_transparent_colour_is_refused(lossless, tmp_path):
    import imagecodecs
    src = tmp_path / "t16.png"
    src.write_bytes(with_chunks(imagecodecs.png_encode(np.ascontiguousarray(_rng16((8, 8, 3)))), chunk(b"tRNS", b"\x00" * 6)))
    out, r = convert(lossless, src, ("png",))
    assert r["err"] and "tRNS" in r["err"] and not (out / "png").exists()


@needs_png16
def test_16_bit_png_without_imagecodecs_png_codec_is_refused_not_truncated(tmp_path):
    import imagecodecs
    module = load_program("Lossless", HAS_PNG16=False)
    src = tmp_path / "n16.png"
    src.write_bytes(imagecodecs.png_encode(np.ascontiguousarray(_rng16((8, 8, 3)))))
    out, r = convert(module, src, ("png",))
    assert r["err"] and "16 bits" in r["err"]


# --- entrée PNG : EXIF, profil, animation, couleurs ---------------------------------------------------------------------
def test_exif_orientation_is_applied_and_reset_to_one(lossless, tmp_path):
    exif = Image.Exif()
    exif[274] = 6
    exif[271] = "TestMake"
    src = save_png(tmp_path, "o.png", make_rgb(100, 60), exif=exif.tobytes())
    with Image.open(src) as ref:
        ref.load()
        expected = np.array(ImageOps.exif_transpose(ref))
    assert expected.shape == (100, 60, 3)
    out, r = convert(lossless, src, ("png", "jpg"))
    assert r["err"] is None
    for ext in ("png", "jpg"):
        with Image.open(out / ext / f"o.{ext}") as got:
            got.load()
            ex = got.getexif()
            assert got.size == (60, 100) and ex.get(274) == 1 and ex.get(271) == "TestMake"
            if ext == "png":
                assert np.array_equal(np.array(got), expected)


def test_icc_profile_is_kept_in_png_and_jpg(lossless, tmp_path):
    ImageCms = pytest.importorskip("PIL.ImageCms")
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    src = save_png(tmp_path, "c.png", make_rgb(), icc_profile=icc)
    out, r = convert(lossless, src, ("png", "jpg", "heic"))
    assert r["err"] is None
    for ext in ("png", "jpg", "heic"):
        with Image.open(out / ext / f"c.{ext}") as got:
            assert got.info.get("icc_profile") == icc


def test_text_xmp_and_resolution_chunks_are_not_carried_over(lossless, tmp_path):
    info = PngInfo()
    info.add_text("Comment", "hello")
    info.add_itxt("XML:com.adobe.xmp", "<x:xmpmeta/>")
    src = save_png(tmp_path, "t.png", make_rgb(), pnginfo=info, dpi=(300, 300))
    assert {t for t, _ in chunks_of(src.read_bytes())} >= {b"tEXt", b"iTXt", b"pHYs"}
    out, r = convert(lossless, src, ("png",))
    assert r["err"] is None
    assert {t for t, _ in chunks_of((out / "png" / "t.png").read_bytes())} == {b"IHDR", b"IDAT", b"IEND"}


def test_exif_stored_as_text_is_not_read(lossless, tmp_path):
    exif = Image.Exif()
    exif[271] = "TextMake"
    hexa = exif.tobytes().hex()
    info = PngInfo()
    info.add_text("Raw profile type exif", f"\nexif\n{len(hexa) // 2:8d}\n{hexa}\n")
    src = save_png(tmp_path, "r.png", make_rgb(), pnginfo=info)
    with Image.open(src) as im:
        assert "exif" not in im.info and "Raw profile type exif" in im.info          # la prémisse : EXIF en texte seulement
    out, r = convert(lossless, src, ("png", "jpg"))
    assert r["err"] is None
    assert b"eXIf" not in {t for t, _ in chunks_of((out / "png" / "r.png").read_bytes())}
    with Image.open(out / "jpg" / "r.jpg") as got:
        assert not dict(got.getexif())


def test_apng_keeps_the_default_image_and_says_so(lossless, tmp_path):
    red = Image.new("RGB", (64, 48), (255, 0, 0))
    frames = [Image.new("RGB", (64, 48), c) for c in ((0, 255, 0), (0, 0, 255))]
    src = tmp_path / "anim.png"
    red.save(src, save_all=True, append_images=frames, default_image=True, duration=100)
    with Image.open(src) as check:
        assert check.is_animated and check.n_frames == 3
    out, r = convert(lossless, src, ("png",))
    assert r["err"] is None and r["degraded"] and any("APNG" in n for n in r["notes"])
    assert (pixels(out / "png" / "anim.png")[1] == (255, 0, 0)).all()


def _cicp(tmp_path, primaries, transfer):
    data = save_png(tmp_path, f"c_{primaries}_{transfer}.png", make_rgb(64, 48)).read_bytes()
    path = tmp_path / f"cicp_{primaries}_{transfer}.png"
    path.write_bytes(with_chunks(data, chunk(b"cICP", bytes((primaries, transfer, 0, 1)))))
    return path


@pytest.mark.parametrize("transfer, word", [(16, "PQ"), (18, "HLG")])
def test_hdr_png_input_is_refused(transfer, word, lossless, tmp_path):
    out, r = convert(lossless, _cicp(tmp_path, 9, transfer), ("png",))
    assert r["err"] and word in r["err"] and not (out / "png").exists()


def test_srgb_cicp_is_accepted_silently(lossless, tmp_path):
    out, r = convert(lossless, _cicp(tmp_path, 1, 13), ("png",))
    assert r["err"] is None and not r["degraded"] and not r["notes"]


def test_other_sdr_cicp_is_flagged_as_treated_as_srgb(lossless, tmp_path):
    out, r = convert(lossless, _cicp(tmp_path, 12, 13), ("png",))
    assert r["err"] is None and r["degraded"] and any("cICP" in n and "sRGB" in n for n in r["notes"])


def test_gamma_chunk_far_from_srgb_is_noted_but_not_degraded(lossless, tmp_path):
    data = save_png(tmp_path, "g.png", make_rgb(64, 48)).read_bytes()
    for gama, expect in ((100000, True), (45455, False)):
        src = tmp_path / f"gama_{gama}.png"
        src.write_bytes(with_chunks(data, chunk(b"gAMA", struct.pack(">I", gama))))
        out, r = convert(lossless, src, ("png",))
        assert r["err"] is None and not r["degraded"] and any("gAMA" in n for n in r["notes"]) == expect


# --- fichiers défectueux, type lu dans le contenu ----------------------------------------------------------------------
def test_truncated_png_is_refused(lossless, tmp_path):
    src = save_png(tmp_path, "cut.png", make_rgb())
    raw = src.read_bytes()
    src.write_bytes(raw[:len(raw) // 2])
    out, r = convert(lossless, src, ("png",))
    assert r["err"] and "tronqué" in r["err"] and not (out / "png").exists()


def test_not_an_image_named_png(lossless, tmp_path):
    src = tmp_path / "no.png"
    src.write_bytes(b"hello")
    out, r = convert(lossless, src, ("png",))
    assert r["err"] and "illisible" in r["err"]


def test_type_comes_from_content_for_png_too(lossless, tmp_path):
    jpeg_named_png = tmp_path / "a.png"
    make_rgb().save(jpeg_named_png, "JPEG", quality=90)
    png_named_jpg = tmp_path / "b.jpg"
    make_rgb().save(png_named_jpg, "PNG")
    assert convert(lossless, jpeg_named_png, ("jxl",))[1]["source"] == "jpeg"
    assert convert(lossless, png_named_jpg, ("jxl",))[1]["source"] == "png"


def test_png_output_never_replaces_the_source(lossless, tmp_path):
    (tmp_path / "png").mkdir()
    src = tmp_path / "png" / "same.png"
    make_rgb().save(src, "PNG")
    before = src.read_bytes()
    out, r = convert(lossless, src, ("png", "jxl"), out=tmp_path)
    assert r["err"] and "fichier source" in r["err"]
    assert src.read_bytes() == before and (tmp_path / "jxl" / "same.jxl").exists()


# --- sortie PNG d'une photo HDR ---------------------------------------------------------------------------------------
@pytest.fixture
def hdr_file(lossy, tmp_path):
    path = tmp_path / "uhdr.jpg"
    make_ultrahdr(lossy, path)
    return path


def test_hdr_photo_gives_an_sdr_png_by_default(lossy, hdr_file):
    out, r = convert(lossy, hdr_file, ("png",))
    assert r["err"] is None and r["kind"] == "HDR" and r["hdr"] == [] and not r["degraded"]
    assert any("PNG_HDR = False" in n for n in r["notes"])
    assert pixels(out / "png" / "uhdr.png")[0] == "RGB"


@needs_png16
def test_hdr_photo_gives_a_16_bit_pq_png_when_asked(hdr_file):
    pytest.importorskip("imagecodecs")
    import imagecodecs
    module = load_program("Lossy", PNG_HDR=True)
    if not module.HAS_HDR_ENC:
        pytest.skip("imagecodecs sans AVIF / JPEG XL : pas de HDR")
    out, r = convert(module, hdr_file, ("png",))
    assert r["err"] is None and r["hdr"] == ["png"] and not r["degraded"]
    data = (out / "png" / "uhdr.png").read_bytes()
    chunks = chunks_of(data)
    types = [t for t, _ in chunks]
    assert types[0] == b"IHDR" and types.index(b"cICP") < types.index(b"IDAT") and types[-1] == b"IEND"
    assert dict(chunks)[b"cICP"] == bytes((9, 16, 0, 1))                          # Rec.2020 / PQ / RVB / plage complète
    w, h, depth, ctype = struct.unpack(">IIBB", chunks[0][1][:10])
    assert (w, h, depth, ctype) == (320, 240, 16, 2)
    exif = Image.Exif()
    exif.load(dict(chunks)[b"eXIf"])
    assert exif.get(0x010F) == "Test"
    dec = imagecodecs.png_decode(data)
    assert dec.dtype == np.uint16 and dec.shape == (240, 320, 3) and dec.max() > 256
    assert "cICP" in r["details"][0]


# --- fonctions internes -----------------------------------------------------------------------------------------------
def test_png_chunk_and_insert_are_valid_png_structures(lossy, tmp_path):
    data = save_png(tmp_path, "x.png", make_rgb(32, 32)).read_bytes()
    assert lossy._png_chunk(b"cICP", bytes((9, 16, 0, 1))) == chunk(b"cICP", bytes((9, 16, 0, 1)))
    inserted = lossy._png_insert(data, [lossy._png_chunk(b"cICP", bytes((9, 16, 0, 1))), lossy._png_chunk(b"eXIf", b"MM\x00*")])
    types = [t for t, _ in chunks_of(inserted)]
    assert types[:3] == [b"IHDR", b"cICP", b"eXIf"] and types[-1] == b"IEND"
    with Image.open(io.BytesIO(inserted)) as im:
        im.load()
        assert im.size == (32, 32)
    assert lossy._png_chunks(inserted)[0][0] == b"IHDR"
    with pytest.raises(ValueError):
        lossy._png_chunks(b"not a png")
    with pytest.raises(ValueError):
        lossy._png_insert(b"not a png", [])


def test_u16_to_u8_rounds_to_nearest(lossy):
    pytest.importorskip("imagecodecs")
    v = np.arange(0, 65536, dtype=np.uint16).reshape(256, 256)
    assert np.array_equal(lossy._u16_to_u8(v), u8(v))


def test_same_format_warning_for_png_describes_a_lossless_recompression(lossy):
    text = lossy._same_format_warning("png", 3)
    assert "PNG -> PNG" in text and "sans perte" in text and "perte de génération" not in text
    for label in ("jpeg", "heic"):                                                # les textes des autres formats n'ont pas changé
        assert "perte de génération" in lossy._same_format_warning(label, 1) and "déjà compressée avec perte" in lossy._same_format_warning(label, 1)


def test_preset_summary_mentions_png(lossy):
    assert "png sans perte (compression 6)" in lossy._preset_summary("png", ("png",))
    assert "HDR" in load_program("Lossy", PNG_HDR=True)._preset_summary("png", ("png",))
    assert lossy._preset_summary("png").startswith("jpg")                          # formats par défaut d'un PNG


@pytest.mark.parametrize("line, value, ok", [
    ("PNG_FOND", "(0, 0, 0)", True), ("PNG_FOND", "[10, 20, 30]", True), ("PNG_FOND", "(300, 0, 0)", False),
    ("PNG_FOND", "(255, 255)", False), ("PNG_FOND", "(1.5, 0, 0)", False), ("PNG_FOND", "(True, 0, 0)", False),
    ("PNG_NIVEAU", "9", True), ("PNG_NIVEAU", "0", True), ("PNG_NIVEAU", "10", False), ("PNG_NIVEAU", "-1", False),
    ("PNG_NIVEAU", "6.0", False), ("PNG_NIVEAU", "True", False),
])
def test_png_settings_are_validated(line, value, ok, tmp_path):
    text = re.sub(rf"^{line} = .*$", f"{line} = {value}", PROGRAM.read_text(encoding="utf-8"), count=1, flags=re.M)
    path = tmp_path / "patched.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("patched_hjc", path)
    module = importlib.util.module_from_spec(spec)
    if ok:
        spec.loader.exec_module(module)
    else:
        with pytest.raises(SystemExit, match=line):
            spec.loader.exec_module(module)
