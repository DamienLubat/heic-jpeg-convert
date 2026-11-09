#!/usr/bin/env python3
# heic_jpeg_convert.py : HEIC / JPEG vers JPEG, HEIC, JPEG XL et AVIF, avec perte minimale, EXIF et HDR conservés.
# Copyright (C) 2026 DamienLubat
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
r"""HEIC ou JPEG -> fichiers convertis avec une perte minimale, EXIF conservé ; HDR conservé quand la source est HDR.

  HEIC / HEIF (.heic .heif)        -> JPEG + JPEG XL + AVIF
  JPEG (.jpg .jpeg .jpe .jfif)     -> HEIC + JPEG XL + AVIF
Le type est lu dans le contenu du fichier, pas dans son extension.

Usage : python heic_jpeg_convert.py ["<dossier_source>" ["<dossier_sortie>"]] [-f formats] [-y]
Sans argument : convertit les HEIC et les JPEG du dossier courant (sous-dossiers exclus).
Sortie par défaut : <dossier_source>/converti/{jpg,heic,jxl,avif}/  (un dossier par format, créé au besoin)
-f, --formats LISTE : choisit les formats de sortie, voir « Choix des formats » plus bas. -y : confirme d'avance. --aide : aide.
Prérequis : python -m pip install --upgrade pillow pillow-heif imagecodecs numpy
            (pillow-jxl-plugin : facultatif ; il ajoute une relecture de l'étiquette couleur des JXL SDR, voir README.md)
Homonymes (IMG_1.HEIC et IMG_1.jpg dans le même dossier) : leurs sorties reçoivent le suffixe _<extension d'origine>
(IMG_1_heic, IMG_1_jpg), sinon leurs fichiers jxl et avif s'écraseraient. Relancer remplace les fichiers de sortie.

Référence de la fidélité : les pixels de la source une fois décodés (HEIC : libheif ; JPEG : libjpeg-turbo via Pillow,
orientation EXIF appliquée). Une source HEIC ou JPEG est déjà compressée avec perte : rien ne peut le restaurer.
Pour une source HDR : les codes PQ calculés depuis l'image SDR + la carte de gain.

Trois préréglages (variable FIDELITE ci-dessous), à taper avec ou sans majuscules.

=== Choix des formats de sortie (option -f / --formats, ou réglage FORMATS_SORTIE en tête de programme) ===
Un ou plusieurs de heic, jpg, jxl, avif, séparés par une virgule (« heif » = heic, « jpeg » = jpg ; « avi » est lu comme « avif »,
avec un avis : AVI est un format vidéo). Sans choix (« auto ») : HEIC -> jpg, jxl, avif ; JPEG -> heic, jxl, avif, comme avant.
La liste vaut pour tous les fichiers du dossier. L'option remplace le réglage. Exemples :
  python heic_jpeg_convert.py "D:\Photos" -f jxl             JPEG XL seulement
  python heic_jpeg_convert.py "D:\Photos" -f heic,avif       HEIC (pour les JPEG) et AVIF
Format identique à la source (heic pour un HEIC, jpg pour un JPEG) : c'est une RECOMPRESSION des pixels décodés, pas une copie.
Avant de convertir, le programme affiche ce que cela implique et demande « Convertir vraiment N fichier(s) X en X ? [o/N] » (non par
défaut), une fois par type de source. Refus : seule cette sortie est abandonnée, les autres formats demandés sont produits.
-y / --yes / --oui répond « oui » d'avance. Sans clavier (entrée redirigée, tâche planifiée) et sans -y, ces sorties sont ignorées,
avec un avertissement, et le code retour est 1. Une sortie ne remplace jamais le fichier source (erreur si les deux coïncident).
Mesures des sorties de même format. Échantillons : 5 photos d'iPhone HDR (12 et 24 Mpx), 3 JPEG de 12 Mpx (q85 et q92 en 4:2:0,
q97 en 4:4:4), 2 JPEG Ultra HDR de 12 Mpx. Tailles en multiples de la source ; écarts max affichés par le programme, mesurés contre
les pixels de la source DÉCODÉE : la perte déjà présente dans la source n'y est pas comptée. Aucune mesure de ΔE pour ces sorties.
  préréglage  HEIC HDR -> HEIC               HEIC SDR -> HEIC (HEIC_HDR = False)  JPEG SDR -> JPG            JPEG Ultra HDR -> JPG
  Lossless    4,7 à 6,0 x ; 1 code PQ        3,3 à 4,4 x ; 1 niveau               1,2 à 2,1 x ; 4-5 niv.     1,02 à 1,03 x ; 3 niv.
  minLossy    1,4 à 1,7 x ; PSNR PQ 57-59    2,3 à 2,8 x ; 10-12 niv.             1,0 à 1,6 x ; 7-10 niv.    0,80 x ; 8 niv.
  Lossy       0,54 à 0,64 x ; PSNR PQ 49-51  0,56 à 0,67 x ; 19-29 niv.           0,60 à 1,13 x ; 5-18 niv.  0,45 x ; 16-20 niv.
  HEIC HDR -> HEIC : la structure Apple (image SDR + carte de gain, item tmap) disparaît ; le fichier est du HEVC 10 bits
         Rec.2020 / PQ (mêmes codes que l'AVIF HDR). JPEG Ultra HDR -> JPG : image SDR et carte de gain recompressées ; métadonnées
         ISO 21496-1 recopiées telles quelles (fabriquées depuis le XMP si la source n'en a pas), relues et comparées à la source ;
         orientation EXIF : pixels et carte de gain tournés, étiquette 1.

=== HEIC en entrée -> jpg, jxl, avif ===
Chiffres mesurés sur 5 photos d'iPhone HDR (12 et 24 Mpx), moyennes, tailles en multiples du HEIC ; ΔE2000 en SDR,
ΔE_ITP en HDR (environ 1 = seuil indicatif de différence à peine perceptible).
FIDELITE = "Lossless" (défaut) : fichiers de 2,5 à 13 fois le HEIC
  jxl  : sans perte. Contrôlé après encodage : pixels décodés identiques à la source.
  avif : 10 bits, 4:4:4, qualité 100 (sans perte dans le domaine YUV). Contrôlé : écart <= 1 niveau (SDR) / 2 codes (HDR).
         Le 4:4:4 relève du profil AV1 « High » (le 4:2:0 du profil « Main ») ; son affichage n'a pas été vérifié sur
         toutes les visionneuses : si l'une l'affiche mal, mettre AVIF_444 = False (repli 4:2:0, niveau 98,
         un peu plus de perte, fichiers environ 2 fois plus petits).
  jpg  : qualité 100, 4:4:4. Un JPEG ne peut pas être sans perte : quelques niveaux d'écart au plus.
FIDELITE = "minLossy" : perte minimale à taille raisonnable, fichiers de 1,8 à 2,9 fois le HEIC,
  ΔE moyen de 0 à 0,6 en SDR et de 0,3 à 0,9 en HDR
  jpg  : qualité 98, 4:4:4 (carte de gain du JPEG HDR : qualité 100).
  jxl  : SDR sans perte (un JXL avec perte proche de la source ne coûte guère moins cher) ; HDR 16 bits, distance 0,1.
  avif : SDR 10 bits 4:4:4 niveau 96 ; HDR 10 bits 4:2:0 niveau 98 (AVIF_444 = False : SDR en 4:2:0 niveau 98).
FIDELITE = "Lossy" : les réglages d'origine (JPG q92, AVIF q65 en SDR / niveau 80 en HDR, JXL distance 1),
  fichiers de 0,45 à 1,4 fois le HEIC, ΔE moyen de 0,4 à 1,2 en SDR et de 1,1 à 2,4 en HDR.

=== JPEG en entrée -> heic, jxl, avif ===
Un JPEG ne peut pas être recréé sans perte à partir de pixels. Seul le JXL garde le JPEG lui-même : transcodage réversible
(coefficients DCT recompressés), JPEG restitué octet pour octet (contrôlé), fichier plus petit que le JPEG. Les autres
formats reçoivent les pixels décodés : le « sans perte » y désigne la copie des pixels, pas le JPEG, et ces fichiers sont
plus gros que lui (un codeur sans perte code aussi le bruit de quantification du JPEG).
Chiffres mesurés sur 3 JPEG de 12 Mpx fabriqués à partir d'une photo d'iPhone (q85 4:2:0, q92 4:2:0, q97 4:4:4, profil
Display P3), tailles en multiples du JPEG, ΔE2000 moyen contre le JPEG décodé par libjpeg-turbo :
  préréglage  heic                              jxl SDR                           avif SDR
  Lossless    HEVC sans perte 4:4:4             transcodage sans perte            10 bits 4:4:4 niveau 100
              1,5 à 3,3 x ; ΔE 0,002            0,78 à 0,82 x ; ΔE 0,4 à 0,6      2,5 à 5,2 x ; pixels identiques
              écart max 1 niveau                (écart de décodeur, voir ci-dessous) (décodage 10 bits)
  minLossy    q90 4:2:0                         comme Lossless                    10 bits 4:4:4 niveau 96
              1,1 à 2,1 x ; ΔE 0,08 à 0,10                                        1,0 à 1,6 x ; ΔE 0,22 à 0,24
              écart max 10 à 11 niveaux                                           écart max 5 à 7 niveaux
  Lossy       q50 4:2:0                         transcodage, ou distance 1 si     Pillow q65 4:2:0
              0,30 à 0,69 x ; ΔE 0,71 à 0,78    ce JXL est >= 20 % plus petit     0,26 à 0,60 x ; ΔE 1,1 à 1,2
              écart max 17 à 21 niveaux         0,40 à 0,82 x ; ΔE 0,56 à 0,63    écart max 24 niveaux
  Les sorties HDR (JPEG Ultra HDR) : voir la règle HDR. Écart « de décodeur » du JXL transcodé : libjxl et libjpeg-turbo
  décodent le même JPEG avec quelques niveaux d'écart (PSNR environ 51 dB) ; ce n'est pas une perte, le JPEG est restitué.
  heic : le 4:4:4 relève des profils HEVC « Range Extensions » (le 4:2:0 des profils « Main ») ; son affichage n'a pas été
         vérifié sur toutes les visionneuses : si l'une l'affiche mal, mettre HEIC_444 = False (HEIC Lossless en 4:2:0 q95).
         Image unique tant que le flux HEVC tient sous 15 Mo ; au-delà, grille de tuiles de 1024 px (structure des HEIC
         d'iPhone), car le décodeur libde265 de pillow-heif refuse une image unique de plus de 16 Mio (mesuré).

Règle HDR : source HDR -> sorties HDR ; source SDR -> sorties SDR.
  HEIC HDR (iPhone, iOS 18+ : image SDR + carte de gain, item `tmap`) : sorties jpg, avif, jxl HDR.
  JPEG « Ultra HDR » (image SDR + carte de gain monocanal ; métadonnées ISO 21496-1, sinon XMP hdrgm) : sorties heic, avif,
  jxl HDR. Testé sur des JPEG Ultra HDR issus de HEIC d'iPhone et sur un fichier Pixel (un seul) ; autres appareils Android non testés.
  Un JPEG ordinaire n'a pas de carte de gain : sorties SDR.
  jpg  HDR : JPEG « Ultra HDR » (SDR + carte de gain ISO 21496-1 recopiée du HEIC). Affiché en HDR par
             Photos / Quick Look sur iPhone, JPEG normal ailleurs.
  avif HDR : AVIF 10 bits, Rec.2020 / PQ (HDR10), reconstruit depuis SDR + carte de gain (blanc SDR = 203 nits).
  jxl  HDR : JPEG XL 16 bits, Rec.2100 / PQ, même reconstruction.
  heic HDR : HEVC 10 bits, Rec.2020 / PQ (étiquettes nclx 9 / 16 / 9, plage complète), même reconstruction. Relu après
             encodage. Affichage en HDR constaté sur un iPhone (un seul appareil) ; non vérifié
             sur macOS ni Windows (HEIC_HDR = False donne un HEIC SDR). Le HEIC Lossless HDR garde les codes PQ à 1 près ;
             minLossy q90 4:2:0, Lossy q60 4:2:0.
  Mesuré sur 2 JPEG Ultra HDR issus de HEIC d'iPhone (convertis par ce programme, même préréglage) : ΔE_ITP moyen contre le HEIC d'origine = Lossless
  0,15 à 0,76 ; minLossy 0,50 à 1,26 ; Lossy 1,30 à 3,09 (la perte du JPEG source est comprise). Tailles en multiples du JPEG
  HDR : Lossless heic / avif 1,5 à 1,6 x, jxl 3,8 à 3,9 x ; minLossy 0,65 à 1,04 x ; Lossy 0,34 à 0,60 x.
Un fichier HDR dont la version HDR est impossible (bibliothèque absente, carte de gain d'un format non géré, erreur) est
écrit en SDR, avec un message explicite et un code retour non nul.

Couleurs SDR : le profil Display P3 / sRGB de la source devient une étiquette CICP dans l'AVIF et le JXL (relue après
encodage) ; il est recopié tel quel dans le JPEG et le HEIC, et conservé tel quel dans un JXL transcodé. Autre profil ICC :
le JPEG, le HEIC et l'AVIF (Pillow) le gardent, le JXL en pixels est converti en sRGB (aucune bibliothèque ne sait écrire un
ICC dans un JXL ici) : signalé, code retour non nul. JPEG sans profil : traité comme sRGB. JPEG en niveaux de gris : écrit
en RGB (profil gris converti en sRGB).
Orientation EXIF d'un JPEG : les pixels sont tournés et l'étiquette vaut 1, sauf dans le JXL transcodé, qui garde le
JPEG et son étiquette d'origine.

Chaque sortie est relue par un décodeur et contrôlée avant d'être écrite (pixels, étiquettes couleur, EXIF complet,
orientation ; pour le JPEG HDR : structure MPF / XMP / ISO ; pour le JXL transcodé : JPEG restitué octet pour octet).
Un format indisponible (par exemple le HEIC sans encodeur HEVC dans pillow-heif) est ignoré avec un avertissement et la
commande à lancer. Code retour non nul si une conversion échoue, si un format manque ou si un repli ou une perte est signalé.

Réglages en tête de programme : FIDELITE ; AVIF_444 (False : AVIF toujours en 4:2:0) ; HEIC_444 (False : HEIC Lossless en
4:2:0 q95) ; HEIC_HDR (False : photo HDR -> HEIC SDR) ; FORMATS_SORTIE ("auto", ou une liste de formats) ;
JXL_LOSSY_MIN_SAVING (préréglage Lossy : JXL avec perte gardé s'il est au moins 20 % plus petit que le transcodage) ;
HDR (False : tout en SDR).

Non conservés : HEIC en entrée : cartes auxiliaires Apple (style, ciel, peau, portrait, profondeur), miniatures, bloc
« Styles photographiques », XMP ; un HEIC 10 bits (hors iPhone) est lu en 8 bits par pillow-heif : signalé.
JPEG en entrée : XMP, IPTC et commentaires (sauf dans le JXL transcodé, qui restitue le JPEG entier), images secondaires
d'un fichier MPO (signalé) ; un JPEG CMYK / YCCK est refusé (une conversion en RGB donnerait de fausses couleurs).
"""
import math
import os
import re
import struct
import sys
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
from pathlib import Path

