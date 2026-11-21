import re
import json
import shutil
import subprocess
from pathlib import Path

SOURCE_DIR = Path("/home/simon-kaguru-kimara/Pictures/upscaled")
PROJECT_DIR = Path("/home/simon-kaguru-kimara/boldwear-arts")
ARTWORKS_DIR = PROJECT_DIR / "assets/artworks"
MOCKUPS_DIR = PROJECT_DIR / "assets/mockups"
WALL_TEMPLATE = PROJECT_DIR / "templates/gallery_wall.jpg"
GALLERY_JSON = PROJECT_DIR / "gallery.json"
PICTOREM_GALLERY = "https://www.pictorem.com/gallery/BoldWearArts.Collective"

MAGICK_BIN = shutil.which("magick") or shutil.which("convert")

# Map folder keywords to your Pictorem series and specific known URLs
SERIES_RULES = [
    (["dancer", "procession", "gathering", "rite", "ceremonial", "masquerade", "festival"], "African Art / Figurative Art / Dance"),
    (["surreal", "coast", "baobab", "river", "landscape", "village", "city", "street", "settlement", "migration"], "African celestial elegance"),
    (["wedding", "funeral", "workshop", "harvest"], "African Culture Community Celebration"),
    (["woman", "figure"], "African Identity Beauty Cultural Expression"),
]

KNOWN_URLS = {
    "celestial-desert-elegance": "https://www.pictorem.com/2815616/celestial-desert-elegance-1/",
    "ancestral-profiles": "https://www.pictorem.com/2815614/ancestral-profiles-regal-heritage-a-striking-macro-portrait-of-a-man-and-woman-in-serene-profile-adorned-with-elaborate-cultural-jewelry-coral-and-turquoise-beads-and-sculptural-gold-toned-ornaments-1/",
    "contemplation": "https://www.pictorem.com/2815586/african-woman-in-contemplation-sacred-teal-gold-1/",
    "celebrating-together": "https://www.pictorem.com/2815578/african-women-celebrating-together-expressive-oil-painting-1/",
    "intricate-afro": "https://www.pictorem.com/2815577/african-woman-with-an-intricate-afro-stylized-portrait-1/",
}

def clean_title_from_folder(folder_name: str) -> str:
    # Strip trailing _AI_6x_YYYYMMDD-HHMMSS
    base = re.sub(r'_AI_\d+x_\d{8}-\d{6}$', '', folder_name)
    return base.replace("_", " ").strip()

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def guess_series(slug: str) -> str:
    for keywords, series in SERIES_RULES:
        if any(k in slug for k in keywords):
            return series
    return "African Spirituality Ancestral Heritage."

def guess_url(slug: str) -> str:
    for key, url in KNOWN_URLS.items():
        if key in slug:
            return url
    return PICTOREM_GALLERY

def ensure_wall_template():
    if WALL_TEMPLATE.exists():
        return
    subprocess.run([
        MAGICK_BIN, "-size", "1600x1200",
        "radial-gradient:#ebe6dc-#cdc4b5",
        "-fill", "#b8afa0", "-draw", "rectangle 0,980 1600,1200",
        "-fill", "#9f9586", "-draw", "rectangle 0,974 1600,982",
        "-quality", "90", str(WALL_TEMPLATE)
    ], check=True)

def build_assets(src_img: Path, slug: str):
    art_out = ARTWORKS_DIR / f"{slug}.jpg"
    room_out = MOCKUPS_DIR / f"{slug}-room.jpg"

    subprocess.run([
        MAGICK_BIN, str(src_img),
        "-auto-orient", "-strip",
        "-resize", "1200x1200>",
        "-quality", "86",
        str(art_out)
    ], check=True)

    subprocess.run([
        MAGICK_BIN, str(WALL_TEMPLATE),
        "(",
            str(art_out),
            "-resize", "680x560>",
            "-bordercolor", "#141416", "-border", "14x14",
            "(", "+clone", "-background", "black", "-shadow", "55x14+10+16", ")",
            "+swap", "-background", "none", "-layers", "merge", "+repage",
        ")",
        "-gravity", "north", "-geometry", "+0+190",
        "-compose", "over", "-composite",
        "-quality", "86",
        str(room_out)
    ], check=True)

    return f"assets/artworks/{slug}.jpg", f"assets/mockups/{slug}-room.jpg"

def main():
    ensure_wall_template()
    gallery = []

    for folder in sorted(SOURCE_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        # Prefer *_AI_6x_Q100.jpg master in each subfolder
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

        title = clean_title_from_folder(folder.name)
        slug = slugify(title)
        series = guess_series(slug)
        pictorem_url = guess_url(slug)
        art_rel, room_rel = build_assets(master_img, slug)

        gallery.append({
            "id": slug,
            "title": title,
            "series": series,
            "artwork_img": art_rel,
            "room_img": room_rel,
            "pictorem_url": pictorem_url,
            "description": f"Contemporary African fine art work ({title}) by BoldWearArts Collective. View in space or order museum-grade prints via Pictorem."
        })
        print(f"[OK] {title} -> {series}")

    GALLERY_JSON.write_text(json.dumps(gallery, indent=2))
    print(f"\nGenerated {len(gallery)} artworks in {GALLERY_JSON}")

if __name__ == "__main__":
    main()
