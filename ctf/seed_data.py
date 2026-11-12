"""Contenu de démarrage : défis débutants entièrement hors ligne et parcours associés.

Chaque énoncé est généré à partir du flag, ce qui garantit que tous les défis sont résolubles.
Pour ajouter tes propres défis, passe plutôt par l'interface d'administration (/admin/).
"""
import base64
import io
import struct
import zipfile
import zlib


# ---------------------------------------------------------------- outils
def caesar(text, shift):
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def xor_hex(text, key):
    return bytes(b ^ key for b in text.encode()).hex()


def png_with_text(keyword, value, size=48):
    """PNG uni (orange) contenant un champ texte dans ses métadonnées."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes([255, 165, 74]) * size for _ in range(size))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"tEXt", keyword.encode("latin-1") + b"\x00" + value.encode("latin-1"))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------- catégories
CATEGORIES = [
    ("Découverte", "decouverte", "intro", "Pour prendre en main la plateforme.", 0),
    ("Crypto", "crypto", "crypto", "Encodages, chiffrements classiques et modernes.", 1),
    ("Web", "web", "web", "Failles des sites et des applications web.", 2),
    ("Forensics", "forensics", "foren", "Analyse de fichiers, de disques et de traces.", 3),
    ("Réseau", "reseau", "net", "Captures de trafic et protocoles.", 4),
    ("Stégano", "stegano", "steg", "Messages cachés dans des images, des sons, des textes.", 5),
    ("Reverse", "reverse", "rev", "Comprendre un programme sans son code source.", 6),
]

# ---------------------------------------------------------------- défis
F_WELCOME = "BRCH{b13nv3nu3_sur_br3ch3}"
F_CAESAR = "BRCH{l3_d3c4l4g3_d3_tr0is}"
F_B64 = "BRCH{3nc0d3r_n3st_p4s_chiffr3r}"
F_HEX = "BRCH{h3x4_c_3st_s1mpl3}"
F_XOR = "BRCH{x0r_un_s3ul_0ct3t}"
F_SOURCE = "BRCH{l3_c0d3_s0urc3_p4rl3}"
F_ZIP = "BRCH{n3_cr01s_p4s_l3xt3ns10n}"
F_META = "BRCH{l3s_m3t4d0nn33s_b4v4rd3nt}"
F_BASIC = "BRCH{b4s1c_4uth_3n_cl41r}"
F_ACRO = "BRCH{cachette}"
F_REV = "BRCH{l1r3_4_l3nv3rs}"

ACROSTIC = """Chaque soir, le serveur ronronne en silence,
Attendant qu'un visiteur trouve enfin la faille,
Cachée sous des lignes d'apparence anodine.
Hors de vue pour qui lit trop vite,
Elle patiente au tout début de chaque vers.
Tu n'as qu'à regarder la première lettre,
Tout en haut, puis en descendant,
Et le secret t'apparaîtra en entier."""

SOURCE_HTML = f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Intranet · connexion</title></head>
<body>
  <h1>Intranet de la société Krypton</h1>
  <!-- TODO (Kevin) : retirer avant la mise en production -->
  <!-- identifiants de test : admin / admin -->
  <form id="login">
    <input name="user" placeholder="Utilisateur"><input name="pass" type="password" placeholder="Mot de passe">
    <button>Entrer</button>
  </form>
  <script>
    // Le flag est découpé pour ne pas être trouvé par une simple recherche de "BRCH"
    const morceaux = {[p for p in [F_SOURCE[:7], F_SOURCE[7:15], F_SOURCE[15:]]]!r};
    console.log("debug :", morceaux.join(""));
  </script>
</body>
</html>
"""

REV_SCRIPT = f'''#!/usr/bin/env python3
"""Coffre-fort numérique v0.1 : seul le bon mot de passe ouvre le coffre."""

SECRET = "{F_REV[::-1]}"


def verifier(mot_de_passe: str) -> bool:
    return mot_de_passe[::-1] == SECRET


if __name__ == "__main__":
    essai = input("Mot de passe : ")
    print("Coffre ouvert !" if verifier(essai) else "Accès refusé.")
'''

HTTP_CAPTURE = f"""# Extrait d'une capture réseau (trafic HTTP non chiffré, port 80)
GET /admin/ HTTP/1.1
Host: intranet.krypton.local
User-Agent: Mozilla/5.0 (X11; Linux x86_64) Firefox/131.0
Accept: text/html

HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Zone admin"

GET /admin/ HTTP/1.1
Host: intranet.krypton.local
User-Agent: Mozilla/5.0 (X11; Linux x86_64) Firefox/131.0
Authorization: Basic {base64.b64encode(f"admin:{F_BASIC}".encode()).decode()}
Accept: text/html

HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
"""

CHALLENGES = [
    {
        "slug": "bienvenue", "title": "Bienvenue à bord", "cat": "decouverte", "difficulty": 1, "points": 10,
        "flag": F_WELCOME, "author": "Brèche",
        "description": (
            "Bienvenue sur Brèche !\n\n"
            "Sur cette plateforme, chaque défi cache un **flag** : une chaîne de caractères au format "
            "`BRCH{...}`. Quand tu le trouves, tu le colles dans le champ en bas de la page et tu gagnes les points.\n\n"
            f"Pour ce premier défi, pas de piège : voici ton flag.\n\n```\n{F_WELCOME}\n```\n\n"
            "Copie-le exactement, accolades comprises, puis valide."
        ),
        "hints": [],
    },
    {
        "slug": "cesar-en-vacances", "title": "César en vacances", "cat": "crypto", "difficulty": 1, "points": 50,
        "flag": F_CAESAR, "author": "Brèche",
        "description": (
            "Un espion romain a laissé ce message sur un forum. Il paraît que Jules César utilisait la même "
            f"méthode pour écrire à ses généraux.\n\n```\n{caesar(F_CAESAR, 3)}\n```\n\n"
            "Le format du flag (`BRCH{...}`) te donne un sacré coup de pouce."
        ),
        "hints": [("Compare les quatre premières lettres du message avec `BRCH`. De combien de positions sont-elles décalées dans l'alphabet ?", 0),
                  ("Décalage de 3. Recule chaque lettre de 3 positions (E → B, U → R…). Les chiffres et symboles ne bougent pas.", 15)],
    },
    {
        "slug": "base64", "title": "Ceci n'est pas du chiffrement", "cat": "crypto", "difficulty": 1, "points": 50,
        "flag": F_B64, "author": "Brèche",
        "description": (
            "Un développeur affirme avoir « chiffré » le mot de passe de la base de données dans le fichier de configuration :\n\n"
            f"```\nDB_PASSWORD={base64.b64encode(F_B64.encode()).decode()}\n```\n\n"
            "Est-ce vraiment protégé ?"
        ),
        "hints": [("Les caractères utilisés (A–Z, a–z, 0–9, + et /) et la longueur multiple de 4 sont typiques d'un encodage très courant.", 0),
                  ("C'est du Base64. Dans un terminal : `echo 'la_chaine' | base64 -d`, ou la recette « From Base64 » de CyberChef.", 15)],
    },
    {
        "slug": "hexadecimal", "title": "Seize symboles", "cat": "crypto", "difficulty": 1, "points": 50,
        "flag": F_HEX, "author": "Brèche",
        "description": (
            "Ce message a été intercepté dans la mémoire d'un programme :\n\n"
            f"```\n{' '.join(F_HEX.encode().hex()[i:i+2] for i in range(0, len(F_HEX) * 2, 2))}\n```\n\n"
            "Chaque paire de caractères représente un octet."
        ),
        "hints": [("Seuls les chiffres 0–9 et les lettres a–f apparaissent : c'est de l'hexadécimal. `42` en hexadécimal vaut 66, le code ASCII de la lettre B.", 10)],
    },
    {
        "slug": "xor-un-octet", "title": "XOR à un octet", "cat": "crypto", "difficulty": 2, "points": 150,
        "flag": F_XOR, "author": "Brèche",
        "description": (
            "Le flag a été chiffré en appliquant un XOR avec **une seule clé d'un octet** (une valeur entre 0 et 255) "
            f"sur chacun de ses caractères. Voici le résultat en hexadécimal :\n\n```\n{xor_hex(F_XOR, 0x2A)}\n```\n\n"
            "Retrouve la clé, puis le flag."
        ),
        "hints": [("Il n'y a que 256 clés possibles : tu peux toutes les essayer avec une petite boucle en Python.", 10),
                  ("Encore plus rapide : tu sais que le texte clair commence par `B` (0x42). Or `chiffré XOR clair = clé`.", 30)],
    },
    {
        "slug": "code-source", "title": "Regarde sous le capot", "cat": "web", "difficulty": 1, "points": 50,
        "flag": F_SOURCE, "author": "Brèche",
        "description": (
            "Nous avons récupéré la page de connexion de l'intranet d'une entreprise. "
            "Les développeurs ont-ils laissé traîner quelque chose ?\n\n"
            "Télécharge le fichier et lis-le attentivement. Tu peux aussi l'ouvrir dans ton navigateur "
            "et utiliser les outils de développement (touche <kbd>F12</kbd>)."
        ),
        "files": {"index.html": SOURCE_HTML.encode()},
        "hints": [("Regarde les commentaires HTML et le script en bas de page.", 0),
                  ("Le flag est découpé en trois morceaux dans une variable JavaScript. Recolle-les, ou ouvre la page et regarde la console (F12).", 10)],
    },
    {
        "slug": "mauvaise-extension", "title": "Photo de vacances", "cat": "forensics", "difficulty": 1, "points": 75,
        "flag": F_ZIP, "author": "Brèche",
        "description": (
            "Un suspect a envoyé cette « photo de vacances » à un complice. "
            "Impossible de l'ouvrir avec une visionneuse d'images… bizarre.\n\n"
            "Que contient vraiment ce fichier ?"
        ),
        "files": {"vacances.jpg": zip_bytes({"flag.txt": F_ZIP + "\n", "a_lire.txt": "Rendez-vous mardi, quai n°3.\n"})},
        "hints": [("L'extension d'un fichier n'est qu'une partie de son nom. Sous Linux, la commande `file vacances.jpg` lit son vrai type.", 0),
                  ("Les deux premiers octets sont `PK` : c'est une archive ZIP. Renomme-la en `.zip` et extrais-la.", 20)],
    },
    {
        "slug": "metadonnees", "title": "Image bavarde", "cat": "forensics", "difficulty": 1, "points": 100,
        "flag": F_META, "author": "Brèche",
        "description": (
            "Cette image orange n'a rien d'intéressant à l'œil nu. Mais les fichiers en disent souvent plus "
            "que ce qu'ils montrent."
        ),
        "files": {"logo.png": png_with_text("Author", F_META)},
        "hints": [("Les images contiennent des **métadonnées** : auteur, logiciel, date, position GPS…", 0),
                  ("`exiftool logo.png`, ou simplement `strings logo.png`.", 20)],
    },
    {
        "slug": "authentification-basique", "title": "Mot de passe en transit", "cat": "reseau", "difficulty": 2, "points": 100,
        "flag": F_BASIC, "author": "Brèche",
        "description": (
            "L'équipe de sécurité a capturé le trafic d'un administrateur qui se connecte à l'intranet "
            "**sans HTTPS**. Retrouve son mot de passe : c'est le flag."
        ),
        "files": {"capture_http.txt": HTTP_CAPTURE.encode()},
        "hints": [("Repère l'en-tête `Authorization` envoyé par le navigateur.", 0),
                  ("L'authentification « Basic » envoie `utilisateur:motdepasse` encodé en Base64. Encodé, pas chiffré !", 20)],
    },
    {
        "slug": "acrostiche", "title": "Poème du serveur", "cat": "stegano", "difficulty": 1, "points": 50,
        "flag": F_ACRO, "author": "Brèche",
        "description": (
            "Un administrateur système poète a laissé ce texte dans le fichier `motd` du serveur.\n\n"
            + "\n".join("> " + l for l in ACROSTIC.splitlines()) + "\n\n"
            "Le flag est le mot caché, **en minuscules**, au format `BRCH{mot}`."
        ),
        "hints": [("Le poème lui-même te dit où regarder.", 10)],
    },
    {
        "slug": "coffre-fort", "title": "Coffre-fort à l'envers", "cat": "reverse", "difficulty": 1, "points": 75,
        "flag": F_REV, "author": "Brèche",
        "description": (
            "Ce petit programme Python protège un coffre-fort numérique. "
            "Trouve le mot de passe qui l'ouvre : c'est le flag.\n\n"
            "Lancer le programme n'est pas nécessaire, lire son code suffit."
        ),
        "files": {"coffre.py": REV_SCRIPT.encode()},
        "hints": [("En Python, `texte[::-1]` renvoie le texte à l'envers.", 10)],
    },
]

# ---------------------------------------------------------------- parcours
PATHS = [
    {
        "slug": "bases-du-ctf", "title": "Bases du CTF", "level": "debutant", "color": "intro", "order": 0,
        "summary": "Comprendre ce qu'est un CTF, distinguer encodage et chiffrement, et installer ta boîte à outils.",
        "lessons": [
            ("quest-ce-quun-ctf", "Qu'est-ce qu'un CTF ?", 6, "bienvenue", """