import pillow_heif
from PIL import Image, ImageChops

pillow_heif.register_heif_opener()
try:
    import pillow_jxl  # noqa: F401  (enregistre le format JXL dans Pillow ; repli et relecture de l'étiquette couleur)
except ImportError:
    pass
Image.init()
try:
    from PIL import ImageCms
except ImportError:
    ImageCms = None
try:  # AVIF / JXL 10 bits, 16 bits, sans perte, étiquettes CICP : Pillow ne sait pas le faire
    import imagecodecs
    import numpy as np
    HAS_HDR_ENC = bool(imagecodecs.AVIF.available and imagecodecs.JPEGXL.available)
except ImportError:
    HAS_HDR_ENC = False
HDR_ENC_HINT = "python -m pip install --upgrade imagecodecs numpy"

# ----------------------------------------------------------------------------------------------
# Réglages
# ----------------------------------------------------------------------------------------------
FIDELITE = "Lossless"                 # "Lossless", "minLossy" ou "Lossy" (voir PRESETS)
AVIF_444 = True                       # False : AVIF toujours en 4:2:0 (profil AV1 le plus répandu), dans les trois préréglages
HEIC_444 = True                       # False : le HEIC « Lossless » (JPEG en entrée) passe en 4:2:0 qualité 95 (profil HEVC le plus répandu)
HEIC_HDR = True                       # False : un JPEG Ultra HDR donne un HEIC SDR (HEIC 10 bits PQ : affichage constaté sur un iPhone, non vérifié sur macOS / Windows)
FORMATS_SORTIE = "auto"               # formats de sortie : "auto" (HEIC -> jpg, jxl, avif ; JPEG -> heic, jxl, avif) ou une liste, ex. "heic, jxl" ; l'option -f la remplace
JXL_LOSSY_MIN_SAVING = 0.20           # préréglage « Lossy », JPEG -> JXL : JXL avec perte gardé seulement s'il est au moins 20 % plus petit que le transcodage
HDR = True                            # False : tout convertir en SDR
HDR_SDR_WHITE_NITS = 203.0            # blanc SDR de référence BT.2408 (valeur utilisée par Apple/Google)
MIN_PSNR_PQ = 38.0                    # contrôle des pixels HDR avec perte (dB, domaine PQ)
# jxl_*_distance : None = sans perte, sinon distance libjxl (0 = sans perte, 1 ~ qualité 90).
# avif_sdr / avif_hdr : chroma "444" ou "420" voulu, niveau imagecodecs de ce chroma (100 = sans perte en 4:4:4),
#   level_420 = niveau utilisé quand AVIF_444 = False. avif_sdr : engine "pillow" = Pillow, "imagecodecs" = 10 bits.
PRESETS = {
    "Lossless": dict(                                               # sans perte, sauf JPG (impossible) ; fichiers les plus gros
        jpg=dict(quality=100, subsampling=0, optimize=True),        # JPEG SDR et image SDR du JPEG HDR
        jpg_gain=dict(quality=100, optimize=True),                  # carte de gain du JPEG HDR (niveaux de gris)
        min_psnr=30.0,                                              # filet de sécurité des sorties 8 bits avec perte (mesuré sur photos : 49 à 57 dB)
        jxl_sdr_distance=None, jxl_hdr_distance=None, jxl_sdr_effort=4, jxl_hdr_effort=5,      # efforts choisis par mesure (taille / temps)
        avif_sdr=dict(engine="imagecodecs", chroma="444", level=100, level_420=98),
        avif_hdr=dict(chroma="444", level=100, level_420=98),
        pillow_avif=dict(quality=100, subsampling="4:4:4"),         # AVIF SDR via Pillow (profil ICC inconnu)
        heic_sdr=dict(quality=-1, chroma=444), heic_sdr_420=dict(quality=95, chroma=420),      # JPEG -> HEIC : -1 = HEVC sans perte
        heic_hdr=dict(quality=-1, chroma=444), heic_hdr_420=dict(quality=95, chroma=420),      # (_420 : repli HEIC_444 = False)
        jxl_jpeg="transcode",                                       # JPEG -> JXL : transcodage réversible (sinon "pixels")
    ),
    "minLossy": dict(                                               # perte minimale à taille raisonnable (points mesurés, voir l'en-tête)
        jpg=dict(quality=98, subsampling=0, optimize=True),
        jpg_gain=dict(quality=100, optimize=True),
        min_psnr=30.0,
        jxl_sdr_distance=None, jxl_hdr_distance=0.1, jxl_sdr_effort=4, jxl_hdr_effort=5,       # SDR : un JXL avec perte proche de la source ne coûte guère moins que le sans-perte
        avif_sdr=dict(engine="imagecodecs", chroma="444", level=96, level_420=98),
        avif_hdr=dict(chroma="420", level=98, level_420=98),
        pillow_avif=dict(quality=95, subsampling="4:4:4"),
        heic_sdr=dict(quality=90, chroma=420), heic_sdr_420=dict(quality=90, chroma=420),
        heic_hdr=dict(quality=90, chroma=420), heic_hdr_420=dict(quality=90, chroma=420),
        jxl_jpeg="transcode",
    ),
    "Lossy": dict(                                                  # fichiers les plus petits (réglages d'origine)
        jpg=dict(quality=92, optimize=True),
        jpg_gain=dict(quality=95, optimize=True),
        min_psnr=30.0,                                              # (mesuré sur photos : 39 à 47 dB)
        jxl_sdr_distance=1.0, jxl_hdr_distance=1.0, jxl_sdr_effort=7, jxl_hdr_effort=7,
        avif_sdr=dict(engine="pillow", chroma="420", level=65, level_420=65),
        avif_hdr=dict(chroma="420", level=80, level_420=80),
        pillow_avif=dict(quality=65),
        heic_sdr=dict(quality=50, chroma=420), heic_sdr_420=dict(quality=50, chroma=420),
        heic_hdr=dict(quality=60, chroma=420), heic_hdr_420=dict(quality=60, chroma=420),
        jxl_jpeg="auto",                                            # JXL avec perte (distance 1) seulement s'il est nettement plus petit que le transcodage
    ),
}
_PRESET_NAMES = {k.lower(): k for k in PRESETS}                     # casse libre : "lossless", "MINLOSSY"...
if str(FIDELITE).lower() not in _PRESET_NAMES:
    sys.exit('FIDELITE doit valoir "Lossless", "minLossy" ou "Lossy" (valeur actuelle : %r)' % (FIDELITE,))
FIDELITE = _PRESET_NAMES[str(FIDELITE).lower()]
P = PRESETS[FIDELITE]

def _heic_writable():
    """pillow-heif sait-il ENCODER du HEVC ici ? (la roue Windows embarque x265 ; sans encodeur, l'écriture échoue)"""
    try:
        buf = BytesIO()
        Image.new("RGB", (16, 16)).save(buf, "HEIF", quality=50)
        return buf.tell() > 0
    except Exception:
        return False


# extension : (format Pillow, commande si indisponible) ; l'AVIF et le JXL passent de préférence par imagecodecs
ALL_FORMATS = {
    "jpg": ("JPEG", "python -m pip install --upgrade pillow"),
    "heic": ("HEIF", "python -m pip install --upgrade pillow-heif   (encodeur HEVC x265 requis)"),
    "jxl": ("JXL", "python -m pip install --upgrade imagecodecs numpy   (pillow-jxl-plugin, facultatif, sert de repli)"),
    "avif": ("AVIF", "python -m pip install --upgrade pillow imagecodecs numpy   (Pillow >= 11.3 sans imagecodecs)"),
}
HEIC_OUT = ("jpg", "jxl", "avif")        # sans choix (FORMATS_SORTIE = "auto"), un HEIC / HEIF donne ces trois fichiers
JPEG_OUT = ("heic", "jxl", "avif")       # un JPEG donne ceux-là
CANON = ("jpg", "heic", "jxl", "avif")   # ordre de traitement et d'affichage des formats choisis
SAME_FORMAT = {"heic": "heic", "jpeg": "jpg"}    # type de source -> sortie de même format (recompression : sur confirmation)
_NAMES = {"jpg": "jpg", "jpeg": "jpg", "jpe": "jpg", "jfif": "jpg", "heic": "heic", "heif": "heic",
          "jxl": "jxl", "jpegxl": "jxl", "avif": "avif", "avi": "avif"}


def parse_formats(text):
    """Liste de formats de sortie saisie par l'utilisateur -> (formats rangés dans l'ordre CANON ou None pour « auto », avis).
    Séparateurs : virgule, espace, point-virgule, « + ». Noms acceptés : heic (heif), jpg (jpeg), jxl, avif.
    « avi » est lu comme « avif » (AVI est un format vidéo : avis affiché). ValueError (message français) si un nom est inconnu."""
    tokens = [t.lstrip(".") for t in re.split(r"[,;+\s]+", (text or "").strip().lower()) if t.strip(".")]
    if not tokens or tokens == ["auto"]:
        return None, []
    if "auto" in tokens:
        raise ValueError("« auto » ne se combine pas avec d'autres formats")
    bad = [t for t in tokens if t not in _NAMES]
    if bad:
        raise ValueError("format inconnu : " + ", ".join(f"« {t} »" for t in bad) + " (possibles : heic, jpg, jxl, avif, ou auto)")
    notices = ["« avi » lu comme « avif » (AVI est un format vidéo)"] if "avi" in tokens else []
    chosen = {_NAMES[t] for t in tokens}
    return tuple(e for e in CANON if e in chosen), notices


def plan_outputs(label, selected):
    """Formats à produire pour un type de source ('heic' | 'jpeg') : le choix de l'utilisateur, ou les trois formats par défaut."""
    if selected is None:
        return tuple(HEIC_OUT if label == "heic" else JPEG_OUT)
    return tuple(e for e in CANON if e in selected)


FORMATS = {e: f for e, (f, _) in ALL_FORMATS.items()
           if (f in Image.SAVE and (e != "heic" or _heic_writable())) or (HAS_HDR_ENC and e in ("jxl", "avif"))}
MISSING = {e: h for e, (f, h) in ALL_FORMATS.items() if e not in FORMATS}


# ----------------------------------------------------------------------------------------------
# JPEG HDR : image SDR + carte de gain Apple + métadonnées ISO 21496-1 (item `tmap` du HEIC).
# Structure : format « Ultra HDR » (XMP hdrgm + MPF + segment ISO 21496-1), voir
# developer.android.com/media/platform/hdr-image-format
# ----------------------------------------------------------------------------------------------
GAIN_AUX = "urn:com:apple:photo:2020:aux:hdrgainmap"
ISO_NS = b"urn:iso:std:iso:ts:21496:-1\x00"
XMP_NS = b"http://ns.adobe.com/xap/1.0/\x00"
HDRGM_NAMESPACE = "http://ns.adobe.com/hdr-gain-map/1.0/"
CONTAINER_NAMESPACE = "http://ns.google.com/photos/1.0/container/"
ITEM_NAMESPACE = "http://ns.google.com/photos/1.0/container/item/"


class HdrSkip(Exception):
    """Version HDR impossible pour ce fichier (raison lisible) : ce n'est pas une erreur du fichier."""


class NotHdr(HdrSkip):
    """La source est SDR (aucune carte de gain) : convertie en SDR, rien à signaler."""


def _be(d, o, n):
    return int.from_bytes(d[o:o + n], "big")


def _boxes(d, start, end):
    """Itère les boîtes ISOBMFF : (type, début du contenu, fin)."""
    o = start
    while o + 8 <= end:
        size, typ = _be(d, o, 4), d[o + 4:o + 8].decode("latin1")
        hdr = 8
        if size == 1:
            size, hdr = _be(d, o + 8, 8), 16
        elif size == 0:
            size = end - o
        if size < hdr:
            return
        yield typ, o + hdr, o + size
        o += size


def _heif_index(d):
    """Index d'un fichier HEIF/AVIF : (items {id: type}, refs [(type, de, [vers])], iloc {id: (méthode, [(offset, taille)])},
    id de l'image principale, début de la boîte idat)."""
    meta = next((b for b in _boxes(d, 0, len(d)) if b[0] == "meta"), None)
    if meta is None:
        raise HdrSkip("pas de boîte meta")
    items, refs, iloc, pitm, idat = {}, [], {}, None, None
    for typ, s, e in _boxes(d, meta[1] + 4, meta[2]):   # meta est une FullBox (+4)
        if typ == "pitm":
            pitm = _be(d, s + 4, 2 if d[s] == 0 else 4)
        elif typ == "idat":
            idat = s
        elif typ == "iinf":
            v = d[s]
            for t2, s2, e2 in _boxes(d, s + 4 + (2 if v == 0 else 4), e):
                if t2 != "infe":
                    continue
                v2, o2 = d[s2], s2 + 4
                idsz = 2 if v2 < 3 else 4
                iid = _be(d, o2, idsz)
                o2 += idsz + 2
                items[iid] = d[o2:o2 + 4].decode("latin1") if v2 >= 2 else "?"
        elif typ == "iref":
            sz = 2 if d[s] == 0 else 4
            for t2, s2, e2 in _boxes(d, s + 4, e):
                n = _be(d, s2 + sz, 2)
                refs.append((t2, _be(d, s2, sz), [_be(d, s2 + sz + 2 + i * sz, sz) for i in range(n)]))
        elif typ == "iloc":
            v, o = d[s], s + 4
            osz, lsz, bsz, isz = d[o] >> 4, d[o] & 15, d[o + 1] >> 4, d[o + 1] & 15
            o += 2
            cnt = _be(d, o, 2 if v < 2 else 4)
            o += 2 if v < 2 else 4
            for _ in range(cnt):
                iid = _be(d, o, 2 if v < 2 else 4)
                o += 2 if v < 2 else 4
                cm = 0
                if v in (1, 2):
                    cm = _be(d, o, 2) & 15
                    o += 2
                o += 2  # data_reference_index
                base = _be(d, o, bsz)
                o += bsz
                ec = _be(d, o, 2)
                o += 2
                ext = []
                for _ in range(ec):
                    if v in (1, 2) and isz:
                        o += isz
                    off = _be(d, o, osz)
                    o += osz
                    ln = _be(d, o, lsz)
                    o += lsz
                    ext.append((base + off, ln))
                iloc[iid] = (cm, ext)
    return items, refs, iloc, pitm, idat


def _read_tmap(path):
    """Renvoie (payload du tmap, ids des images d'entrée du tmap, id de l'image principale)."""
    d = Path(path).read_bytes()
    items, refs, iloc, pitm, idat = _heif_index(d)
    tm = [i for i, t in items.items() if t == "tmap"]
    if not tm:
        raise NotHdr("pas de tmap")
    if len(tm) > 1 or tm[0] not in iloc:
        raise HdrSkip("tmap multiple ou sans données")
    cm, ext = iloc[tm[0]]
    if len(ext) != 1 or cm not in (0, 1) or (cm == 1 and idat is None):
        raise HdrSkip("emplacement du tmap non pris en charge")
    off, ln = ext[0]
    payload = d[(idat if cm == 1 else 0) + off:(idat if cm == 1 else 0) + off + ln]
    inputs = [to for t, f, to in refs if t == "dimg" and f == tm[0]]
    if len(inputs) != 1 or len(payload) != ln:
        raise HdrSkip("entrées du tmap non reconnues")
    return payload, inputs[0], pitm


