const detectionsUrl = "../detections.json";

const elements = {
  totalDetections: document.getElementById("totalDetections"),
  latestConfidence: document.getElementById("latestConfidence"),
  latestFrame: document.getElementById("latestFrame"),
  latestDrone: document.getElementById("latestDrone"),
  latestImage: document.getElementById("latestImage"),
  latestDetails: document.getElementById("latestDetails"),
  lastUpdated: document.getElementById("lastUpdated"),
  groupCount: document.getElementById("groupCount"),
  galleryCount: document.getElementById("galleryCount"),
  logCount: document.getElementById("logCount"),
  logBody: document.getElementById("logBody"),
  groupList: document.getElementById("groupList"),
  gallery: document.getElementById("gallery"),
  fileInput: document.getElementById("fileInput"),
  clearViewBtn: document.getElementById("clearViewBtn"),
};

let manualMode = false;
let lastLoadedSignature = "";
let activeDate = "all";
let currentDetections = [];

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

function getDateKey(entry) {
  if (entry.date) {
    return entry.date;
  }

  if (entry.time) {
    return String(entry.time).slice(0, 10);
  }

  return "unknown";
}

function groupDetectionsByDate(detections) {
  return detections.reduce((groups, entry) => {
    const dateKey = getDateKey(entry);
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(entry);
    return groups;
  }, {});
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
  currentDetections = detections;
  elements.totalDetections.textContent = detections.length.toString();
  elements.logCount.textContent = `${detections.length} rows`;

  const grouped = groupDetectionsByDate(detections);
  const dateKeys = Object.keys(grouped).sort().reverse();
  elements.groupCount.textContent = `${dateKeys.length} groups`;

  const filteredDetections = activeDate === "all"
    ? detections
    : detections.filter((entry) => getDateKey(entry) === activeDate);

  elements.galleryCount.textContent = `${filteredDetections.filter((entry) => entry.image).length} images`;

  elements.groupList.innerHTML = [
    `<button class="group-chip ${activeDate === "all" ? "active" : ""}" data-date="all">All dates <span>${detections.length}</span></button>`,
    ...dateKeys.map((dateKey) => `
      <button class="group-chip ${activeDate === dateKey ? "active" : ""}" data-date="${dateKey}">
        ${dateKey}
        <span>${grouped[dateKey].length}</span>
      </button>
    `),
  ].join("");

  if (!detections.length) {
    elements.latestConfidence.textContent = "0.00";
    elements.latestFrame.textContent = "-";
    elements.latestDrone.textContent = "-";
    elements.latestImage.removeAttribute("src");
    elements.latestDetails.innerHTML = "<p>No detections loaded yet.</p>";
    elements.lastUpdated.textContent = "Waiting for data...";
    elements.logBody.innerHTML = "";
    elements.groupList.innerHTML = "<p class='muted-copy'>No groups yet.</p>";
    elements.gallery.innerHTML = "";
    elements.groupCount.textContent = "0 groups";
    elements.galleryCount.textContent = "0 images";
    return;
  }

  const latest = filteredDetections.length ? filteredDetections[filteredDetections.length - 1] : detections[detections.length - 1];
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

  const galleryEntries = filteredDetections.filter((entry) => entry.image);

  elements.gallery.innerHTML = galleryEntries
    .slice()
    .reverse()
    .map(
      (entry) => `
        <figure class="shot-card">
          <a href="${resolveImageSrc(entry.image)}" target="_blank" rel="noreferrer">
            <img src="${resolveImageSrc(entry.image)}" alt="Detection screenshot">
          </a>
          <figcaption>
            <strong>${entry.time ?? "-"}</strong>
            <span>${Number(entry.confidence ?? 0).toFixed(2)} confidence</span>
          </figcaption>
        </figure>
      `,
    )
    .join("");

  elements.logBody.innerHTML = filteredDetections
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

  elements.groupList.querySelectorAll("[data-date]").forEach((button) => {
    button.addEventListener("click", () => {
      activeDate = button.dataset.date || "all";
      renderDetections(currentDetections);
    });
  });
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

elements.clearViewBtn.addEventListener("click", () => {
  activeDate = "all";
  renderDetections(currentDetections);
});

loadDashboard();
setInterval(loadDashboard, 1000);