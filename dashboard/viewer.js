const params = new URLSearchParams(window.location.search);
const imgParam = params.get("img") || "";

const elements = {
  subtitle: document.getElementById("subtitle"),
  viewImage: document.getElementById("viewImage"),
  details: document.getElementById("details"),
  openRaw: document.getElementById("openRaw"),
};

function parseDetections(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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

function formatCoordinate(group) {
  if (!group) return "-";
  // Prefer metric if present
  if (group.north_m !== undefined && group.east_m !== undefined) {
    return `N: ${group.north_m} m\nE: ${group.east_m} m${group.altitude_m ? `\nAlt: ${group.altitude_m} m` : ''}`;
  }
  if (group.latitude !== undefined && group.longitude !== undefined) {
    return `Latitude: ${group.latitude} \nLongitude: ${group.longitude}`;
  }
  return Object.entries(group).map(([k, v]) => `${k}: ${v}`).join(" | ");
}

async function loadViewer() {
  if (!imgParam) {
    elements.subtitle.textContent = "No image specified.";
    elements.details.innerHTML = "";
    return;
  }

  try {
    const resp = await fetch("../detections.json", { cache: "no-store" });
    const text = await resp.text();
    const detections = text ? parseDetections(text) : [];

    const match = detections.find((d) => {
      const img = d.image || "";
      const basename = img.split(/[\\/]/).pop();
      return basename === imgParam;
    });

    let src = `../detections/${imgParam}`;
    if (match && match.image) {
      src = resolveImageSrc(match.image);
    }

    elements.viewImage.src = src;
    elements.openRaw.href = src;

    if (!match) {
      elements.subtitle.textContent = `Image: ${imgParam}`;
      elements.details.innerHTML = `<p>No matching detection metadata found in detections.json.</p>`;
      return;
    }

    elements.subtitle.textContent = match.time || "";

    const detailsHtml = `
      <p><span class="pill">Time</span> ${match.time ?? "-"}</p>
      <p><span class="pill">Frame</span> ${match.frame ?? "-"}</p>
      <p><span class="pill">Confidence</span> ${Number(match.confidence ?? 0).toFixed(2)}</p>
      <p><span class="pill">BBox</span> [${(match.bbox || []).join(", ")}]</p>
      <p><span class="pill">Drone</span><br>${formatCoordinate(match.drone_position)}</p>
      <p><span class="pill">Human</span><br>${formatCoordinate(match.human_position)}</p>
      <p><span class="pill">Coordinate system</span> ${match.coordinate_system ?? "-"}</p>
    `;

    elements.details.innerHTML = detailsHtml;
  } catch (err) {
    elements.subtitle.textContent = "Error loading detections.json";
    elements.details.innerHTML = `<p>${err.message}</p>`;
  }
}

loadViewer();