def _f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def _frac(n, d):
    """Fraction ISO convertie comme le fait libultrahdr / ultrahdr-rs (flottant 32 bits)."""
    return _f32(_f32(float(n)) / _f32(float(d)))


def _parse_iso(payload):
    """Décode le payload ISO 21496-1 d'un `tmap` (avec octet de version). Gain map monocanal seulement."""
    if len(payload) < 62:
        raise HdrSkip("métadonnées ISO trop courtes")
    version, min_v, flags = payload[0], _be(payload, 1, 2), payload[5]
    if version != 0 or min_v != 0:
        raise HdrSkip(f"version ISO 21496-1 non prise en charge ({version}/{min_v})")
    if flags & 0x80:
        raise HdrSkip("gain map multicanal non prise en charge")
    if flags & 0x08:
        raise HdrSkip("encodage à dénominateur commun non pris en charge")
    if flags & 0x04:
        raise HdrSkip("direction inverse (base HDR) non prise en charge")
    vals, pos = [], 6
    for signed in (False, False, True, True, False, True, True):   # headroom base/alt, min, max, gamma, offsets
        n = _be(payload, pos, 4)
        if signed and n >= 2 ** 31:
            n -= 2 ** 32
        d = _be(payload, pos + 4, 4)
        if d == 0:
            raise HdrSkip("dénominateur nul dans les métadonnées ISO")
        vals.append(_frac(n, d))
        pos += 8
    keys = ("base_headroom", "alt_headroom", "gain_min", "gain_max", "gamma", "base_offset", "alt_offset")
    return dict(zip(keys, vals))


def _container_directory(gain_len):
    return ("      <Container:Directory>\n        <rdf:Seq>\n"
            "          <rdf:li rdf:parseType=\"Resource\">\n"
            "            <Container:Item\n"
            "                Item:Semantic=\"Primary\"\n"
            "                Item:Mime=\"image/jpeg\"/>\n"
            "          </rdf:li>\n"
            "          <rdf:li rdf:parseType=\"Resource\">\n"
            "            <Container:Item\n"
            "                Item:Semantic=\"GainMap\"\n"
            "                Item:Mime=\"image/jpeg\"\n"
            f"                Item:Length=\"{gain_len}\"/>\n"
            "          </rdf:li>\n"
            "        </rdf:Seq>\n      </Container:Directory>")


def _xmp_primary(gain_len):
    return (f'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
            f'<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core">\n'
            f'  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
            f'    <rdf:Description rdf:about=""\n'
            f'        xmlns:hdrgm="{HDRGM_NAMESPACE}"\n'
            f'        xmlns:Container="{CONTAINER_NAMESPACE}"\n'
            f'        xmlns:Item="{ITEM_NAMESPACE}"\n'
            f'        hdrgm:Version="1.0">\n'
            f'{_container_directory(gain_len)}\n'
            f'    </rdf:Description>\n'
            f'  </rdf:RDF>\n'
            f'</x:xmpmeta>\n'
            f'<?xpacket end="w"?>')


def _xmp_gainmap(m):
    return (f'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
            f'<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core">\n'
            f'  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
            f'    <rdf:Description rdf:about=""\n'
            f'        xmlns:hdrgm="{HDRGM_NAMESPACE}"\n'
            f'        hdrgm:Version="1.0"\n'
            f'        hdrgm:GainMapMin="{m["gain_min"]:.6f}"\n'
            f'        hdrgm:GainMapMax="{m["gain_max"]:.6f}"\n'
            f'        hdrgm:Gamma="{m["gamma"]:.6f}"\n'
            f'        hdrgm:OffsetSDR="{m["base_offset"]:.6f}"\n'
            f'        hdrgm:OffsetHDR="{m["alt_offset"]:.6f}"\n'
            f'        hdrgm:HDRCapacityMin="{m["base_headroom"]:.6f}"\n'
            f'        hdrgm:HDRCapacityMax="{m["alt_headroom"]:.6f}"\n'
            f'        hdrgm:BaseRenditionIsHDR="False"/>\n'
            f'  </rdf:RDF>\n'
            f'</x:xmpmeta>\n'
            f'<?xpacket end="w"?>')


def _segment(marker, body):
    return b"\xff" + bytes([marker]) + struct.pack(">H", len(body) + 2) + body


def _insert_after_soi(jpeg, segment):
    if jpeg[:2] != b"\xff\xd8":
        raise ValueError("JPEG invalide (SOI absent)")
    return jpeg[:2] + segment + jpeg[2:]


def _strip_app0(jpeg):
    """Retire le segment JFIF (APP0) qu'ajoute Pillow : il doit être le premier segment ou absent."""
    if jpeg[2:4] == b"\xff\xe0":
        return jpeg[:2] + jpeg[4 + _be(jpeg, 4, 2):]
    return jpeg


def _icc_segments(icc):
    chunk = 65533 - 12 - 2
    parts = [icc[i:i + chunk] for i in range(0, len(icc), chunk)]
    return [_segment(0xE2, b"ICC_PROFILE\x00" + bytes([i + 1, len(parts)]) + p) for i, p in enumerate(parts)]


def _mpf_segment(primary_len, gain_len, insert_pos=2):
    """Index MPF (CIPA DC-007) : image principale + une image secondaire (la carte de gain)."""
    tiff_pos = insert_pos + 4 + 4            # marqueur + longueur, puis « MPF\0 »
    m = bytearray(b"MM\x00\x2a" + struct.pack(">I", 8) + struct.pack(">H", 3))
    m += struct.pack(">HHII", 0xB000, 7, 4, int.from_bytes(b"0100", "big"))
    m += struct.pack(">HHII", 0xB001, 4, 1, 2)
    m += struct.pack(">HHII", 0xB002, 7, 32, len(m) + 12 + 4)
    m += struct.pack(">I", 0)
    m += struct.pack(">IIIHH", 0x00030000, primary_len, 0, 0, 0)
    m += struct.pack(">IIIHH", 0x00000000, gain_len, max(primary_len - tiff_pos, 0), 0, 0)
    return _segment(0xE2, b"MPF\x00" + bytes(m))


def _assemble_hdr_jpeg(base_jpeg, gain_jpeg, iso_payload, meta, icc):
    """Même recette que ultrahdr-rs::encode_ultrahdr_with_format, avec le profil ICC d'origine."""
    gm = _insert_after_soi(gain_jpeg, _segment(0xE2, ISO_NS + iso_payload[1:]))        # payload sans octet de version
    gm = _insert_after_soi(gm, _segment(0xE1, XMP_NS + _xmp_gainmap(meta).encode()))
    p = _insert_after_soi(base_jpeg, _segment(0xE1, XMP_NS + _xmp_primary(len(gm)).encode()))
    p = _insert_after_soi(p, _segment(0xE2, ISO_NS + b"\x00\x00\x00\x00"))             # version seule
    for seg in reversed(_icc_segments(icc) if icc else []):
        p = _insert_after_soi(p, seg)
    est = len(_mpf_segment(0, 0))
    mpf = _mpf_segment(len(p) + est, len(gm))
    return _insert_after_soi(p, mpf) + gm


def _verify_hdr_jpeg(data, base_size, gain_size, icc):
    """Contrôle de structure : MPF cohérent, carte de gain située où l'index l'annonce, XMP, ICC, décodage."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("SOI absent")
    o, tiff = 2, None
    while data[o] == 0xFF and data[o + 1] != 0xDA:
        if data[o + 1] == 0xE2 and data[o + 4:o + 8] == b"MPF\x00":
            tiff = o + 8
        o += 2 + _be(data, o + 2, 2)
    if tiff is None:
        raise ValueError("MPF absent")
    ent = next(tiff + _be(data, tiff + 18 + 12 * k, 4) for k in range(_be(data, tiff + 8, 2))
               if _be(data, tiff + 10 + 12 * k, 2) == 0xB002)
    prim_size, gain_len, gain_off = (_be(data, ent + 4, 4), _be(data, ent + 20, 4), _be(data, ent + 24, 4))
    gm = tiff + gain_off
    if data[gm:gm + 2] != b"\xff\xd8":
        raise ValueError("la carte de gain n'est pas là où le MPF l'annonce")
    if gm != prim_size or len(data) - gm != gain_len:
        raise ValueError("tailles MPF incohérentes")
    found = re.search(rb'Item:Length="(\d+)"', data[:gm])
    if not found or int(found.group(1)) != gain_len:
        raise ValueError("XMP : Item:Length incohérent")
    with Image.open(BytesIO(data[:gm])) as prim:
        prim.load()
        if prim.size != base_size or (icc and prim.info.get("icc_profile") != icc):
            raise ValueError("image principale ou profil ICC altéré")
    with Image.open(BytesIO(data[gm:])) as g:
        g.load()
        if g.size != gain_size or g.mode != "L":
            raise ValueError("carte de gain illisible")


def hdr_source(src, im):
    """Données HDR d'un HEIC : dict(payload, meta, gain). NotHdr si la source est SDR, HdrSkip si HDR non géré."""
    heif = pillow_heif.open_heif(str(src))[0]
    gids = (heif.info.get("aux") or {}).get(GAIN_AUX)
    try:
        payload, inputs, pitm = _read_tmap(src)
    except NotHdr:
        if gids:
            raise HdrSkip("carte de gain Apple sans item tmap : format non géré")
        raise
    meta = _parse_iso(payload)
    if not gids or inputs != [pitm, gids[0]]:
        raise HdrSkip("le tmap ne référence pas la carte de gain Apple")
    if im.mode != "RGB":
        raise HdrSkip(f"mode d'image {im.mode} non pris en charge")
    gain = heif.get_aux_image(gids[0]).to_pillow()
    if gain.mode != "L":
        raise HdrSkip(f"carte de gain en mode {gain.mode} (attendu L)")
    return dict(payload=payload, meta=meta, gain=gain)


_ISO_DEN = 1_000_000


def _iso_payload(meta):
    """Payload ISO 21496-1 d'un `tmap` (octet de version compris), carte de gain monocanal, depuis les métadonnées (clés de
    _parse_iso) : pour un JPEG Ultra HDR qui n'avait que du XMP hdrgm. Fractions de dénominateur 10^6 (6 décimales, comme le XMP).
    Octets 0 à 5 : version, version minimale, version d'écriture, indicateurs (0x40 comme dans les tmap iPhone)."""
    out = b"\x00\x00\x00\x00\x00\x40"
    for key, signed in (("base_headroom", False), ("alt_headroom", False), ("gain_min", True), ("gain_max", True),
                        ("gamma", False), ("base_offset", True), ("alt_offset", True)):
        n = round(meta[key] * _ISO_DEN)
        if not (-2 ** 31 <= n < 2 ** 31 if signed else 0 <= n < 2 ** 32):
            raise HdrSkip(f"valeur {key} = {meta[key]} hors des limites du format ISO 21496-1")
        out += struct.pack(">i" if signed else ">I", n) + struct.pack(">I", _ISO_DEN)
    return out


def build_hdr_jpeg(hs, im, exif, icc):
    """Octets du JPEG Ultra HDR : image SDR + carte de gain + métadonnées ISO du tmap."""
    buf = BytesIO()
    im.save(buf, "JPEG", **P["jpg"], **({"exif": exif} if exif else {}))
    base = _strip_app0(buf.getvalue())
    buf = BytesIO()
    hs["gain"].save(buf, "JPEG", **P["jpg_gain"])
    gain_jpeg = _strip_app0(buf.getvalue())
    out = _assemble_hdr_jpeg(base, gain_jpeg, hs["payload"] or _iso_payload(hs["meta"]), hs["meta"], icc)
    _verify_hdr_jpeg(out, im.size, hs["gain"].size, icc)
    return out


# ----------------------------------------------------------------------------------------------
# AVIF / JXL en HDR : HDR = (SDR_lin + offset_sdr) * 2^(gain) - offset_hdr  (ISO 21496-1, pleine
# amplitude), puis Rec.2020 + PQ, blanc SDR = 203 nits. Reconstruction recoupée avec libultrahdr
# (référence de Google) : écart relatif moyen ~0,6 %.
# ----------------------------------------------------------------------------------------------
SRGB_PARA = (2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045)    # courbe sRGB (aussi celle de Display P3)
_M2020_XYZ = ((0.636958, 0.144617, 0.168881), (0.262700, 0.677998, 0.059302), (0.0, 0.028073, 1.060985))
_BRADFORD_D65_D50 = ((1.0478112, 0.0228866, -0.0501270), (0.0295424, 0.9904844, -0.0170491),
                     (-0.0092345, 0.0150436, 0.7521316))


def _s15(d, o):
    return int.from_bytes(d[o:o + 4], "big", signed=True) / 65536


