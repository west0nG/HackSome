"use strict";

const PROFILE_KEY = "hacksome.relay.profile.v1";
const DRAFT_KEY = "hacksome.relay.draft.v1";
const RESOLUTION_DRAFT_KEY = "hacksome.relay.resolution.v1";
const REACTION_NAMES = ["surprise", "fun", "mystery", "confusion"];
const REACTION_LABELS = {
  surprise: "惊喜",
  fun: "好玩",
  mystery: "神秘",
  confusion: "困惑",
};
const REACTION_VALUES = ["yes", "maybe", "no"];
const REACTION_VALUE_LABELS = { yes: "是", maybe: "也许", no: "否" };

const state = {
  snapshot: null,
  profile: null,
  currentConceptIndex: 0,
  currentPairIndex: 0,
  pairMode: false,
  pairPreference: null,
  draft: null,
  staleDraft: false,
  submittedReviewId: null,
  resolutionId: null,
};

function byId(id) {
  return document.getElementById(id);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function text(value, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function shortHash(value) {
  const hash = text(value);
  return hash ? hash.slice(0, 12) : "hash unknown";
}

function randomId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (part) => part.toString(16).padStart(2, "0")).join("");
}

function safeReadStorage(key) {
  try {
    const raw = globalThis.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (_error) {
    return null;
  }
}

function safeWriteStorage(key, value) {
  try {
    globalThis.localStorage.setItem(key, JSON.stringify(value));
  } catch (_error) {
    setPageState("浏览器无法保存本地草稿；本页仍可继续使用。", "error");
  }
}

function safeRemoveStorage(key) {
  try {
    globalThis.localStorage.removeItem(key);
  } catch (_error) {
    // Storage failure must not block an explicit user action.
  }
}

function getRound() {
  return asObject(asObject(state.snapshot).round);
}

function getConcepts() {
  return asArray(asObject(state.snapshot).concepts);
}

function getPairs() {
  const snapshotPairs = asArray(asObject(state.snapshot).pairs);
  return snapshotPairs.length ? snapshotPairs : asArray(getRound().pairs);
}

function conceptRef(concept) {
  return text(concept.ref, text(concept.concept_ref, text(concept.id)));
}

function conceptHash(concept) {
  return text(concept.sha256, text(concept.concept_sha256));
}

function conceptTitle(concept) {
  return text(concept.title, text(concept.hook, conceptRef(concept)));
}

function fieldText(concept, ...names) {
  for (const name of names) {
    const value = concept[name];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return "本轮没有提供这一段。";
}

function setPageState(message, kind = "info") {
  byId("page-state-text").textContent = message;
  byId("page-state").dataset.kind = kind;
}

function setError(elementId, message) {
  const target = byId(elementId);
  target.textContent = message;
  target.hidden = !message;
}

async function api(path, options = {}) {
  const request = {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
    ...options,
  };
  if (request.body !== undefined) {
    request.headers = { ...request.headers, "Content-Type": "application/json" };
    request.body = JSON.stringify(request.body);
  }
  const response = await fetch(path, request);
  let payload = {};
  try {
    payload = await response.json();
  } catch (_error) {
    payload = {};
  }
  if (!response.ok) {
    const error = new Error(text(payload.message, `请求失败（${response.status}）`));
    error.code = text(payload.code, "request_failed");
    error.status = response.status;
    throw error;
  }
  return payload;
}

function loadOrCreateProfile() {
  const saved = asObject(safeReadStorage(PROFILE_KEY));
  const reviewerId = text(saved.reviewer_id) || randomId();
  const profile = { reviewer_id: reviewerId, reviewer_name: text(saved.reviewer_name) };
  safeWriteStorage(PROFILE_KEY, profile);
  return profile;
}

async function registerReviewerSession() {
  await api("/api/reviewer-sessions", {
    method: "POST",
    body: { reviewer_id: state.profile.reviewer_id },
  });
}

function emptyDraft() {
  return {
    round_sha256: text(getRound().sha256),
    review_id: randomId(),
    reviewer_name: text(state.profile.reviewer_name),
    concept_reviews: {},
    pairwise: {},
    overall_comment: "",
  };
}

function loadDraft() {
  const saved = asObject(safeReadStorage(DRAFT_KEY));
  const currentHash = text(getRound().sha256);
  if (!saved.round_sha256) {
    state.draft = emptyDraft();
    return;
  }
  if (saved.round_sha256 !== currentHash) {
    state.draft = saved;
    state.staleDraft = true;
    byId("stale-warning").hidden = false;
    byId("submit-review").disabled = true;
    return;
  }
  state.draft = {
    ...emptyDraft(),
    ...saved,
    concept_reviews: asObject(saved.concept_reviews),
    pairwise: asObject(saved.pairwise),
  };
}

function saveDraft() {
  if (!state.draft || state.staleDraft) {
    return;
  }
  state.draft.round_sha256 = text(getRound().sha256);
  safeWriteStorage(DRAFT_KEY, state.draft);
}

function persistProfileName(name) {
  state.profile.reviewer_name = name;
  safeWriteStorage(PROFILE_KEY, state.profile);
  byId("profile-label").textContent = name || "尚未登记";
}

function makeTextElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  element.textContent = text(value);
  return element;
}

function renderConceptList() {
  const list = byId("concept-list");
  list.replaceChildren();
  const concepts = getConcepts();
  concepts.forEach((concept, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.index = String(index);
    button.setAttribute("aria-current", index === state.currentConceptIndex ? "true" : "false");
    const title = makeTextElement("span", "list-title", conceptTitle(concept));
    button.append(title);
    button.addEventListener("click", () => {
      storeCurrentConceptDraft();
      state.currentConceptIndex = index;
      state.pairMode = false;
      render();
      byId("concept-stage").focus();
    });
    item.append(button);
    list.append(item);
  });
}

function renderConcept() {
  const concepts = getConcepts();
  const concept = concepts[state.currentConceptIndex];
  const card = byId("concept-card");
  if (!concept) {
    card.hidden = true;
    return;
  }
  card.hidden = state.pairMode;
  byId("concept-id").textContent = conceptRef(concept);
  byId("concept-territory").textContent = text(
    concept.primary_territory_ref,
    text(concept.territory),
  );
  byId("concept-hash").textContent = `sha256 ${shortHash(conceptHash(concept))}`;
  byId("concept-hook").textContent = fieldText(concept, "hook", "one_sentence_hook", "title");
  byId("concept-first-impression").textContent = fieldText(
    concept,
    "first_impression",
    "first_thirty_seconds",
  );
  byId("concept-action").textContent = fieldText(concept, "audience_action", "action");
  byId("concept-reveal").textContent = fieldText(
    concept,
    "reveal",
    "setup_reveal_aftertaste",
  );
  byId("concept-mechanism").textContent = fieldText(concept, "core_mechanism", "mechanism");
  byId("concept-demo").textContent = fieldText(
    concept,
    "minimum_hackathon_demo",
    "minimum_demo",
  );
  byId("concept-novelty").textContent = fieldText(
    concept,
    "novelty",
    "novelty_and_references",
  );
  byId("concept-risks").textContent = fieldText(
    concept,
    "risks",
    "assumptions_confusion_and_risks",
  );
}

function currentConceptDraft() {
  const concept = getConcepts()[state.currentConceptIndex];
  if (!concept || !state.draft) {
    return {};
  }
  const ref = conceptRef(concept);
  if (!state.draft.concept_reviews[ref]) {
    state.draft.concept_reviews[ref] = {
      concept_ref: ref,
      concept_sha256: conceptHash(concept),
      one_sentence_retell: "",
      share_target: "",
      reactions: {
        surprise: "maybe",
        fun: "maybe",
        mystery: "maybe",
        confusion: "maybe",
      },
      recommendation: "no_opinion",
      comment: "",
    };
  }
  return state.draft.concept_reviews[ref];
}

function storeCurrentConceptDraft() {
  const draft = currentConceptDraft();
  if (!draft || state.staleDraft) {
    return;
  }
  draft.one_sentence_retell = byId("retell").value;
  draft.share_target = byId("share-target").value;
  draft.recommendation = byId("recommendation").value;
  draft.comment = byId("comment").value;
  state.draft.overall_comment = byId("overall-comment").value;
  persistProfileName(byId("reviewer-name").value.trim());
  saveDraft();
}

function renderReactionChips() {
  const container = byId("reaction-chips");
  container.replaceChildren();
  const draft = currentConceptDraft();
  const reactions = asObject(draft.reactions);
  REACTION_NAMES.forEach((name) => {
    const wrapper = document.createElement("div");
    wrapper.className = "reaction-group";
    wrapper.setAttribute("role", "group");
    wrapper.setAttribute("aria-label", REACTION_LABELS[name]);
    REACTION_VALUES.forEach((value) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "reaction-chip";
      button.dataset.reaction = name;
      button.dataset.value = value;
      button.setAttribute("aria-pressed", reactions[name] === value ? "true" : "false");
      button.textContent = `${REACTION_LABELS[name]} · ${REACTION_VALUE_LABELS[value]}`;
      button.addEventListener("click", () => {
        draft.reactions[name] = value;
        saveDraft();
        renderReactionChips();
      });
      wrapper.append(button);
    });
    container.append(wrapper);
  });
}

