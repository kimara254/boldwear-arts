let artworks = [];
let activeSeries = "All";
let roomState = {};
let modalItem = null;
let modalInRoom = false;

const gridEl = document.getElementById("gallery-grid");
const filterEl = document.getElementById("filter-bar");
const countEl = document.getElementById("piece-count");
const lightboxEl = document.getElementById("lightbox");

document.getElementById("year").textContent = new Date().getFullYear();

fetch("gallery.json")
  .then((res) => res.json())
  .then((data) => {
    artworks = data;
    renderFilters();
    renderGrid();
  });

function renderFilters() {
  const seriesList = ["All", ...new Set(artworks.map((a) => a.series))];
  filterEl.innerHTML = "";
  seriesList.forEach((s) => {
    const btn = document.createElement("button");
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

function getImgSrc(item, inRoom) {
  return inRoom && item.room_img ? item.room_img : item.artwork_img;
}

function renderGrid() {
  const filtered = activeSeries === "All"
    ? artworks
    : artworks.filter((a) => a.series === activeSeries);

  countEl.textContent = `Showing ${filtered.length} of ${artworks.length} works`;
  gridEl.innerHTML = "";

  filtered.forEach((item) => {
    const isRoom = Boolean(roomState[item.id]);
    const card = document.createElement("article");
    card.className = "art-card";
    card.innerHTML = `
      <div class="art-media">
        <img src="${getImgSrc(item, isRoom)}" alt="${item.title}" loading="lazy" />
      </div>
      <div class="art-body">
        <span class="art-series">${item.series}</span>
        <h4 class="art-title">${item.title}</h4>
        <p class="art-desc">${item.description}</p>
        <div class="art-actions">
          <button class="btn secondary toggle-room">${isRoom ? "Show Artwork" : "View in Room"}</button>
          <a class="btn primary" href="${item.pictorem_url}" target="_blank" rel="noopener">Order on Pictorem</a>
        </div>
      </div>
    `;

    card.querySelector(".art-media").onclick = () => openModal(item, isRoom);
    card.querySelector(".toggle-room").onclick = () => {
      roomState[item.id] = !roomState[item.id];
      renderGrid();
    };

    gridEl.appendChild(card);
  });
}

function openModal(item, inRoom) {
  modalItem = item;
  modalInRoom = inRoom;
  updateModal();
  lightboxEl.classList.remove("hidden");
  lightboxEl.setAttribute("aria-hidden", "false");
}

function updateModal() {
  if (!modalItem) return;
  document.getElementById("lightbox-img").src = getImgSrc(modalItem, modalInRoom);
  document.getElementById("lightbox-img").alt = modalItem.title;
  document.getElementById("lightbox-series").textContent = modalItem.series;
  document.getElementById("lightbox-title").textContent = modalItem.title;
  document.getElementById("lightbox-desc").textContent = modalItem.description;
  document.getElementById("lightbox-pictorem").href = modalItem.pictorem_url;
  document.getElementById("lightbox-toggle-room").textContent = modalInRoom
    ? "Show Artwork"
    : "View in Room";
}

document.getElementById("lightbox-toggle-room").onclick = () => {
  modalInRoom = !modalInRoom;
  updateModal();
};

document.getElementById("close-lightbox").onclick = () => {
  lightboxEl.classList.add("hidden");
  lightboxEl.setAttribute("aria-hidden", "true");
};
