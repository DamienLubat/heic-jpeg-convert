# heic-jpeg-convert

**EN (summary).** A single-file Python command-line tool that converts HEIC/HEIF photos to JPEG, JPEG XL and AVIF, JPEG photos to HEIC, JPEG XL and AVIF, and PNG images to JPEG, HEIC, JPEG XL and AVIF, with minimal loss; PNG is also an output format (`-f png`). It keeps EXIF and colour profiles, and keeps HDR (iPhone HEIC gain maps, Ultra HDR JPEG) when the source is HDR. Transparency cannot be kept in the JPEG, HEIC, JXL and AVIF outputs: it is flattened onto a background colour, and reported. Every output is decoded again and checked before it is written. It runs locally and makes no network connection. The documentation below is in French; the program's messages are in French too.

---

Convertit **HEIC / HEIF → JPEG + JPEG XL + AVIF**, **JPEG → HEIC + JPEG XL + AVIF** et **PNG → JPEG + HEIC + JPEG XL + AVIF**, avec une perte minimale, l'EXIF conservé et le **HDR conservé** quand la source est HDR. Le **PNG** est aussi un format de sortie (`-f png`). Un seul fichier Python : [`heic_jpeg_convert.py`](heic_jpeg_convert.py).

Chaque sortie est **relue par un décodeur et contrôlée avant d'être écrite** (pixels, étiquettes couleur, EXIF, orientation ; pour le HDR : structure et métadonnées de la carte de gain).

## Sommaire