function restoreForm() {
  const draft = currentConceptDraft();
  byId("reviewer-name").value = text(state.draft.reviewer_name, state.profile.reviewer_name);
  byId("retell").value = text(draft.one_sentence_retell);
  byId("share-target").value = text(draft.share_target);
  byId("recommendation").value = text(draft.recommendation, "no_opinion");
  byId("comment").value = text(draft.comment);
  byId("overall-comment").value = text(state.draft.overall_comment);
  renderReactionChips();
  updateAllCounts();
}

function updateCount(inputId, countId) {
  byId(countId).textContent = String(byId(inputId).value.length);
}

function updateAllCounts() {
  updateCount("retell", "retell-count");
  updateCount("share-target", "share-target-count");
  updateCount("comment", "comment-count");
  updateCount("overall-comment", "overall-comment-count");
  updateCount("pair-reason", "pair-reason-count");
  updateCount("coverage-override", "coverage-override-count");
}

function renderRoundMeta() {
  const round = getRound();
  const status = text(round.status, "open");
  byId("round-status").textContent = status === "closed" ? "本轮已关闭" : "本轮正在接力";
  byId("round-status").dataset.status = status;
  const concepts = getConcepts();
  byId("relay-position").textContent = concepts.length
    ? `${String(state.currentConceptIndex + 1).padStart(2, "0")} / ${String(
        concepts.length,
      ).padStart(2, "0")}`
    : "00 / 00";
  byId("profile-label").textContent = text(state.profile.reviewer_name, "尚未登记");
  const coverage = asObject(asObject(state.snapshot).coverage_summary);
  const covered = Number(coverage.covered_concept_count || 0);
  const reviewerCount = Number(coverage.reviewer_count || 0);
  byId("coverage-summary").textContent =
    `匿名覆盖：${covered}/${concepts.length} 个候选 · ${reviewerCount} 位评审者`;
}

