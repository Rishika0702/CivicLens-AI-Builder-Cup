let map;
let markers = [];
let geminiConfigured = false;

const samples = {
  pothole: {
    description:
      "A large pothole near Jubilee Hills Junction is causing accidents. Vehicles are swerving into traffic and someone could get hurt.",
    lat: 17.4318,
    lng: 78.4071,
  },
  streetlight: {
    description:
      "Street lights are not working near Kukatpally Metro after sunset. The dark stretch feels unsafe for pedestrians.",
    lat: 17.4845,
    lng: 78.4111,
  },
  water: {
    description: "నీటి పైపు లీక్ అవుతోంది. ఫుట్‌పాత్ దగ్గర నీరు నిరంతరం కారుతోంది.",
    lat: 17.4375,
    lng: 78.4483,
  },
};

function html(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

async function refresh() {
  const [stats, incidents] = await Promise.all([
    fetch("/api/stats").then((response) => response.json()),
    fetch("/api/incidents").then((response) => response.json()),
  ]);

  for (const [id, key] of Object.entries({
    reports: "reports",
    incidents: "incidents",
    merged: "duplicates_merged",
    critical: "critical",
  })) {
    document.getElementById(id).textContent = stats[key];
  }

  document.getElementById("incident-list").innerHTML = incidents
    .map(
      (incident) => `
        <div class="incident">
          <div>
            <b>${html(incident.category)}</b>
            <span class="badge">${html(incident.status)}</span>
            <small>${html(incident.id)} • ${incident.report_count} reports • urgency ${incident.max_urgency}/5</small>
            <small>${html(incident.title)}</small>
          </div>
          <div class="score">${incident.priority}<small>PRIORITY</small></div>
        </div>
      `,
    )
    .join("");

  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];
  incidents.forEach((incident) => {
    const marker = L.circleMarker([incident.lat, incident.lng], {
      radius: 12 + incident.report_count * 0.4,
      color: "#49e7c3",
      weight: 3,
      fillColor: incident.max_urgency >= 5 ? "#ff956d" : "#49e7c3",
      fillOpacity: 0.55,
    }).addTo(map);
    marker.bindPopup(
      `<b>${html(incident.category)}</b><br>${incident.report_count} reports<br>Urgency ${incident.max_urgency}/5<br>${html(incident.id)}`,
    );
    markers.push(marker);
  });
}

function loadSample() {
  const sample = samples[document.getElementById("sample").value];
  document.getElementById("description").value = sample.description;
  document.getElementById("lat").value = sample.lat;
  document.getElementById("lng").value = sample.lng;
  document.getElementById("photo").value = "";
  document.getElementById("file-name").textContent = "";
  document.getElementById("result").textContent = "";
  document.getElementById("response-json").style.display = "none";
}

function init() {
  map = L.map("map", { zoomControl: false }).setView([17.451, 78.445], 12);
  L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    { attribution: "Tiles &copy; Esri", maxZoom: 19 },
  ).addTo(map);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  loadSample();
  refresh();
  fetch("/health")
    .then((response) => response.json())
    .then((health) => {
      geminiConfigured = health.gemini_configured;
      document.getElementById("mode").textContent =
        (geminiConfigured ? "GEMINI CONFIGURED · " : "LOCAL RULES CLASSIFIER · ") +
        (health.mode === "firestore" ? "FIRESTORE" : "DEMO MODE");
      if (!geminiConfigured) {
        const notice = document.getElementById("gemini-notice");
        notice.textContent =
          "Gemini API key is not configured. Submissions use the local fallback classifier. To enable Gemini, add GEMINI_API_KEY as a secret in your deployment settings.";
        notice.style.display = "block";
      }
    });
}

document.getElementById("sample").addEventListener("change", loadSample);
document.getElementById("photo").addEventListener("change", (event) => {
  document.getElementById("file-name").textContent =
    event.target.files[0]?.name || "";
});

document.getElementById("voice").addEventListener("click", () => {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Browser speech recognition is unavailable. Use Chrome or type the complaint.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = document.getElementById("voice-lang").value;
  recognition.onresult = (event) => {
    document.getElementById("description").value =
      event.results[0][0].transcript;
  };
  recognition.onerror = (event) => alert(`Speech input error: ${event.error}`);
  recognition.start();
});

document.getElementById("complaint-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("submit");
  const result = document.getElementById("result");
  const responseJson = document.getElementById("response-json");
  button.disabled = true;
  result.textContent = "Classifying complaint and clustering incident…";
  responseJson.style.display = "none";

  try {
    const file = document.getElementById("photo").files[0];
    let encoded = null;
    if (file) {
      if (file.size > 3_000_000) {
        throw new Error("Choose an image smaller than 3MB");
      }
      encoded = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    const response = await fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        description: document.getElementById("description").value,
        lat: Number(document.getElementById("lat").value),
        lng: Number(document.getElementById("lng").value),
        image_base64: encoded,
        image_mime: file?.type || "image/jpeg",
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to submit");
    }

    result.textContent =
      `✓ ${data.report.id} → ${data.incident.id} · ${data.triage.category} · ` +
      `urgency ${data.triage.urgency}/5 · ` +
      `${data.duplicate ? "merged with existing incident" : "new incident created"} · ` +
      `${data.triage.ai_provider}`;
    if (!geminiConfigured) {
      result.textContent +=
        "\nGemini API key is not configured; this used the local fallback. Add GEMINI_API_KEY in your deployment settings to enable Gemini.";
    }
    responseJson.textContent = JSON.stringify(data, null, 2);
    responseJson.style.display = "block";
    await refresh();
  } catch (error) {
    result.textContent = `Error: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

init();