def _srgb_eotf(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _trc_is_srgb(icc, o):
    """La courbe ICC située à l'offset `o` est-elle la courbe sRGB ? Type `para` (iPhone) ou table `curv` (>= 256 points)."""
    typ = icc[o:o + 4]
    if typ == b"para":
        return _be(icc, o + 8, 2) == 3 and all(abs(_s15(icc, o + 12 + 4 * k) - v) <= 2e-3 for k, v in enumerate(SRGB_PARA))
    if typ == b"curv":
        n = _be(icc, o + 8, 4)
        if n < 256:
            return False
        tab = struct.unpack(f">{n}H", icc[o + 12:o + 12 + 2 * n])
        return all(abs(v / 65535 - _srgb_eotf(i / (n - 1))) <= 1e-3 for i, v in enumerate(tab))
    return False


def _icc_matrix_profile(icc):
    """(colonnes XYZ D50 de r, g, b ; courbes == sRGB ?) d'un profil ICC « matrice + courbes ». HdrSkip sinon."""
    if not icc:
        raise HdrSkip("pas de profil ICC")
    try:
        n_tags = _be(icc, 128, 4)
        if len(icc) < 132 or n_tags > (len(icc) - 132) // 12:
            raise KeyError("table des étiquettes")
        tags = {icc[132 + 12 * i:136 + 12 * i].decode("latin1"): _be(icc, 136 + 12 * i, 4) for i in range(n_tags)}
        cols = []
        for t in ("rXYZ", "gXYZ", "bXYZ"):
            o = tags[t]
            if icc[o:o + 4] != b"XYZ ":
                raise KeyError(t)
            cols.append([_s15(icc, o + 8 + 4 * k) for k in range(3)])
        srgb = all(_trc_is_srgb(icc, tags[t]) for t in ("rTRC", "gTRC", "bTRC"))
    except (KeyError, IndexError, struct.error):
        raise HdrSkip("profil ICC illisible ou de type LUT (matrice + courbes attendus)")
    return cols, srgb


# colonnes XYZ (D50) des profils de référence : Display P3 d'Apple et sRGB IEC 61966-2.1
_COLORANTS = {
    "p3": ((0.51512, 0.24120, -0.00105), (0.29198, 0.69225, 0.04189), (0.15710, 0.06657, 0.78407)),
    "srgb": ((0.43604, 0.22249, 0.01392), (0.38512, 0.71690, 0.09706), (0.14305, 0.06061, 0.71393)),
}


def _icc_kind(icc):
    """'srgb' (pas de profil, ou profil sRGB), 'p3' (Display P3) ou None (autre profil : pas d'étiquette CICP équivalente)."""
    if not icc:
        return "srgb"
    try:
        cols, srgb = _icc_matrix_profile(icc)
    except HdrSkip:
        return None
    if not srgb:
        return None
    for kind, ref in _COLORANTS.items():
        if all(abs(c - r) <= 4e-3 for col, rc in zip(cols, ref) for c, r in zip(col, rc)):
            return kind
    return None


def _icc_to_rec2020(icc, assume_srgb=False):
    """Matrice « RGB linéaire du profil ICC -> Rec.2020 linéaire ». Profils matrice + courbe sRGB seulement ;
    sans profil : HdrSkip, sauf assume_srgb (un JPEG sans profil est du sRGB)."""
    cols, srgb = ([list(col) for col in _COLORANTS["srgb"]], True) if (assume_srgb and not icc) else _icc_matrix_profile(icc)
    if not srgb:
        raise HdrSkip("courbe du profil ICC différente de sRGB (sRGB / Display P3 attendu)")
    to_d50 = np.array(_BRADFORD_D65_D50) @ np.array(_M2020_XYZ)      # Rec.2020 -> XYZ (D50)
    m = np.linalg.inv(to_d50) @ np.array(cols).T                     # ICC RGB -> Rec.2020
    return (m / m.sum(axis=1, keepdims=True)).astype(np.float32)     # le blanc reste exactement blanc


def _pq(nits):
    """OETF PQ (SMPTE ST 2084) : luminance absolue en nits -> code [0, 1]."""
    y = np.power(np.clip(nits / 10000.0, 0.0, 1.0), 0.1593017578125)
    return np.power((0.8359375 + 18.8515625 * y) / (1.0 + 18.6875 * y), 78.84375)


def hdr_pixels(im, hs, icc, assume_srgb=False):
    """Codes PQ Rec.2020 de l'image : dict(u16 = 0..65535, u10 = 0..1023), tableaux (h, w, 3)."""
    if not HAS_HDR_ENC:
        raise HdrSkip("imagecodecs / numpy absents (" + HDR_ENC_HINT + ")")
    m, mat = hs["meta"], _icc_to_rec2020(icc, assume_srgb)
    w, h = im.size
    sdr = np.asarray(im)                                              # (h, w, 3) uint8
    gm = np.asarray(hs["gain"].resize((w, h), Image.BILINEAR))        # (h, w) uint8
    x = np.arange(256, dtype=np.float32) / 255
    lin_lut = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)
    g = x ** (1.0 / m["gamma"])
    gain_lut = np.exp2(m["gain_min"] * (1 - g) + m["gain_max"] * g).astype(np.float32)
    u16 = np.empty((h, w, 3), np.uint16)
    u10 = np.empty((h, w, 3), np.uint16)
    for y in range(0, h, 256):                                        # par bandes : peu de mémoire
        lin = lin_lut[sdr[y:y + 256]]
        hdr = (lin + np.float32(m["base_offset"])) * gain_lut[gm[y:y + 256]][..., None] - np.float32(m["alt_offset"])
        code = _pq(np.maximum(hdr @ mat.T, 0.0) * np.float32(HDR_SDR_WHITE_NITS))
        u16[y:y + 256] = np.rint(code * 65535)
        u10[y:y + 256] = np.rint(code * 1023)
    return dict(u16=u16, u10=u10)


def _box(typ, payload):
    return struct.pack(">I", 8 + len(payload)) + typ + payload


def _tiff_exif(exif):
    """Octets TIFF de l'EXIF (sans l'en-tête « Exif\\0\\0 »), orientation ramenée à 1 (pixels déjà tournés)."""
    if not exif:
        return None
    ex = Image.Exif()
    ex.load(exif)
    if ex.get(274, 1) != 1:
        ex[274] = 1
        exif = ex.tobytes()
    pos = [k for k in (exif.find(b"II*\x00"), exif.find(b"MM\x00*")) if 0 <= k <= 8]
    return exif[min(pos):] if pos else None


def _jxl_add_exif(code, tiff):
    """Enveloppe un codestream JXL nu dans un conteneur avec une boîte Exif (octets = décalage TIFF + EXIF)."""
    sig = b"\x00\x00\x00\x0cJXL \r\n\x87\n"
    exif_box = _box(b"Exif", b"\x00\x00\x00\x00" + tiff)
    if code[:2] == b"\xff\x0a":
        return sig + _box(b"ftyp", b"jxl \x00\x00\x00\x00jxl ") + exif_box + _box(b"jxlc", code)
    if code[:12] == sig:                       # déjà un conteneur : Exif juste après ftyp
        end = 12 + _be(code, 12, 4)
        return code[:end] + exif_box + code[end:]
    raise ValueError("flux JXL inattendu")


def _avif_add_exif(data, tiff):
    """Ajoute un item Exif (+ référence cdsc) à un AVIF : meta (iinf, iref, iloc) réécrit, données en fin de mdat."""
    top = list(_boxes(data, 0, len(data)))
    meta = next((b for b in top if b[0] == "meta"), None)
    if meta is None or top[-1][0] != "mdat" or top[-1][1] < meta[1]:
        raise ValueError("structure AVIF inattendue (meta puis mdat en dernier attendus)")
    m_start, md_start = meta[1] - 8, top[-1][1] - 8
    if _be(data, m_start, 4) != meta[2] - m_start or _be(data, md_start, 4) not in (0, len(data) - md_start):
        raise ValueError("boîtes AVIF à taille étendue non prises en charge")
    kids = [(t, cs, ce) for t, cs, ce in _boxes(data, meta[1] + 4, meta[2])]
    pitm = next(_be(data, cs + 4, 2 if data[cs] == 0 else 4) for t, cs, ce in kids if t == "pitm")
    iinf = next((k for k in kids if k[0] == "iinf"), None)
    iloc = next((k for k in kids if k[0] == "iloc"), None)
    iref = next((k for k in kids if k[0] == "iref"), None)
    if iinf is None or iloc is None or (iref and data[iref[1]] != 0) or data[iinf[1]] != 0 or data[iloc[1]] > 1:
        raise ValueError("versions iinf/iref/iloc non prises en charge")
    # nouvel identifiant d'item
    ids = []
    for t, cs, ce in _boxes(data, iinf[1] + 6, iinf[2]):
        if t == "infe":
            ids.append(_be(data, cs + 4, 2 if data[cs] < 3 else 4))
    new_id = max(ids) + 1
    if new_id > 0xFFFF:
        raise ValueError("identifiant d'item hors limite")
    payload = b"\x00\x00\x00\x00" + tiff
    # iinf : une entrée de plus
    infe = _box(b"infe", struct.pack(">B3xHH4s", 2, new_id, 0, b"Exif") + b"\x00")
    cnt = _be(data, iinf[1] + 4, 2) + 1
    new_iinf = _box(b"iinf", data[iinf[1]:iinf[1] + 4] + struct.pack(">H", cnt) + data[iinf[1] + 6:iinf[2]] + infe)
    # iref : cdsc (Exif -> image principale)
    cdsc = _box(b"cdsc", struct.pack(">HHH", new_id, 1, pitm))
    new_iref = _box(b"iref", (data[iref[1]:iref[2]] if iref else b"\x00\x00\x00\x00") + cdsc)
    # iloc : décalage des offsets existants (le meta grossit) + nouvel item
    v, o = data[iloc[1]], iloc[1] + 4
    osz, lsz, bsz, isz = data[o] >> 4, data[o] & 15, data[o + 1] >> 4, data[o + 1] & 15
    if osz < 4 or lsz < 1:
        raise ValueError("iloc : tailles de champs non prises en charge")
    o += 2
    n = _be(data, o, 2)
    o += 2
    entries = []
    for _ in range(n):
        iid = _be(data, o, 2)
        o += 2
        cm = 0
        if v == 1:
            cm = _be(data, o, 2)
            o += 2
        o += 2
        base = _be(data, o, bsz)
        o += bsz
        ec = _be(data, o, 2)
        o += 2
        ext = []
        for _ in range(ec):
            idx = 0
            if v == 1 and isz:
                idx = _be(data, o, isz)
                o += isz
            ext.append((idx, _be(data, o, osz), _be(data, o + osz, lsz)))
            o += osz + lsz
        entries.append((iid, cm & 15, base, ext))

    def build_meta(delta, exif_off):
        rows = b""
        for iid, cm, base, ext in entries + [(new_id, 0, 0, [(0, exif_off, len(payload))])]:
            shift = delta if (cm == 0 and iid != new_id) else 0
            row = struct.pack(">H", iid) + (struct.pack(">H", cm) if v == 1 else b"") + b"\x00\x00"
            row += (base + (shift if bsz else 0)).to_bytes(bsz, "big") + struct.pack(">H", len(ext))
            for idx, off, ln in ext:
                row += (idx.to_bytes(isz, "big") if v == 1 and isz else b"")
                row += (off + (shift if not bsz else 0)).to_bytes(osz, "big") + ln.to_bytes(lsz, "big")
            rows += row
        iloc_box = _box(b"iloc", data[iloc[1]:iloc[1] + 4] + data[iloc[1] + 4:iloc[1] + 6]
                        + struct.pack(">H", len(entries) + 1) + rows)
        parts = b""
        for t, cs, ce in kids:
            if t == "iinf":
                parts += new_iinf + (new_iref if not iref else b"")
            elif t == "iref":
                parts += new_iref
            elif t == "iloc":
                parts += iloc_box
            else:
                parts += data[cs - 8:ce]
        return _box(b"meta", data[meta[1]:meta[1] + 4] + parts)

    delta = len(build_meta(0, 0)) - (meta[2] - m_start)
    new_meta = build_meta(delta, len(data) + delta)
    md_size = _be(data, md_start, 4)
    new_mdat_hdr = struct.pack(">I", 0 if md_size == 0 else md_size + len(payload)) + b"mdat"
    return data[:m_start] + new_meta + data[meta[2]:md_start] + new_mdat_hdr + data[top[-1][1]:] + payload


def _avif_read_exif(data):
    """Relit l'EXIF d'un AVIF par ses tables (iinf/iloc/iref), indépendamment de l'écriture : octets TIFF ou None."""
    items, refs, iloc, pitm, idat = _heif_index(data)
    ids = [i for i, t in items.items() if t == "Exif"]
    if len(ids) != 1 or ("cdsc", ids[0], [pitm]) not in refs or ids[0] not in iloc:
        return None
    (off, ln), = iloc[ids[0]][1]
    raw = data[off:off + ln]
    return raw[4 + _be(raw, 0, 4):]


# ----------------------------------------------------------------------------------------------
# Entrée JPEG : orientation, EXIF, profil ; JPEG « Ultra HDR » (image SDR + carte de gain, index MPF)
# ----------------------------------------------------------------------------------------------
_T = Image.Transpose
_ORIENT_OPS = {2: _T.FLIP_LEFT_RIGHT, 3: _T.ROTATE_180, 4: _T.FLIP_TOP_BOTTOM, 5: _T.TRANSPOSE, 6: _T.ROTATE_270,
               7: _T.TRANSVERSE, 8: _T.ROTATE_90}                    # les opérations de ImageOps.exif_transpose


def _exif_orientation_slot(exif):
    """(position de la valeur, ordre des octets) de l'étiquette Orientation (IFD0) d'un EXIF, ou None. Lecture des octets."""
    if not exif:
        return None
    starts = [k for k in (exif.find(b"II*\x00"), exif.find(b"MM\x00*")) if 0 <= k <= 8]
    if not starts:
        return None
    base = min(starts)
    order = "little" if exif[base:base + 2] == b"II" else "big"

    def rd(p, n):
        return int.from_bytes(exif[p:p + n], order)

    ifd = base + rd(base + 4, 4)
    for k in range(min(rd(ifd, 2), 512)):
        e = ifd + 2 + 12 * k
        if e + 12 > len(exif):
            return None
        if rd(e, 2) == 274 and rd(e + 2, 2) == 3 and rd(e + 4, 4) == 1:
            return e + 8, order
    return None


def _exif_orientation(exif):
    slot = _exif_orientation_slot(exif)
    return int.from_bytes(exif[slot[0]:slot[0] + 2], slot[1]) if slot else 1


def _exif_orientation_to_1(exif):
    """EXIF dont l'orientation vaut 1 : 2 octets modifiés sur place, aucune autre étiquette ni aucun décalage ne bouge."""
    slot = _exif_orientation_slot(exif)
    if not slot or _exif_orientation(exif) == 1:
        return exif
    return exif[:slot[0]] + (1).to_bytes(2, slot[1]) + exif[slot[0] + 2:]


def _segments(d):
    """Segments d'en-tête d'un JPEG, jusqu'au SOS : (marqueur, début du corps, fin)."""
    o = 2
    while o + 4 <= len(d) and d[o] == 0xFF and d[o + 1] not in (0xDA, 0xD9):
        n = _be(d, o + 2, 2)
        if n < 2:
            return
        yield d[o + 1], o + 4, o + 2 + n
        o += 2 + n


def _mpf_images(d):
    """[(début, taille)] des images de l'index MPF (CIPA DC-007) d'un JPEG, l'image principale en premier ; [] sans MPF."""
    for marker, s, e in _segments(d):
        if marker == 0xE2 and d[s:s + 4] == b"MPF\x00":
            t = s + 4                                            # en-tête TIFF de l'index
            order = "little" if d[t:t + 2] == b"II" else "big"

            def rd(p, n):
                return int.from_bytes(d[p:p + n], order)

            ifd, tags = t + rd(t + 4, 4), {}
            for k in range(min(rd(ifd, 2), 32)):
                tags[rd(ifd + 2 + 12 * k, 2)] = rd(ifd + 10 + 12 * k, 4)
            if 0xB001 not in tags or 0xB002 not in tags:
                return []
            out = []
            for i in range(min(tags[0xB001], 16)):
                p = t + tags[0xB002] + 16 * i
                out.append((0 if i == 0 else t + rd(p + 8, 4), rd(p + 4, 4)))
            return out
    return []


def _split_ultrahdr(raw):
    """(octets de l'image principale, octets de la carte de gain ou None) d'un JPEG ; l'image principale seule
    quand le fichier porte d'autres images (MPO, carte de gain) : c'est elle qu'on transcode."""
    imgs = _mpf_images(raw)
    if len(imgs) > 1 and 0 < imgs[0][1] < len(raw) and raw[imgs[0][1] - 2:imgs[0][1]] == b"\xff\xd9":
        prim = raw[:imgs[0][1]]
        for off, size in imgs[1:]:
            blob = raw[off:off + size]
            if blob[:2] == b"\xff\xd8" and (b"hdrgm:" in blob[:65536] or ISO_NS in blob[:65536]):
                return prim, blob
        return prim, None
    for m in re.finditer(rb"Container:Item\b([^>]*)>", raw[:65536]):      # repli : répertoire Container du XMP
        ln = re.search(rb'Item:Length="(\d+)"', m.group(1))
        if b'Item:Semantic="GainMap"' in m.group(1) and ln and 0 < int(ln.group(1)) < len(raw):
            blob = raw[len(raw) - int(ln.group(1)):]
            if blob[:2] == b"\xff\xd8":
                return raw[:len(raw) - len(blob)], blob
    return raw, None


