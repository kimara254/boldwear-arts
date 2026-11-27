let artworks = [];
let activeSeries = "All";
let searchQuery = "";
let viewModeById = {};
let shortlistIds = [];
let modalIndex = -1;
let modalMode = "art";

const STORAGE_KEY = "boldwear_shortlist_v1";

const gridEl = document.getElementById("gallery-grid");
const filterEl = document.getElementById("filter-bar");
const searchEl = document.getElementById("search-input");
const countEl = document.getElementById("piece-count");
const lightboxEl = document.getElementById("lightbox");
const drawerEl = document.getElementById("shortlist-drawer");
const shortlistCountEl = document.getElementById("shortlist-count");
const shortlistItemsEl = document.getElementById("shortlist-items");

document.getElementById("year").textContent = new Date().getFullYear();

try {
  shortlistIds = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
} catch {
  shortlistIds = [];
}

fetch("gallery.json")
  .then((res) => res.json())
  .then((data) => {
    artworks = data;
    updateShortlistUI();
    renderFilters();
    renderGrid();
  })
  .catch((error) => {
    console.error("BoldWearArts catalogue could not be loaded:", error);
    countEl.textContent = "The collection could not be loaded. Please refresh the page.";
    gridEl.innerHTML = '<p class="subcount">The artwork catalogue is temporarily unavailable. Please try again shortly.</p>';
  });

searchEl.addEventListener("input", (e) => {
  searchQuery = e.target.value.trim().toLowerCase();
  renderGrid();
});

function saveShortlist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(shortlistIds));
  updateShortlistUI();
}

function toggleShortlist(id) {
  if (shortlistIds.includes(id)) {
    shortlistIds = shortlistIds.filter((x) => x !== id);
  } else {
    shortlistIds.push(id);
  }
  saveShortlist();
  renderGrid();
  if (modalIndex >= 0) updateModal();
}

function updateShortlistUI() {
  shortlistCountEl.textContent = shortlistIds.length;
  const selected = artworks.filter((a) => shortlistIds.includes(a.id));
  if (!selected.length) {
    shortlistItemsEl.innerHTML = `<p class="subcount">No pieces saved yet. Click <strong>Save</strong> on any artwork to build a collector shortlist.</p>`;
    return;
  }
  shortlistItemsEl.innerHTML = selected
    .map(
      (item) => `
      <div class="shortlist-row">
        <div>
          <strong>${item.title}</strong>
          <small>${item.series} · ${item.orientation || ""}</small>
        </div>
        <button type="button" class="room-chip" onclick="toggleShortlist('${item.id}')">Remove</button>
      </div>
    `
    )
    .join("");
}

function renderFilters() {
  const seriesList = ["All", ...new Set(artworks.map((a) => a.series))];
  filterEl.innerHTML = "";
  seriesList.forEach((s) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `filter-btn ${s === activeSeries ? "active" : ""}`;
    btn.textContent = s;
    btn.onclick = () => {
      activeSeries = s;
      renderFilters();
      renderGrid();
    };
    filterEl.appendChild(btn);
  });
}

function getFilteredArtworks() {
  return artworks.filter((a) => {
    const matchesSeries = activeSeries === "All" || a.series === activeSeries;
    const hay = `${a.title} ${a.series} ${a.description} ${a.orientation || ""}`.toLowerCase();
    const matchesSearch = !searchQuery || hay.includes(searchQuery);
    return matchesSeries && matchesSearch;
  });
}