Un **CTF** (*Capture The Flag*) est une compétition de sécurité informatique. Les organisateurs préparent des défis volontairement vulnérables : un site web mal protégé, un fichier qui cache un secret, un programme à décortiquer. Ton objectif est de trouver le **flag**, une chaîne de caractères qui prouve que tu as résolu le défi.

Sur Brèche, tous les flags ont la même forme :

```
BRCH{quelque_chose_ici}
```

## Les grandes catégories

| Catégorie | Ce qu'on y fait |
|---|---|
| Web | Trouver des failles dans des sites (injections, cookies, mauvaises configurations) |
| Crypto | Casser des chiffrements mal utilisés |
| Forensics | Analyser des fichiers, des disques, des captures pour retrouver des traces |
| Réseau | Lire du trafic réseau intercepté |
| Stégano | Retrouver un message caché dans une image, un son ou un texte |
| Reverse | Comprendre ce que fait un programme sans avoir son code source |

## Les règles du jeu

- Ne partage pas les flags : le plaisir vient de la recherche.
- N'attaque que les défis de la plateforme, jamais l'infrastructure elle-même ni d'autres sites.
- Les indices sont là pour t'aider. Certains coûtent quelques points, c'est normal d'en utiliser.

> Les techniques apprises ici ne s'utilisent que sur des systèmes pour lesquels tu as une autorisation explicite. En dehors de ce cadre, c'est illégal (en France, articles 323-1 et suivants du Code pénal).