function pairRefs(pair) {
  return {
    id: text(pair.pair_id, text(pair.id)),
    leftRef: text(pair.left_ref),
    rightRef: text(pair.right_ref),
    leftHash: text(pair.left_sha256),
    rightHash: text(pair.right_sha256),
  };
}

function findConcept(ref) {
  return getConcepts().find((concept) => conceptRef(concept) === ref) || {};
}

function pairDraft(pair) {
  const refs = pairRefs(pair);
  if (!state.draft.pairwise[refs.id]) {
    state.draft.pairwise[refs.id] = {
      pair_id: refs.id,
      left_ref: refs.leftRef,
      right_ref: refs.rightRef,
      left_sha256: refs.leftHash,
      right_sha256: refs.rightHash,
      preference: null,
      reason: "",
    };
  }
  return state.draft.pairwise[refs.id];
}

function renderPairMode() {
  const pairs = getPairs();
  const pair = pairs[state.currentPairIndex];
  byId("pair-stage").hidden = !state.pairMode;
  if (!state.pairMode || !pair) {
    return;
  }
  const refs = pairRefs(pair);
  const draft = pairDraft(pair);
  const swapped = pair.display_swapped === true;
  state.pairPreference = draft.preference;
  const left = findConcept(swapped ? refs.rightRef : refs.leftRef);
  const right = findConcept(swapped ? refs.leftRef : refs.rightRef);
  const leftButton = byId("pair-left");
  const rightButton = byId("pair-right");
  leftButton.textContent = `${conceptTitle(left)}\n\n${fieldText(left, "hook", "one_sentence_hook")}`;
  rightButton.textContent = `${conceptTitle(right)}\n\n${fieldText(
    right,
    "hook",
    "one_sentence_hook",
  )}`;
  leftButton.setAttribute(
    "aria-pressed",
    draft.preference === (swapped ? "right" : "left") ? "true" : "false",
  );
  rightButton.setAttribute(
    "aria-pressed",
    draft.preference === (swapped ? "left" : "right") ? "true" : "false",
  );
  byId("pair-reason").value = text(draft.reason);
  updateCount("pair-reason", "pair-reason-count");
}

