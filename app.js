let artworks = [];
let activeSeries = "All";
let searchQuery = "";
let shortlistIds = [];
let modalIndex = -1;
let modalMode = "art";

const STORAGE_KEY = "boldwear_shortlist_v1";
const $ = (id) => document.getElementById(id);
const gridEl = $("gallery-grid");
const filterEl = $("filter-bar");
const searchEl = $("search-input");
const countEl = $("piece-count");
const lightboxEl = $("lightbox");
const drawerEl = $("shortlist-drawer");
const shortlistCountEl = $("shortlist-count");
const shortlistItemsEl = $("shortlist-items");

$("year").textContent = new Date().getFullYear();

try {
  shortlistIds = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  if (!Array.isArray(shortlistIds)) shortlistIds = [];
} catch {
  shortlistIds = [];
}

fetch("./gallery.json")
  .then((response) => {
    if (!response.ok) throw new Error("Catalogue request failed: " + response.status);
    return response.json();
  })
  .then((data) => {
    if (!Array.isArray(data)) throw new Error("Catalogue format is invalid");
    artworks = data;
    updateShortlistUI();
    renderFilters();
    renderGrid();
  })
  .catch((error) => {
    console.error("BoldWearArts catalogue could not be loaded:", error);
    countEl.textContent = "The collection could not be loaded. Please refresh.";
    gridEl.innerHTML = '<p class="subcount">The artwork catalogue is temporarily unavailable. Please try again shortly.</p>';
  });

searchEl.addEventListener("input", (event) => {
  searchQuery = event.target.value.trim().toLowerCase();
  renderGrid();
});

function saveShortlist() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(shortlistIds)); } catch (error) {
    console.warn("Shortlist could not be saved on this device.", error);
  }
  updateShortlistUI();
}

function toggleShortlist(id) {
  shortlistIds = shortlistIds.includes(id)
    ? shortlistIds.filter((value) => value !== id)
    : [...shortlistIds, id];
  saveShortlist();
  renderGrid();
  if (modalIndex >= 0) updateModal();
}

function updateShortlistUI() {
  shortlistCountEl.textContent = shortlistIds.length;
  const selected = artworks.filter((artwork) => shortlistIds.includes(artwork.id));
  if (!selected.length) {
    shortlistItemsEl.innerHTML = '<p class="subcount">No pieces saved yet. Use Save on any artwork to build a collector shortlist.</p>';
    return;
  }
  shortlistItemsEl.innerHTML = selected.map((item) => `
    <div class="shortlist-row">
      <div><strong>${item.title}</strong><small>${item.series} · ${item.orientation || ""}</small></div>
      <button type="button" class="room-chip" data-remove="${item.id}">Remove</button>
    </div>`).join("");
  shortlistItemsEl.querySelectorAll("[data-remove]").forEach((button) => {
    button.addEventListener("click", () => toggleShortlist(button.dataset.remove));
  });
}

function renderFilters() {
  const seriesList = ["All", ...new Set(artworks.map((item) => item.series))];
  filterEl.innerHTML = "";
  seriesList.forEach((series) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "filter-btn" + (series === activeSeries ? " active" : "");
    button.textContent = series;
    button.addEventListener("click", () => {
      activeSeries = series;
      renderFilters();
      renderGrid();
    });
    filterEl.appendChild(button);
  });
}

function getFilteredArtworks() {
  return artworks.filter((item) => {
    const matchesSeries = activeSeries === "All" || item.series === activeSeries;
    const searchable = `${item.title} ${item.series} ${item.description || ""} ${item.orientation || ""}`.toLowerCase();
    return matchesSeries && (!searchQuery || searchable.includes(searchQuery));
  });
}

function renderGrid() {
  const filtered = getFilteredArtworks();
  countEl.textContent = `Showing ${filtered.length} of ${artworks.length} works`;
  gridEl.innerHTML = "";
  if (!filtered.length) {
    gridEl.innerHTML = '<p class="subcount">No artworks match this search. Try another title or collection.</p>';
    return;
  }

  filtered.forEach((item) => {
    const saved = shortlistIds.includes(item.id);
    const card = document.createElement("article");
    card.className = "art-card";
    card.innerHTML = `
      <div class="art-media"><img src="${item.artwork_img}" alt="${item.title}" loading="lazy"></div>
      <div class="art-body">
        <div class="meta-top-row"><span class="art-series"></span><span class="spec-badge"></span></div>
        <h4 class="art-title"></h4><p class="art-desc"></p>
        <div class="art-actions">
          <button type="button" class="btn secondary save-btn">${saved ? "Saved" : "Save"}</button>
          <a class="btn primary" target="_blank" rel="noopener">Order on Pictorem ↗</a>
        </div>
      </div>`;
    card.querySelector(".art-series").textContent = item.series;
    card.querySelector(".spec-badge").textContent = item.orientation || "Fine Art";
    card.querySelector(".art-title").textContent = item.title;
    card.querySelector(".art-desc").textContent = item.description || "";
    card.querySelector(".art-media").addEventListener("click", () => openModal(artworks.findIndex((art) => art.id === item.id), "art"));
    card.querySelector(".save-btn").addEventListener("click", () => toggleShortlist(item.id));
    card.querySelector(".art-actions a").href = item.pictorem_url || "https://www.pictorem.com/gallery/BoldWearArts.Collective";
    gridEl.appendChild(card);
  });
}