def _xmp_text(d):
    for marker, s, e in _segments(d):
        if marker == 0xE1 and d[s:s + len(XMP_NS)] == XMP_NS:
            txt = d[s + len(XMP_NS):e].decode("utf-8", "replace")
            if "hdrgm:" in txt:
                return txt
    return None


def _hdrgm_meta(xmp):
    """Métadonnées de la carte de gain d'un XMP « hdrgm » (Ultra HDR v1) ; mêmes clés que _parse_iso."""
    def val(name, default):
        m = re.search(rf'hdrgm:{name}\s*=\s*"([^"]*)"', xmp)
        if m:
            txt = m.group(1)
        else:
            m = re.search(rf"<hdrgm:{name}\b[^>]*>(.*?)</hdrgm:{name}>", xmp, re.S)
            if not m:
                return default
            items = re.findall(r"<rdf:li[^>]*>\s*([^<\s]+)\s*</rdf:li>", m.group(1))
            if len(set(items)) > 1:
                raise HdrSkip("gain map multicanal (une valeur par canal) non prise en charge")
            txt = items[0] if items else m.group(1).strip()
        try:
            return float(txt)
        except ValueError:
            raise HdrSkip(f"valeur hdrgm:{name} illisible ({txt!r})")

    if re.search(r'hdrgm:BaseRenditionIsHDR\s*=\s*"true"', xmp, re.I):
        raise HdrSkip("image de base HDR non prise en charge")
    gmax, cap = val("GainMapMax", None), val("HDRCapacityMax", None)
    if gmax is None or cap is None:
        raise HdrSkip("métadonnées hdrgm incomplètes (GainMapMax / HDRCapacityMax)")
    meta = dict(gain_min=val("GainMapMin", 0.0), gain_max=gmax, gamma=val("Gamma", 1.0), base_offset=val("OffsetSDR", 1 / 64),
                alt_offset=val("OffsetHDR", 1 / 64), base_headroom=val("HDRCapacityMin", 0.0), alt_headroom=cap)
    if meta["gamma"] <= 0:
        raise HdrSkip("gamma de la carte de gain nul ou négatif")
    return meta


def jpeg_hdr_source(prim, blob, orient):
    """Données HDR d'un JPEG Ultra HDR : dict(payload, meta, gain), comme hdr_source (payload : ISO d'origine, ou None). NotHdr sans carte de gain,
    HdrSkip si la carte ou ses métadonnées ne sont pas gérées. Métadonnées : ISO 21496-1 si présentes (valeurs
    exactes), sinon XMP hdrgm."""
    if blob is None:
        raise NotHdr("pas de carte de gain")
    meta, err, raw_iso = None, None, None
    payloads = [d[s + len(ISO_NS):e] for d in (blob, prim) for marker, s, e in _segments(d)
                if marker == 0xE2 and d[s:s + len(ISO_NS)] == ISO_NS]
    full = max(payloads, key=len, default=b"")
    if len(full) >= 61:                                  # le segment « version seule » de l'image principale est plus court
        try:
            meta = _parse_iso(b"\x00" + full)            # _parse_iso attend l'octet de version du tmap en tête
            raw_iso = b"\x00" + full                     # payload d'origine, recopié tel quel dans un JPEG Ultra HDR de sortie
        except HdrSkip as e:
            err = e
    if meta is None:
        xmp = _xmp_text(blob) or _xmp_text(prim)
        if xmp:
            meta = _hdrgm_meta(xmp)
        elif err is not None:
            raise err
        else:
            raise HdrSkip("métadonnées de la carte de gain introuvables (ni ISO 21496-1 ni XMP hdrgm)")
    with Image.open(BytesIO(blob)) as g:
        g.load()
        if g.mode != "L":
            raise HdrSkip(f"carte de gain en mode {g.mode} (monocanal L attendu)")
        gain = g.copy()
    if orient in _ORIENT_OPS:
        gain = gain.transpose(_ORIENT_OPS[orient])       # la carte suit l'orientation de l'image principale
    return dict(payload=raw_iso, meta=meta, gain=gain)       # payload None : métadonnées XMP seules (voir _iso_payload)


def _gray_to_rgb(im, icc, notes):
    """Image « L » -> RGB ; un profil gris est converti en sRGB (sinon ignoré, avec une note)."""
    if icc and icc[16:20] == b"GRAY" and ImageCms is not None:
        try:
            rgb = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(BytesIO(icc)), ImageCms.createProfile("sRGB"),
                                            renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode="RGB")
            notes.append("JPEG en niveaux de gris avec profil gris : converti en sRGB")
            return rgb
        except Exception as e:
            notes.append(f"profil gris illisible ({type(e).__name__}) : ignoré")
    elif icc:
        notes.append("profil ICC ignoré (JPEG en niveaux de gris)")
    return im.convert("RGB")


def _prepare_jpeg(raw, im0, notes):
    """(Ctx, dégradé) d'un JPEG ouvert : image RGB orientée, EXIF à orientation 1, profil, JPEG principal, carte de gain."""
    degraded = False
    if im0.mode == "CMYK":
        raise ValueError("JPEG CMYK / YCCK non pris en charge (une conversion en RGB sans profil donnerait de fausses couleurs)")
    if im0.mode not in ("RGB", "L"):
        raise ValueError(f"mode JPEG {im0.mode} non pris en charge")
    icc, exif0 = im0.info.get("icc_profile"), im0.info.get("exif")
    orient = _exif_orientation(exif0)
    im = im0
    if im0.mode == "L":
        im, icc = _gray_to_rgb(im0, icc, notes), None
    exif = exif0
    if orient != 1:
        exif = _exif_orientation_to_1(exif0)             # les pixels sont tournés ci-dessous : l'étiquette doit valoir 1
        if orient in _ORIENT_OPS:
            im = im.transpose(_ORIENT_OPS[orient])
        else:
            notes.append(f"orientation EXIF {orient} invalide : ignorée")
    prim, blob = _split_ultrahdr(raw)
    if blob is None and len(prim) < len(raw):
        notes.append("images secondaires du fichier (MPO) ignorées : seule l'image principale est convertie")
    hs = None
    if HDR:
        try:
            hs = jpeg_hdr_source(prim, blob, orient)
        except NotHdr:
            pass
        except HdrSkip as e:
            notes.append(f"HDR non géré ({e}) -> sorties SDR")
            degraded = True
        except Exception as e:
            notes.append(f"HDR illisible ({type(e).__name__}: {e}) -> sorties SDR")
            degraded = True
    return Ctx(im, hs, exif, icc, jpeg=prim, exif_orig=exif0), degraded


# ----------------------------------------------------------------------------------------------
# Encodeurs et contrôles. Une « route » encode une photo dans un format et renvoie (octets, contrôle) ;
# le contrôle RELIT les octets produits (décodage indépendant de l'encodage) et renvoie un résumé,
# ou lève ValueError. Rien n'est écrit sur le disque avant que le contrôle soit passé.
# ----------------------------------------------------------------------------------------------
def _avif_params(which):
    """(niveau imagecodecs, '4:4:4' ou '4:2:0', sans perte ?) du préréglage pour which = 'sdr' ou 'hdr'.
    Le 4:4:4 voulu par le préréglage devient du 4:2:0 quand AVIF_444 = False."""
    a = P["avif_" + which]
    if a["chroma"] == "444" and AVIF_444:
        return a["level"], "4:4:4", a["level"] == 100
    return a["level_420"], "4:2:0", False


CICP_PRIMARIES = {"p3": 12, "srgb": 1}        # H.273 : 12 = Display P3 (SMPTE EG 432-1), 1 = BT.709 / sRGB
MO_PAR_MPX = 90                               # mémoire de pointe mesurée par processus et par mégapixel (voir _workers)


def _to10(rgb8):
    """8 -> 10 bits par arrondi de v * 1023 / 255 ; _to8 le défait exactement."""
    out = np.empty(rgb8.shape, np.uint16)
    for y in range(0, rgb8.shape[0], 256):
        out[y:y + 256] = (rgb8[y:y + 256].astype(np.uint32) * 1023 + 127) // 255
    return out


def _to8(a10):
    out = np.empty(a10.shape, np.uint8)
    for y in range(0, a10.shape[0], 256):
        out[y:y + 256] = (a10[y:y + 256].astype(np.uint32) * 255 + 511) // 1023
    return out


def _diff(a, b):
    """(PSNR en dB, None si identiques ; écart max en niveaux) entre deux images PIL 8 bits de même taille."""
    hist = ImageChops.difference(a, b).histogram()
    n = a.size[0] * a.size[1] * (len(hist) // 256)
    sse = sum(cnt * (i % 256) ** 2 for i, cnt in enumerate(hist))
    mx = max((i % 256 for i, cnt in enumerate(hist) if cnt), default=0)
    return (None if sse == 0 else 10 * math.log10(255.0 ** 2 * n / sse)), mx


def _fmt_diff(psnr, mx):
    if mx == 0:
        return "pixels identiques"
    return f"PSNR {psnr:.1f} dB, écart max {mx} niveau{'x' if mx > 1 else ''} sur 255"


def _maxdiff(a, b):
    m = 0
    for y in range(0, a.shape[0], 256):
        m = max(m, int(np.abs(a[y:y + 256].astype(np.int32) - b[y:y + 256]).max()))
    return m


def _psnr_codes(a, b, scale):
    x, y = a[::4, ::4].astype(np.float32) / scale, b[::4, ::4].astype(np.float32) / scale
    return 10 * np.log10(1.0 / max(float(np.mean((x - y) ** 2)), 1e-12))


def _avif_colr(data):
    """((primaires, transfert, matrice), plage complète) de la boîte colr/nclx d'un AVIF, ou None."""
    found = re.search(rb"colrnclx(..)(..)(..)(.)", data[:8192], re.S)
    if not found:
        return None
    return tuple(_be(found.group(k), 0, 2) for k in (1, 2, 3)), bool(found.group(4)[0] & 0x80)


def _brotli_ok():
    """Le codec brotli d'imagecodecs est-il disponible ? (les boîtes « brob » d'un JXL transcodé sont compressées avec)"""
    try:
        return bool(HAS_HDR_ENC and imagecodecs.BROTLI.available)
    except Exception:
        return False


def _jxl_read_exif(data):
    """Octets TIFF de l'EXIF d'un JXL : boîte Exif, ou boîte « brob » (Brotli) qui enveloppe une boîte Exif, ou None."""
    for typ, s, e in _boxes(data, 0, len(data)):
        if typ == "Exif":
            return data[s + 4:e]
        if typ == "brob" and data[s:s + 4] == b"Exif" and _brotli_ok():
            return imagecodecs.brotli_decode(data[s + 4:e])[4:]
    return None


def _nan_safe(v):
    """NaN != NaN : un rationnel 0/0 (GPSImgDirection des Pixel, par exemple) se lirait « altéré » à chaque comparaison.
    Remplacé par (« NaN », numérateur, dénominateur), qui se compare normalement."""
    if isinstance(v, tuple):
        return tuple(_nan_safe(x) for x in v)
    try:
        if isinstance(v, float) or hasattr(v, "denominator"):
            if v != v:
                return ("NaN", getattr(v, "numerator", None), getattr(v, "denominator", None))
    except Exception:
        pass
    return v


def _exif_tags(raw):
    """({(IFD, étiquette): valeur} sans l'orientation, orientation) d'un EXIF (avec ou sans l'en-tête « Exif\\0\\0 »)."""
    ex = Image.Exif()
    ex.load(raw)
    tags = {(0, k): _nan_safe(v) for k, v in ex.items() if k not in (0x8769, 0x8825, 0xA005, 274)}
    for ifd in (0x8769, 0x8825, 0xA005):
        try:
            tags.update({(ifd, k): _nan_safe(v) for k, v in ex.get_ifd(ifd).items()})
        except Exception:
            pass
    return tags, ex.get(274, 1)


def _check_exif(src, got):
    """EXIF relu == EXIF de la source (toutes étiquettes), orientation 1 (les pixels sont déjà tournés)."""
    if not src:
        return
    if not got:
        raise ValueError("EXIF absent")
    a, _ = _exif_tags(src)
    b, orient = _exif_tags(got)
    if a != b:
        bad = sorted({k for k in set(a) | set(b) if a.get(k) != b.get(k)}, key=str)[:5]
        raise ValueError(f"EXIF altéré (étiquettes {bad})")
    if orient != 1:
        raise ValueError(f"orientation EXIF {orient} : l'image serait tournée deux fois")


def _to_srgb(im, icc):
    """Image convertie en sRGB depuis son profil ICC (les formats qui ne peuvent pas porter ce profil)."""
    if not icc:
        return im
    if ImageCms is None:
        raise RuntimeError("ImageCms indisponible : conversion en sRGB impossible")
    return ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(BytesIO(icc)), ImageCms.createProfile("sRGB"),
                                     renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode="RGB",
                                     flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)


class Ctx:
    """Une photo décodée et ce qui s'en déduit (calculé à la demande, une seule fois)."""

    def __init__(self, im, hs, exif, icc, jpeg=None, exif_orig=None):
        self.im, self.hs = im, hs
        self.exif, self.icc = exif, icc
        self.meta = {k: v for k, v in (("exif", self.exif), ("icc_profile", self.icc)) if v}
        self.tiff = _tiff_exif(self.exif)
        self.kind = _icc_kind(self.icc)
        self.jpeg, self.exif_orig = jpeg, exif_orig      # JPEG d'entrée : octets de l'image principale et EXIF d'origine
        self.notes, self.degraded = [], False
        self._rgb8 = self._px = None

    @property
    def rgb8(self):
        if self._rgb8 is None:
            self._rgb8 = np.array(self.im)
        return self._rgb8

    @property
    def px(self):
        if self._px is None:
            self._px = hdr_pixels(self.im, self.hs, self.icc, assume_srgb=self.jpeg is not None)   # JPEG sans profil = sRGB
        return self._px

    def warn(self, text):
        self.notes.append(text)
        self.degraded = True


def _check_pillow(d, c, ref=None, icc=True):
    """Relit une sortie Pillow (JPEG, AVIF, JXL) : dimensions, profil ICC, EXIF, fidélité des pixels."""
    ref = c.im if ref is None else ref
    with Image.open(BytesIO(d)) as chk:
        chk.load()
        if chk.size != ref.size:
            raise ValueError(f"dimensions {chk.size} != {ref.size}")
        if icc and c.icc and chk.info.get("icc_profile") != c.icc:
            raise ValueError("profil ICC absent ou altéré")
        _check_exif(c.exif, chk.info.get("exif"))
        psnr, mx = _diff(ref, chk.convert("RGB"))
    if psnr is not None and psnr < P["min_psnr"]:
        raise ValueError(f"pixels trop éloignés de la source (PSNR {psnr:.1f} dB < {P['min_psnr']})")
    return _fmt_diff(psnr, mx)