function choosePairPreference(displayValue) {
  const pair = getPairs()[state.currentPairIndex];
  if (!pair) {
    return;
  }
  const draft = pairDraft(pair);
  const value =
    pair.display_swapped === true
      ? displayValue === "left"
        ? "right"
        : "left"
      : displayValue;
  draft.preference = draft.preference === value ? null : value;
  state.pairPreference = draft.preference;
  saveDraft();
  renderPairMode();
}

function savePair(skip = false) {
  const pairs = getPairs();
  const pair = pairs[state.currentPairIndex];
  if (!pair) {
    return;
  }
  const draft = pairDraft(pair);
  draft.reason = byId("pair-reason").value;
  if (skip) {
    delete state.draft.pairwise[pairRefs(pair).id];
  } else if (!draft.preference) {
    setPageState("请选择一边，或使用“跳过这一组”。", "error");
    return;
  }
  saveDraft();
  if (state.currentPairIndex + 1 < pairs.length) {
    state.currentPairIndex += 1;
    renderPairMode();
  } else {
    state.pairMode = false;
    render();
    setPageState("Pairwise 已保存；没有回答的 pair 不会被当成平局或拒绝。");
  }
}

function renderTeamWall() {
  const wall = byId("team-wall");
  const viewer = asObject(asObject(state.snapshot).viewer);
  const entries = asArray(asObject(state.snapshot).team_wall);
  wall.hidden = !viewer.has_submitted || !entries.length;
  const content = byId("team-wall-content");
  content.replaceChildren();
  entries.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "wall-receipt";
    card.append(makeTextElement("p", "eyebrow", text(entry.reviewer_name, "匿名队友")));
    card.append(makeTextElement("strong", "", text(entry.one_sentence_retell, "未填写复述")));
    card.append(
      makeTextElement(
        "p",
        "",
        text(entry.share_target) ? `想递给：${entry.share_target}` : "没有填写分享对象",
      ),
    );
    if (text(entry.comment)) {
      card.append(makeTextElement("p", "", entry.comment));
    }
    content.append(card);
  });
}

function renderReceiptState() {
  const viewer = asObject(asObject(state.snapshot).viewer);
  if (text(viewer.latest_review_id)) {
    state.submittedReviewId = text(viewer.latest_review_id);
  }
  const submitted = Boolean(viewer.has_submitted || state.submittedReviewId);
  byId("receipt-form-wrap").hidden = submitted;
  byId("receipt-signal").hidden = !submitted;
  if (!submitted) {
    return;
  }
  const current = currentConceptDraft();
  byId("receipt-signature").textContent =
    `${text(state.profile.reviewer_name, "你")} 复述：${text(
      current.one_sentence_retell,
      "已提交本轮回执",
    )}`;
  byId("receipt-target").textContent = text(current.share_target)
    ? `想递给：${current.share_target}`
    : "这次没有指定分享对象。";
  const concept = getConcepts()[state.currentConceptIndex];
  byId("receipt-binding").textContent =
    `✓ 已绑定 ${conceptRef(concept)} / ${shortHash(conceptHash(concept))}`;
}

function renderCurator() {
  const isCurator = text(asObject(asObject(state.snapshot).viewer).role) === "curator";
  const workbench = byId("curator-workbench");
  workbench.hidden = !isCurator;
  if (!isCurator) {
    return;
  }
  const curation = asObject(asObject(state.snapshot).curation);
  renderCuratorCoverage(curation);
  renderCuratorMemory(curation);
  renderResolutionActions(curation);
  byId("curator-name").value = text(state.profile.reviewer_name);
  const round = getRound();
  byId("close-round").disabled = text(round.status) === "closed";
}