function getModeImage(item) {
  return item.artwork_img;
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
    const mode = viewModeById[item.id] || "art";
    document.querySelectorAll("#lightbox-room-bar .room-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.mode === modalMode);
  });

  const isSaved = shortlistIds.includes(item.id);
    const card = document.createElement("article");
    card.className = "art-card";

    card.innerHTML = `
      <div class="art-media">
        <img src="${getModeImage(item, mode)}" alt="${item.title}" loading="lazy" />
      </div>
      <div class="art-body">
        <div class="meta-top-row">
          <span class="art-series">${item.series}</span>
          <span class="spec-badge">${item.orientation || "Fine Art"}</span>
        </div>
        <h4 class="art-title">${item.title}</h4>
        <p class="art-desc">${item.description}</p>
        <div class="art-actions">
          <button type="button" class="btn secondary save-btn ${isSaved ? "saved" : ""}">${isSaved ? "Saved" : "Save"}</button>
          <a class="btn primary" href="${item.pictorem_url}" target="_blank" rel="noopener">Order on Pictorem</a>
        </div>
      </div>
    `;

    card.querySelector(".art-media").onclick = () => {
      const globalIdx = artworks.findIndex((a) => a.id === item.id);
      openModal(globalIdx, mode);
    };

    card.querySelector(".save-btn").onclick = () => toggleShortlist(item.id);

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

  const lightboxImage = document.getElementById("lightbox-img");
  lightboxImage.src = getModeImage(item, "art");
  lightboxImage.alt = item.title;
  const roomStage = document.getElementById("room-stage");
  const isRoomView = modalMode !== "art";
  lightboxImage.hidden = isRoomView;
  roomStage.hidden = !isRoomView;
  if (isRoomView) {
    roomStage.className = `room-stage room-${modalMode}`;
    const furniture = {
      gallery: '<div class="room-console"></div><div class="room-plant plant-left"></div><div class="room-plinth"></div>',
      living: '<div class="room-sofa"><i></i><i></i><i></i></div><div class="room-coffee-table"></div><div class="room-plant plant-right"></div>',
      bedroom: '<div class="room-headboard"></div><div class="room-bed"><i></i><i></i></div><div class="room-nightstand"></div>',
      office: '<div class="room-desk"></div><div class="room-office-chair"></div><div class="room-bookcase"></div>',
      dining: '<div class="room-dining-table"></div><div class="room-dining-chairs"></div><div class="room-vase"></div>'
    };
    roomStage.innerHTML = `<div class="room-wall"><div class="room-ceiling-light"></div><div class="room-art-frame"><img src="${item.artwork_img}" alt="${item.title} displayed on the wall"></div>${furniture[modalMode] || ""}</div><div class="room-floor"></div><span class="room-view-label">${({gallery:"Gallery Room",living:"Living Room",bedroom:"Bedroom",office:"Home Office",dining:"Dining & Entrance"})[modalMode]}</span>`;
  }
  document.getElementById("lightbox-series").textContent = item.series;
  document.getElementById("lightbox-spec").textContent = `${item.orientation || ""} ${item.dimensions ? "· " + item.dimensions : ""}`.trim();
  document.getElementById("lightbox-title").textContent = item.title;
  document.getElementById("lightbox-desc").textContent = item.description;
  document.getElementById("lightbox-pictorem").href = item.pictorem_url;

  const isSaved = shortlistIds.includes(item.id);
  const saveBtn = document.getElementById("lightbox-save");
  saveBtn.textContent = isSaved ? "Saved in Shortlist" : "Save to Shortlist";
  saveBtn.classList.toggle("saved", isSaved);

  document.querySelectorAll("#lightbox-room-bar .room-chip").forEach((chip) => {
  chip.onclick = () => {
    modalMode = chip.dataset.mode;
    updateModal();
  };
});

document.getElementById("lightbox-save").onclick = () => {
  if (modalIndex >= 0) toggleShortlist(artworks[modalIndex].id);
};

document.getElementById("prev-piece").onclick = () => {
  if (!artworks.length) return;
  openModal((modalIndex - 1 + artworks.length) % artworks.length, modalMode);
};

document.getElementById("next-piece").onclick = () => {
  if (!artworks.length) return;
  openModal((modalIndex + 1) % artworks.length, modalMode);
};

function closeLightbox() {
  lightboxEl.classList.add("hidden");
  lightboxEl.setAttribute("aria-hidden", "true");
  modalIndex = -1;
}

document.getElementById("close-lightbox").onclick = closeLightbox;

document.getElementById("open-shortlist-btn").onclick = () => {
  updateShortlistUI();
  drawerEl.classList.remove("hidden");
  drawerEl.setAttribute("aria-hidden", "false");
};

function closeDrawer() {
  drawerEl.classList.add("hidden");
  drawerEl.setAttribute("aria-hidden", "true");
}

document.getElementById("close-drawer").onclick = closeDrawer;

document.getElementById("copy-shortlist-btn").onclick = async () => {
  const selected = artworks.filter((a) => shortlistIds.includes(a.id));
  if (!selected.length) return;
  const summary =
    "BoldWearArts Collective — Collector Selection:\n" +
    selected.map((a, i) => `${i + 1}. ${a.title} (${a.series}) — ${a.pictorem_url}`).join("\n");
  try {
    await navigator.clipboard.writeText(summary);
    const btn = document.getElementById("copy-shortlist-btn");
    const orig = btn.textContent;
    btn.textContent = "Copied Selection!";
    setTimeout(() => (btn.textContent = orig), 1800);
  } catch {
    alert(summary);
  }
};

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeLightbox();
    closeDrawer();
  } else if (modalIndex >= 0 && e.key === "ArrowRight") {
    openModal((modalIndex + 1) % artworks.length, modalMode);
  } else if (modalIndex >= 0 && e.key === "ArrowLeft") {
    openModal((modalIndex - 1 + artworks.length) % artworks.length, modalMode);
  }
});