# --- SDR ---------------------------------------------------------------------------------------
def sdr_jpg(c):
    buf = BytesIO()
    c.im.save(buf, "JPEG", **P["jpg"], **c.meta)
    return buf.getvalue(), lambda d: _check_pillow(d, c)


def _check_jxl_sdr(d, im, rgb8, kind, c):
    dec = imagecodecs.jpegxl_decode(d)
    if dec.dtype != np.uint8 or dec.ndim != 3 or dec.shape[:2] != rgb8.shape[:2] or dec.shape[2] < 3:
        raise ValueError(f"décodage inattendu : {dec.dtype} {dec.shape}")
    dec = dec[..., :3]
    if P["jxl_sdr_distance"] is None:
        if not np.array_equal(dec, rgb8):
            raise ValueError("JXL sans perte mais pixels décodés différents de la source")
        txt = "sans perte : pixels identiques"
    else:
        psnr, mx = _diff(im, Image.fromarray(dec))
        if psnr is not None and psnr < P["min_psnr"]:
            raise ValueError(f"pixels trop éloignés de la source (PSNR {psnr:.1f} dB < {P['min_psnr']})")
        txt = _fmt_diff(psnr, mx)
    if c.tiff and _jxl_read_exif(d) != c.tiff:
        raise ValueError("EXIF absent ou altéré")
    if "JXL" in Image.OPEN:       # pillow-jxl-plugin présent : libjxl restitue un profil ICC déduit de l'étiquette couleur
        with Image.open(BytesIO(d)) as chk:
            got = _icc_kind(chk.info.get("icc_profile"))
        if got != kind:
            raise ValueError(f"étiquette couleur JXL relue : {got}, attendu : {kind}")
        txt += f", étiquette couleur {'Display P3' if kind == 'p3' else 'sRGB'} relue"
    return txt


def sdr_jxl(c):
    im, kind = c.im, c.kind
    if kind != "srgb" and (kind is None or not HAS_HDR_ENC):
        # ni imagecodecs ni pillow-jxl-plugin n'écrivent de profil ICC dans un JXL : seules les étiquettes sRGB / P3 passent
        im, kind = _to_srgb(c.im, c.icc), "srgb"
        c.warn("jxl: profil colorimétrique non étiquetable en JPEG XL -> pixels convertis en sRGB (gamut éventuellement réduit)")
    if HAS_HDR_ENC:
        J = imagecodecs.JPEGXL
        rgb8 = c.rgb8 if im is c.im else np.array(im)
        q = dict(lossless=True) if P["jxl_sdr_distance"] is None else dict(distance=P["jxl_sdr_distance"])
        data = imagecodecs.jpegxl_encode(rgb8, effort=P["jxl_sdr_effort"], bitspersample=8,
                                         primaries=J.PRIMARIES.P3 if kind == "p3" else J.PRIMARIES.SRGB,
                                         transfer=J.TRANSFER_FUNCTION.SRGB, **q)
        if c.tiff:
            data = _jxl_add_exif(data, c.tiff)
        return data, lambda d: _check_jxl_sdr(d, im, rgb8, kind, c) + (" (après conversion en sRGB)" if im is not c.im else "")
    buf = BytesIO()
    im.save(buf, "JXL", **(dict(lossless=True) if P["jxl_sdr_distance"] is None else dict(quality=90)),
            **({"exif": c.exif} if c.exif else {}))
    return buf.getvalue(), lambda d: _check_pillow(d, c, ref=im, icc=False) + (" (après conversion en sRGB)" if im is not c.im else "")


def _check_avif_sdr(d, im, rgb8, prim, c):
    if _avif_colr(d) != ((prim, 13, 6), True):
        raise ValueError(f"étiquettes couleur AVIF {_avif_colr(d)} au lieu de {prim}/13/6 plage complète")
    dec = imagecodecs.avif_decode(d)
    if dec.dtype != np.uint16 or dec.shape[:2] != rgb8.shape[:2] or dec.shape[2] < 3 or dec.max() > 1023:
        raise ValueError(f"décodage inattendu : {dec.dtype} {dec.shape}")
    _, chroma, lossless = _avif_params("sdr")
    psnr, mx = _diff(im, Image.fromarray(_to8(dec[..., :3])))
    if lossless:
        if mx > 1:
            raise ValueError(f"AVIF sans perte mais écart max {mx} niveaux")
    elif psnr is not None and psnr < P["min_psnr"]:
        raise ValueError(f"pixels trop éloignés de la source (PSNR {psnr:.1f} dB < {P['min_psnr']})")
    if c.tiff and _avif_read_exif(d) != c.tiff:
        raise ValueError("EXIF absent ou altéré")
    return _fmt_diff(psnr, mx) + f", 10 bits {chroma}"


def sdr_avif(c):
    if "AVIF" in Image.SAVE and (P["avif_sdr"]["engine"] == "pillow" or not HAS_HDR_ENC or c.kind is None):
        buf = BytesIO()                       # Pillow : profil ICC conservé tel quel
        opts = dict(P["pillow_avif"])
        if not AVIF_444 and opts.get("subsampling") == "4:4:4":
            opts["subsampling"] = "4:2:0"     # AVIF_444 = False vaut aussi pour cette voie
        c.im.save(buf, "AVIF", **opts, **c.meta)
        return buf.getvalue(), lambda d: _check_pillow(d, c)
    if not HAS_HDR_ENC:
        raise RuntimeError("ni AVIF dans Pillow, ni imagecodecs (" + HDR_ENC_HINT + ")")
    im, kind = c.im, c.kind
    if kind is None:
        im, kind = _to_srgb(c.im, c.icc), "srgb"
        c.warn("avif: profil colorimétrique non étiquetable (imagecodecs) -> pixels convertis en sRGB")
    A = imagecodecs.AVIF
    rgb8 = c.rgb8 if im is c.im else np.array(im)
    level, chroma, _ = _avif_params("sdr")
    fmt = A.PIXEL_FORMAT.YUV444 if chroma == "4:4:4" else A.PIXEL_FORMAT.YUV420
    prim = CICP_PRIMARIES[kind]
    data = imagecodecs.avif_encode(_to10(rgb8), level=level, bitspersample=10, speed=6, pixelformat=fmt,
                                   primaries=prim, transfer=13, matrix=6)          # transfert 13 = sRGB, matrice 6 = BT.601
    if c.tiff:
        data = _avif_add_exif(data, c.tiff)
    return data, lambda d: _check_avif_sdr(d, im, rgb8, prim, c) + (" (après conversion en sRGB)" if im is not c.im else "")


# --- HDR ---------------------------------------------------------------------------------------
def _check_hdr_jpg(d, c):
    glen = int(re.search(rb'Item:Length="(\d+)"', d[:20000]).group(1))
    with Image.open(BytesIO(d[:-glen])) as base:
        base.load()
        psnr, mx = _diff(c.im, base.convert("RGB"))
        _check_exif(c.exif, base.info.get("exif"))
    with Image.open(BytesIO(d[-glen:])) as gain:
        gain.load()
        _, gmx = _diff(c.hs["gain"], gain)
    if psnr is not None and psnr < P["min_psnr"]:
        raise ValueError(f"image SDR trop éloignée de la source (PSNR {psnr:.1f} dB < {P['min_psnr']})")
    _check_hdr_meta(d, c)
    return f"image SDR : {_fmt_diff(psnr, mx)} ; carte de gain : " + ("identique" if gmx == 0 else f"écart max {gmx} sur 255")


def hdr_jpg(c):
    data = build_hdr_jpeg(c.hs, c.im, c.exif, c.icc)       # contrôle de structure inclus
    return data, lambda d: _check_hdr_jpg(d, c)


def _check_avif_hdr(d, c):
    if _avif_colr(d) != ((9, 16, 9), True):
        raise ValueError(f"étiquettes couleur AVIF {_avif_colr(d)} au lieu de Rec.2020 / PQ / matrice 9, plage complète")
    dec, ref = imagecodecs.avif_decode(d), c.px["u10"]
    if dec.dtype != np.uint16 or dec.shape[:2] != ref.shape[:2] or dec.shape[2] < 3 or dec.max() > 1023:
        raise ValueError(f"décodage inattendu : {dec.dtype} {dec.shape} / max {dec.max()}")
    dec = dec[..., :3]
    _, chroma, lossless = _avif_params("hdr")
    if lossless:
        mx = _maxdiff(dec, ref)
        if mx > 2:
            raise ValueError(f"AVIF 10 bits sans perte mais écart max {mx} codes sur 1023")
        txt = "codes PQ identiques" if mx == 0 else f"écart max {mx} code{'s' if mx > 1 else ''} PQ sur 1023"
        txt += f", 10 bits {chroma}"
    else:
        psnr = _psnr_codes(dec, ref, 1023.0)
        if psnr < MIN_PSNR_PQ:
            raise ValueError(f"pixels HDR trop éloignés après encodage (PSNR PQ {psnr:.1f} dB < {MIN_PSNR_PQ})")
        txt = f"PSNR PQ {psnr:.1f} dB, 10 bits {chroma}"
    if c.tiff and _avif_read_exif(d) != c.tiff:
        raise ValueError("EXIF absent ou altéré")
    return txt


def hdr_avif(c):
    A = imagecodecs.AVIF if HAS_HDR_ENC else None
    px = c.px                                              # HdrSkip si imagecodecs / numpy absents
    level, chroma, _ = _avif_params("hdr")
    fmt = A.PIXEL_FORMAT.YUV444 if chroma == "4:4:4" else A.PIXEL_FORMAT.YUV420
    data = imagecodecs.avif_encode(px["u10"], level=level, bitspersample=10, speed=6, pixelformat=fmt,
                                   primaries=9, transfer=16, matrix=9)             # Rec.2020 / PQ / BT.2020 NCL
    if c.tiff:
        data = _avif_add_exif(data, c.tiff)
    return data, lambda d: _check_avif_hdr(d, c)


def _check_jxl_hdr(d, c):
    dec, ref = imagecodecs.jpegxl_decode(d), c.px["u16"]
    if dec.dtype != np.uint16 or dec.shape[:2] != ref.shape[:2] or dec.shape[2] < 3:
        raise ValueError(f"décodage inattendu : {dec.dtype} {dec.shape}")
    dec = dec[..., :3]
    if P["jxl_hdr_distance"] is None:
        if not np.array_equal(dec, ref):
            raise ValueError("JXL sans perte mais codes décodés différents")
        txt = "sans perte : codes PQ 16 bits identiques"
    else:
        psnr = _psnr_codes(dec, ref, 65535.0)
        if psnr < MIN_PSNR_PQ:
            raise ValueError(f"pixels HDR trop éloignés après encodage (PSNR PQ {psnr:.1f} dB < {MIN_PSNR_PQ})")
        txt = f"PSNR PQ {psnr:.1f} dB"
    if c.tiff and _jxl_read_exif(d) != c.tiff:
        raise ValueError("EXIF absent ou altéré")
    return txt


def hdr_jxl(c):
    px = c.px
    J = imagecodecs.JPEGXL
    q = dict(lossless=True) if P["jxl_hdr_distance"] is None else dict(distance=P["jxl_hdr_distance"])
    data = imagecodecs.jpegxl_encode(px["u16"], effort=P["jxl_hdr_effort"], bitspersample=16,
                                     primaries=J.PRIMARIES.BT2100, transfer=J.TRANSFER_FUNCTION.PQ, **q)
    if c.tiff:
        data = _jxl_add_exif(data, c.tiff)
    return data, lambda d: _check_jxl_hdr(d, c)


# --- JPEG en entrée : HEIC (SDR 8 bits, ou HDR 10 bits PQ), JXL (transcodage sans perte) -------------------------------------
class HdrOff(HdrSkip):
    """Choix explicite de l'utilisateur (HEIC_HDR = False) : sortie SDR sans que ce soit un repli à signaler."""


def _heic_params(which):
    """(qualité, chroma 444 | 420) du préréglage pour which = 'sdr' ou 'hdr' ; HEIC_444 = False impose le repli 4:2:0."""
    p = P["heic_" + which]
    if p["chroma"] == 444 and not HEIC_444:
        p = P["heic_" + which + "_420"]
    return p["quality"], p["chroma"]


def _chroma_txt(chroma):
    return "4:4:4" if chroma == 444 else "4:2:0"


def _check_hdr_meta(d, c):
    """JPEG en entrée (Ultra HDR) : les métadonnées de la carte de gain relues dans la sortie, en ISO 21496-1 puis en XMP hdrgm,
    doivent être celles de la source (le payload ISO est recopié tel quel, ou fabriqué à partir du XMP de la source)."""
    if c.jpeg is None:
        return
    prim, blob = _split_ultrahdr(d)
    if blob is None:
        raise ValueError("carte de gain introuvable dans la sortie")
    iso = [blob[s + len(ISO_NS):e] for mk, s, e in _segments(blob) if mk == 0xE2 and blob[s:s + len(ISO_NS)] == ISO_NS]
    iso = [p for p in iso if len(p) >= 61]
    xmp = _xmp_text(blob)
    if not iso or not xmp:
        raise ValueError("métadonnées ISO 21496-1 ou XMP hdrgm absentes de la carte de gain")
    ref = c.hs["meta"]
    for name, got in (("ISO 21496-1", _parse_iso(b"\x00" + iso[0])), ("XMP hdrgm", _hdrgm_meta(xmp))):
        bad = [k for k in ref if abs(got[k] - ref[k]) > 2e-6]
        if bad:
            raise ValueError(f"métadonnées {name} de la carte de gain différentes de la source ({', '.join(bad)})")


# libde265 (le décodeur de pillow-heif) refuse une image HEVC unique de plus de 16 Mio : mesuré, relue à 16,6 Mo, refusée
# à 16,8 Mo, alors que ffmpeg décode le même flux. Au-delà, le HEIC est écrit en grille de tuiles, comme ceux de l'iPhone.
HEIC_SINGLE_MAX = 15_000_000        # octets : taille maximale gardée pour une image unique (marge de 10 % sous 16 Mio)
HEIC_TILE = 1024                    # côté des tuiles de la grille (multiple de 64 : un côté non aligné coûte +16 % de taille)
HEIC_GRID_PIXELS = 18_000_000       # HDR 10 bits sans perte : grille d'emblée au-delà de 18 Mpx (le flux dépasse alors presque
                                    # toujours 15 Mo ; mesuré : 20 Mo à 24 Mpx) ; une grille y coûte environ 1 % de plus


def _heic_encode(save, size, grid_first=False):
    """(octets HEIC, grille ?). save(tile) encode l'image (tile = 0 : image unique). Image unique tant que le flux tient
    sous HEIC_SINGLE_MAX ; sinon grille de tuiles HEIC_TILE x HEIC_TILE (les tuiles sont relues avec les mêmes contrôles).
    grid_first : grille d'emblée (évite d'encoder deux fois quand l'image unique est presque sûrement trop grosse)."""
    big = max(size) > HEIC_TILE
    if big and grid_first:
        return save(HEIC_TILE), True
    d = save(0)
    if big and len(d) > HEIC_SINGLE_MAX:
        return save(HEIC_TILE), True
    return d, False