Prêt ? Ton premier flag t'attend dans le défi ci-dessous.
"""),
            ("encoder-nest-pas-chiffrer", "Encoder n'est pas chiffrer", 10, "base64", """
Deux mots qu'on confond souvent, et c'est la source de nombreuses failles.

- **Encoder**, c'est changer la représentation d'une donnée pour la transporter ou la stocker. Il n'y a **aucun secret** : tout le monde peut décoder.
- **Chiffrer**, c'est rendre une donnée illisible sans une **clé** secrète.

## Les encodages à reconnaître au premier coup d'œil

**Hexadécimal** : seulement `0-9` et `a-f`, souvent par paires.
```
42 52 43 48   →   B R C H
```

**Base64** : lettres, chiffres, `+` et `/`, longueur multiple de 4, parfois terminé par `=` ou `==`.
```
QlJDSA==   →   BRCH
```

**Binaire** : des 0 et des 1 par groupes de 8.
```
01000010   →   B
```

## Décoder en ligne de commande

```
echo 'QlJDSA==' | base64 -d
echo '42524348' | xxd -r -p
```

L'outil en ligne **CyberChef** fait tout ça, et bien plus, avec des « recettes » que l'on enchaîne. Garde-le dans tes favoris.

Si quelqu'un te dit qu'un mot de passe est « protégé en Base64 », il ne l'est pas du tout. Le défi suivant le prouve.
"""),
            ("boite-a-outils", "Ta boîte à outils", 12, "mauvaise-extension", """
Pas besoin d'un équipement sophistiqué pour débuter. Voici l'essentiel.

## Un terminal Linux

Sous Windows, installe **WSL** (Ubuntu). Sous macOS, le Terminal suffit pour commencer. Quelques commandes que tu utiliseras tout le temps :

