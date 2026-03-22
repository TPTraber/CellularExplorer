const API = "http://localhost:7070";

const urlParams = new URLSearchParams(window.location.search);
const simId = urlParams.get("id");
if (!simId) window.location.href = "index.html";

const form = document.getElementById("params-form");
const statusEl = document.getElementById("status");
const runBtn = document.getElementById("run-btn");
const saveBtn = document.getElementById("save-btn");
const nameInput = document.getElementById("slime-name");
document.getElementById("edit-name-btn").addEventListener("click", () => {
  nameInput.focus();
  nameInput.select();
});
const authorEl = document.getElementById("slime-author");
const typeBadge = document.getElementById("type-badge");

const TYPE_LABELS = { slime: "Slime Mold", boids: "Boids", cells: "Cells", fluid: "Fluid", cubes: "Cubes" };

const SCHEMAS = {
  slime: [
    { group: "Agents", fields: [
      { name: "n_agents",   label: "Agent Count",  min: 1000,  max: 200000, step: 1000 },
      { name: "n_species",  label: "Species (1-3)", min: 1,    max: 3,      step: 1    },
      { name: "colors", label: "Colors", type: "colorpickers", keys: ["color_0", "color_1", "color_2"], defaults: ["#00ffff", "#ff00ff", "#0000ff"] },
    ]},
    { group: "Sensors", fields: [
      { name: "sensor_distance", label: "Sensor Distance",   min: 1,  max: 30,  step: 0.5 },
      { name: "sensor_size",     label: "Sensor Kernel Size", min: 1,  max: 15,  step: 2   },
      { name: "sensor_angle",    label: "Sensor Angle (°)",   min: 1,  max: 180, step: 1   },
      { name: "turn_speed",      label: "Turn Speed (°)",     min: 1,  max: 90,  step: 1   },
    ]},
    { group: "Trail", fields: [
      { name: "deposit_amount",   label: "Deposit Amount",   min: 10,  max: 255, step: 5   },
      { name: "evaporation_speed",label: "Evaporation Speed",min: 0.1, max: 10,  step: 0.1 },
      { name: "diffusion_speed",  label: "Diffusion Speed",  min: 0,   max: 1,   step: 0.01},
    ]},
    { group: "Grid", fields: [
      { name: "grid_width",   label: "Grid Width",    min: 100, max: 1000, step: 50 },
      { name: "grid_height",  label: "Grid Height",   min: 100, max: 1000, step: 50 },
      { name: "display_size", label: "Display Size",  min: 200, max: 1200, step: 50 },
    ]},
  ],

  boids: [
    { group: "Flock", fields: [
      { name: "num_boids",  label: "Boid Count", min: 1,   max: 10000, step: 1   },
      { name: "max_speed",  label: "Max Speed",  min: 0.1, max: 20,    step: 0.1 },
      { name: "min_speed",  label: "Min Speed",  min: 0.1, max: 20,    step: 0.1 },
    ]},
    { group: "Perception", fields: [
      { name: "perception_radius",  label: "Perception Radius",  min: 1, max: 300, step: 1 },
      { name: "separation_radius",  label: "Separation Radius",  min: 1, max: 150, step: 1 },
    ]},
    { group: "Weights", fields: [
      { name: "alignment_weight",   label: "Alignment",   min: 0, max: 5, step: 0.01 },
      { name: "cohesion_weight",    label: "Cohesion",    min: 0, max: 5, step: 0.01 },
      { name: "separation_weight",  label: "Separation",  min: 0, max: 5, step: 0.01 },
    ]},
    { group: "Canvas", fields: [
      { name: "width",  label: "Width",  min: 100, max: 2000, step: 10 },
      { name: "height", label: "Height", min: 100, max: 2000, step: 10 },
    ]},
  ],

  fluid: [
    { group: "Simulation", fields: [
      { name: "swirl_strength", label: "Swirl Strength", min: 0, max: 0.05, step: 0.001 },
      { name: "dt",             label: "Time Step",      min: 0.01, max: 0.2, step: 0.01 },
    ]},
    { group: "Dye", fields: [
      { name: "decay",           label: "Decay (0.98=fast, 0.999=slow)", min: 0.95, max: 0.999, step: 0.001 },
      { name: "source_strength", label: "Source Strength", min: 0.01, max: 0.3, step: 0.01 },
      { name: "dye_amount",      label: "Mouse Dye Amount", min: 0.1, max: 3, step: 0.1 },
    ]},
    { group: "Color", fields: [
      { name: "theme", label: "Theme", type: "swatches", options: [
          { value: 0, label: "Turbo",   gradient: "linear-gradient(to right,#30123b,#4145ab,#39a2fc,#1bcfd4,#61fc6c,#efcf2e,#e95807,#c82103)" },
          { value: 1, label: "Ocean",   gradient: "linear-gradient(to right,#000033,#003366,#0066aa,#33ccff,#99eeff)" },
          { value: 2, label: "Inferno", gradient: "linear-gradient(to right,#000,#8b0000,#ff4500,#ffa500,#fff)" },
          { value: 3, label: "Magma",   gradient: "linear-gradient(to right,#000004,#3b0f70,#8c2981,#de4968,#fea16e,#fcfdbf)" },
          { value: 4, label: "Viridis", gradient: "linear-gradient(to right,#440154,#31688e,#21918c,#35b779,#fde725)" },
        ]},
      { name: "color_speed",   label: "Cycle Speed (frames)",   min: 30, max: 600, step: 10  },
    ]},
    { group: "Advanced", fields: [
      { name: "brush_size",    label: "Brush Size",    min: 4, max: 40, step: 1 },
      { name: "mouse_force",   label: "Mouse Force",   min: 10, max: 200, step: 5 },
      { name: "project_iters", label: "Solver Quality", min: 5, max: 40, step: 1 },
    ]},
  ],

  cubes: [
    { group: "Grid", fields: [
      { name: "gridsize_x", label: "Grid X", min: 10, max: 100, step: 5 },
      { name: "gridsize_y", label: "Grid Y", min: 10, max: 100, step: 5 },
      { name: "gridsize_z", label: "Grid Z", min: 10, max: 100, step: 5 },
    ]},
    { group: "Display", fields: [
      { name: "screensize", label: "Screen Size", min: 400, max: 1200, step: 50 },
    ]},
    { group: "Initial State", fields: [
      { name: "density", label: "Density (0–1)", min: 0.01, max: 0.5, step: 0.01 },
    ]},
  ],

  automaton: [
    { group: "Rule", fields: [
      { name: "rule_number", label: "Rule (8-bit binary)", type: "binary8" },
      { name: "wrap",        label: "Wrap (0/1)",   min: 0,   max: 1,   step: 1 },
    ]},
    { group: "Display", fields: [
      { name: "width",        label: "Width",        min: 50,  max: 500, step: 10 },
      { name: "display_rows", label: "Visible Rows", min: 50,  max: 400, step: 10 },
      { name: "cell_size",    label: "Cell Size",    min: 1,   max: 20,  step: 1  },
      { name: "fps",          label: "FPS",          min: 1,   max: 30,  step: 1  },
    ]},
  ],
};

