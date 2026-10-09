document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const youtubeUrlInput = document.getElementById("youtubeUrl");
  const btnFetchInfo = document.getElementById("btnFetchInfo");
  
  const videoPreviewCard = document.getElementById("videoPreviewCard");
  const settingsCard = document.getElementById("settingsCard");
  const copyrightCard = document.getElementById("copyrightCard");
  const metadataCard = document.getElementById("metadataCard");
  const actionCard = document.getElementById("actionCard");
  const resultsCard = document.getElementById("resultsCard");

  // Video Info Elements
  const previewThumb = document.getElementById("previewThumb");
  const previewDurationBadge = document.getElementById("previewDurationBadge");
  const previewTitle = document.getElementById("previewTitle");
  const previewChannel = document.getElementById("previewChannel");
  const previewDuration = document.getElementById("previewDuration");
  const previewResolution = document.getElementById("previewResolution");
  const downloadQuality = document.getElementById("downloadQuality");

  // Settings Elements
  const durationRadios = document.querySelectorAll('input[name="clipDurationRadio"]');
  const customDurationBox = document.getElementById("customDurationBox");
  const customDurationVal = document.getElementById("customDurationVal");
  const calcSummaryText = document.getElementById("calcSummaryText");

  const modeCards = document.querySelectorAll(".mode-card");
  const cinematicOptionsBox = document.getElementById("cinematicOptionsBox");
  const templateOptionsBox = document.getElementById("templateOptionsBox");
  const templateSelect = document.getElementById("templateSelect");
  const partCustomCaption = document.getElementById("partCustomCaption");
  
  // Sliders & Badges
  const blurIntensity = document.getElementById("blurIntensity");
  const valBlur = document.getElementById("valBlur");
  const bgBrightness = document.getElementById("bgBrightness");
  const valBrightness = document.getElementById("valBrightness");
  const bgSaturation = document.getElementById("bgSaturation");
  const valSat = document.getElementById("valSat");
  const bgContrast = document.getElementById("bgContrast");
  const valCont = document.getElementById("valCont");
  const fgScale = document.getElementById("fgScale");
  const valScale = document.getElementById("valScale");
  const fgPosition = document.getElementById("fgPosition");
  const bgVignette = document.getElementById("bgVignette");

  // Audio Elements
  const audioEnabled = document.getElementById("audioEnabled");
  const audioVolume = document.getElementById("audioVolume");
  const valAudioVol = document.getElementById("valAudioVol");
  const audioFadeIn = document.getElementById("audioFadeIn");
  const audioFadeOut = document.getElementById("audioFadeOut");
  const audioPitch = document.getElementById("audioPitch");
  const valAudioPitch = document.getElementById("valAudioPitch");
  const audioBass = document.getElementById("audioBass");
  const valBass = document.getElementById("valBass");
  const audioTreble = document.getElementById("audioTreble");
  const valTreble = document.getElementById("valTreble");
  const audioLoudnorm = document.getElementById("audioLoudnorm");
  const audioNoiseRed = document.getElementById("audioNoiseRed");

  // Visual Elements
  const visualEnabled = document.getElementById("visualEnabled");
  const visBright = document.getElementById("visBright");
  const valVisBright = document.getElementById("valVisBright");
  const visCont = document.getElementById("visCont");
  const valVisCont = document.getElementById("valVisCont");
  const visSat = document.getElementById("visSat");
  const valVisSat = document.getElementById("valVisSat");
  const glitchIntensity = document.getElementById("glitchIntensity");
  const valGlitch = document.getElementById("valGlitch");
  const visSharpen = document.getElementById("visSharpen");
  const visVignette = document.getElementById("visVignette");
  const visFilmLook = document.getElementById("visFilmLook");
  const visSubtleZoom = document.getElementById("visSubtleZoom");
  const visGlitch = document.getElementById("visGlitch");

  // Part Elements
  const partEnabled = document.getElementById("partEnabled");
  const partTemplate = document.getElementById("partTemplate");
  const partCustomTemplateBox = document.getElementById("partCustomTemplateBox");
  const partCustomTemplate = document.getElementById("partCustomTemplate");
  const partFontSize = document.getElementById("partFontSize");
  const valPartFontSize = document.getElementById("valPartFontSize");
  const partOffset = document.getElementById("partOffset");
  const valPartOffset = document.getElementById("valPartOffset");
  const partStyle = document.getElementById("partStyle");
  const partFontPath = document.getElementById("partFontPath");
  // Header Title Elements
  const headerTitleEnabled = document.getElementById("headerTitleEnabled");
  const headerTitleControlsGrid = document.getElementById("headerTitleControlsGrid");
  const headerTitleText = document.getElementById("headerTitleText");
  const headerTitleTemplate = document.getElementById("headerTitleTemplate");
  const headerTitleCustomBox = document.getElementById("headerTitleCustomBox");
  const headerTitleCustom = document.getElementById("headerTitleCustom");
  const headerTitlePosition = document.getElementById("headerTitlePosition");
  const headerTitleFontSize = document.getElementById("headerTitleFontSize");
  const valHeaderTitleFontSize = document.getElementById("valHeaderTitleFontSize");
  const headerTitleStyle = document.getElementById("headerTitleStyle");

  // Copyright & Metadata
  const licenseStatus = document.getElementById("licenseStatus");
  const metaTitle = document.getElementById("metaTitle");
  const metaSummary = document.getElementById("metaSummary");
  const metaHashtags = document.getElementById("metaHashtags");
  const metaCta = document.getElementById("metaCta");
  const metaImageCount = document.getElementById("metaImageCount");
  const metaFolderName = document.getElementById("metaFolderName");

  // Action & Progress
  const btnStartProcess = document.getElementById("btnStartProcess");
  const btnCancelProcess = document.getElementById("btnCancelProcess");
  const progressContainer = document.getElementById("progressContainer");
  const currentStepText = document.getElementById("currentStepText");
  const progressPercentBadge = document.getElementById("progressPercentBadge");
  const progressBarFill = document.getElementById("progressBarFill");
  const clipCounterText = document.getElementById("clipCounterText");
  const terminalLogs = document.getElementById("terminalLogs");
  const btnClearLog = document.getElementById("btnClearLog");

  // Results
  const resultsSummaryText = document.getElementById("resultsSummaryText");
  const clipsGrid = document.getElementById("clipsGrid");
  const metaJsonDisplay = document.getElementById("metaJsonDisplay");
  const btnCopyJson = document.getElementById("btnCopyJson");
  const btnOpenFolder = document.getElementById("btnOpenFolder");
  const btnDownloadZip = document.getElementById("btnDownloadZip");

  // State Variables
  let currentVideoData = null;
  let activeTaskId = null;
  let eventSource = null;

  // Sync Slider Display Badges
  function setupSliderBadge(slider, badge, unit = "") {
    if (!slider || !badge) return;
    slider.addEventListener("input", () => {
      badge.textContent = `${slider.value}${unit}`;
    });
  }

  setupSliderBadge(blurIntensity, valBlur);
  setupSliderBadge(bgBrightness, valBrightness);
  setupSliderBadge(bgSaturation, valSat);
  setupSliderBadge(bgContrast, valCont);
  setupSliderBadge(fgScale, valScale);
  setupSliderBadge(audioVolume, valAudioVol, " dB");
  setupSliderBadge(audioPitch, valAudioPitch, "x");
  setupSliderBadge(audioBass, valBass, " dB");
  setupSliderBadge(audioTreble, valTreble, " dB");
  setupSliderBadge(visBright, valVisBright);
  setupSliderBadge(visCont, valVisCont);
  setupSliderBadge(visSat, valVisSat);
  setupSliderBadge(glitchIntensity, valGlitch);
  setupSliderBadge(partFontSize, valPartFontSize, " px");
  setupSliderBadge(partOffset, valPartOffset, " px");
  setupSliderBadge(headerTitleFontSize, valHeaderTitleFontSize, " px");

  if (headerTitleEnabled && headerTitleControlsGrid) {
    headerTitleEnabled.addEventListener("change", () => {
      if (headerTitleEnabled.checked) {
        headerTitleControlsGrid.classList.remove("hidden");
      } else {
        headerTitleControlsGrid.classList.add("hidden");
      }
    });
  }

  if (headerTitleTemplate && headerTitleCustomBox) {
    headerTitleTemplate.addEventListener("change", () => {
      if (headerTitleTemplate.value === "custom") {
        headerTitleCustomBox.classList.remove("hidden");
      } else {
        headerTitleCustomBox.classList.add("hidden");
      }
    });
  }

  if (partTemplate && partCustomTemplateBox) {
    partTemplate.addEventListener("change", () => {
      if (partTemplate.value === "custom") {
        partCustomTemplateBox.classList.remove("hidden");
      } else {
        partCustomTemplateBox.classList.add("hidden");
      }
    });
  }

  // Mode Selection Cards
  modeCards.forEach(card => {
    card.addEventListener("click", () => {
      modeCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      const mode = card.dataset.mode;
      if (mode === "cinematic_blur") {
        cinematicOptionsBox.classList.remove("hidden");
        if (templateOptionsBox) templateOptionsBox.classList.add("hidden");
      } else if (mode === "template_frame") {
        if (templateOptionsBox) templateOptionsBox.classList.remove("hidden");
        cinematicOptionsBox.classList.add("hidden");
      } else {
        cinematicOptionsBox.classList.add("hidden");
        if (templateOptionsBox) templateOptionsBox.classList.add("hidden");
      }
    });
  });

  // Dynamic Template List Loading
  async function loadTemplatesList() {
    if (!templateSelect) return;
    try {
      const resp = await fetch("/api/templates");
      const res = await resp.json();
      if (res.success && res.templates && res.templates.length > 0) {
        templateSelect.innerHTML = res.templates.map(t => 
          `<option value="${t.filename}">${t.name} (${t.filename})</option>`
        ).join("");
      }
    } catch (e) {
      console.warn("Could not load templates:", e);
    }
  }
  loadTemplatesList();

  // Duration Selection & Clip Calculation
  function getSelectedClipDuration() {
    let dur = 60;
    const selectedRadio = document.querySelector('input[name="clipDurationRadio"]:checked');
    if (selectedRadio) {
      if (selectedRadio.value === "custom") {
        dur = parseFloat(customDurationVal.value) || 60;
      } else {
        dur = parseFloat(selectedRadio.value) || 60;
      }
    }
    return dur;
  }

  function updateClipCalculation() {
    if (!currentVideoData || !currentVideoData.duration) {
      calcSummaryText.textContent = "Masukkan video untuk melihat perkiraan klip.";
      return;
    }

    const totalDur = currentVideoData.duration;
    const clipDur = getSelectedClipDuration();
    if (clipDur <= 0) return;

    const totalClips = Math.ceil(totalDur / clipDur);
    const lastClipDur = (totalDur % clipDur) || clipDur;

    calcSummaryText.textContent = 
      `Total durasi ${Math.round(totalDur)}s dibagi per ${clipDur}s akan menghasilkan ` +
      `${totalClips} klip Reels (clip_001 s/d clip_${String(totalClips).padStart(3, "0")}). ` +
      `Bagian terakhir (${Math.round(lastClipDur)}s) tetap disimpan utuh.`;
  }

  durationRadios.forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.value === "custom") {
        customDurationBox.classList.remove("hidden");
      } else {
        customDurationBox.classList.add("hidden");
      }
      updateClipCalculation();
    });
  });

  customDurationVal.addEventListener("input", updateClipCalculation);

  // Fetch Video Info Action
  btnFetchInfo.addEventListener("click", async () => {
    const url = youtubeUrlInput.value.trim();
    if (!url) {
      alert("Silakan masukkan URL YouTube terlebih dahulu.");
      return;
    }

    btnFetchInfo.disabled = true;
    btnFetchInfo.innerHTML = '<span class="btn-icon">⏳</span> Mengambil...';

    try {
      const response = await fetch("/api/video-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });

      const res = await response.json();
      if (!res.success) {
        throw new Error(res.error || "Gagal mengambil info video.");
      }

      currentVideoData = res.data;

      // Populate preview card
      previewThumb.src = currentVideoData.thumbnail;
      previewDurationBadge.textContent = currentVideoData.duration_formatted;
      previewTitle.textContent = currentVideoData.title;
      previewChannel.textContent = currentVideoData.channel;
      previewDuration.textContent = `${currentVideoData.duration_formatted} (${Math.round(currentVideoData.duration)} detik)`;
      previewResolution.textContent = currentVideoData.source_resolution;

      // Populate metadata form
      metaTitle.value = currentVideoData.suggested_post_title || currentVideoData.title;
      metaSummary.value = currentVideoData.suggested_summary || "";
      metaHashtags.value = (currentVideoData.suggested_hashtags || []).join(" ");
      metaCta.value = currentVideoData.suggested_cta || "Bagikan pendapatmu di kolom komentar!";
      metaFolderName.value = currentVideoData.suggested_folder_name || "reels-video";

      // Show cards
      videoPreviewCard.classList.remove("hidden");
      settingsCard.classList.remove("hidden");
      copyrightCard.classList.remove("hidden");
      metadataCard.classList.remove("hidden");
      actionCard.classList.remove("hidden");
      resultsCard.classList.add("hidden");

      updateClipCalculation();
      videoPreviewCard.scrollIntoView({ behavior: "smooth" });

    } catch (err) {
      alert(`Terjadi kesalahan:\n${err.message}`);
    } finally {
      btnFetchInfo.disabled = false;
      btnFetchInfo.innerHTML = '<span class="btn-icon">🔍</span> Ambil Video';
    }
  });

  // Append Log to Terminal
  function appendLog(message) {
    terminalLogs.textContent += message + "\n";
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  btnClearLog.addEventListener("click", () => {
    terminalLogs.textContent = "";
  });

  // Start Processing Action
  btnStartProcess.addEventListener("click", async () => {
    const url = youtubeUrlInput.value.trim();
    if (!url) {
      alert("URL YouTube belum diisi.");
      return;
    }

    const selectedModeRadio = document.querySelector('input[name="portraitMode"]:checked');
    const mode = selectedModeRadio ? selectedModeRadio.value : "cinematic_blur";
    const clipDur = getSelectedClipDuration();

    const payload = {
      url: url,
      quality: downloadQuality.value,
      clip_duration: clipDur,
      mode: mode,
      template_choice: templateSelect ? templateSelect.value : "",
      cinematic_opts: {
        blur_intensity: parseInt(blurIntensity.value) || 20,
        bg_brightness: parseFloat(bgBrightness.value) || -0.15,
        bg_contrast: parseFloat(bgContrast.value) || 1.1,
        bg_saturation: parseFloat(bgSaturation.value) || 1.2,
        fg_scale: parseFloat(fgScale.value) || 1.0,
        fg_position: fgPosition.value || "center",
        bg_vignette: bgVignette.checked
      },
      visual_opts: {
        enabled: visualEnabled.checked,
        brightness: parseFloat(visBright.value) || 0.0,
        contrast: parseFloat(visCont.value) || 1.0,
        saturation: parseFloat(visSat.value) || 1.0,
        sharpen: visSharpen.checked,
        vignette: visVignette.checked,
        film_look: visFilmLook.checked,
        subtle_zoom: visSubtleZoom.checked,
        glitch: visGlitch.checked,
        glitch_intensity: parseFloat(glitchIntensity.value) || 30,
        glitch_frequency: 3.5
      },
      audio_opts: {
        enabled: audioEnabled.checked,
        volume: parseFloat(audioVolume.value) || 0.0,
        fade_in: parseFloat(audioFadeIn.value) || 0.0,
        fade_out: parseFloat(audioFadeOut.value) || 0.0,
        pitch: parseFloat(audioPitch.value) || 1.0,
        bass_gain: parseFloat(audioBass.value) || 0.0,
        treble_gain: parseFloat(audioTreble.value) || 0.0,
        loudnorm: audioLoudnorm.checked,
        noise_reduction: audioNoiseRed.checked
      },
      part_opts: {
        enabled: partEnabled ? partEnabled.checked : true,
        template: (partTemplate && partTemplate.value === "custom") ? (partCustomTemplate.value.trim() || "PART {n}") : (partTemplate ? partTemplate.value : "PART {n}"),
        caption: partCustomCaption ? partCustomCaption.value.trim() : "",
        font_size: partFontSize ? (parseInt(partFontSize.value) || 59) : 59,
        style: partStyle ? partStyle.value : "default",
        font_path: partFontPath ? (partFontPath.value.trim() || "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf") : "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf"
      },
      header_opts: {
        enabled: headerTitleEnabled ? headerTitleEnabled.checked : true,
        custom_title: headerTitleText ? headerTitleText.value.trim() : "",
        template: (headerTitleTemplate && headerTitleTemplate.value === "custom") 
                  ? (headerTitleCustom ? headerTitleCustom.value.trim() || "{title}" : "{title}") 
                  : (headerTitleTemplate ? headerTitleTemplate.value : "{title}"),
        position: headerTitlePosition ? headerTitlePosition.value : "above_video",
        font_size: headerTitleFontSize ? (parseInt(headerTitleFontSize.value) || 59) : 59,
        style: headerTitleStyle ? headerTitleStyle.value : "default",
        font_path: partFontPath ? (partFontPath.value.trim() || "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf") : "/data/data/com.termux/files/home/VideoTemplate/junction.bold.otf"
      },
      metadata: {
        post_title: metaTitle.value.trim(),
        caption: partCustomCaption ? partCustomCaption.value.trim() : "",
        summary: metaSummary.value.trim(),
        hashtags: metaHashtags.value.trim(),
        cta: metaCta.value.trim(),
        image_count: parseInt(metaImageCount.value) || 0,
        folder_name: metaFolderName.value.trim()
      },
      source_info: {
        license_status: licenseStatus.value
      }
    };

    btnStartProcess.disabled = true;
    btnStartProcess.classList.add("hidden");
    btnCancelProcess.classList.remove("hidden");
    progressContainer.classList.remove("hidden");
    resultsCard.classList.add("hidden");
    terminalLogs.textContent = "";

    try {
      const resp = await fetch("/api/start-process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (!data.success) {
        throw new Error(data.error || "Gagal memulai proses.");
      }

      activeTaskId = data.task_id;
      listenToProgress(activeTaskId);

    } catch (err) {
      alert(`Gagal memulai: ${err.message}`);
      btnStartProcess.disabled = false;
      btnStartProcess.classList.remove("hidden");
      btnCancelProcess.classList.add("hidden");
    }
  });

  // Cancel Process Action
  btnCancelProcess.addEventListener("click", async () => {
    if (!activeTaskId) return;
    if (!confirm("Apakah Anda yakin ingin membatalkan proses ini?")) return;

    try {
      await fetch(`/api/cancel/${activeTaskId}`, { method: "POST" });
      appendLog("Mengirim sinyal pembatalan ke backend...");
    } catch (err) {
      console.error(err);
    }
  });

  // SSE Progress Streaming
  function listenToProgress(taskId) {
    if (eventSource) {
      eventSource.close();
    }

    eventSource = new EventSource(`/api/progress/${taskId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "log") {
          appendLog(data.message);
        } else if (data.type === "progress") {
          const pct = Math.max(0, Math.min(100, data.percent || 0));
          progressBarFill.style.width = `${pct}%`;
          progressPercentBadge.textContent = `${pct.toFixed(1)}%`;
          currentStepText.textContent = data.step || "Memproses...";

          if (data.clip_total > 0) {
            clipCounterText.textContent = `Proses klip: ${data.clip_current || 0} / ${data.clip_total}`;
          }
        } else if (data.type === "completed") {
          progressBarFill.style.width = "100%";
          progressPercentBadge.textContent = "100%";
          currentStepText.textContent = "Selesai!";
          eventSource.close();
          handleCompletion(data.result);
        } else if (data.type === "error") {
          currentStepText.textContent = "Gagal!";
          appendLog(`ERROR: ${data.error}`);
          alert(`Proses gagal: ${data.error}`);
          resetActionButtons();
          eventSource.close();
        } else if (data.type === "cancelled") {
          currentStepText.textContent = "Dibatalkan.";
          appendLog("Proses dibatalkan.");
          resetActionButtons();
          eventSource.close();
        }
      } catch (e) {
        console.error("Parse event error:", e);
      }
    };

    let pollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${taskId}`);
        const s = await res.json();
        if (s.success && s.state) {
          const pct = Math.max(0, Math.min(100, s.state.percent || 0));
          progressBarFill.style.width = `${pct}%`;
          progressPercentBadge.textContent = `${pct.toFixed(1)}%`;
          currentStepText.textContent = s.state.step || "Memproses...";

          if (s.state.status === "completed") {
            clearInterval(pollTimer);
            if (eventSource) eventSource.close();
            handleCompletion(s.state.result);
          } else if (s.state.status === "error") {
            clearInterval(pollTimer);
            if (eventSource) eventSource.close();
            currentStepText.textContent = "Gagal!";
            alert(`Proses gagal: ${s.state.error}`);
            resetActionButtons();
          } else if (s.state.status === "cancelled") {
            clearInterval(pollTimer);
            if (eventSource) eventSource.close();
            currentStepText.textContent = "Dibatalkan.";
            resetActionButtons();
          }
        }
      } catch (_) {}
    }, 2500);

    eventSource.onerror = () => {
      // Keep running via pollTimer even if SSE disconnects
      console.log("SSE disconnected, relying on background poller...");
    };
  }

  function resetActionButtons() {
    btnStartProcess.disabled = false;
    btnStartProcess.classList.remove("hidden");
    btnCancelProcess.classList.add("hidden");
  }

  // Handle Successful Completion
  function handleCompletion(result) {
    resetActionButtons();
    if (!result) return;

    resultsCard.classList.remove("hidden");
    resultsSummaryText.innerHTML = 
      `Berhasil membuat <strong>${result.clip_count} klip</strong> di folder <code>Post/${result.folder_name}/</code>`;

    // Render Clips Grid
    clipsGrid.innerHTML = "";
    if (result.clips && result.clips.length > 0) {
      result.clips.forEach(clip => {
        const card = document.createElement("div");
        card.className = "clip-card";
        card.innerHTML = `
          <div class="clip-video-wrapper">
            <video controls preload="metadata">
              <source src="${clip.url}" type="video/mp4">
              Browser Anda tidak mendukung tag video.
            </video>
          </div>
          <div class="clip-card-info">
            <span class="clip-name">${clip.filename}</span>
            <span class="clip-size">${clip.size_mb} MB</span>
            <a href="${clip.url}" download="${clip.filename}" class="btn btn-sm btn-primary mt-2">
              ⬇ Unduh Klip
            </a>
          </div>
        `;
        clipsGrid.appendChild(card);
      });
    }

    // Display metadata json
    metaJsonDisplay.textContent = JSON.stringify(result.metadata, null, 2);

    // Setup ZIP download button
    btnDownloadZip.href = `/api/download-zip/${result.folder_name}`;

    // Setup Open Folder button
    btnOpenFolder.onclick = async () => {
      try {
        const res = await fetch("/api/open-folder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ folder_name: result.folder_name })
        });
        const data = await res.json();
        alert(data.message || `Folder: ${result.folder_path}`);
      } catch (e) {
        alert(`Folder tersimpan di: ${result.folder_path}`);
      }
    };

    resultsCard.scrollIntoView({ behavior: "smooth" });
  }

  // Copy JSON button
  btnCopyJson.addEventListener("click", () => {
    const text = metaJsonDisplay.textContent;
    navigator.clipboard.writeText(text).then(() => {
      const orig = btnCopyJson.textContent;
      btnCopyJson.textContent = "Tersalin!";
      setTimeout(() => { btnCopyJson.textContent = orig; }, 2000);
    });
  });

  // Reset & Start New Video button
  const btnNewProcess = document.getElementById("btnNewProcess");
  if (btnNewProcess) {
    btnNewProcess.addEventListener("click", () => {
      localStorage.removeItem("activeTaskId");
      activeTaskId = null;
      if (eventSource) eventSource.close();
      
      resultsCard.classList.add("hidden");
      actionCard.classList.add("hidden");
      progressContainer.classList.add("hidden");
      settingsCard.classList.add("hidden");
      copyrightCard.classList.add("hidden");
      metadataCard.classList.add("hidden");
      videoPreviewCard.classList.add("hidden");
      
      youtubeUrlInput.value = "";
      terminalLogs.textContent = "";
      btnStartProcess.disabled = false;
      btnStartProcess.classList.remove("hidden");
      btnCancelProcess.classList.add("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Auto-reconnect to running or completed task on browser load/refresh
  async function checkActiveTaskOnLoad() {
    try {
      const res = await fetch("/api/latest-task");
      const data = await res.json();
      if (!data.has_task) return;

      const state = data.state;
      const taskId = data.task_id;

      if (data.is_active) {
        // Task is actively running in backend!
        activeTaskId = taskId;
        localStorage.setItem("activeTaskId", taskId);

        actionCard.classList.remove("hidden");
        progressContainer.classList.remove("hidden");
        btnStartProcess.disabled = true;
        btnStartProcess.classList.add("hidden");
        btnCancelProcess.classList.remove("hidden");
        resultsCard.classList.add("hidden");

        const pct = Math.max(0, Math.min(100, state.percent || 0));
        progressBarFill.style.width = `${pct}%`;
        progressPercentBadge.textContent = `${pct.toFixed(1)}%`;
        currentStepText.textContent = state.step || "Menyambung kembali ke proses...";

        if (state.clip_total > 0) {
          clipCounterText.textContent = `Proses klip: ${state.clip_current || 0} / ${state.clip_total}`;
        }

        // Restore historical logs
        if (state.logs && state.logs.length > 0) {
          terminalLogs.textContent = state.logs.join("\n") + "\n";
        }
        appendLog(`[Sistem] Browser tersambung kembali ke proses aktif (${taskId})...`);

        listenToProgress(taskId);
      } else if (state.status === "completed" && state.result) {
        const storedId = localStorage.getItem("activeTaskId");
        if (storedId === taskId) {
          activeTaskId = taskId;
          handleCompletion(state.result);
        }
      }
    } catch (e) {
      console.log("Check active task error:", e);
    }
  }

  checkActiveTaskOnLoad();
});
