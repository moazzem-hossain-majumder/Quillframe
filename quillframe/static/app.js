const $ = (sel) => document.querySelector(sel);

// Build DOM nodes with textContent only, so model output can never inject HTML.
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

async function api(path, body) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : undefined;
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join("; ") : data.detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return data;
}

function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle("error", isError);
}

async function loadHealth() {
  const box = $("#providers");
  try {
    const h = await api("/api/health");
    box.replaceChildren();
    if (!h.text.length) {
      box.append(el("span", { class: "chip warn" }, "No API keys found: copy .env.example to .env"));
    }
    h.text.forEach((p) => box.append(el("span", { class: "chip ok" }, `text: ${p.provider} / ${p.model}`)));
    h.image.forEach((p) => box.append(el("span", { class: "chip ok" }, `image: ${p.provider}`)));
    box.append(el("span", { class: "chip ok" }, `voice: ${h.voice.engine}`));
  } catch (err) {
    box.replaceChildren(el("span", { class: "chip warn" }, "Backend unreachable"));
  }
}

function renderCampaign(m) {
  const b = m.brief;
  const root = el("div", { class: "result" });

  root.append(
    el("h3", { class: "title" }, b.campaign_name),
    el("p", {}, b.concept),
    el("span", { class: "pill" }, `Tone: ${b.tone}`),
    el("span", { class: "pill" }, `Audience: ${b.audience}`),
    el("p", { class: "hint" }, b.visual_direction),
    el("h3", {}, "Slogans"),
    el("ul", { class: "slogans" }, b.slogans.map((s) => el("li", {}, s)))
  );

  root.append(el("h3", {}, "Text model comparison"));
  root.append(
    el(
      "table",
      {},
      el("tr", {}, ["Provider", "Model", "Latency", "Valid", "First slogan / error"].map((h) => el("th", {}, h))),
      m.text_comparison.map((r) =>
        el(
          "tr",
          {},
          el("td", {}, r.provider + (r.provider === m.brief_provider ? " (used)" : "")),
          el("td", {}, r.model),
          el("td", {}, `${r.latency_s}s`),
          el("td", { class: r.valid ? "ok-text" : "bad-text" }, r.valid ? "yes" : "no"),
          el("td", {}, r.first_slogan || r.error || "")
        )
      )
    )
  );

  if (m.images.length) {
    root.append(el("h3", {}, "Images"));
    root.append(
      el(
        "div",
        { class: "grid" },
        m.images.map((img) =>
          el(
            "div",
            { class: img.file ? "box" : "box err" },
            img.file ? el("img", { class: "shot", src: `/outputs/${m.id}/${img.file}`, alt: img.prompt }) : null,
            el("h4", {}, `${img.provider}, prompt ${img.index}`),
            el("div", { class: "meta" }, img.file ? `${img.latency_s}s` : `Failed: ${img.error}`)
          )
        )
      )
    );
  }

  root.append(el("h3", {}, "Voiceover"));
  root.append(
    m.voice.file
      ? el("audio", { controls: "", src: `/outputs/${m.id}/${m.voice.file}` })
      : el("p", { class: "bad-text" }, `Voiceover failed: ${m.voice.error}`),
    el("p", { class: "hint" }, b.voiceover_script)
  );

  root.append(el("h3", {}, "Social media pack"));
  if (m.social) {
    root.append(
      el(
        "div",
        { class: "grid" },
        Object.entries(m.social).map(([platform, post]) =>
          el(
            "div",
            { class: "box" },
            el("h4", {}, platform),
            el("p", { class: "caption" }, post.caption),
            el("div", { class: "meta" }, post.hashtags.join(" "))
          )
        )
      )
    );
  } else {
    root.append(el("p", { class: "bad-text" }, `Skipped: ${m.social_error}`));
  }

  root.append(
    el("h3", {}, "Experiment log"),
    el("p", {}, el("a", { href: `/api/campaigns/${m.id}/log`, target: "_blank" }, "Open EXPERIMENT_LOG.md"),
      ` (total ${m.total_s}s, saved in outputs/${m.id})`)
  );
  return root;
}

async function runCampaign() {
  const brief = $("#brief").value.trim();
  const status = $("#campaign-status");
  const button = $("#run-campaign");
  if (brief.length < 10) return setStatus(status, "Please describe the brand in at least a sentence.", true);
  button.disabled = true;
  setStatus(status, "Working... free tiers can take 30-90 seconds.");
  $("#campaign-result").replaceChildren();
  try {
    const manifest = await api("/api/campaign", {
      brief,
      images: Number($("#images").value),
      voice: $("#voice").value.trim() || null,
    });
    $("#campaign-result").replaceChildren(renderCampaign(manifest));
    setStatus(status, "Done.");
    loadHistory();
  } catch (err) {
    setStatus(status, err.message, true);
  } finally {
    button.disabled = false;
  }
}

async function runArena() {
  const prompt = $("#arena-prompt").value.trim();
  const status = $("#arena-status");
  const button = $("#run-arena");
  if (!prompt) return setStatus(status, "Enter a prompt first.", true);
  button.disabled = true;
  setStatus(status, "Asking every model...");
  $("#arena-result").replaceChildren();
  try {
    const { results } = await api("/api/compare", { prompt });
    $("#arena-result").replaceChildren(
      ...results.map((r) =>
        el(
          "div",
          { class: r.error ? "box err" : "box" },
          el("h4", {}, r.provider),
          el("div", { class: "meta" }, `${r.model} · ${r.latency_s.toFixed(2)}s`),
          el("pre", {}, r.error ? `Error: ${r.error}` : r.text)
        )
      )
    );
    setStatus(status, "");
  } catch (err) {
    setStatus(status, err.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadHistory() {
  const box = $("#history");
  try {
    const { campaigns } = await api("/api/campaigns");
    if (!campaigns.length) return box.replaceChildren(el("p", { class: "hint" }, "Nothing yet."));
    box.replaceChildren(
      ...campaigns.map((m) =>
        el(
          "div",
          { class: "history-item" },
          el("div", {}, el("strong", {}, m.brief.campaign_name), " ", el("small", {}, m.created)),
          el("button", {
            onclick: () => {
              $("#campaign-result").replaceChildren(renderCampaign(m));
              $("#campaign-result").scrollIntoView({ behavior: "smooth" });
            },
          }, "Open")
        )
      )
    );
    if (!$("#campaign-result").children.length && campaigns.length > 0) {
      $("#campaign-result").replaceChildren(renderCampaign(campaigns[0]));
    }
  } catch (err) {
    box.replaceChildren(el("p", { class: "hint" }, "Could not load history."));
  }
}

$("#run-campaign").addEventListener("click", runCampaign);
$("#run-arena").addEventListener("click", runArena);
loadHealth();
loadHistory();
