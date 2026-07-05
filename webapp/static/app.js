(() => {
  "use strict";

  const form = document.getElementById("poster-form");
  const generateBtn = document.getElementById("generate-btn");
  const formError = document.getElementById("form-error");

  const themeGrid = document.getElementById("theme-grid");
  let selectedTheme = null;

  const distanceInput = document.getElementById("distance");
  const distanceValue = document.getElementById("distance-value");
  const distanceHint = document.getElementById("distance-hint");

  const sizePreset = document.getElementById("size-preset");
  const customSizeRow = document.getElementById("custom-size-row");
  const widthInput = document.getElementById("width");
  const heightInput = document.getElementById("height");

  const locateBtn = document.getElementById("locate-btn");
  const locateStatus = document.getElementById("locate-status");
  const latitudeInput = document.getElementById("latitude");
  const longitudeInput = document.getElementById("longitude");
  const mapPreviewRow = document.getElementById("map-preview-row");
  const mapPreviewFrame = document.getElementById("map-preview-frame");
  const mapPreviewLink = document.getElementById("map-preview-link");

  const previewEmpty = document.getElementById("preview-empty");
  const previewLoading = document.getElementById("preview-loading");
  const previewResult = document.getElementById("preview-result");
  const previewImage = document.getElementById("preview-image");
  const previewPdfNote = document.getElementById("preview-pdf-note");
  const progressMessage = document.getElementById("progress-message");
  const downloadLink = document.getElementById("download-link");

  let pollHandle = null;

  function showError(message) {
    formError.textContent = message;
    formError.hidden = false;
  }

  function clearError() {
    formError.hidden = true;
    formError.textContent = "";
  }

  function distanceGuide(meters) {
    if (meters <= 6000) return "Small / dense cities (e.g. Venice, Amsterdam center)";
    if (meters <= 12000) return "Medium cities, focused downtown (e.g. Paris, Barcelona)";
    return "Large metros, full city view (e.g. Tokyo, Mumbai)";
  }

  distanceInput.addEventListener("input", () => {
    distanceValue.textContent = distanceInput.value;
    distanceHint.textContent = distanceGuide(Number(distanceInput.value));
  });
  distanceValue.textContent = distanceInput.value;
  distanceHint.textContent = distanceGuide(Number(distanceInput.value));

  const SIZE_PRESETS = {
    "12x16": [12, 16],
    "12x12": [12, 12],
    "16x12": [16, 12],
    "3.6x3.6": [3.6, 3.6],
  };

  function applySizePreset() {
    const value = sizePreset.value;
    if (value === "custom") {
      customSizeRow.hidden = false;
      return;
    }
    customSizeRow.hidden = true;
    const [w, h] = SIZE_PRESETS[value];
    widthInput.value = w;
    heightInput.value = h;
  }
  sizePreset.addEventListener("change", applySizePreset);
  applySizePreset();

  async function loadThemes() {
    const res = await fetch("/api/themes");
    if (!res.ok) {
      showError("Could not load themes from the server.");
      return;
    }
    const themes = await res.json();
    themeGrid.innerHTML = "";
    themes.forEach((theme, index) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "theme-swatch";
      btn.setAttribute("role", "radio");
      btn.dataset.themeId = theme.id;
      btn.title = theme.description || theme.name;
      btn.innerHTML = `
        <span class="swatch-preview" style="background:${theme.bg}">
          <span style="background:${theme.water}"></span>
          <span style="background:${theme.parks}"></span>
          <span style="background:${theme.road_primary}"></span>
        </span>
        <span class="swatch-name">${theme.name}</span>
      `;
      btn.addEventListener("click", () => selectTheme(theme.id));
      themeGrid.appendChild(btn);
      if (index === 0 || theme.id === "terracotta") {
        selectedTheme = theme.id;
      }
    });
    selectTheme(selectedTheme);
  }

  function selectTheme(themeId) {
    selectedTheme = themeId;
    document.querySelectorAll(".theme-swatch").forEach((el) => {
      const isSelected = el.dataset.themeId === themeId;
      el.classList.toggle("selected", isSelected);
      el.setAttribute("aria-checked", String(isSelected));
    });
  }

  function showMapPreview(lat, lon) {
    const latDelta = 0.02;
    const lonDelta = latDelta / Math.max(Math.cos((lat * Math.PI) / 180), 0.15);
    const minLat = (lat - latDelta).toFixed(6);
    const maxLat = (lat + latDelta).toFixed(6);
    const minLon = (lon - lonDelta).toFixed(6);
    const maxLon = (lon + lonDelta).toFixed(6);

    const bbox = `${minLon}%2C${minLat}%2C${maxLon}%2C${maxLat}`;
    mapPreviewFrame.src = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lon}`;
    mapPreviewLink.href = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=15/${lat}/${lon}`;
    mapPreviewRow.hidden = false;
  }

  locateBtn.addEventListener("click", async () => {
    const city = document.getElementById("city").value.trim();
    const country = document.getElementById("country").value.trim();
    if (!city || !country) {
      locateStatus.textContent = "Enter a city and country first.";
      return;
    }
    locateStatus.textContent = "Looking up...";
    locateBtn.disabled = true;
    try {
      const res = await fetch("/api/geocode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, country }),
      });
      const data = await res.json();
      if (!res.ok) {
        locateStatus.textContent = data.detail || "Could not find that location.";
        return;
      }
      latitudeInput.value = data.latitude.toFixed(6);
      longitudeInput.value = data.longitude.toFixed(6);
      locateStatus.textContent = `Found: ${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}`;
      showMapPreview(data.latitude, data.longitude);
    } catch (err) {
      locateStatus.textContent = "Network error while looking up the location.";
    } finally {
      locateBtn.disabled = false;
    }
  });

  function setPreviewState(state) {
    previewEmpty.hidden = state !== "empty";
    previewLoading.hidden = state !== "loading";
    previewResult.hidden = state !== "result";
  }

  function stopPolling() {
    if (pollHandle !== null) {
      clearTimeout(pollHandle);
      pollHandle = null;
    }
  }

  async function pollJob(jobId) {
    try {
      const res = await fetch(`/api/jobs/${jobId}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Lost track of the generation job.");
      }

      if (data.status === "running" || data.status === "pending") {
        progressMessage.textContent = data.message || "Working...";
        pollHandle = setTimeout(() => pollJob(jobId), 1200);
        return;
      }

      if (data.status === "error") {
        showError(data.error || "Poster generation failed.");
        setPreviewState("empty");
        generateBtn.disabled = false;
        return;
      }

      // status === "done"
      const format = new FormData(form).get("format");
      if (format === "pdf") {
        previewImage.hidden = true;
        previewPdfNote.hidden = false;
      } else {
        previewImage.hidden = false;
        previewPdfNote.hidden = true;
        previewImage.src = `${data.preview_url}?t=${Date.now()}`;
      }
      downloadLink.href = data.download_url;
      setPreviewState("result");
      generateBtn.disabled = false;
    } catch (err) {
      showError(err.message || "Something went wrong while checking job status.");
      setPreviewState("empty");
      generateBtn.disabled = false;
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    stopPolling();

    const city = document.getElementById("city").value.trim();
    const country = document.getElementById("country").value.trim();
    if (!city || !country) {
      showError("City and country are required.");
      return;
    }
    if (!selectedTheme) {
      showError("Pick a map theme.");
      return;
    }

    const payload = {
      city,
      country,
      theme: selectedTheme,
      distance: Number(distanceInput.value),
      width: Number(widthInput.value),
      height: Number(heightInput.value),
      format: document.getElementById("format").value,
    };

    const countryLabel = document.getElementById("country_label").value.trim();
    if (countryLabel) payload.country_label = countryLabel;

    const lat = latitudeInput.value.trim();
    const lon = longitudeInput.value.trim();
    if (lat && lon) {
      payload.latitude = Number(lat);
      payload.longitude = Number(lon);
    }

    generateBtn.disabled = true;
    setPreviewState("loading");
    progressMessage.textContent = "Starting...";

    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Could not start generation.");
      }
      pollJob(data.id);
    } catch (err) {
      showError(err.message || "Could not start generation.");
      setPreviewState("empty");
      generateBtn.disabled = false;
    }
  });

  loadThemes();
})();
