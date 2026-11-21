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

ROOM_PRESETS = {
    "gallery": {
        "cmd": [
            "-size", "1600x1200",
            "radial-gradient:#efeae0-#cfc5b4",
            "-fill", "#bab09e", "-draw", "rectangle 0,980 1600,1200",
            "-fill", "#9f9482", "-draw", "rectangle 0,974 1600,982",
        ],
        "frame_color": "#161619",
        "frame_px": "14x14",
        "offset": "+0+190",
        "max_box": "680x560",
    },
    "loft": {
        "cmd": [
            "-size", "1600x1200",
            "gradient:#f6f4ef-#e3dfd5",
            "-fill", "#cfc8ba", "-draw", "rectangle 0,990 1600,1200",
            "-fill", "#b5ac9b", "-draw", "rectangle 0,985 1600,991",
        ],
        "frame_color": "#c9a84c",
        "frame_px": "12x12",
        "offset": "+0+180",
        "max_box": "700x580",
    },
    "lounge": {
        "cmd": [
            "-size", "1600x1200",
            "radial-gradient:#29272d-#141317",
            "-fill", "#1d1b20", "-draw", "rectangle 0,980 1600,1200",
            "-fill", "#3a352c", "-draw", "rectangle 0,975 1600,981",
        ],
        "frame_color": "#0b0b0d",
        "frame_px": "16x16",
        "offset": "+0+190",
        "max_box": "680x560",
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
    for name, cfg in ROOM_PRESETS.items():
        tpl = TEMPLATES_DIR / f"wall_{name}.jpg"
        if not tpl.exists():
            subprocess.run([MAGICK_BIN, *cfg["cmd"], "-quality", "90", str(tpl)], check=True)
        paths[name] = tpl
    return paths

def build_assets(src_img: Path, slug: str, templates: dict):
    art_out = ARTWORKS_DIR / f"{slug}.jpg"
    subprocess.run([
        MAGICK_BIN, str(src_img),
        "-auto-orient", "-strip",
        "-resize", "1200x1200>",
        "-quality", "86",
        str(art_out)
    ], check=True)

    room_map = {}
    for preset_name, cfg in ROOM_PRESETS.items():
        room_out = MOCKUPS_DIR / f"{slug}-room-{preset_name}.jpg"
        subprocess.run([
            MAGICK_BIN, str(templates[preset_name]),
            "(",
                str(art_out),
                "-resize", f"{cfg['max_box']}>",
                "-bordercolor", cfg["frame_color"], "-border", cfg["frame_px"],
                "(", "+clone", "-background", "black", "-shadow", "55x14+10+16", ")",
                "+swap", "-background", "none", "-layers", "merge", "+repage",
            ")",
            "-gravity", "north", "-geometry", cfg["offset"],
            "-compose", "over", "-composite",
            "-quality", "85",
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
            f"Contemporary African fine art work ({title}) by BoldWearArts Collective. {orientation} composition staged for modern spaces and printed to order via Pictorem."
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
    print(f"\nGenerated {len(gallery)} artworks with 3 room presets each in {GALLERY_JSON}")

if __name__ == "__main__":
    main()