[Ce que fait le programme](#ce-que-fait-le-programme) · [Installation](#installation) · [Utilisation](#utilisation) · [Préréglages](#préréglages) · [HDR](#hdr) · [PNG](#png) · [Confidentialité](#confidentialité) · [Limites connues](#limites-connues) · [Tests](#tests) · [Versions testées](#versions-testées) · [Licences](#licences)

## Ce que fait le programme

| Source | Sorties par défaut | Remarque |
|---|---|---|
| HEIC / HEIF (`.heic`, `.heif`) | `jpg`, `jxl`, `avif` | HDR iPhone (image SDR + carte de gain) → sorties HDR |
| JPEG (`.jpg`, `.jpeg`, `.jpe`, `.jfif`) | `heic`, `jxl`, `avif` | JPEG « Ultra HDR » → sorties HDR ; JPEG ordinaire → SDR |
| PNG (`.png`) | `jpg`, `heic`, `jxl`, `avif` | toujours SDR ; transparence aplatie, 16 bits réduit à 8 : voir [PNG](#png) |

Le **PNG en sortie** n'est jamais un défaut : il se demande avec `-f png`, pour n'importe quelle source.

- Le type est lu dans le **contenu** du fichier, pas dans son extension.
- Un dossier de sortie par format : `<source>/converti/{jpg,heic,jxl,avif,png}/`.
- Les formats de sortie se choisissent avec `-f` (voir [Utilisation](#utilisation)). Une sortie **de même format que la source** (HEIC → HEIC, JPEG → JPG, PNG → PNG) est une *recompression* : elle demande une confirmation.
- JPEG → JXL est un **transcodage réversible** : le JPEG d'origine est restitué octet pour octet (contrôlé) dans un fichier plus petit.
- Plusieurs fichiers sont traités en parallèle ; le nombre de processus est limité par les cœurs et la mémoire disponible.

## Installation

Python 3.12 (version testée), puis :

```bash
python -m pip install -r requirements.txt
```

Dépendances : [Pillow](https://pypi.org/project/pillow/), [pillow-heif](https://pypi.org/project/pillow-heif/) (lecture/écriture HEIC, encodeur HEVC x265 inclus dans ses roues binaires), [imagecodecs](https://pypi.org/project/imagecodecs/) et [numpy](https://pypi.org/project/numpy/) (AVIF et JXL 10/16 bits, HDR).

`pillow-jxl-plugin` est **facultatif** (`requirements-optional.txt`) : sur 18 sorties JXL / AVIF comparées (3 préréglages, SDR et HDR), les fichiers étaient octet pour octet identiques avec ou sans lui ; il ajoute seulement une relecture de l'étiquette couleur des JXL SDR. Il est sous licence GPL (voir [Licences](#licences)).

Un format dont la bibliothèque manque (par exemple le HEIC sans encodeur HEVC) est **ignoré avec un avertissement** qui donne la commande à lancer, et le code retour est non nul.

## Utilisation

```text
python heic_jpeg_convert.py ["<dossier_source>" ["<dossier_sortie>"]] [-f formats] [-y]
```

Sans argument : convertit les HEIC, JPEG et PNG du dossier courant (sous-dossiers exclus).

```bash
python heic_jpeg_convert.py "D:\Photos"                    # formats par défaut
python heic_jpeg_convert.py "D:\Photos" -f jxl             # JPEG XL seulement
python heic_jpeg_convert.py "D:\Photos" -f heic,avif       # HEIC (pour les JPEG et les PNG) et AVIF
python heic_jpeg_convert.py "D:\Photos" -f png             # PNG (pour les HEIC et les JPEG ; PNG -> PNG sur confirmation)
python heic_jpeg_convert.py ~/Photos ~/Photos/sortie -f avif
python heic_jpeg_convert.py --aide
```

| Option | Effet |
|---|---|
| `-f`, `--formats LISTE` | un ou plusieurs de `heic`, `jpg`, `jxl`, `avif`, `png` (séparateurs : virgule, espace, `;`, `+`). `heif` = `heic`, `jpeg` = `jpg` ; `avi` est lu comme `avif`, avec un avis (AVI est un format vidéo). Sans option : formats par défaut. |
| `-y`, `--yes`, `--oui` | répond « oui » d'avance à la confirmation de recompression |
| `-h`, `--help`, `--aide` | aide |

**Recompression (même format que la source).** Avant de convertir, le programme demande « Convertir vraiment N fichier(s) X en X ? [o/N] » (non par défaut), une fois par type de source. Un refus n'abandonne que cette sortie. **Sans clavier** (entrée redirigée, tâche planifiée) et sans `-y`, ces sorties sont ignorées avec un avertissement et le code retour est 1. Une sortie ne remplace **jamais** le fichier source (erreur si les deux coïncident).

**Homonymes** (`IMG_1.HEIC` et `IMG_1.jpg` dans le même dossier) : leurs sorties reçoivent le suffixe `_<extension d'origine>` pour ne pas s'écraser. Relancer remplace les fichiers de sortie.

**Code retour** : `0` tout est bon ; `1` une conversion a échoué, un format manque, un repli (HDR → SDR, profil couleur converti) ou une sortie non confirmée est signalé, ou aucun fichier à convertir ; `2` erreur d'arguments ; `130` Ctrl+C.

**Réglages** en tête du fichier : `FIDELITE`, `FORMATS_SORTIE`, `AVIF_444`, `HEIC_444`, `HEIC_HDR`, `PNG_FOND`, `PNG_HDR`, `PNG_NIVEAU`, `HDR`, `JXL_LOSSY_MIN_SAVING` (détail dans l'en-tête du programme).

## Préréglages

Réglage `FIDELITE` en tête du programme : `"Lossless"` (défaut), `"minLossy"` ou `"Lossy"`.

| Préréglage | Principe | HEIC en entrée : taille / HEIC | JPEG en entrée : sorties |
|---|---|---|---|
| `Lossless` | sans perte quand le format le permet | 2,5 à 13 x | JXL transcodé ; AVIF 10 bits 4:4:4 niveau 100 ; HEIC HEVC sans perte |
| `minLossy` | perte minimale, taille raisonnable | 1,8 à 2,9 x | HEIC q90 ; AVIF 10 bits niveau 96 |
| `Lossy` | fichiers les plus petits | 0,45 à 1,4 x | HEIC q50 ; AVIF q65 |

Un JPEG ou un HEIC est **déjà compressé avec perte** : aucun préréglage ne peut le restaurer. « Sans perte » désigne la copie des pixels décodés de la source. Un JPEG de sortie ne peut jamais être sans perte (écart de quelques niveaux au plus).

Chiffres mesurés sur 5 photos d'iPhone HDR (12 et 24 Mpx) pour les HEIC en entrée (ΔE moyen de 0 à 0,6 en SDR et de 0,3 à 0,9 en HDR avec `minLossy` ; de 0,4 à 1,2 et de 1,1 à 2,4 avec `Lossy`), et sur 3 JPEG de 12 Mpx pour les JPEG en entrée. Ces photos ne sont pas dans ce dépôt. Tableaux complets, mesures des sorties de même format et limites : en-tête de [`heic_jpeg_convert.py`](heic_jpeg_convert.py).

## HDR

Règle : **source HDR → sorties HDR ; source SDR → sorties SDR.** La reconstruction part de l'image SDR et de la carte de gain (ISO 21496-1 ou XMP `hdrgm`) vers du Rec.2020 / PQ, blanc SDR à 203 nits.

| Sortie HDR | Format |
|---|---|
| `jpg` | JPEG « Ultra HDR » (SDR + carte de gain + MPF / XMP / ISO) |
| `avif` | AVIF 10 bits, Rec.2020 / PQ (HDR10) |
| `jxl` | JPEG XL 16 bits, PQ |
| `heic` | HEVC 10 bits, Rec.2020 / PQ (HDR10) |
| `png` | **seulement avec `PNG_HDR = True`** (défaut : `False`) : PNG 16 bits, Rec.2020 / PQ, balise cICP — voir [PNG](#png) |

Si la version HDR est impossible (bibliothèque absente, carte de gain d'un format non géré, erreur), le fichier est écrit **en SDR**, avec un message explicite et un code retour non nul.

## PNG

**PNG en entrée** : RVB, RVBA, gris, gris + alpha, palette, 1 bit ; 8 ou 16 bits par canal ; entrelacé ou non. Les sorties `jpg`, `heic`, `jxl` et `avif` reçoivent les pixels 8 bits décodés, avec les réglages du préréglage choisi, comme pour un HEIC ou un JPEG en SDR. Un PNG n'a pas de HDR.

| Cas | Ce que fait le programme |
|---|---|
| **Transparence** | `jpg`, `heic`, `jxl` et `avif` ne la gardent pas : elle est **aplatie sur un fond** (`PNG_FOND`, blanc par défaut), **signalé, code retour 1**. Un canal alpha entièrement opaque est ignoré sans signalement. |
| **16 bits par canal** | lu avec imagecodecs puis arrondi à 8 bits (v / 257) ; **signalé, code retour 1**. Sans imagecodecs (avec son codec PNG) : refusé, car Pillow lirait un PNG RVB 16 bits en 8 bits sans le dire. Un PNG 16 bits avec « couleur transparente » (bloc `tRNS`) est refusé. |
| **PNG animé (APNG)** | seule l'image par défaut est convertie ; signalé, code retour 1. |
| **Orientation EXIF** (bloc `eXIf`) | pixels tournés et étiquette à 1, comme pour un JPEG. La façon dont les visionneuses traitent l'orientation EXIF d'un PNG **n'a pas été vérifiée**. |
| **Couleurs** | profil ICC (`iCCP`) recopié (`jpg`, `heic`, `png`) ou converti en étiquette CICP (`avif`, `jxl`), comme pour un JPEG ; PNG sans profil : sRGB ; bloc `gAMA` ignoré (une note s'affiche s'il est loin de sRGB). Étiquette `cICP` : sRGB acceptée, autre étiquette SDR traitée comme sRGB (signalé), **PQ ou HLG refusé** (PNG HDR non lu : les couleurs seraient fausses). |

**PNG en sortie** (`-f png`) : 8 bits RVB, **sans perte**, relu et comparé pixel pour pixel à la source décodée. Profil ICC et EXIF recopiés ; une source PNG transparente garde son alpha (RVBA). Compression : `PNG_NIVEAU` (6 ; le niveau 9 donne des fichiers 1 à 2 % plus petits et environ 3 fois plus lents, mesuré sur 2 photos d'iPhone de 12 et 24 Mpx). Taille : environ 0,26 fois le volume brut non compressé (9,6 Mo et 19 Mo pour ces 2 photos). **Non conservés** : texte PNG (`tEXt`, `iTXt`, `zTXt`), XMP, résolution (`pHYs`) et EXIF stocké en texte (« Raw profile type exif », ImageMagick).

**PNG → PNG** est une recompression (sans perte pour les pixels 8 bits) : elle demande la confirmation décrite plus haut. Ce qui change : 16 bits → 8 bits, palette → RVB, canal alpha entièrement opaque supprimé, animation → image par défaut.

**Photo HDR → PNG** : par défaut (`PNG_HDR = False`) un PNG SDR 8 bits est écrit (le PNG n'a pas de carte de gain), avec une note. Avec `PNG_HDR = True`, un PNG **16 bits Rec.2020 / PQ** avec balise `cICP` (9 / 16 / 0 / 1) : mêmes codes PQ que le JXL HDR, relus et comparés à l'identique. Il est environ 5 fois plus gros (2 photos de 12 Mpx : 45 à 47 Mo contre 8 à 10 Mo en SDR). La structure a été relue par FFmpeg 6.1.1 (primaires Rec.2020, transfert SMPTE ST 2084, plage complète, pixels `rgb48be`) ; **affichage en HDR constaté sur un iPhone (app Photos), un seul appareil** ; non vérifié sur macOS, Windows ni dans d'autres visionneuses, et un lecteur qui ignore `cICP` affiche des couleurs fausses. D'où le défaut `False`.

## Confidentialité

- **Tout est local.** Le programme n'ouvre aucune connexion réseau, ne collecte ni n'envoie aucune donnée, ne lance aucun programme externe (hors ses propres processus de calcul parallèle) et n'exécute aucun code dynamique. Il lit les fichiers du dossier source et écrit uniquement dans le dossier de sortie (fichiers `.tmp` temporaires remplacés atomiquement). La seule lecture système est la mémoire disponible (`/proc/meminfo` sous Linux, `GlobalMemoryStatusEx` sous Windows) pour limiter le nombre de processus.
- Ces points sont vérifiés par des tests automatiques ([`tests/test_privacy.py`](tests/test_privacy.py)) : aucun module réseau ou de sous-processus importé, aucun `eval` / `exec` / `os.system`, aucune photo ni chemin personnel dans le dépôt. Ils ne remplacent pas la lecture du code : il fait un seul fichier.
- **L'EXIF est recopié tel quel dans les sorties, position GPS comprise.** Le programme n'a pas d'option pour le retirer : supprimez-le avec un outil dédié avant de partager une photo convertie.
- **Aucune photo dans ce dépôt.** Les tests fabriquent leurs images (dégradés avec bruit). Pour signaler un problème, **ne joignez pas de photo personnelle** (elle contient souvent la position GPS et la date) : décrivez le cas, ou joignez une image fabriquée.
- Le `.gitignore` exclut les formats d'image et le dossier `converti/` pour éviter d'en publier par erreur.

## Limites connues

- **Affichage** : le HEIC HDR écrit par ce programme (HEVC 10 bits PQ) a été constaté en HDR sur un iPhone, un seul appareil ; non vérifié sur macOS ni Windows (`HEIC_HDR = False` donne un HEIC SDR). L'AVIF 4:4:4 et le HEIC 4:4:4 n'ont pas été vérifiés sur toutes les visionneuses (`AVIF_444 = False`, `HEIC_444 = False` : repli en 4:2:0).
- **Ultra HDR** : testé sur des JPEG issus de HEIC d'iPhone et sur un fichier de Pixel (un seul) ; les autres appareils Android ne sont pas testés. Le HEIC HDR d'iPhone iOS 18+ est testé sur des photos réelles (non fournies) ; le test automatique correspondant est facultatif (voir [Tests](#tests)).
- **Non conservés** — HEIC en entrée : cartes auxiliaires Apple (style, ciel, peau, portrait, profondeur), miniatures, « Styles photographiques », XMP ; un HEIC 10 bits hors iPhone est lu en 8 bits (signalé). JPEG en entrée : XMP, IPTC et commentaires (sauf dans le JXL transcodé), images secondaires d'un MPO (signalé) ; un JPEG CMYK / YCCK est refusé. PNG en entrée : texte, XMP, résolution, EXIF écrit en texte, animation, transparence (sauf vers `png`), précision au-delà de 8 bits (sauf PNG HDR en sortie) : voir [PNG](#png).
- **PNG** : l'affichage d'un PNG HDR (`PNG_HDR = True`) a été constaté en HDR sur un iPhone (app Photos), un seul appareil ; il n'est pas vérifié ailleurs. Le traitement de l'orientation EXIF d'un PNG par les visionneuses n'est pas vérifié (voir [PNG](#png)). Un PNG 16 bits entrelacé fait afficher à libpng le message « Interlace handling should be turned on » : sans effet constaté sur les pixels (32 fichiers de 1 × 1 à 64 × 3 px fabriqués avec ImageMagick, hors suite de tests, et 4 fabriqués à la main dans les tests : tous décodés à l'identique des échantillons d'origine).
- **Profil ICC autre que sRGB / Display P3** : gardé dans JPEG, HEIC et AVIF ; le JXL en pixels est converti en sRGB (signalé, code retour non nul).
- **Images très grandes (sorties HEIC)** : le décodeur libde265 de pillow-heif refuse une image HEVC unique de plus de 16 Mio ; au-delà de 15 Mo de flux, le programme écrit donc une grille de tuiles de 1024 px (structure des HEIC d'iPhone).
- **Mémoire** : un encodage sans perte coûte de l'ordre de 1 à 2 Go par photo de 12 à 24 Mpx.
- Pas de traitement récursif des sous-dossiers, pas d'interface graphique ; les fichiers vidéo (dont la partie vidéo des Live Photos) ne sont pas traités.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Les tests n'utilisent **que des images fabriquées** (formats et arguments, conversions SDR dans les quatre formats, PNG en entrée et en sortie — types de couleur, transparence, 16 bits, entrelacé, APNG, EXIF, cICP —, JPEG Ultra HDR synthétique et variante XMP seul, EXIF avec rationnel 0/0, refus d'écraser la source, ligne de commande, garde-fous de confidentialité). Ils durent une douzaine de secondes. Le test de confirmation au clavier utilise un pseudo-terminal et est ignoré sous Windows.

Test facultatif sur un vrai HEIC HDR d'iPhone (image SDR + carte de gain Apple), à fournir soi-même :

```bash
HJC_TEST_HEIC_HDR=/chemin/IMG_0001.HEIC python -m pytest tests/test_hdr.py     # PowerShell : $env:HJC_TEST_HEIC_HDR="C:\...\IMG_0001.HEIC"
```

## Versions testées

| Composant | Versions |
|---|---|
| Python | 3.12 |
| Pillow | 11.1.0 et 13.0.0 (suite de tests complète dans les deux) |
| pillow-heif | 1.8.1 (libheif 1.23.6, libde265 1.1.3, x265 4.3) |
| imagecodecs | 2026.10.10 |
| numpy | 2.5.4 |
| pillow-jxl-plugin (facultatif) | 1.3.8 |

Systèmes : Linux (suite de tests), Windows (programme exécuté sous Wine avec Python 3.12 pour Windows, et utilisé sur un PC Windows). Les versions plus anciennes et les autres versions de Python ne sont pas testées.

## Licences

Ce projet : copyright © 2026 DamienLubat, licence **GNU GPL version 3 ou ultérieure** (`GPL-3.0-or-later`, texte complet dans [`LICENSE`](LICENSE)). Elle autorise l'usage, la modification et la redistribution, y compris commerciales, mais quiconque distribue une version modifiée, ou un programme qui l'incorpore, doit la distribuer sous la même licence avec ses sources : une version fermée n'est pas permise.

Dépendances, d'après les métadonnées des paquets installés et le fichier `LICENSES_bundled.txt` de pillow-heif 1.8.1 :

| Paquet | Licence déclarée |
|---|---|
| Pillow | MIT-CMU |
| pillow-heif | code source BSD-3-Clause ; **roues binaires : GPLv2**, à cause des bibliothèques embarquées (libheif et libde265 : LGPLv3 ; x265 : GPLv2) |
| imagecodecs | BSD-3-Clause (les composants embarqués ont chacun leur licence, dans le paquet) |
| numpy | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pillow-jxl-plugin (facultatif) | GPL-3.0-or-later |

Ce dépôt **ne redistribue aucune de ces bibliothèques** : l'utilisateur les installe lui-même avec `pip`. Les conditions de licence de ce qu'il installe lui incombent. Ce qui suit n'est pas un avis juridique.

- **HEVC / x265** : le HEIC repose sur le codec HEVC (H.265), lu et encodé par des bibliothèques embarquées dans les roues de pillow-heif (libde265, x265), pas par ce dépôt. La documentation de x265 indique que sa licence (GPL v2 ou licence commerciale) régit le code source mais **ne couvre pas les brevets** : l'utilisateur est responsable des licences de brevets nécessaires à l'usage ou à la distribution d'applications construites avec x265 ([x265, mentions légales](https://x265.readthedocs.io/en/stable/introduction.html)). Les implications éventuelles pour votre usage ne sont pas évaluées ici.
- **Compatibilité** entre la GPL-3.0-or-later de ce projet et les licences des dépendances ci-dessus (dont « GPLv2 » pour les roues de pillow-heif) : non évaluée. Ce dépôt ne redistribue pas ces bibliothèques.
- Ces licences sont celles des versions listées dans [Versions testées](#versions-testées) ; relire les licences si vous changez de version.
