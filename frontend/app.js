const API = "http://localhost:6000";
const form = document.getElementById("params-form");
const status = document.getElementById("status");
const runBtn = document.getElementById("run-btn");

function setStatus(msg, type = "") {
  status.textContent = msg;
  status.className = type;
}

// Load default params from backend on page load
async function loadDefaults() {
  try {
    const res = await fetch(`${API}/api/params`);
    if (!res.ok) throw new Error("Backend unreachable");
    const params = await res.json();
    for (const [key, val] of Object.entries(params)) {
      const input = form.elements[key];
      if (input) input.value = val;
    }
    setStatus("Connected to backend", "ok");
  } catch {
    setStatus("Backend offline — using defaults", "error");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  runBtn.disabled = true;
  setStatus("Sending...");

  const data = Object.fromEntries(
    Array.from(form.elements)
      .filter((el) => el.name)
      .map((el) => [el.name, Number(el.value)])
  );

  try {
    const res = await fetch(`${API}/api/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    setStatus("Simulation started", "ok");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    runBtn.disabled = false;
  }
});

loadDefaults();
