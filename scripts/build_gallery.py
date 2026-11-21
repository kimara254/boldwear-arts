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

# Real room templates normalized to 1600x1200 with wall placement geometry
ROOM_CONFIGS = {
    "gallery": {
        "source": TEMPLATES_DIR / "room_living.jpg",
        "prepared": TEMPLATES_DIR / "_prepared_living.jpg",
        "frame_color": "#191715",
        "frame_px": "14x14",
        "max_box": "560x420",
        "offset": "+0+145",
    },
    "loft": {
        "source": TEMPLATES_DIR / "room_studio.jpg",
        "prepared": TEMPLATES_DIR / "_prepared_studio.jpg",
        "frame_color": "#c59b38",
        "frame_px": "12x12",
        "max_box": "560x420",
        "offset": "+0+140",
    },
    "lounge": {
        "source": TEMPLATES_DIR / "room_lounge.jpg",
        "prepared": TEMPLATES_DIR / "_prepared_lounge.jpg",
        "frame_color": "#111012",
        "frame_px": "14x14",
        "max_box": "560x420",
        "offset": "+0+145",
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

def prepare_room_templates():
    ready = {}
    for name, cfg in ROOM_CONFIGS.items():
        src = cfg["source"]
        prep = cfg["prepared"]
        if src.exists():
            # Normalize real interior photo to 1600x1200 fill & keep natural photography
            subprocess.run([
                MAGICK_BIN, str(src),
                "-auto-orient", "-strip",
                "-resize", "1600x1200^",
                "-gravity", "center",
                "-extent", "1600x1200",
                "-quality", "90",
                str(prep)
            ], check=True)
            ready[name] = prep
        else:
            ready[name] = None
    return ready

def build_assets(src_img: Path, slug: str, room_bases: dict):
    art_out = ARTWORKS_DIR / f"{slug}.jpg"
    subprocess.run([
        MAGICK_BIN, str(src_img),
        "-auto-orient", "-strip",
        "-resize", "1200x1200>",
        "-quality", "88",
        str(art_out)
    ], check=True)

    room_map = {}
    for preset_name, cfg in ROOM_CONFIGS.items():
        base_img = room_bases.get(preset_name)
        if not base_img:
            continue
        room_out = MOCKUPS_DIR / f"{slug}-room-{preset_name}.jpg"
        subprocess.run([
            MAGICK_BIN, str(base_img),
            "(",
                str(art_out),
                "-resize", f"{cfg['max_box']}>",
                "-bordercolor", "#faf8f3", "-border", "12x12",
                "-bordercolor", cfg["frame_color"], "-border", cfg["frame_px"],
                "(", "+clone", "-background", "black", "-shadow", "60x18+8+18", ")",
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
    room_bases = prepare_room_templates()
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
            f"Contemporary African fine art work ({title}) by BoldWearArts Collective. {orientation} composition staged in interior spaces and available as museum-grade prints via Pictorem."
        )

        art_rel, room_map = build_assets(master_img, slug, room_bases)

        gallery.append({
            "id": slug,
            "title": title,
            "series": series,
            "orientation": orientation,
            "dimensions": f"{w}x{h}px",
            "artwork_img": art_rel,
            "room_img": room_map.get("gallery", art_rel),
            "room_imgs": room_map,
            "pictorem_url": pictorem_url,
            "description": description
        })
        print(f"[OK] {title} [{orientation}] -> {len(room_map)} rooms")

    GALLERY_JSON.write_text(json.dumps(gallery, indent=2))
    print(f"\nGenerated {len(gallery)} artworks in {GALLERY_JSON}")

if __name__ == "__main__":
    main()