function buildSwatches(field) {
  const wrap = document.createElement("div");
  wrap.className = "swatch-field";
  const lbl = document.createElement("span");
  lbl.className = "swatch-label";
  lbl.textContent = field.label;
  wrap.appendChild(lbl);
  const row = document.createElement("div");
  row.className = "swatch-row";
  const hidden = document.createElement("input");
  hidden.type = "hidden";
  hidden.name = field.name;
  hidden.value = field.options[0].value;
  field.options.forEach((opt) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "swatch-btn";
    btn.title = opt.label;
    btn.style.background = opt.gradient;
    btn.dataset.value = opt.value;
    btn.addEventListener("click", () => {
      row.querySelectorAll(".swatch-btn").forEach((b) => b.classList.remove("swatch-active"));
      btn.classList.add("swatch-active");
      hidden.value = opt.value;
    });
    row.appendChild(btn);
  });
  wrap.appendChild(row);
  wrap.appendChild(hidden);
  return wrap;
}

function buildColorPickers(field) {
  const wrap = document.createElement("label");
  wrap.className = "colorpickers-field";
  wrap.innerHTML = `<span>${field.label}</span>`;
  const row = document.createElement("div");
  row.className = "colorpickers-row";
  field.keys.forEach((key, i) => {
    const inp = document.createElement("input");
    inp.type = "color";
    inp.name = key;
    inp.className = "color-dot";
    inp.value = field.defaults[i];
    inp.dataset.index = i;
    row.appendChild(inp);
  });
  wrap.appendChild(row);
  return wrap;
}

