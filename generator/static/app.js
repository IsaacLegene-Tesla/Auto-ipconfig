function showAlert(el, ok, htmlOrText) {
  el.classList.add("visible");
  el.classList.toggle("ok", ok);
  el.classList.toggle("err", !ok);
  if (ok && htmlOrText.includes("<")) el.innerHTML = htmlOrText;
  else el.textContent = htmlOrText;
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.classList.toggle("loading", loading);
}

function bindFileZone(zone) {
  const input = zone.querySelector('input[type="file"]');
  const nameEl = zone.querySelector(".file-name");
  if (!input || !nameEl) return;

  const show = () => {
    nameEl.textContent = input.files?.[0]?.name || "";
  };
  input.addEventListener("change", show);

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files?.length) {
      input.files = e.dataTransfer.files;
      show();
    }
  });
}

document.querySelectorAll(".file-zone").forEach(bindFileZone);

async function loadBranding() {
  const img = document.getElementById("teslaLogo");
  if (!img) return;
  try {
    const r = await fetch("/api/branding");
    const d = await r.json();
    if (d.logo_url) {
      img.src = d.logo_url;
      img.classList.remove("hidden");
      img.classList.toggle("banner-logo--invert", !!d.logo_invert);
      img.classList.toggle("banner-logo--symbol", !!d.logo_banner && !d.logo_invert);
      img.onerror = () => img.classList.add("hidden");
    }
  } catch {
    /* no logo */
  }
}

loadBranding();

async function refreshStatus() {
  const amrEl = document.getElementById("statAmr");
  const chips = document.getElementById("baselineChips");

  try {
    const r = await fetch("/api/status");
    const d = await r.json();
    if (d.ok) {
      amrEl.textContent = d.amr_count;
      if (d.baselines.length) {
        chips.innerHTML = d.baselines
          .map((b) => {
            const m = b.match(/AMR[_\s-]*(\d+)/i);
            const label = m ? `AMR_${m[1]}` : b.replace(/\.conf$/i, "");
            return `<span class="chip">${label}</span>`;
          })
          .join("");
      } else {
        chips.innerHTML = '<span class="chip muted-chip">No baselines yet</span>';
      }
    } else {
      amrEl.textContent = "—";
      chips.innerHTML = `<span class="chip">${d.error || "Error"}</span>`;
    }
  } catch (e) {
    amrEl.textContent = "!";
    chips.innerHTML = `<span class="chip">${e}</span>`;
  }
}

refreshStatus();

document.getElementById("fleetForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("fleetBtn");
  const status = document.getElementById("fleetStatus");
  const fd = new FormData(e.target);
  const policyFile = fd.get("config");
  const hasFile = policyFile && policyFile.size > 0;
  if (!hasFile && !fd.get("config_path")?.trim()) {
    showAlert(status, false, "Choose a policy file or enter a path.");
    return;
  }
  setLoading(btn, true);
  showAlert(status, true, "Building fleet configs…");
  try {
    const res = await fetch("/api/build", { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      let msg =
        `Created <strong>${data.count}</strong> configs in Downloads:<br><code>${data.folder}</code>`;
      if (data.policy_archive) {
        msg += `<br>Policy archived:<br><code>${data.policy_archive}</code>`;
      }
      showAlert(status, true, msg);
    } else {
      showAlert(status, false, data.error || "Build failed");
    }
  } catch (err) {
    showAlert(status, false, String(err));
  }
  setLoading(btn, false);
});

document.getElementById("baselineForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("baselineBtn");
  const status = document.getElementById("baselineStatus");
  const fd = new FormData(e.target);
  const file = fd.get("baseline");
  const path = (fd.get("baseline_path") || "").trim();
  const hasFile = file && file.size > 0;
  if (!hasFile && !path) {
    showAlert(status, false, "Choose a .conf file or enter a path.");
    return;
  }
  setLoading(btn, true);
  showAlert(status, true, "Saving baseline…");
  try {
    const res = await fetch("/api/baselines/add", { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      let msg = `Saved <code>${data.filename}</code>`;
      if (data.overwritten) msg += " (replaced existing)";
      msg += `<br>inventory.csv — <strong>${data.inventory_count}</strong> AMR(s).`;
      showAlert(status, true, msg);
      e.target.reset();
      document.querySelectorAll(".file-name").forEach((el) => (el.textContent = ""));
      refreshStatus();
    } else {
      showAlert(status, false, data.error || "Failed");
    }
  } catch (err) {
    showAlert(status, false, String(err));
  }
  setLoading(btn, false);
});