| Commande | Rôle |
|---|---|
| `file fichier` | Donne le vrai type d'un fichier, quelle que soit son extension |
| `strings fichier` | Affiche tout le texte lisible caché dans un fichier |
| `xxd fichier` | Montre le contenu octet par octet, en hexadécimal |
| `unzip`, `tar -xf` | Extraire des archives |
| `grep -r BRCH .` | Chercher un motif dans tous les fichiers d'un dossier |

## Les signatures de fichiers

Un fichier commence presque toujours par quelques octets qui trahissent son type, les **magic bytes** :

| Début du fichier | Type |
|---|---|
| `FF D8 FF` | JPEG |
| `89 50 4E 47` (`.PNG`) | PNG |
| `50 4B 03 04` (`PK`) | ZIP (et aussi .docx, .apk, .jar…) |
| `25 50 44 46` (`%PDF`) | PDF |
| `7F 45 4C 46` (`.ELF`) | Programme Linux |

L'extension (`.jpg`, `.txt`) n'est qu'une partie du nom, librement modifiable. C'est le contenu qui compte.

## Un navigateur et ses outils de développement

La touche <kbd>F12</kbd> ouvre l'inspecteur : code HTML, requêtes réseau, cookies, console JavaScript. C'est l'outil n°1 des défis web.
"""),
            ("code-source", "Lire le code source d'une page", 8, "code-source", """
Tout ce que ton navigateur affiche, il l'a d'abord **téléchargé**. Le code HTML, CSS et JavaScript d'une page est donc entre tes mains, y compris ce que le développeur aurait préféré cacher.

## Où regarder

- **Afficher le code source** : <kbd>Ctrl</kbd>+<kbd>U</kbd>. Cherche les commentaires `<!-- ... -->`, souvent oubliés.
- **L'inspecteur** (<kbd>F12</kbd>) : montre la page telle qu'elle est après l'exécution du JavaScript, y compris les éléments masqués.
- **La console** : affiche les messages de débogage laissés par les développeurs.
- **Les fichiers .js** : la logique « secrète » d'une page (vérification de mot de passe côté client, clés d'API…) s'y trouve souvent en clair.

## La leçon à retenir

Une vérification faite uniquement dans le navigateur n'est jamais une protection : le visiteur peut lire et modifier le code. Toute vérification de sécurité doit se faire **côté serveur**.
"""),
        ],
    },
    {
        "slug": "cryptographie-premiers-pas", "title": "Cryptographie : premiers pas", "level": "debutant", "color": "crypto", "order": 1,
        "summary": "Des chiffrements de l'Antiquité au XOR, et pourquoi une clé trop petite ne protège rien.",
        "lessons": [
            ("chiffre-de-cesar", "Le chiffre de César", 8, "cesar-en-vacances", """
Le chiffre de César décale chaque lettre d'un nombre fixe de positions dans l'alphabet. Avec un décalage de 3 :

```
A B C D E F G ...
↓ ↓ ↓ ↓ ↓ ↓ ↓
D E F G H I J ...
```

`BRCH` devient `EUFK`. Pour déchiffrer, on décale dans l'autre sens.

## Pourquoi c'est faible

Il n'existe que **25 décalages possibles**. On peut tous les essayer à la main en quelques minutes : c'est une **attaque par force brute**.

Encore plus rapide : si tu connais un morceau du texte clair (ici, le début `BRCH{`), tu peux calculer le décalage directement. C'est une **attaque à texte clair connu**, et elle marche contre beaucoup de chiffrements faibles.

## Pour aller plus loin

Le ROT13 est un César de décalage 13 : l'appliquer deux fois redonne le texte d'origine. Le chiffre de **Vigenère** utilise un décalage différent pour chaque lettre, selon un mot-clé.
"""),
            ("hexadecimal-ascii", "Octets, ASCII et hexadécimal", 10, "hexadecimal", """
Un ordinateur ne manipule que des nombres. Pour stocker du texte, on associe un nombre à chaque caractère : c'est la table **ASCII**.

| Caractère | Décimal | Hexadécimal | Binaire |
|---|---|---|---|
| `B` | 66 | 42 | 01000010 |
| `R` | 82 | 52 | 01010010 |
| `{` | 123 | 7b | 01111011 |
| `0` | 48 | 30 | 00110000 |