function openModal(index, mode = "art") {
  if (index < 0 || index >= artworks.length) return;
  modalIndex = index;
  modalMode = mode;
  updateModal();
  lightboxEl.classList.remove("hidden");
  lightboxEl.setAttribute("aria-hidden", "false");
}

function updateModal() {
  const item = artworks[modalIndex];
  if (!item) return;

  const artworkImage = $("lightbox-img");
  const roomStage = $("room-stage");
  const isRoomView = modalMode !== "art";
  artworkImage.src = item.artwork_img;
  artworkImage.alt = item.title;
  artworkImage.hidden = isRoomView;
  roomStage.hidden = !isRoomView;

  if (isRoomView) {
    const stem = item.artwork_img.split("/").pop().replace(/\\.[^.]+$/, "");
    const roomImages = {
      gallery: item.room_imgs && item.room_imgs.gallery,
      living: `assets/mockups/${stem}-room.jpg`,
      loft: item.room_imgs && item.room_imgs.loft,
      lounge: item.room_imgs && item.room_imgs.lounge
    };
    const roomNames = {
      gallery: "Gallery Room",
      living: "Living Room",
      loft: "Sunlit Loft",
      lounge: "Salon Lounge",
      studio: "Studio"
    };

    if (modalMode === "studio") {
      roomStage.className = "room-stage room-photo-stage";
      roomStage.innerHTML = `
        <img class="room-photo-background" src="templates/room_studio.jpg" alt="Photographic studio interior">
        <div class="room-photo-art"><img src="${item.artwork_img}" alt="${item.title} displayed on the studio wall"></div>
        <span class="room-view-label">${roomNames.studio}</span>`;
    } else {
      const source = roomImages[modalMode];
      roomStage.className = "room-stage room-photo-stage";
      roomStage.innerHTML = `
        <img class="room-photo-background" src="${source || item.artwork_img}" alt="${item.title} in ${roomNames[modalMode] || "an interior"}">
        <span class="room-view-label">${roomNames[modalMode] || "Interior view"}</span>`;
    }
  }

  $("lightbox-series").textContent = item.series;
  $("lightbox-spec").textContent = `${item.orientation || ""} ${item.dimensions ? "· " + item.dimensions : ""}`.trim();
  $("lightbox-title").textContent = item.title;
  $("lightbox-desc").textContent = item.description || "";
  $("lightbox-pictorem").href = item.pictorem_url || "https://www.pictorem.com/gallery/BoldWearArts.Collective";
  const saveButton = $("lightbox-save");
  const saved = shortlistIds.includes(item.id);
  saveButton.textContent = saved ? "Saved in Shortlist" : "Save to Shortlist";
  saveButton.classList.toggle("saved", saved);
  document.querySelectorAll("#lightbox-room-bar .room-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.mode === modalMode);
  });
}

document.querySelectorAll("#lightbox-room-bar .room-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    modalMode = chip.dataset.mode;
    updateModal();
  });
});

$("lightbox-save").addEventListener("click", () => {
  if (modalIndex >= 0) toggleShortlist(artworks[modalIndex].id);
});
$("prev-piece").addEventListener("click", () => {
  if (artworks.length) openModal((modalIndex - 1 + artworks.length) % artworks.length, modalMode);
});
$("next-piece").addEventListener("click", () => {
  if (artworks.length) openModal((modalIndex + 1) % artworks.length, modalMode);
});

function closeLightbox() {
  lightboxEl.classList.add("hidden");
  lightboxEl.setAttribute("aria-hidden", "true");
  modalIndex = -1;
}
$("close-lightbox").addEventListener("click", closeLightbox);
$("open-shortlist-btn").addEventListener("click", () => {
  updateShortlistUI();
  drawerEl.classList.remove("hidden");
  drawerEl.setAttribute("aria-hidden", "false");
});
function closeDrawer() {
  drawerEl.classList.add("hidden");
  drawerEl.setAttribute("aria-hidden", "true");
}
$("close-drawer").addEventListener("click", closeDrawer);
$("copy-shortlist-btn").addEventListener("click", async () => {
  const selected = artworks.filter((item) => shortlistIds.includes(item.id));
  if (!selected.length) return;
  const summary = "BoldWearArts Collective — Collector Selection:\n" +
    selected.map((item, index) => `${index + 1}. ${item.title} (${item.series}) — ${item.pictorem_url}`).join("\n");
  try {
    await navigator.clipboard.writeText(summary);
    $("copy-shortlist-btn").textContent = "Copied Selection!";
  } catch {
    alert(summary);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeLightbox();
    closeDrawer();
  } else if (modalIndex >= 0 && event.key === "ArrowRight") {
    openModal((modalIndex + 1) % artworks.length, modalMode);
  } else if (modalIndex >= 0 && event.key === "ArrowLeft") {
    openModal((modalIndex - 1 + artworks.length) % artworks.length, modalMode);
  }
});