def sdr_heic(c):
    q, chroma = _heic_params("sdr")

    def save(tile):
        buf = BytesIO()
        c.im.save(buf, "HEIF", quality=q, chroma=chroma, **({"tile_size": tile} if tile else {}), **c.meta)   # q = -1 : HEVC sans perte
        return buf.getvalue()

    d, tiled = _heic_encode(save, c.im.size)
    return d, lambda d: _check_heic_sdr(d, c, q, chroma, tiled)


def _check_heic_sdr(d, c, q, chroma, tiled=False):
    with Image.open(BytesIO(d)) as chk:                           # relu par libheif / libde265
        chk.load()
        if chk.size != c.im.size:
            raise ValueError(f"dimensions {chk.size} != {c.im.size}")
        if chk.info.get("bit_depth", 8) != 8:
            raise ValueError(f"profondeur {chk.info.get('bit_depth')} bits au lieu de 8")
        if c.icc and chk.info.get("icc_profile") != c.icc:
            raise ValueError("profil ICC absent ou altéré")
        _check_exif(c.exif, chk.info.get("exif"))
        psnr, mx = _diff(c.im, chk.convert("RGB"))
    if q == -1:
        if mx > 2:                                                # mesuré : 1 au plus sur les 16,7 millions de couleurs RGB
            raise ValueError(f"HEIC sans perte mais écart max {mx} niveaux")
    elif psnr is not None and psnr < P["min_psnr"]:
        raise ValueError(f"pixels trop éloignés de la source (PSNR {psnr:.1f} dB < {P['min_psnr']})")
    return (_fmt_diff(psnr, mx) + f", 8 bits {_chroma_txt(chroma)}" + (" sans perte (domaine YCbCr)" if q == -1 else "")
            + (f", grille de tuiles {HEIC_TILE}" if tiled else ""))


def hdr_heic(c):
    if not HEIC_HDR:
        raise HdrOff("HEIC_HDR = False : HEIC écrit en SDR")
    px = c.px                                                     # HdrSkip si imagecodecs / numpy absents
    q, chroma = _heic_params("hdr")
    u10 = px["u10"]
    h, w = u10.shape[:2]
    d16 = np.empty_like(u10)
    for y in range(0, h, 256):                                    # 10 bits -> 16 bits, poids forts alignés (comme libheif les attend)
        s = u10[y:y + 256]
        d16[y:y + 256] = (s << 6) | (s >> 4)
    img = pillow_heif.from_bytes("RGB;16", (w, h), d16.tobytes())
    del d16

    def save(tile):
        buf = BytesIO()
        img.save(buf, quality=q, chroma=chroma, bit_depth=10, color_primaries=9, transfer_characteristics=16,
                 matrix_coefficients=9, full_range_flag=1, **({"tile_size": tile} if tile else {}),
                 **({"exif": c.exif} if c.exif else {}))                                      # Rec.2020 / PQ / BT.2020 NCL
        return buf.getvalue()

    d, tiled = _heic_encode(save, (w, h), q == -1 and w * h > HEIC_GRID_PIXELS)
    return d, lambda d: _check_heic_hdr(d, c, q, chroma, tiled)


def _check_heic_hdr(d, c, q, chroma, tiled=False):
    f = pillow_heif.open_heif(BytesIO(d), convert_hdr_to_8bit=False)[0]
    nclx = f.info.get("nclx_profile") or {}
    got = tuple(nclx.get(k) for k in ("color_primaries", "transfer_characteristics", "matrix_coefficients", "full_range_flag"))
    if got != (9, 16, 9, 1):
        raise ValueError(f"étiquettes couleur HEIC {got} au lieu de (9, 16, 9, 1) = Rec.2020 / PQ / matrice 9, plage complète")
    ref = c.px["u10"]
    if f.info.get("bit_depth") != 10 or tuple(f.size) != (ref.shape[1], ref.shape[0]):
        raise ValueError(f"HEIC relu : {f.size}, {f.info.get('bit_depth')} bits (attendu {ref.shape[1]}x{ref.shape[0]}, 10 bits)")
    dec = np.frombuffer(f.data, dtype=np.uint16).reshape(f.size[1], -1)[:, :f.size[0] * 3].reshape(f.size[1], f.size[0], 3)
    if dec.max() > 1023:                                          # codes alignés sur les poids forts : on les ramène sur 10 bits
        dec = dec >> 6
    if q == -1:
        mx = _maxdiff(dec, ref)
        if mx > 2:
            raise ValueError(f"HEIC 10 bits sans perte mais écart max {mx} codes sur 1023")
        txt = "codes PQ identiques" if mx == 0 else f"écart max {mx} code{'s' if mx > 1 else ''} PQ sur 1023"
    else:
        psnr = _psnr_codes(dec, ref, 1023.0)
        if psnr < MIN_PSNR_PQ:
            raise ValueError(f"pixels HDR trop éloignés après encodage (PSNR PQ {psnr:.1f} dB < {MIN_PSNR_PQ})")
        txt = f"PSNR PQ {psnr:.1f} dB"
    _check_exif(c.exif, f.info.get("exif"))
    if c.jpeg is None:                                            # source HEIC (iPhone) : image SDR + carte de gain Apple (tmap)
        c.notes.append("heic: HEIC HDR (image SDR + carte de gain Apple) réécrit en HEVC 10 bits Rec.2020 / PQ : "
                       "la structure Apple (tmap) n'est pas conservée")
    return txt + f", 10 bits {_chroma_txt(chroma)}" + (f", grille de tuiles {HEIC_TILE}" if tiled else "")


def _check_jxl_transcode(d, c):
    if imagecodecs.jpegxl_decode_jpeg(d) != c.jpeg:
        raise ValueError("le JPEG d'origine n'est pas restitué octet pour octet")
    dec = imagecodecs.jpegxl_decode(d)
    if dec.ndim == 2 or (dec.ndim == 3 and dec.shape[2] == 1):    # JPEG en niveaux de gris
        dec = np.repeat(dec.reshape(dec.shape[0], dec.shape[1], 1), 3, axis=2)
    w, h = c.im.size
    if dec.dtype != np.uint8 or dec.ndim != 3 or dec.shape[:2] != (h, w) or dec.shape[2] < 3:
        raise ValueError(f"décodage inattendu : {dec.dtype} {dec.shape} (attendu {h}x{w}, orientation appliquée)")
    psnr, mx = _diff(c.im, Image.fromarray(dec[..., :3]))
    if psnr is not None and psnr < P["min_psnr"]:
        raise ValueError(f"rendu libjxl trop éloigné du décodage libjpeg (PSNR {psnr:.1f} dB < {P['min_psnr']})")
    if c.exif_orig:
        got = _jxl_read_exif(d) if _brotli_ok() else None
        if got is None:
            c.notes.append("jxl: EXIF non relu dans le JXL (codec brotli absent) ; le JPEG reste restitué octet pour octet")
        else:
            a, ao = _exif_tags(c.exif_orig)
            b, bo = _exif_tags(got)
            if a != b or ao != bo:
                raise ValueError("EXIF de la boîte Exif différent de celui du JPEG")
    return ("transcodage sans perte : JPEG restitué octet pour octet ; rendu libjxl vs libjpeg : "
            + _fmt_diff(psnr, mx))


def sdr_jxl_jpeg(c):
    """JPEG -> JXL. "transcode" : transcodage réversible (coefficients DCT recompressés, JPEG restitué à l'octet) ; en cas d'échec,
    voie pixels du préréglage. "auto" : JXL avec perte (voie pixels) seulement s'il est au moins JXL_LOSSY_MIN_SAVING plus
    petit que le transcodage, sinon transcodage : on ne perd pas de données pour gagner quelques pour cent."""
    mode, lossless = P["jxl_jpeg"], None
    if not HAS_HDR_ENC:
        c.notes.append("jxl: imagecodecs absent -> pas de transcodage sans perte, voie pixels")
    else:
        try:
            lossless = imagecodecs.jpegxl_encode_jpeg(c.jpeg)
        except Exception as e:
            c.notes.append(f"jxl: transcodage sans perte impossible ({type(e).__name__}: {e}) -> voie pixels")
    if lossless is not None and mode == "transcode":
        return lossless, lambda d: _check_jxl_transcode(d, c)
    n_notes, was_degraded = len(c.notes), c.degraded
    lossy = sdr_jxl(c)
    if lossless is not None and len(lossy[0]) > (1 - JXL_LOSSY_MIN_SAVING) * len(lossless):
        del c.notes[n_notes:]
        c.degraded = was_degraded
        return lossless, lambda d: _check_jxl_transcode(d, c)
    return lossy


# HEIC en entrée ; « heic » = même format que la source : recompression, produite seulement sur confirmation
SDR_ROUTES = {"jpg": sdr_jpg, "heic": sdr_heic, "jxl": sdr_jxl, "avif": sdr_avif}
HDR_ROUTES = {"jpg": hdr_jpg, "heic": hdr_heic, "jxl": hdr_jxl, "avif": hdr_avif}
# JPEG en entrée ; « jpg » = même format que la source (recompression, sur confirmation)
JPEG_SDR_ROUTES = {"heic": sdr_heic, "jpg": sdr_jpg, "jxl": sdr_jxl_jpeg, "avif": sdr_avif}
JPEG_HDR_ROUTES = {"heic": hdr_heic, "jpg": hdr_jpg, "jxl": hdr_jxl, "avif": hdr_avif}


def _make(route, c):
    data, check = route(c)
    return data, check(data)


def _sniff(src):
    """Type d'un fichier d'après son CONTENU (pas son extension) : 'heic' ou 'jpeg'."""
    with Image.open(src) as im:
        fmt = im.format
    if fmt == "HEIF":
        return "heic"
    if fmt in ("JPEG", "MPO"):
        return "jpeg"
    raise ValueError(f"format {fmt} non pris en charge (HEIC / HEIF et JPEG seulement)")


def _prepare_heic(src, im0, notes):
    """(Ctx, dégradé) d'un HEIC ouvert et chargé."""
    degraded = False
    im = im0
    if im0.mode != "RGB":
        im = im0.convert("RGB")
        im.info.update(im0.info)
        if "A" in im0.mode:
            notes.append("canal alpha abandonné (ni le JPEG ni les contrôles ne le gèrent)")
            degraded = True
    hs = None
    if HDR:
        try:
            hs = hdr_source(src, im)
        except NotHdr:
            pass
        except HdrSkip as e:
            notes.append(f"HDR non géré ({e}) -> sorties SDR")
            degraded = True
        except Exception as e:
            notes.append(f"HDR illisible ({type(e).__name__}: {e}) -> sorties SDR")
            degraded = True
    c = Ctx(im, hs, im.info.get("exif"), im.info.get("icc_profile"))
    bits = im.info.get("bit_depth", 8)
    if bits > 8:
        c.warn(f"source {bits} bits lue en 8 bits par pillow-heif : {bits - 8} bits de précision perdus à la lecture")
    nclx = im.info.get("nclx_profile")
    if nclx and not c.icc and nclx.get("color_primaries") not in (None, 1, 2):
        c.warn(f"étiquette couleur nclx (primaires {nclx.get('color_primaries')}) non gérée : traitée comme sRGB")
    return c, degraded


def _write_outputs(c, label, out, stem, errors, details, done, src=None, wanted=None):
    """Fabrique, contrôle puis écrit chaque format de sortie. wanted : formats à produire (par défaut HEIC en entrée : jpg, jxl,
    avif ; JPEG : heic, jxl, avif). Un format identique à celui de la source (recompression) n'y figure qu'après confirmation."""
    exts = wanted if wanted is not None else (HEIC_OUT if label == "heic" else JPEG_OUT)
    sdr_routes = SDR_ROUTES if label == "heic" else JPEG_SDR_ROUTES
    hdr_routes = HDR_ROUTES if label == "heic" else JPEG_HDR_ROUTES
    for ext in exts:
        if ext not in FORMATS:
            continue
        dest = out / ext / f"{stem}.{ext}"
        if src is not None and dest.exists() and os.path.samefile(dest, src):    # la sortie remplacerait la source elle-même
            errors.append(f"{ext}: la sortie ({dest}) est le fichier source : choisir un autre dossier de sortie")
            continue
        got, is_hdr = None, False
        if c.hs is not None:
            try:
                got, is_hdr = _make(hdr_routes[ext], c), True
            except HdrOff as e:
                c.notes.append(f"{ext}: {e}")
            except Exception as e:
                why = str(e) if isinstance(e, HdrSkip) else f"{type(e).__name__}: {e}"
                c.warn(f"{ext}: HDR NON produit ({why}) -> SDR")
        if got is None:
            try:
                got = _make(sdr_routes[ext], c)
            except Exception as e:
                errors.append(f"{ext}: {type(e).__name__}: {e}")
                continue
        data, summary = got
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        try:
            tmp.write_bytes(data)
            if tmp.stat().st_size != len(data):
                raise OSError("écriture incomplète")
            os.replace(tmp, dest)               # le fichier final n'existe jamais à moitié écrit
        except OSError as e:
            tmp.unlink(missing_ok=True)
            errors.append(f"{ext}: écriture impossible ({e})")
            continue
        details.append(f"{ext:<4} {len(data) / 1e6:6.1f} Mo  {'HDR' if is_hdr else 'SDR'}  {summary}")
        if is_hdr:
            done.append(ext)


# ----------------------------------------------------------------------------------------------
def _plain_error(e):
    """Message lisible pour les erreurs de lecture les plus courantes (les textes de Pillow sont en anglais)."""
    if type(e).__name__ == "UnidentifiedImageError":
        return "fichier illisible : ni HEIC ni JPEG valide (corrompu, ou autre format)"
    if isinstance(e, OSError) and "truncated" in str(e):
        return "fichier JPEG incomplet (tronqué) : lecture refusée plutôt que d'écrire une image à moitié décodée"
    return f"{type(e).__name__}: {e}"


def convert(job):
    """Renvoie (nom, erreur | None, type 'HDR'/'SDR', formats HDR produits, notes, dégradé, détails par format, source 'heic'/'jpeg').
    job = (fichier, dossier de sortie, nom de base[, formats à produire]) ; sans le 4e élément : les trois formats par défaut."""
    src, out, stem, *rest = job
    wanted = rest[0] if rest else None
    done, notes, details, errors, degraded, label = [], [], [], [], False, "?"
    try:
        label = _sniff(src)
        if label == "heic":
            with Image.open(src) as im0:
                im0.load()
                c, degraded = _prepare_heic(src, im0, notes)
                _write_outputs(c, label, out, stem, errors, details, done, src, wanted)
        else:
            raw = Path(src).read_bytes()
            with Image.open(BytesIO(raw)) as im0:
                im0.load()
                c, degraded = _prepare_jpeg(raw, im0, notes)
                _write_outputs(c, label, out, stem, errors, details, done, src, wanted)
        notes += c.notes
        degraded = degraded or c.degraded
        return (src.name, "; ".join(errors) or None, "HDR" if c.hs is not None else "SDR", done, notes, degraded, details, label)
    except Exception as e:  # un fichier en échec n'arrête pas les autres
        return src.name, _plain_error(e), "?", done, notes, degraded, details, label


