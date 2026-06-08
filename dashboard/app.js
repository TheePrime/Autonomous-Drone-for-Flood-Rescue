const detectionsUrl = "../detections.json";

const elements = {
  totalDetections: document.getElementById("totalDetections"),
  latestConfidence: document.getElementById("latestConfidence"),
  latestFrame: document.getElementById("latestFrame"),
  latestDrone: document.getElementById("latestDrone"),
  latestImage: document.getElementById("latestImage"),
  latestDetails: document.getElementById("latestDetails"),
  lastUpdated: document.getElementById("lastUpdated"),
  logCount: document.getElementById("logCount"),
  logBody: document.getElementById("logBody"),
  fileInput: document.getElementById("fileInput"),
};

let manualMode = false;
let lastLoadedSignature = "";

function parseDetections(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function formatBox(bbox) {
  return `[${bbox.join(", ")}]`;
}

function formatCoordinate(group) {
  if (!group) {
    return "-";
  }

  const values = Object.entries(group)
    .map(([key, value]) => `${key}: ${value}`)
    .join(" | ");

  return values || "-";
}

function resolveImageSrc(imagePath) {
  if (!imagePath) {
    return "";
  }

  if (/^[a-zA-Z]:[\\/]/.test(imagePath) || imagePath.startsWith("file:")) {
    const filename = imagePath.split(/[\\/]/).pop();
    return filename ? `../detections/${filename}` : "";
  }

  return `../${imagePath.replace(/^\.\//, "")}`;
}

function renderDetections(detections) {
  elements.totalDetections.textContent = detections.length.toString();
  elements.logCount.textContent = `${detections.length} rows`;

  if (!detections.length) {
    elements.latestConfidence.textContent = "0.00";
    elements.latestFrame.textContent = "-";
    elements.latestDrone.textContent = "-";
    elements.latestImage.removeAttribute("src");
    elements.latestDetails.innerHTML = "<p>No detections loaded yet.</p>";
    elements.lastUpdated.textContent = "Waiting for data...";
    elements.logBody.innerHTML = "";
    return;
  }

  const latest = detections[detections.length - 1];
  elements.latestConfidence.textContent = Number(latest.confidence).toFixed(2);
  elements.latestFrame.textContent = latest.frame ?? "-";
  elements.latestDrone.textContent = formatCoordinate(latest.drone_position);
  elements.latestDetails.innerHTML = `
    <p><span class="pill">Time</span> ${latest.time ?? "-"}</p>
    <p><span class="pill">BBox</span> ${formatBox(latest.bbox ?? [])}</p>
    <p><span class="pill">Human</span> ${formatCoordinate(latest.human_position)}</p>
    <p><span class="pill">Image</span> ${latest.image ?? "-"}</p>
  `;
  elements.lastUpdated.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

  if (latest.image) {
    elements.latestImage.src = resolveImageSrc(latest.image);
  }

  elements.logBody.innerHTML = detections
    .slice()
    .reverse()
    .map(
      (entry) => `
        <tr>
          <td>${entry.time ?? "-"}</td>
          <td>${entry.frame ?? "-"}</td>
          <td>${Number(entry.confidence ?? 0).toFixed(2)}</td>
          <td>${formatBox(entry.bbox ?? [])}</td>
          <td>${formatCoordinate(entry.drone_position)}</td>
          <td>${formatCoordinate(entry.human_position)}</td>
        </tr>
      `,
    )
    .join("");
}

function buildSignature(text) {
  return text.trim();
}

async function loadDashboard() {
  if (manualMode) {
    return;
  }

  try {
    const response = await fetch(detectionsUrl, { cache: "no-store" });
    const text = await response.text();

    const signature = buildSignature(text);
    if (signature === lastLoadedSignature) {
      return;
    }

    lastLoadedSignature = signature;

    const detections = text ? parseDetections(text) : [];
    renderDetections(detections);
  } catch (error) {
    if (!lastLoadedSignature) {
      elements.lastUpdated.textContent = "Fetch blocked. Load detections.json manually.";
      elements.latestDetails.innerHTML = `<p>${error.message}</p>`;
    }
  }
}

elements.fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];

  if (!file) {
    return;
  }

  manualMode = true;
  const text = await file.text();
  const detections = text ? parseDetections(text) : [];
  renderDetections(detections);
});

loadDashboard();
setInterval(loadDashboard, 1000);