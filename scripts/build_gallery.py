import re
import json
import shutil
import subprocess
from pathlib import Path

SOURCE_DIR = Path("/home/simon-kaguru-kimara/Pictures/upscaled")
PROJECT_DIR = Path("/home/simon-kaguru-kimara/boldwear-arts")
ARTWORKS_DIR = PROJECT_DIR / "assets/artworks"
MOCKUPS_DIR = PROJECT_DIR / "assets/mockups"
TEMPLATES_DIR = PROJECT_DIR / "templates"
GALLERY_JSON = PROJECT_DIR / "gallery.json"
META_FILE = PROJECT_DIR / "scripts/artworks_meta.json"
PICTOREM_GALLERY = "https://www.pictorem.com/gallery/BoldWearArts.Collective"

MAGICK_BIN = shutil.which("magick") or shutil.which("convert")
IDENTIFY_BIN = shutil.which("identify")

SERIES_RULES = [
    (["dancer", "procession", "gathering", "rite", "ceremonial", "masquerade", "festival"], "African Art / Figurative Art / Dance"),
    (["surreal", "coast", "baobab", "river", "landscape", "village", "city", "street", "settlement", "migration"], "African Celestial Elegance"),
    (["wedding", "funeral", "workshop", "harvest"], "African Culture & Community Celebration"),
    (["woman", "figure"], "African Identity, Beauty & Cultural Expression"),
]

KNOWN_URLS = {
    "celestial-desert-elegance": "https://www.pictorem.com/2815616/celestial-desert-elegance-1/",
    "ancestral-profiles": "https://www.pictorem.com/2815614/ancestral-profiles-regal-heritage-a-striking-macro-portrait-of-a-man-and-woman-in-serene-profile-adorned-with-elaborate-cultural-jewelry-coral-and-turquoise-beads-and-sculptural-gold-toned-ornaments-1/",
    "contemplation": "https://www.pictorem.com/2815586/african-woman-in-contemplation-sacred-teal-gold-1/",
    "celebrating-together": "https://www.pictorem.com/2815578/african-women-celebrating-together-expressive-oil-painting-1/",
    "intricate-afro": "https://www.pictorem.com/2815577/african-woman-with-an-intricate-afro-stylized-portrait-1/",
}

ROMANS = ["", " (II)", " (III)", " (IV)", " (V)"]