function syncColorPickers() {
  const nSpecies = parseInt(form.elements["n_species"]?.value ?? 1);
  form.querySelectorAll("input.color-dot").forEach((inp) => {
    inp.style.display = parseInt(inp.dataset.index) < nSpecies ? "" : "none";
  });
}

function buildForm(type) {
  const schema = SCHEMAS[type] ?? SCHEMAS.slime;
  form.innerHTML = "";
  schema.forEach(({ group, fields }) => {
    const groupEl = document.createElement("div");
    groupEl.className = "param-group";
    groupEl.innerHTML = `<h2>${group}</h2>`;
    fields.forEach((field) => {
      if (field.type === "swatches") {
        groupEl.appendChild(buildSwatches(field));
      } else if (field.type === "colorpickers") {
        groupEl.appendChild(buildColorPickers(field));
      } else if (field.type === "binary8") {
        const lbl = document.createElement("label");
        lbl.innerHTML = `${field.label}<input type="text" name="${field.name}" maxlength="8" pattern="[01]{8}" placeholder="01101110" class="binary8-input" />`;
        groupEl.appendChild(lbl);
      } else {
        const lbl = document.createElement("label");
        lbl.innerHTML = `${field.label}<input type="number" name="${field.name}" min="${field.min}" max="${field.max}" step="${field.step}" />`;
        groupEl.appendChild(lbl);
      }
    });
    form.appendChild(groupEl);
  });
}

function fillForm(params) {
  for (const [key, val] of Object.entries(params)) {
    const input = form.elements[key];
    if (!input) continue;
    if (input.type === "color") input.value = val;
    else if (input.classList.contains("binary8-input")) input.value = parseInt(val).toString(2).padStart(8, "0");
    else input.value = val;
    // Sync swatch active state if this is a hidden swatch input
    const row = input.previousElementSibling;
    if (row && row.classList.contains("swatch-row")) {
      row.querySelectorAll(".swatch-btn").forEach((b) => {
        b.classList.toggle("swatch-active", Number(b.dataset.value) === Number(val));
      });
    }
  }
}

function getFormParams() {
  return Object.fromEntries(
    Array.from(form.elements)
      .filter((el) => el.name)
      .map((el) => [
        el.name,
        el.type === "color"
          ? el.value
          : el.classList.contains("binary8-input")
            ? parseInt(el.value, 2)
            : Number(el.value),
      ])
  );
}

function setStatus(msg, type = "") {
  statusEl.textContent = msg;
  statusEl.className = type;
}

async function load() {
  try {
    const res = await fetch(`${API}/api/slimes/${simId}`);
    if (!res.ok) throw new Error("Not found");
    const sim = await res.json();
    nameInput.value = sim.name;
    authorEl.textContent = `by ${sim.author}`;
    typeBadge.textContent = TYPE_LABELS[sim.type] ?? sim.type;
    typeBadge.className = `type-badge type-badge--${sim.type}`;
    document.title = `${sim.name} | AutomatonLab`;
    currentSim = sim;
    const p = sim.params ?? {};
    const pw = p.display_size ?? (p.grid_width ?? p.width ?? 320) * (p.cell_size ?? 1);
    const ph = p.display_size ?? (p.grid_height ?? p.height ?? 240) * (p.cell_size ?? 1);
    simPlaceholder.style.width  = pw + "px";
    simPlaceholder.style.height = ph + "px";
    if (sim.preview) {
      simPlaceholder.style.backgroundImage = `url('${sim.preview}')`;
      simPlaceholder.style.backgroundSize = "cover";
    }
    buildForm(sim.type);
    fillForm(sim.params);
    if (sim.type === "slime") {
      syncColorPickers();
      form.elements["n_species"]?.addEventListener("input", syncColorPickers);
    }
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  }
}

