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

const TYPE_LABELS = { slime: "Slime Mold", boids: "Boids", cells: "Cells", fluid: "Fluid" };

const SCHEMAS = {
  slime: [
    { group: "Agents", fields: [
      { name: "num_agents",    label: "Agent Count",       min: 1,    max: 100000, step: 1    },
      { name: "step_size",     label: "Step Size",         min: 0.1,  max: 10,     step: 0.1  },
    ]},
    { group: "Sensors", fields: [
      { name: "sensor_angle",    label: "Sensor Angle (°)",  min: 1,  max: 180, step: 1   },
      { name: "sensor_distance", label: "Sensor Distance",   min: 1,  max: 50,  step: 1   },
      { name: "rotation_angle",  label: "Rotation Angle (°)",min: 1,  max: 180, step: 1   },
    ]},
    { group: "Trail", fields: [
      { name: "deposit_amount", label: "Deposit Amount", min: 0.1, max: 50, step: 0.1 },
      { name: "decay_rate",     label: "Decay Rate",     min: 0.01, max: 1, step: 0.01 },
      { name: "diffuse_rate",   label: "Diffuse Rate",   min: 0.01, max: 1, step: 0.01 },
    ]},
    { group: "Canvas", fields: [
      { name: "width",  label: "Width",  min: 100, max: 2000, step: 10 },
      { name: "height", label: "Height", min: 100, max: 2000, step: 10 },
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
      { name: "alignment_weight",   label: "Alignment",   min: 0, max: 5, step: 0.1 },
      { name: "cohesion_weight",    label: "Cohesion",    min: 0, max: 5, step: 0.1 },
      { name: "separation_weight",  label: "Separation",  min: 0, max: 5, step: 0.1 },
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
      { name: "theme",         label: "Theme (0=turbo 1=ocean 2=inferno 3=plasma)", min: 0, max: 3, step: 1 },
      { name: "color_change",  label: "Auto Color Cycle (0/1)", min: 0, max: 1,   step: 1    },
      { name: "color_speed",   label: "Cycle Speed (frames)",   min: 30, max: 600, step: 10  },
    ]},
    { group: "Advanced", fields: [
      { name: "brush_size",    label: "Brush Size",    min: 4, max: 40, step: 1 },
      { name: "mouse_force",   label: "Mouse Force",   min: 10, max: 200, step: 5 },
      { name: "project_iters", label: "Solver Quality", min: 5, max: 40, step: 1 },
    ]},
  ],

  cells: [
    { group: "Grid", fields: [
      { name: "grid_width",  label: "Grid Width",  min: 10, max: 500, step: 1 },
      { name: "grid_height", label: "Grid Height", min: 10, max: 500, step: 1 },
    ]},
    { group: "Birth Rule", fields: [
      { name: "birth_min", label: "Min Neighbors", min: 0, max: 8, step: 1 },
      { name: "birth_max", label: "Max Neighbors", min: 0, max: 8, step: 1 },
    ]},
    { group: "Survival Rule", fields: [
      { name: "survival_min", label: "Min Neighbors", min: 0, max: 8, step: 1 },
      { name: "survival_max", label: "Max Neighbors", min: 0, max: 8, step: 1 },
    ]},
    { group: "Initial State", fields: [
      { name: "initial_density", label: "Density (0–1)", min: 0, max: 1, step: 0.01 },
    ]},
  ],
};

function buildForm(type) {
  const schema = SCHEMAS[type] ?? SCHEMAS.slime;
  form.innerHTML = "";
  schema.forEach(({ group, fields }) => {
    const groupEl = document.createElement("div");
    groupEl.className = "param-group";
    groupEl.innerHTML = `<h2>${group}</h2>`;
    fields.forEach(({ name, label, min, max, step }) => {
      const lbl = document.createElement("label");
      lbl.innerHTML = `${label}<input type="number" name="${name}" min="${min}" max="${max}" step="${step}" />`;
      groupEl.appendChild(lbl);
    });
    form.appendChild(groupEl);
  });
}

function fillForm(params) {
  for (const [key, val] of Object.entries(params)) {
    const input = form.elements[key];
    if (input) input.value = val;
  }
}

function getFormParams() {
  return Object.fromEntries(
    Array.from(form.elements)
      .filter((el) => el.name)
      .map((el) => [el.name, Number(el.value)])
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
    document.title = `${sim.name} | Cellular Simulations`;
    currentSim = sim;
    const p = sim.params ?? {};
    const pw = (p.grid_width ?? p.width ?? 320) * (p.cell_size ?? 1);
    const ph = (p.grid_height ?? p.height ?? 240) * (p.cell_size ?? 1);
    simPlaceholder.style.width  = pw + "px";
    simPlaceholder.style.height = ph + "px";
    if (sim.preview) {
      simPlaceholder.style.backgroundImage = `url('${sim.preview}')`;
      simPlaceholder.style.backgroundSize = "cover";
    }
    buildForm(sim.type);
    fillForm(sim.params);
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  }
}

const simStream      = document.getElementById("sim-stream");
const simPlaceholder = document.getElementById("sim-placeholder");
simPlaceholder.addEventListener("click", () => runBtn.click());

let currentSim = null;  // holds loaded sim object
let mouseDrawing = false;
let interactThrottle = null;

function sendMouse(clientX, clientY, drawing) {
  if (!currentSim || currentSim.type !== "fluid") return;
  const cs    = currentSim.params.cell_size   ?? 3;
  const gCols = currentSim.params.grid_width  ?? 320;
  const gRows = currentSim.params.grid_height ?? 240;
  const rect  = simStream.getBoundingClientRect();
  // Convert display pixels to grid cell coords using known sim dimensions
  const c = Math.max(0, Math.min(gCols - 1,
    Math.floor(((clientX - rect.left) / rect.width)  * gCols)));
  const r = Math.max(0, Math.min(gRows - 1,
    Math.floor(((clientY - rect.top)  / rect.height) * gRows)));
  // Always send mousedown; throttle mousemove to every 30ms
  if (!drawing || !interactThrottle) {
    if (drawing) {
      interactThrottle = setTimeout(() => { interactThrottle = null; }, 30);
    }
    fetch(`${API}/api/interact/${simId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: currentSim.type, r, c, drawing }),
    }).catch(() => {});
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
    simStream.classList.remove("hidden");
    simPlaceholder.classList.add("hidden");
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
    canvas.width  = (p.grid_width  ?? 320) * (p.cell_size ?? 3);
    canvas.height = (p.grid_height ?? 240) * (p.cell_size ?? 3);
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