function renderCuratorCoverage(curation) {
  const coverageTarget = byId("curator-coverage");
  coverageTarget.replaceChildren();
  const rows = asArray(curation.coverage);
  rows.forEach((row) => {
    const card = document.createElement("article");
    card.className = "coverage-row";
    card.append(makeTextElement("strong", "", text(row.concept_ref, text(row.ref))));
    card.append(
      makeTextElement(
        "p",
        "",
        `${Number(row.review_count || 0)} 份回执 · ${
          row.covered === false ? "尚未覆盖" : "已覆盖"
        }`,
      ),
    );
    coverageTarget.append(card);
  });

  const receiptsTarget = byId("curator-receipts");
  receiptsTarget.replaceChildren();
  asArray(curation.receipts).forEach((receipt) => {
    const card = document.createElement("article");
    card.className = "wall-receipt";
    card.append(makeTextElement("p", "eyebrow", text(receipt.reviewer_name, "匿名评审者")));
    asArray(receipt.concept_reviews).forEach((review) => {
      card.append(
        makeTextElement(
          "strong",
          "",
          `${text(review.concept_ref)}：${text(review.one_sentence_retell)}`,
        ),
      );
      card.append(makeTextElement("p", "", `想递给：${text(review.share_target, "未填写")}`));
      card.append(makeTextElement("p", "", text(review.comment)));
    });
    receiptsTarget.append(card);
  });
}

function renderCuratorMemory(curation) {
  const target = byId("curator-memory");
  target.replaceChildren();
  const records = asArray(curation.memory_provenance);
  if (!records.length) {
    target.append(makeTextElement("p", "", "本轮没有可披露的 Idea Memory 来源。"));
    return;
  }
  records.forEach((record) => {
    const card = document.createElement("article");
    card.className = "memory-note";
    card.append(makeTextElement("p", "eyebrow", text(record.concept_ref, "Memory")));
    card.append(
      makeTextElement("strong", "", text(record.source_ref, text(record.source_run_id))),
    );
    card.append(
      makeTextElement(
        "p",
        "",
        `借用 / 规避：${text(record.cue_role, "未标注")} · ${text(
          record.transformation,
          "未提供变换说明",
        )}`,
      ),
    );
    card.append(
      makeTextElement("p", "", `Copy-risk：${text(record.copy_risk, "未提供")}`),
    );
    target.append(card);
  });
}

function fragmentsForConcept(curation, ref) {
  return asArray(curation.feedback_fragments).filter((fragment) => {
    const related = asArray(fragment.concept_refs);
    return text(fragment.concept_ref) === ref || related.includes(ref);
  });
}

function renderResolutionActions(curation) {
  const target = byId("resolution-actions");
  target.replaceChildren();
  getConcepts().forEach((concept) => {
    const ref = conceptRef(concept);
    const card = document.createElement("section");
    card.className = "resolution-action";
    card.dataset.conceptRef = ref;
    card.append(makeTextElement("h3", "", conceptTitle(concept)));

    const actionLabel = document.createElement("label");
    actionLabel.textContent = "Action";
    const action = document.createElement("select");
    action.className = "action-select";
    action.dataset.conceptRef = ref;
    [
      ["", "请选择"],
      ["keep", "keep"],
      ["revise", "revise"],
      ["reject", "reject"],
      ["taste_veto", "taste veto"],
      ["merge", "merge"],
    ].forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      action.append(option);
    });
    actionLabel.append(action);
    card.append(actionLabel);

    const mergeLabel = document.createElement("label");
    mergeLabel.textContent = "Merge group（同组至少两个 source）";
    const mergeInput = document.createElement("input");
    mergeInput.className = "merge-group";
    mergeInput.dataset.conceptRef = ref;
    mergeInput.placeholder = "例如 relay-merge-a";
    mergeLabel.append(mergeInput);
    card.append(mergeLabel);

    const reasonLabel = document.createElement("label");
    reasonLabel.textContent = "动作理由（taste veto / merge 必填）";
    const reasonInput = document.createElement("textarea");
    reasonInput.className = "action-reason";
    reasonInput.dataset.conceptRef = ref;
    reasonInput.maxLength = 4000;
    reasonInput.rows = 3;
    reasonLabel.append(reasonInput);
    card.append(reasonLabel);

    const instructionLabel = document.createElement("label");
    instructionLabel.textContent = "允许交给 Agent 的策展指令";
    const instructionInput = document.createElement("textarea");
    instructionInput.className = "action-instruction";
    instructionInput.dataset.conceptRef = ref;
    instructionInput.maxLength = 4000;
    instructionInput.rows = 3;
    instructionLabel.append(instructionInput);
    card.append(instructionLabel);

    const fragmentTitle = makeTextElement("p", "eyebrow", "Approved fragments（默认不选）");
    card.append(fragmentTitle);
    const fragmentList = document.createElement("div");
    fragmentList.className = "fragment-list";
    fragmentsForConcept(curation, ref).forEach((fragment) => {
      const label = document.createElement("label");
      label.className = "fragment-option";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "approved-fragment";
      checkbox.dataset.conceptRef = ref;
      checkbox.dataset.feedbackRef = text(fragment.feedback_ref);
      checkbox.dataset.feedbackSha256 = text(fragment.feedback_sha256);
      const copy = makeTextElement(
        "span",
        "",
        text(fragment.text, text(fragment.excerpt, fragment.feedback_ref)),
      );
      label.append(checkbox, copy);
      fragmentList.append(label);
    });
    if (!fragmentList.childElementCount) {
      fragmentList.append(makeTextElement("p", "", "暂无可批准的相关反馈片段。"));
    }
    card.append(fragmentList);
    target.append(card);
  });
}

