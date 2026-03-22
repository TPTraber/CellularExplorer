const API = "http://localhost:7070";
const grid = document.getElementById("gallery-grid");
const newBtn = document.getElementById("new-btn");
const picker = document.getElementById("type-picker");
const pickerClose = document.getElementById("picker-close");

let allSims = [];
let activeFilter = "all";

document.querySelectorAll(".filter-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeFilter = btn.dataset.filter;
    renderGallery();
  });
});

const TYPE_LABELS = { slime: "Slime Mold", boids: "Boids", fluid: "Fluid", cubes: "Cubes", automaton: "Automaton" };

function formatDate(ts) {
  return new Date(ts * 1000).toLocaleDateString(undefined, {
    month: "short", day: "numeric", year: "numeric",
  });
}

function createCard(sim) {
  const card = document.createElement("div");
  card.className = "slime-card";
  const previewStyle = sim.preview
    ? `style="background-image: url('${sim.preview}'); background-size: cover; background-position: center;"`
    : "";
  card.innerHTML = `
    <div class="card-preview" ${previewStyle}>${sim.preview ? "" : "no preview"}</div>
    <div class="card-info">
      <div class="card-top-row">
        <span class="card-name">${sim.name}</span>
        <span class="type-badge type-badge--${sim.type}">${TYPE_LABELS[sim.type] ?? sim.type}</span>
      </div>
      <span class="card-meta">${sim.author} &middot; ${formatDate(sim.created_at)}</span>
    </div>
  `;
  card.addEventListener("click", () => {
    window.location.href = `simulation.html?id=${sim.id}`;
  });
  return card;
}

async function createSim(type) {
  const res = await fetch(`${API}/api/slimes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, name: `New ${TYPE_LABELS[type]}`, author: "Anonymous" }),
  });
  if (!res.ok) throw new Error("Failed to create");
  return res.json();
}

function renderGallery() {
  const filtered = activeFilter === "all" ? allSims : allSims.filter((s) => s.type === activeFilter);
  grid.innerHTML = "";
  filtered.forEach((s) => grid.appendChild(createCard(s)));
  if (filtered.length === 0) {
    const empty = document.createElement("div");
    empty.className = "gallery-empty";
    empty.textContent = allSims.length === 0
      ? "No simulations yet. Hit + New to get started."
      : `No ${activeFilter} simulations yet.`;
    grid.appendChild(empty);
  }
}

function populateTypePreviews(sims) {
  const previews = { ...TYPE_PREVIEWS };
  for (const sim of sims) {
    if (sim.preview && !previews[sim.type]) previews[sim.type] = sim.preview;
  }
  document.querySelectorAll(".type-option").forEach((btn) => {
    const preview = btn.querySelector(".type-preview");
    const img = previews[btn.dataset.type];
    if (img) {
      preview.style.backgroundImage = `url('${img}')`;
      preview.style.backgroundSize = "cover";
      preview.style.backgroundPosition = "center";
    }
  });
}

async function loadGallery() {
  try {
    const res = await fetch(`${API}/api/slimes`);
    if (!res.ok) throw new Error();
    allSims = await res.json();
    renderGallery();
    populateTypePreviews(allSims);
  } catch {
    grid.innerHTML = `<div class="gallery-empty">Could not reach backend.</div>`;
  }
}

// Type picker
newBtn.addEventListener("click", () => {
  picker.classList.remove("hidden");
  populateTypePreviews(allSims);
});
pickerClose.addEventListener("click", () => picker.classList.add("hidden"));
picker.addEventListener("click", (e) => { if (e.target === picker) picker.classList.add("hidden"); });

document.querySelectorAll(".type-option").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const type = btn.dataset.type;
    btn.disabled = true;
    try {
      const sim = await createSim(type);
      window.location.href = `simulation.html?id=${sim.id}`;
    } catch {
      btn.disabled = false;
      alert("Could not reach backend.");
    }
  });
});

loadGallery();