const simStream      = document.getElementById("sim-stream");
const simPlaceholder = document.getElementById("sim-placeholder");
simPlaceholder.addEventListener("click", () => runBtn.click());

let currentSim = null;  // holds loaded sim object
let mouseDrawing = false;
let mouseWs = null;

function openMouseWs() {
  if (mouseWs && mouseWs.readyState <= WebSocket.OPEN) return;
  mouseWs = new WebSocket(`ws://localhost:7070/ws/interact/${simId}`);
  mouseWs.addEventListener("close", () => { mouseWs = null; });
  mouseWs.addEventListener("error", () => { mouseWs = null; });
}

function sendMouse(clientX, clientY, drawing) {
  if (!currentSim || currentSim.type !== "fluid") return;
  const gCols = currentSim.params.grid_width  ?? 320;
  const gRows = currentSim.params.grid_height ?? 240;
  const rect  = simStream.getBoundingClientRect();
  const c = Math.max(0, Math.min(gCols - 1,
    Math.floor(((clientX - rect.left) / rect.width)  * gCols)));
  const r = Math.max(0, Math.min(gRows - 1,
    Math.floor(((clientY - rect.top)  / rect.height) * gRows)));
  if (mouseWs && mouseWs.readyState === WebSocket.OPEN) {
    mouseWs.send(JSON.stringify({ r, c, drawing }));
  }
}

simStream.addEventListener("mousedown", (e) => {
  mouseDrawing = true;
  sendMouse(e.clientX, e.clientY, true);
});
simStream.addEventListener("mousemove", (e) => {
  if (mouseDrawing) sendMouse(e.clientX, e.clientY, true);
});
simStream.addEventListener("mouseup",   () => { mouseDrawing = false; sendMouse(0, 0, false); });
simStream.addEventListener("mouseleave",() => { mouseDrawing = false; sendMouse(0, 0, false); });

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  runBtn.disabled = true;
  setStatus("Saving...");
  try {
    // Save current params first so the stream uses them
    const res = await fetch(`${API}/api/slimes/${simId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: nameInput.value.trim() || "Unnamed", params: getFormParams() }),
    });
    if (!res.ok) throw new Error(`Save failed ${res.status}`);

    // Keep currentSim.params in sync so mouse coords are accurate
    if (currentSim) currentSim.params = { ...currentSim.params, ...getFormParams() };

    // Point img at the MJPEG stream (cache-bust so it restarts on re-run)
    simStream.src = `${API}/api/stream/${simId}?t=${Date.now()}`;
    openMouseWs();
    simStream.classList.remove("hidden");
    simPlaceholder.classList.add("hidden");
    runBtn.textContent = "Reset";
    setStatus("Running", "ok");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    runBtn.disabled = false;
  }
});


function capturePreview() {
  if (simStream.classList.contains("hidden")) return null;
  try {
    const canvas = document.createElement("canvas");
    const p = currentSim?.params ?? {};
    const d = p.display_size;
    canvas.width  = d ?? (p.grid_width  ?? 320) * (p.cell_size ?? 3);
    canvas.height = d ?? (p.grid_height ?? 240) * (p.cell_size ?? 3);
    canvas.getContext("2d").drawImage(simStream, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.75);
  } catch {
    return null;
  }
}

saveBtn.addEventListener("click", async () => {
  saveBtn.disabled = true;
  setStatus("Saving...");
  try {
    const preview = capturePreview();
    const body = { name: nameInput.value.trim() || "Unnamed", params: getFormParams() };
    if (preview) body.preview = preview;
    const res = await fetch(`${API}/api/slimes/${simId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    setStatus("Saved", "ok");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    saveBtn.disabled = false;
  }
});

load();