function render() {
  const concepts = getConcepts();
  if (!concepts.length) {
    byId("concept-card").hidden = true;
    byId("review-panel").hidden = true;
    setPageState("本轮没有待审候选；工作流会直接进入零 Idea 报告。");
  } else {
    byId("review-panel").hidden =
      text(asObject(asObject(state.snapshot).viewer).role) === "curator";
    setPageState(
      state.pairMode
        ? "Pairwise 完全可选；跳过不会被解释为平局或拒绝。"
        : "先看 Concept，再留下自己的独立复述。",
    );
  }
  renderRoundMeta();
  renderConceptList();
  renderConcept();
  renderPairMode();
  restoreForm();
  renderTeamWall();
  renderReceiptState();
  renderCurator();
}

function buildReviewPayload() {
  storeCurrentConceptDraft();
  const conceptReviews = Object.values(asObject(state.draft.concept_reviews)).filter(
    (review) => text(review.one_sentence_retell).trim(),
  );
  if (!state.profile.reviewer_name) {
    throw new Error("请填写评审人名字。");
  }
  if (!conceptReviews.length) {
    throw new Error("至少为一个候选留下一句话复述。");
  }
  const pairwise = Object.values(asObject(state.draft.pairwise)).filter((pair) =>
    ["left", "right", "both", "neither", "cannot_compare"].includes(pair.preference),
  );
  const round = getRound();
  return {
    review_id: text(state.draft.review_id),
    run_id: text(asObject(state.snapshot).run_id),
    round_id: text(round.id, text(round.round_id)),
    round_sha256: text(round.sha256),
    reviewer_id: state.profile.reviewer_id,
    reviewer_name: state.profile.reviewer_name,
    concept_reviews: conceptReviews,
    pairwise,
    overall_comment: text(state.draft.overall_comment),
    supersedes_review_id: state.submittedReviewId,
  };
}

async function submitReview(event) {
  event.preventDefault();
  setError("review-errors", "");
  if (state.staleDraft) {
    setError("review-errors", "轮次 hash 已变化；请先清除旧草稿并重新检查。");
    return;
  }
  const button = byId("submit-review");
  button.disabled = true;
  button.textContent = "正在绑定回执…";
  try {
    const payload = buildReviewPayload();
    const result = await api("/api/reviews", { method: "POST", body: payload });
    state.submittedReviewId = text(result.review_id, payload.review_id);
    safeRemoveStorage(DRAFT_KEY);
    await refreshSnapshot();
    const signal = byId("receipt-signal");
    signal.classList.remove("is-new");
    globalThis.requestAnimationFrame(() => signal.classList.add("is-new"));
    setPageState("回执已绑定到本轮精确 Concept revision。", "success");
  } catch (error) {
    const stale = error.status === 409 || error.code === "stale_round";
    if (stale) {
      state.staleDraft = true;
      byId("stale-warning").hidden = false;
    }
    setError("review-errors", error.message);
  } finally {
    button.disabled = state.staleDraft;
    button.textContent = "传递回执";
  }
}