L'**hexadécimal** (base 16) utilise 16 symboles : `0-9` puis `a-f`. Un octet (8 bits, de 0 à 255) s'écrit toujours avec exactement 2 chiffres hexadécimaux, de `00` à `ff`. C'est pour ça qu'on le retrouve partout : dumps mémoire, captures réseau, couleurs CSS (`#ff8800`)…

## En Python

```
>>> "BRCH".encode().hex()
'42524348'
>>> bytes.fromhex("42524348").decode()
'BRCH'
```
"""),
            ("le-xor", "Le XOR", 12, "xor-un-octet", """
Le **XOR** (ou exclusif, noté `^` en Python) compare deux bits : le résultat vaut 1 s'ils sont différents, 0 s'ils sont identiques.

| a | b | a XOR b |
|---|---|---|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

## La propriété magique

Appliquer deux fois la même clé annule l'opération :

```
clair  XOR clé = chiffré
chiffré XOR clé = clair
```

Et donc : `chiffré XOR clair = clé`. Si tu connais un seul octet du texte clair, tu retrouves l'octet de clé correspondant.

## Force brute en Python

Une clé d'un seul octet n'a que 256 valeurs possibles :

```
data = bytes.fromhex("...")
for k in range(256):
    essai = bytes(b ^ k for b in data)
    if essai.startswith(b"BRCH"):
        print(k, essai)
```

Le XOR est au cœur de presque tous les chiffrements modernes (AES, ChaCha20). Il est sûr quand la clé est aussi longue que le message, aléatoire et jamais réutilisée (c'est le **masque jetable**). Avec une clé courte et répétée, il se casse très facilement.
"""),
        ],
    },
    {
        "slug": "forensics-premiers-pas", "title": "Forensics : premiers pas", "level": "debutant", "color": "foren", "order": 2,
        "summary": "Faire parler les fichiers : métadonnées, contenu caché et trafic réseau intercepté.",
        "lessons": [
            ("metadonnees", "Les métadonnées", 8, "metadonnees", """
Les **métadonnées** sont des données sur les données. Une photo prise avec un téléphone peut contenir :

- le modèle de l'appareil ;
- la date et l'heure exactes ;
- les **coordonnées GPS** du lieu de la prise de vue ;
- le logiciel utilisé pour la retoucher, le nom de l'auteur.

Les documents bureautiques (Word, PDF) contiennent aussi le nom de l'auteur, l'historique de modification, parfois le nom de l'ordinateur.

## Les outils

- `exiftool fichier` : l'outil de référence, il lit presque tous les formats.
- `strings fichier` : plus brutal, il sort tout le texte lisible.

## Côté défense

Avant de publier une photo ou un document, supprime ses métadonnées. En enquête (OSINT, investigation), c'est souvent par là qu'on commence.
"""),
            ("trafic-reseau", "Lire du trafic réseau", 12, "authentification-basique", """
Quand deux machines communiquent, leurs échanges peuvent être **capturés** (avec Wireshark ou tcpdump) puis analysés. Si le protocole n'est pas chiffré, tout passe en clair.

## Une requête HTTP

```
GET /admin/ HTTP/1.1
Host: intranet.exemple.fr
Authorization: Basic YWRtaW46c2VjcmV0
```

- La première ligne donne la méthode (`GET`, `POST`…) et la ressource demandée.
- Les lignes suivantes sont des **en-têtes**.
- L'en-tête `Authorization: Basic` contient `utilisateur:motdepasse` encodé en **Base64**, pas chiffré. Ici : `admin:secret`.

## Ce qu'il faut retenir

HTTP sans S envoie tout en clair : mots de passe, cookies, formulaires. **HTTPS** chiffre la communication avec TLS, ce qui rend la capture inutilisable pour un attaquant.

## Pour s'entraîner avec Wireshark

Ouvre un fichier `.pcap`, puis utilise le filtre `http` ou le menu *Statistiques → Conversations*. Clic droit sur un paquet, *Suivre → Flux TCP* : tu vois l'échange complet.
"""),
        ],
    },
]

ANNOUNCEMENTS = [
    ("Bienvenue sur Brèche", "La plateforme ouvre avec 11 défis débutants et 3 parcours. Commence par **Bases du CTF** si tu découvres les CTF."),
]