# Build rich staged interiors (1600x1200) with wall molding, floor, rug, chair, side table & floral stems
ROOM_SCENES = {
    "gallery": {
        "cmd": [
            "-size", "1600x1200", "xc:none",
            # Warm plaster gallery wall + subtle spotlight glow
            "(", "-size", "1600x920", "plasma:fractal", "-blur", "0x28", "-modulate", "115,22,100", ")",
            "-geometry", "+0+0", "-compose", "over", "-composite",
            "(", "-size", "1600x920", "radial-gradient:rgba(255,248,232,0.45)-rgba(165,148,124,0.35)", ")",
            "-geometry", "+0+0", "-compose", "over", "-composite",
            # Picture rail & baseboard molding
            "-fill", "#dfd6c5", "-draw", "rectangle 0,105 1600,118",
            "-fill", "#bfb39e", "-draw", "rectangle 0,118 1600,124",
            "-fill", "#d8cebc", "-draw", "rectangle 0,898 1600,920",
            # Hardwood floor & woven area rug
            "-fill", "#8c6b4a", "-draw", "rectangle 0,920 1600,1200",
            "-fill", "#765739", "-draw", "rectangle 0,920 1600,928",
            "-fill", "#cfc3ae", "-draw", "roundrectangle 180,948 1420,1165 24,24",
            "-fill", "#b8aa92", "-draw", "roundrectangle 205,962 1395,1150 18,18",
            # Sculpted accent armchair on left
            "-fill", "#2a2725", "-draw", "roundrectangle 255,770 435,965 28,28",
            "-fill", "#3c3631", "-draw", "roundrectangle 240,855 450,955 20,20",
            "-fill", "#191716", "-draw", "rectangle 270,955 284,1035 rectangle 420,955 434,1035",
            # Side table & floral vase on right
            "-fill", "#6d4c33", "-draw", "roundrectangle 1145,865 1335,885 8,8",
            "-fill", "#4e3522", "-draw", "rectangle 1175,885 1190,1035 rectangle 1290,885 1305,1035",
            # Ceramic vase + botanical leaves & blossoms
            "-fill", "#c99b4b", "-draw", "ellipse 1240,825 36,44 0,360",
            "-fill", "#35583c",
            "-draw", "ellipse 1222,745 14,46 -22,338",
            "-draw", "ellipse 1258,742 14,48 24,384",
            "-draw", "ellipse 1240,725 12,54 0,360",
            "-fill", "#e8d6b0",
            "-draw", "circle 1212,715 1212,728",
            "-draw", "circle 1268,712 1268,725",
            "-draw", "circle 1240,685 1240,700",
        ],
        "frame_color": "#1d1a16",
        "frame_px": "16x16",
        "offset": "+0+175",
        "max_box": "640x520",
    },
    "loft": {
        "cmd": [
            "-size", "1600x1200", "xc:none",
            # Sunlit architectural plaster wall
            "(", "-size", "1600x920", "gradient:#f5f1e8-#e6dfd1", ")",
            "-geometry", "+0+0", "-compose", "over", "-composite",
            # Window light wash from upper right
            "(", "-size", "1600x920", "radial-gradient:rgba(255,252,244,0.75)-rgba(255,252,244,0.0)", ")",
            "-geometry", "+420-120", "-compose", "over", "-composite",
            # Floor & textured linen rug
            "-fill", "#b99a78", "-draw", "rectangle 0,920 1600,1200",
            "-fill", "#e3dccd", "-draw", "roundrectangle 210,950 1390,1165 20,20",
            # Low-profile bench on left
            "-fill", "#d8cbb8", "-draw", "roundrectangle 240,860 510,900 12,12",
            "-fill", "#5b432e", "-draw", "rectangle 265,900 280,1015 rectangle 470,900 485,1015",
            # Planter & tall botanical stems on right
            "-fill", "#d5cfc4", "-draw", "roundrectangle 1155,810 1325,975 18,18",
            "-fill", "#2f5233",
            "-draw", "ellipse 1215,710 18,65 -18,342",
            "-draw", "ellipse 1265,700 18,72 18,378",
            "-draw", "ellipse 1240,675 16,78 0,360",
            "-fill", "#d9825b",
            "-draw", "circle 1205,670 1205,684",
            "-draw", "circle 1275,665 1275,679",
        ],
        "frame_color": "#c59b38",
        "frame_px": "14x14",
        "offset": "+0+175",
        "max_box": "640x520",
    },
    "lounge": {
        "cmd": [
            "-size", "1600x1200", "xc:none",
            # Deep collector salon wall with warm gallery sconce glow
            "(", "-size", "1600x920", "radial-gradient:#3a322b-#161418", ")",
            "-geometry", "+0+0", "-compose", "over", "-composite",
            "(", "-size", "1600x920", "radial-gradient:rgba(212,175,55,0.22)-rgba(0,0,0,0.0)", ")",
            "-geometry", "+0+140", "-compose", "over", "-composite",
            # Dark timber floor & deep burgundy/gold accent rug
            "-fill", "#221c18", "-draw", "rectangle 0,920 1600,1200",
            "-fill", "#4a2523", "-draw", "roundrectangle 220,945 1380,1165 24,24",
            "-fill", "#b8933a", "-draw", "roundrectangle 242,962 1358,1148 18,18",
            "-fill", "#3b1d1c", "-draw", "roundrectangle 256,974 1344,1136 14,14",
            # Velvet lounge chair & brass/wood table
            "-fill", "#5a3d28", "-draw", "roundrectangle 255,785 445,965 32,32",
            "-fill", "#745036", "-draw", "roundrectangle 240,865 460,955 18,18",
            "-fill", "#2b2119", "-draw", "rectangle 272,955 286,1035 rectangle 422,955 436,1035",
            "-fill", "#4a3322", "-draw", "roundrectangle 1150,860 1330,880 8,8",
            "-fill", "#c9a248", "-draw", "rectangle 1234,880 1246,1035",
            "-fill", "#8c2f2b", "-draw", "ellipse 1240,820 34,42 0,360",
            "-fill", "#4a6b48",
            "-draw", "ellipse 1218,742 14,44 -20,340",
            "-draw", "ellipse 1262,740 14,46 22,382",
            "-fill", "#f0c96b",
            "-draw", "circle 1240,695 1240,710",
            "-draw", "circle 1215,712 1215,725",
        ],
        "frame_color": "#0d0c0e",
        "frame_px": "16x16",
        "offset": "+0+175",
        "max_box": "640x520",
    },
}