function collectResolutionPayload() {
  const round = getRound();
  const savedResolution = asObject(safeReadStorage(RESOLUTION_DRAFT_KEY));
  if (
    !state.resolutionId ||
    (text(savedResolution.round_sha256) &&
      text(savedResolution.round_sha256) !== text(round.sha256))
  ) {
    state.resolutionId =
      text(savedResolution.round_sha256) === text(round.sha256)
        ? text(savedResolution.resolution_id, randomId())
        : randomId();
    safeWriteStorage(RESOLUTION_DRAFT_KEY, {
      round_sha256: text(round.sha256),
      resolution_id: state.resolutionId,
    });
  }
  const actions = [];
  const mergeGroups = new Map();
  document.querySelectorAll(".resolution-action").forEach((card) => {
    const ref = card.dataset.conceptRef;
    const action = card.querySelector(".action-select").value;
    const mergeGroup = card.querySelector(".merge-group").value.trim();
    const reason = card.querySelector(".action-reason").value.trim();
    const curatorInstruction = card.querySelector(".action-instruction").value.trim();
    const approved = Array.from(card.querySelectorAll(".approved-fragment:checked")).map(
      (checkbox) => ({
        feedback_ref: checkbox.dataset.feedbackRef,
        feedback_sha256: checkbox.dataset.feedbackSha256,
      }),
    );
    actions.push({
      concept_ref: ref,
      action,
      approved_feedback: approved,
      curator_instruction: curatorInstruction,
      reason,
      merge_group_id: action === "merge" ? mergeGroup : null,
    });
    if (action === "merge" && mergeGroup) {
      if (!mergeGroups.has(mergeGroup)) {
        mergeGroups.set(mergeGroup, []);
      }
      mergeGroups.get(mergeGroup).push(ref);
    }
  });
  return {
    resolution_id: state.resolutionId,
    run_id: text(asObject(state.snapshot).run_id),
    round_id: text(round.id, text(round.round_id)),
    round_sha256: text(round.sha256),
    curator_name: byId("curator-name").value.trim(),
    actions,
    merge_groups: Array.from(mergeGroups, ([merge_group_id, source_refs]) => ({
      merge_group_id,
      source_refs,
      reason:
        actions.find((action) => action.merge_group_id === merge_group_id)?.reason || "",
    })),
    coverage_override_reason: byId("coverage-override").value.trim() || null,
  };
}

function validateResolution(payload) {
  if (!payload.curator_name) {
    return "请填写策展人名字。";
  }
  if (payload.actions.some((action) => !action.action)) {
    return "每个候选都必须明确选择一个 action。";
  }
  const mergeSources = new Set();
  for (const group of payload.merge_groups) {
    if (group.source_refs.length < 2) {
      return `Merge group ${group.merge_group_id} 至少需要两个 source。`;
    }
    if (!group.reason) {
      return `Merge group ${group.merge_group_id} 需要明确理由。`;
    }
    for (const ref of group.source_refs) {
      if (mergeSources.has(ref)) {
        return `${ref} 不能进入两个 merge group。`;
      }
      mergeSources.add(ref);
    }
  }
  const overSelected = payload.actions.some(
    (action) => action.approved_feedback.length > 12,
  );
  if (overSelected) {
    return "每个 C6C action 最多批准 12 个 feedback fragment，请减少选择。";
  }
  const needsGuidance = payload.actions.some(
    (action) =>
      ["revise", "merge"].includes(action.action) &&
      !action.approved_feedback.length &&
      !action.curator_instruction,
  );
  if (needsGuidance) {
    return "revise / merge 至少需要一个相关 feedback fragment 或策展指令。";
  }
  const missingTasteReason = payload.actions.some(
    (action) => action.action === "taste_veto" && !action.reason,
  );
  if (missingTasteReason) {
    return "taste veto 必须填写明确的主观品味理由。";
  }
  const curation = asObject(asObject(state.snapshot).curation);
  if (asArray(curation.uncovered_concept_refs).length && !payload.coverage_override_reason) {
    return "覆盖不足；请补齐回执或填写明确的 override reason。";
  }
  return "";
}