def _mem_available_mb():
    """Mémoire disponible en Mo (Windows, Linux), ou None."""
    try:
        if os.name == "nt":
            import ctypes

            class MemStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("total_pf", ctypes.c_ulonglong),
                            ("avail_pf", ctypes.c_ulonglong), ("total_v", ctypes.c_ulonglong),
                            ("avail_v", ctypes.c_ulonglong), ("avail_ext", ctypes.c_ulonglong)]

            st = MemStatus()
            st.length = ctypes.sizeof(st)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return int(st.avail // 2 ** 20)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) // 1024
    except Exception:
        pass
    return None


def _preset_summary(label="heic", exts=None):
    """Une ligne qui décrit les réglages effectifs, pour un type de source et les formats de sortie demandés (par défaut :
    HEIC -> jpg, jxl, avif ; JPEG -> heic, jxl, avif)."""
    def jxl(d):
        return "sans perte" if d is None else f"distance {d:g}"

    def avif(which):
        level, chroma, lossless = _avif_params(which)
        if which == "sdr" and (P["avif_sdr"]["engine"] == "pillow"):
            return f"Pillow q{P['pillow_avif']['quality']}"
        return f"10 bits {chroma} " + ("sans perte" if lossless else f"niveau {level}")

    def heic(which):
        q, chroma = _heic_params(which)
        return ("sans perte" if q == -1 else f"q{q}") + f" {_chroma_txt(chroma)}"

    def both(sdr, hdr):
        return sdr if sdr == hdr else f"SDR {sdr} / HDR {hdr}"

    exts = exts or (HEIC_OUT if label == "heic" else JPEG_OUT)
    s, h = P["jxl_sdr_distance"], P["jxl_hdr_distance"]
    if label == "heic" or P["jxl_jpeg"] == "pixels":
        jx = both(jxl(s), jxl(h))
    elif P["jxl_jpeg"] == "transcode":
        jx = f"SDR transcodage sans perte du JPEG / HDR {jxl(h)}"
    else:
        jx = f"SDR transcodage sans perte, ou {jxl(s)} s'il est {JXL_LOSSY_MIN_SAVING:.0%} plus petit / HDR {jxl(h)}"
    sub = "4:4:4" if P["jpg"].get("subsampling") == 0 else "4:2:0"
    parts = {"jpg": f"jpg q{P['jpg']['quality']} {sub}", "heic": "heic " + both(heic("sdr"), heic("hdr")),
             "jxl": "jxl " + jx, "avif": "avif " + both(avif("sdr"), avif("hdr"))}
    return ", ".join(parts[e] for e in exts)


def _workers(files):
    """(nombre de processus, explication). Limité par les coeurs et par la mémoire : un encodage sans perte
    d'une photo coûte ~MO_PAR_MPX Mo par mégapixel, soit 1 à 2 Go pour 12 à 24 Mpx."""
    n = max(1, min(os.cpu_count() or 1, 4))
    avail = _mem_available_mb()
    if avail is None:
        return min(n, 2), "mémoire disponible inconnue"
    mpx = 12.0
    for f in files:
        try:
            with Image.open(f) as im:
                mpx = max(mpx, im.size[0] * im.size[1] / 1e6)
        except Exception:
            pass
    need = MO_PAR_MPX * mpx
    w = max(1, min(n, int(avail * 0.7 // need)))
    return w, f"~{need / 1024:.1f} Go par photo de {mpx:.0f} Mpx, {avail / 1024:.1f} Go libres"


HEIC_EXT = (".heic", ".heif")
JPEG_EXT = (".jpg", ".jpeg", ".jpe", ".jfif")


def _output_stems(files):
    """Nom de base des sorties : celui du fichier, sauf pour les homonymes (IMG_1.HEIC et IMG_1.jpg, par exemple), qui
    reçoivent le suffixe _<extension d'origine> : leurs sorties jxl / avif ne s'écrasent pas."""
    groups = {}
    for p in files:
        groups.setdefault(p.stem.lower(), []).append(p)
    stems, used = {}, set()
    for single in (True, False):                      # les noms uniques d'abord : un suffixe ne leur prend jamais leur nom
        for ps in groups.values():
            if (len(ps) == 1) != single:
                continue
            for p in ps:
                s = p.stem if single else f"{p.stem}_{p.suffix[1:].lower()}"
                base, k = s, 2
                while s.lower() in used:
                    s, k = f"{base}_{k}", k + 1
                used.add(s.lower())
                stems[p] = s
    return stems


USAGE = r"""Usage : python heic_jpeg_convert.py ["<dossier_source>" ["<dossier_sortie>"]] [-f formats] [-y]

  -f, --formats LISTE  formats de sortie : un ou plusieurs de heic, jpg, jxl, avif, séparés par des virgules (défaut : auto)
                         auto : HEIC -> jpg, jxl, avif ; JPEG -> heic, jxl, avif
                       Un format identique à celui de la source (heic pour un HEIC, jpg pour un JPEG) est une RECOMPRESSION,
                       pas une copie : une confirmation est demandée avant de convertir.
  -y, --yes, --oui     répond « oui » d'avance à cette confirmation (sans clavier : tâche planifiée, redirection)
  -h, --help, --aide   affiche ce message

Exemples :
  python heic_jpeg_convert.py "D:\Photos"                     tous les formats par défaut
  python heic_jpeg_convert.py "D:\Photos" -f jxl              JPEG XL seulement
  python heic_jpeg_convert.py "D:\Photos" -f heic,avif        HEIC (JPEG en entrée) et AVIF
  python heic_jpeg_convert.py "D:\Photos" -f jpg -y           HEIC -> JPG ; JPEG -> JPG recompressé, confirmé d'avance"""


def _parse_argv(argv):
    """(dossier_source | None, dossier_sortie | None, texte de la liste de formats | None, oui, aide). ValueError (français)."""
    pos, spec, yes, show_help, only_pos, it = [], [], False, False, False, iter(argv)
    for a in it:
        if only_pos or a == "-" or not a.startswith("-"):
            pos.append(a)
        elif a == "--":
            only_pos = True
        elif a in ("-h", "--help", "--aide"):
            show_help = True
        elif a in ("-y", "--yes", "--oui"):
            yes = True
        elif a in ("-f", "--formats", "--format"):
            v = next(it, None)
            if v is None or v.startswith("-"):
                raise ValueError(f"{a} attend une liste de formats, par exemple : {a} heic,jxl")
            spec.append(v)
        elif a.startswith(("--formats=", "--format=")):
            spec.append(a.split("=", 1)[1])
        elif a.startswith("-f") and not a.startswith("--"):
            spec.append(a[2:])                                    # -fheic,jxl
        else:
            raise ValueError(f"option inconnue : {a}")
    if len(pos) > 2:
        raise ValueError("trop d'arguments (dossier source, dossier de sortie) : " + " ".join(f'"{x}"' for x in pos))
    return (pos[0] if pos else None), (pos[1] if len(pos) > 1 else None), (",".join(spec) if spec else None), yes, show_help


def _same_format_warning(label, n):
    """Texte de la confirmation demandée quand la sortie demandée a le format de la source."""
    ext = SAME_FORMAT[label]
    name = ext.upper()
    if ext == "heic":
        q, chroma = _heic_params("sdr")
        how = f"HEVC {'sans perte' if q == -1 else 'q' + str(q)}, {_chroma_txt(chroma)}"
        loss = ("Le codage lui-même n'ajoute pas de perte (écart max 1 niveau mesuré), mais le fichier est plusieurs fois plus gros que la source."
                if q == -1 else "Cette recompression se fait avec perte : elle s'ajoute à celle de la source (« perte de génération »).")
        hdr = "Une photo HDR (image SDR + carte de gain Apple) devient du HEVC 10 bits Rec.2020 / PQ : la structure Apple n'est pas conservée."
    else:
        how = f"JPEG q{P['jpg']['quality']}, {'4:4:4' if P['jpg'].get('subsampling') == 0 else '4:2:0'}"
        loss = "Cette recompression se fait avec perte : elle s'ajoute à celle de la source (« perte de génération »)."
        hdr = "Un JPEG Ultra HDR garde sa carte de gain (recompressée) ; XMP, IPTC et commentaires ne sont pas conservés."
    return (f"\nFormat identique à la source : {n} fichier(s) {name} -> {name}.\n"
            f"  Ce n'est pas une copie : les pixels sont décodés puis recompressés ({how}).\n"
            f"  La source est déjà compressée avec perte, rien ne la restaure. {loss}\n"
            f"  {hdr}")


def _confirm_same_format(label, n, yes):
    """'oui' | 'non' | 'impossible' (pas de clavier : entrée standard redirigée, sans --yes)."""
    name = SAME_FORMAT[label].upper()
    print(_same_format_warning(label, n))
    if yes:
        print(f"  Confirmé d'avance (--yes) : {name} -> {name}.")
        return "oui"
    if not sys.stdin or not sys.stdin.isatty():
        print(f"  Confirmation impossible (pas de clavier) : sorties {name} -> {name} IGNORÉES. Ajouter --yes pour les confirmer d'avance.")
        return "impossible"
    try:
        answer = input(f"Convertir vraiment {n} fichier(s) {name} en {name} ? [o/N] ").strip().lower()
    except (EOFError, OSError):                                   # entrée fermée (sous Windows, NUL se déclare parfois comme un clavier)
        print(f"\n  Confirmation impossible (entrée fermée) : sorties {name} -> {name} IGNORÉES. Ajouter --yes pour les confirmer d'avance.")
        return "impossible"
    except KeyboardInterrupt:                                     # Ctrl+C : on arrête tout, on ne convertit rien
        print("\nInterrompu.")
        sys.exit(130)
    if answer in ("o", "oui", "y", "yes"):
        return "oui"
    print(f"  Refusé : sorties {name} -> {name} ignorées.")
    return "non"


def _kind(path):
    """Type d'un fichier d'après son contenu ('heic' | 'jpeg'), sinon d'après son extension (le fichier illisible sera signalé
    par la conversion elle-même)."""
    try:
        return _sniff(path)
    except Exception:
        return "heic" if path.suffix.lower() in HEIC_EXT else "jpeg"


if __name__ == "__main__":
    try:
        src_arg, out_arg, spec, yes, show_help = _parse_argv(sys.argv[1:])
    except ValueError as e:
        print(f"ERREUR : {e}\nAide : python heic_jpeg_convert.py --aide")
        sys.exit(2)
    if show_help:
        print(USAGE)
        sys.exit(0)
    src_dir = Path(src_arg) if src_arg else Path.cwd()
    out_dir = Path(out_arg) if out_arg else src_dir / "converti"
    if not src_dir.is_dir():
        print(f"ERREUR : dossier source introuvable : {src_dir}")
        sys.exit(2)
    try:
        selected, notices = parse_formats(spec if spec is not None else FORMATS_SORTIE)
    except ValueError as e:
        print(f"ERREUR : {'option --formats' if spec is not None else 'réglage FORMATS_SORTIE'} : {e}")
        sys.exit(2)
    for n in notices:
        print("NOTE :", n)
    files = sorted((p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() in HEIC_EXT + JPEG_EXT),
                   key=lambda p: p.name.lower())
    if not files:
        print(f"Aucun fichier HEIC / HEIF / JPEG dans {src_dir}")
        sys.exit(1)
    kind_of = {p: _kind(p) for p in files}
    by_type = {lab: [p for p in files if kind_of[p] == lab] for lab in ("heic", "jpeg")}
    names = {"heic": "HEIC", "jpeg": "JPEG"}
    plans, skipped, impossible = {}, {}, False
    for label in ("heic", "jpeg"):
        if not by_type[label]:
            continue
        exts = list(plan_outputs(label, selected))
        if SAME_FORMAT[label] in exts:                            # recompression : jamais sans confirmation
            answer = _confirm_same_format(label, len(by_type[label]), yes)
            if answer != "oui":
                exts.remove(SAME_FORMAT[label])
                skipped[label] = answer
                impossible |= answer == "impossible"
        plans[label] = tuple(exts)
    needed = {e for exts in plans.values() for e in exts}
    missing = {e: h for e, h in MISSING.items() if e in needed}
    for ext, hint in missing.items():
        print(f"ATTENTION : format {ext.upper()} indisponible -> IGNORÉ.\n"
              f"            Corriger avec : {hint}")
    if HDR and not HAS_HDR_ENC:
        print("ATTENTION : imagecodecs/numpy absents -> AVIF et JXL HDR impossibles (les fichiers HDR "
              f"seront écrits en SDR).\n            Corriger avec : {HDR_ENC_HINT}")
    stems = _output_stems(files)
    renamed = [p for p in files if stems[p] != p.stem]
    if renamed:
        print("Homonymes (même nom, extensions différentes) : sorties suffixées par l'extension d'origine : "
              + ", ".join(f"{p.name} -> {stems[p]}" for p in renamed))
    todo = [p for p in files if plans[kind_of[p]]]
    if not todo:
        print("Rien à convertir : aucun format de sortie retenu pour ces fichiers.")
        sys.exit(1 if impossible else 0)
    workers, why = _workers(todo)
    print(f"Fidélité « {FIDELITE} » ; {workers} processus ({why})")
    for label in ("heic", "jpeg"):
        if plans.get(label):
            print(f"  {names[label]} ({len(by_type[label])}) : {_preset_summary(label, plans[label])}")
        elif by_type[label]:
            print(f"  {names[label]} ({len(by_type[label])}) : ignorés (aucun format de sortie retenu)")
    failed = degraded_n = n_hdr = 0
    heic_hdr_written = False
    jobs = [(f, out_dir, stems[f], plans[kind_of[f]]) for f in todo]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for name, err, kind, done, notes, degraded, details, label in pool.map(convert, jobs):
            tag = f"[{kind}" + (f" : {' '.join(done)}" if done else "") + "]"
            print("OK    " if err is None else "ERREUR", name, err or tag)
            for line in details:
                print("          ", line)
            for n in notes:
                print("        ->", n)
            failed += err is not None
            degraded_n += degraded
            n_hdr += kind == "HDR" and not degraded
            heic_hdr_written |= "heic" in done
    parts = [f"{names[lab]} -> " + ", ".join(e for e in plans[lab] if e in FORMATS) for lab in ("heic", "jpeg") if plans.get(lab)]
    print(f"{len(todo) - failed}/{len(todo)} fichier(s) convertis et vérifiés ({' ; '.join(parts)}) -> {out_dir}")
    if len(todo) < len(files):
        print(f"{len(files) - len(todo)} fichier(s) ignorés : " + "; ".join(
            f"{names[lab]} (sortie de même format "
            f"{'refusée' if skipped[lab] == 'non' else 'non confirmée, pas de clavier'})" for lab in skipped if not plans[lab]))
    if HDR:
        print(f"HDR conservé dans tous les formats demandés : {n_hdr} fichier(s) ; repli ou perte signalés : {degraded_n}")
    if heic_hdr_written:
        print("NOTE : un HEIC HDR écrit par ce programme est du HEVC 10 bits Rec.2020 / PQ (HDR10). Affichage en HDR constaté sur un\n"
              "       iPhone (un seul appareil) ; non vérifié sur macOS / Windows : s'il est faux, mettre HEIC_HDR = False (HEIC SDR).")
    sys.exit(1 if failed or missing or degraded_n or impossible else 0)