def clean_title_from_folder(folder_name: str) -> str:
    base = re.sub(r'_AI_\d+x_\d{8}-\d{6}$', '', folder_name)
    base = re.sub(r'\bRETRY\b', '', base, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', base.replace("_", " ")).strip()

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def guess_series(slug: str) -> str:
    for keywords, series in SERIES_RULES:
        if any(k in slug for k in keywords):
            return series
    return "African Spirituality & Ancestral Heritage"

def guess_url(slug: str) -> str:
    for key, url in KNOWN_URLS.items():
        if key in slug:
            return url
    return PICTOREM_GALLERY

def get_dimensions(img_path: Path):
    cmd = [IDENTIFY_BIN, "-format", "%w %h", str(img_path)] if IDENTIFY_BIN else [MAGICK_BIN, "identify", "-format", "%w %h", str(img_path)]
    out = subprocess.check_output(cmd, text=True).strip().split()
    w, h = int(out[0]), int(out[1])
    if w > h * 1.12:
        orientation = "Landscape"
    elif h > w * 1.12:
        orientation = "Portrait"
    else:
        orientation = "Square"
    return w, h, orientation

def ensure_room_templates():
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, cfg in ROOM_SCENES.items():
        tpl = TEMPLATES_DIR / f"wall_{name}.jpg"
        # Always rebuild staged interior templates so scene upgrades apply cleanly
        subprocess.run([MAGICK_BIN, *cfg["cmd"], "-background", "#1a1816", "-flatten", "-quality", "92", str(tpl)], check=True)
        paths[name] = tpl
    return paths

def build_assets(src_img: Path, slug: str, templates: dict):
    art_out = ARTWORKS_DIR / f"{slug}.jpg"
    subprocess.run([
        MAGICK_BIN, str(src_img),
        "-auto-orient", "-strip",
        "-resize", "1200x1200>",
        "-quality", "88",
        str(art_out)
    ], check=True)

    room_map = {}
    for preset_name, cfg in ROOM_SCENES.items():
        room_out = MOCKUPS_DIR / f"{slug}-room-{preset_name}.jpg"
        subprocess.run([
            MAGICK_BIN, str(templates[preset_name]),
            "(",
                str(art_out),
                "-resize", f"{cfg['max_box']}>",
                "-bordercolor", "#f7f4ed", "-border", "18x18",
                "-bordercolor", cfg["frame_color"], "-border", cfg["frame_px"],
                "(", "+clone", "-background", "black", "-shadow", "65x18+12+22", ")",
                "+swap", "-background", "none", "-layers", "merge", "+repage",
            ")",
            "-gravity", "north", "-geometry", cfg["offset"],
            "-compose", "over", "-composite",
            "-quality", "88",
            str(room_out)
        ], check=True)
        room_map[preset_name] = f"assets/mockups/{slug}-room-{preset_name}.jpg"

    return f"assets/artworks/{slug}.jpg", room_map

def load_meta():
    if META_FILE.exists():
        return json.loads(META_FILE.read_text())
    return {}

def main():
    ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)
    MOCKUPS_DIR.mkdir(parents=True, exist_ok=True)
    templates = ensure_room_templates()
    meta_overrides = load_meta()
    gallery = []
    seen_counts = {}

    for folder in sorted(SOURCE_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        q100_files = sorted(folder.glob("*_AI_6x_Q100.jpg"))
        if q100_files:
            master_img = q100_files[0]
        else:
            valid_imgs = [
                f for f in sorted(folder.iterdir())
                if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
            if not valid_imgs:
                continue
            master_img = valid_imgs[0]

        base_title = clean_title_from_folder(folder.name)
        base_slug = slugify(base_title)

        count = seen_counts.get(base_slug, 0)
        seen_counts[base_slug] = count + 1

        slug = base_slug if count == 0 else f"{base_slug}-{count + 1}"
        suffix = ROMANS[count] if count < len(ROMANS) else f" ({count + 1})"
        default_title = f"{base_title}{suffix}"

        ov = meta_overrides.get(slug) or meta_overrides.get(base_slug) or {}
        title = ov.get("title", default_title)
        series = ov.get("series", guess_series(base_slug))
        pictorem_url = ov.get("pictorem_url", guess_url(base_slug))
        w, h, orientation = get_dimensions(master_img)
        description = ov.get(
            "description",
            f"Contemporary African fine art work ({title}) by BoldWearArts Collective. {orientation} composition with mat & frame staging for modern spaces; museum prints available via Pictorem."
        )

        art_rel, room_map = build_assets(master_img, slug, templates)

        gallery.append({
            "id": slug,
            "title": title,
            "series": series,
            "orientation": orientation,
            "dimensions": f"{w}x{h}px",
            "artwork_img": art_rel,
            "room_img": room_map["gallery"],
            "room_imgs": room_map,
            "pictorem_url": pictorem_url,
            "description": description
        })
        print(f"[OK] {title} [{orientation}] -> {series}")

    GALLERY_JSON.write_text(json.dumps(gallery, indent=2))
    print(f"\nGenerated {len(gallery)} artworks with staged room interiors in {GALLERY_JSON}")

if __name__ == "__main__":
    main()