async function submitResolution(event) {
  event.preventDefault();
  setError("resolution-errors", "");
  const payload = collectResolutionPayload();
  const validationError = validateResolution(payload);
  if (validationError) {
    setError("resolution-errors", validationError);
    return;
  }
  const summary = payload.actions
    .map((action) => `${action.concept_ref}: ${action.action}`)
    .join("\n");
  if (!globalThis.confirm(`关闭后不可继续提交评审。请确认：\n\n${summary}`)) {
    return;
  }
  const button = byId("close-round");
  button.disabled = true;
  button.textContent = "正在冻结本轮…";
  try {
    const result = await api("/api/resolve", { method: "POST", body: payload });
    safeRemoveStorage(RESOLUTION_DRAFT_KEY);
    const command = text(result.next_command, text(asObject(state.snapshot).next_command));
    byId("resume-command").textContent = command || "本轮已关闭，可以返回终端继续 resume。";
    byId("round-status").textContent = "本轮已关闭";
    byId("round-status").dataset.status = "closed";
    setPageState("决议已冻结；服务器即将安全退出。", "success");
    byId("resolution-form").querySelectorAll("input, textarea, select, button").forEach(
      (element) => {
        element.disabled = true;
      },
    );
  } catch (error) {
    setError("resolution-errors", error.message);
    button.disabled = false;
    button.textContent = "关闭本轮并交回 Agent";
  }
}

async function refreshSnapshot() {
  state.snapshot = await api("/api/snapshot");
  const viewer = asObject(state.snapshot.viewer);
  if (typeof viewer.reviewer_id === "string" && viewer.reviewer_id) {
    state.profile.reviewer_id = viewer.reviewer_id;
  }
  render();
}

function bindInputPersistence() {
  ["reviewer-name", "retell", "share-target", "recommendation", "comment", "overall-comment"].forEach(
    (id) => {
      byId(id).addEventListener("input", () => {
        storeCurrentConceptDraft();
        updateAllCounts();
      });
      byId(id).addEventListener("change", storeCurrentConceptDraft);
    },
  );
  [
    ["pair-reason", "pair-reason-count"],
    ["coverage-override", "coverage-override-count"],
  ].forEach(([inputId, countId]) => {
    byId(inputId).addEventListener("input", () => updateCount(inputId, countId));
  });
}

function bindEvents() {
  byId("review-form").addEventListener("submit", submitReview);
  byId("resolution-form").addEventListener("submit", submitResolution);
  byId("pair-mode-button").addEventListener("click", () => {
    if (!getPairs().length) {
      setPageState("本轮候选不足，或没有安排 pair；可以直接提交单项评审。");
      return;
    }
    storeCurrentConceptDraft();
    state.pairMode = true;
    state.currentPairIndex = 0;
    render();
  });
  byId("leave-pair-mode").addEventListener("click", () => {
    state.pairMode = false;
    render();
  });
  byId("pair-left").addEventListener("click", () => choosePairPreference("left"));
  byId("pair-right").addEventListener("click", () => choosePairPreference("right"));
  byId("save-pair").addEventListener("click", () => savePair(false));
  byId("skip-pair").addEventListener("click", () => savePair(true));
  byId("discard-stale-draft").addEventListener("click", () => {
    state.staleDraft = false;
    state.draft = emptyDraft();
    safeRemoveStorage(DRAFT_KEY);
    byId("stale-warning").hidden = true;
    byId("submit-review").disabled = false;
    render();
  });
  byId("edit-after-reveal").addEventListener("click", () => {
    const previous = state.submittedReviewId;
    state.draft = emptyDraft();
    state.draft.review_id = randomId();
    state.submittedReviewId = previous;
    byId("receipt-form-wrap").hidden = false;
    byId("receipt-signal").hidden = true;
    restoreForm();
    byId("retell").focus();
  });
  bindInputPersistence();
}

async function boot() {
  state.profile = loadOrCreateProfile();
  bindEvents();
  try {
    await registerReviewerSession();
    state.snapshot = await api("/api/snapshot");
    loadDraft();
    render();
  } catch (error) {
    setPageState(error.message, "error");
    byId("concept-card").hidden = true;
    byId("review-panel").hidden = true;
  }
}

boot();
