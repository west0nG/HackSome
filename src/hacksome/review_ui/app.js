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
const SHARE_IMPULSE_LABELS = {
  immediate: "会立刻点开 / 转发 / 拉人来试",
  maybe: "也许会分享",
  no: "不会分享",
};
const DEMO_CONFIDENCE_LABELS = {
  yes: "相信比赛时间内能跑起来",
  maybe: "对 Demo 可行性不确定",
  no: "不相信比赛时间内能跑起来",
};

const state = {
  snapshot: null,
  profile: null,
  currentPairIndex: 0,
  pairMode: false,
  pairPreference: null,
  draft: null,
  staleDraft: false,
  submittedReviewId: null,
  editingAfterReveal: false,
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

function reviewSchemaVersion() {
  return Number(asObject(state.snapshot).schema_version) === 1 ? 1 : 2;
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
    schema_version: reviewSchemaVersion(),
    round_sha256: text(getRound().sha256),
    review_id: randomId(),
    reviewer_name: text(state.profile.reviewer_name),
    concept_reviews: {},
    pairwise: {},
    overall_comment: "",
  };
}

function normalizeConceptDraft(value) {
  const draft = asObject(value);
  if (reviewSchemaVersion() >= 2) {
    if (!["immediate", "maybe", "no"].includes(draft.share_impulse)) {
      draft.share_impulse = "maybe";
    }
    if (!["yes", "maybe", "no"].includes(draft.demo_confidence)) {
      draft.demo_confidence = "maybe";
    }
  } else {
    delete draft.share_impulse;
    delete draft.demo_confidence;
  }
  return draft;
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
  const conceptReviews = Object.fromEntries(
    Object.entries(asObject(saved.concept_reviews)).map(([ref, review]) => [
      ref,
      normalizeConceptDraft(review),
    ]),
  );
  state.draft = {
    ...emptyDraft(),
    ...saved,
    schema_version: reviewSchemaVersion(),
    concept_reviews: conceptReviews,
    pairwise: asObject(saved.pairwise),
  };
}

function saveDraft() {
  if (!state.draft || state.staleDraft) {
    return;
  }
  state.draft.schema_version = reviewSchemaVersion();
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

function conceptDraft(concept) {
  if (!concept || !state.draft) {
    return {};
  }
  const ref = conceptRef(concept);
  if (!state.draft.concept_reviews[ref]) {
    const review = {
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
    if (reviewSchemaVersion() >= 2) {
      review.share_impulse = "maybe";
      review.demo_confidence = "maybe";
    }
    state.draft.concept_reviews[ref] = review;
  }
  // Migrate a bound v1 browser draft in place without discarding the user's
  // text. The round hash remains the stale-draft authority.
  return normalizeConceptDraft(state.draft.concept_reviews[ref]);
}

function conceptDraftIsComplete(concept) {
  return Boolean(text(conceptDraft(concept).one_sentence_retell).trim());
}

function reviewedConceptCount() {
  return getConcepts().filter(conceptDraftIsComplete).length;
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
    button.dataset.complete = conceptDraftIsComplete(concept) ? "true" : "false";
    button.setAttribute("aria-label", `跳到项目 ${index + 1}：${conceptTitle(concept)}`);
    button.append(
      makeTextElement(
        "span",
        "list-number",
        String(index + 1).padStart(2, "0"),
      ),
      makeTextElement("span", "list-title", conceptTitle(concept)),
    );
    button.addEventListener("click", () => {
      const card = byId(`concept-card-${index + 1}`);
      if (card) {
        card.focus();
      }
    });
    item.append(button);
    list.append(item);
  });
}

function appendFactCopy(parent, label, value) {
  parent.append(
    makeTextElement("p", "fact-label", label),
    makeTextElement("p", "fact-copy", value),
  );
}

function createFactPanel(title) {
  const panel = document.createElement("section");
  panel.className = "fact-panel";
  panel.append(makeTextElement("h3", "", title));
  return panel;
}

function createExperienceStep(label, value, step) {
  const wrapper = document.createElement("div");
  wrapper.className = "experience-step";
  wrapper.dataset.step = step;
  wrapper.append(
    makeTextElement("p", "fact-label", label),
    makeTextElement("p", "fact-copy", value),
  );
  return wrapper;
}

function appendSelectOptions(select, choices, selectedValue) {
  choices.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = value === selectedValue;
    select.append(option);
  });
}

function bindReviewField(element, index, fieldName) {
  element.dataset.conceptIndex = String(index);
  element.dataset.reviewField = fieldName;
  element.name = fieldName;
}

function createCharacterNote(inputId, help, maximum) {
  const note = document.createElement("p");
  note.className = "field-note";
  if (help) {
    note.append(makeTextElement("span", "", help));
  }
  const countWrap = document.createElement("span");
  const count = makeTextElement("span", "", "0");
  count.dataset.countFor = inputId;
  countWrap.append(count, document.createTextNode(` / ${maximum}`));
  note.append(countWrap);
  return note;
}

function createReactionGroups(index, draft) {
  const container = document.createElement("div");
  container.className = "reaction-groups";
  const reactions = asObject(draft.reactions);
  REACTION_NAMES.forEach((name) => {
    const wrapper = document.createElement("div");
    wrapper.className = "reaction-group";
    wrapper.setAttribute("role", "group");
    wrapper.setAttribute("aria-label", REACTION_LABELS[name]);
    wrapper.append(makeTextElement("p", "reaction-group-name", REACTION_LABELS[name]));
    REACTION_VALUES.forEach((value) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "reaction-chip";
      button.dataset.conceptIndex = String(index);
      button.dataset.reaction = name;
      button.dataset.value = value;
      button.setAttribute("aria-pressed", reactions[name] === value ? "true" : "false");
      button.textContent = REACTION_VALUE_LABELS[value];
      wrapper.append(button);
    });
    container.append(wrapper);
  });
  return container;
}

function createConceptReviewSection(concept, index) {
  const draft = conceptDraft(concept);
  const section = document.createElement("section");
  section.className = "project-review-section";
  section.dataset.conceptIndex = String(index);
  const titleId = `review-sheet-title-${index + 1}`;
  section.setAttribute("aria-labelledby", titleId);

  const heading = document.createElement("header");
  heading.className = "review-sheet-heading";
  const headingCopy = document.createElement("div");
  headingCopy.append(
    makeTextElement("p", "eyebrow", `你的评审 / 项目 ${String(index + 1).padStart(2, "0")}`),
  );
  const title = makeTextElement("h3", "", "这张项目卡自己的回执");
  title.id = titleId;
  headingCopy.append(
    title,
    makeTextElement(
      "p",
      "",
      "写下一句话复述就会把这张卡纳入提交；不想评的项目可以整张跳过。",
    ),
  );
  const status = makeTextElement(
    "span",
    "concept-review-status",
    conceptDraftIsComplete(concept) ? "草稿已记" : "可跳过",
  );
  status.dataset.complete = conceptDraftIsComplete(concept) ? "true" : "false";
  heading.append(headingCopy, status);
  section.append(heading);

  const fields = document.createElement("div");
  fields.className = "project-review-fields";

  const retellWrap = document.createElement("div");
  retellWrap.className = "field field-full";
  const retellId = `retell-${index + 1}`;
  const retellLabel = document.createElement("label");
  retellLabel.htmlFor = retellId;
  retellLabel.textContent = "一句话复述";
  const retell = document.createElement("textarea");
  retell.id = retellId;
  retell.maxLength = 400;
  retell.rows = 3;
  retell.value = text(draft.one_sentence_retell);
  retell.setAttribute("aria-describedby", `${retellId}-note`);
  bindReviewField(retell, index, "one_sentence_retell");
  const retellNote = createCharacterNote(
    retellId,
    "不看原文时，你会怎样讲给下一位？",
    400,
  );
  retellNote.id = `${retellId}-note`;
  retellWrap.append(retellLabel, retell, retellNote);
  fields.append(retellWrap);

  const shareWrap = document.createElement("div");
  shareWrap.className = "field";
  const shareId = `share-target-${index + 1}`;
  const shareLabel = document.createElement("label");
  shareLabel.htmlFor = shareId;
  shareLabel.textContent = "立刻想到想发给谁？";
  const shareTarget = document.createElement("input");
  shareTarget.id = shareId;
  shareTarget.maxLength = 200;
  shareTarget.placeholder = "一个具体的人或一类明确的朋友";
  shareTarget.value = text(draft.share_target);
  bindReviewField(shareTarget, index, "share_target");
  shareWrap.append(
    shareLabel,
    shareTarget,
    createCharacterNote(shareId, "选“会，立刻”时必填。", 200),
  );
  fields.append(shareWrap);

  const recommendationWrap = document.createElement("div");
  recommendationWrap.className = "field";
  const recommendationId = `recommendation-${index + 1}`;
  const recommendationLabel = document.createElement("label");
  recommendationLabel.htmlFor = recommendationId;
  recommendationLabel.textContent = "你希望这个项目接下来怎样？";
  const recommendation = document.createElement("select");
  recommendation.id = recommendationId;
  bindReviewField(recommendation, index, "recommendation");
  appendSelectOptions(
    recommendation,
    [
      ["no_opinion", "暂不表态"],
      ["keep", "保留"],
      ["revise", "修订"],
      ["reject", "拒绝"],
      ["taste_veto", "Taste veto"],
    ],
    text(draft.recommendation, "no_opinion"),
  );
  recommendationWrap.append(recommendationLabel, recommendation);
  fields.append(recommendationWrap);

  if (reviewSchemaVersion() >= 2) {
    const signalGrid = document.createElement("div");
    signalGrid.className = "signal-grid";

    const impulseWrap = document.createElement("div");
    impulseWrap.className = "field";
    const impulseId = `share-impulse-${index + 1}`;
    const impulseLabel = document.createElement("label");
    impulseLabel.htmlFor = impulseId;
    impulseLabel.textContent = "你会马上点开、转发或拉人来试吗？";
    const impulse = document.createElement("select");
    impulse.id = impulseId;
    bindReviewField(impulse, index, "share_impulse");
    appendSelectOptions(
      impulse,
      [
        ["immediate", "会，立刻"],
        ["maybe", "也许，要再看看"],
        ["no", "不会"],
      ],
      text(draft.share_impulse, "maybe"),
    );
    impulseWrap.append(impulseLabel, impulse);

    const confidenceWrap = document.createElement("div");
    confidenceWrap.className = "field";
    const confidenceId = `demo-confidence-${index + 1}`;
    const confidenceLabel = document.createElement("label");
    confidenceLabel.htmlFor = confidenceId;
    confidenceLabel.textContent = "这个最小 Demo 能在比赛时间内跑起来吗？";
    const confidence = document.createElement("select");
    confidence.id = confidenceId;
    bindReviewField(confidence, index, "demo_confidence");
    appendSelectOptions(
      confidence,
      [
        ["yes", "相信能"],
        ["maybe", "不确定"],
        ["no", "不相信能"],
      ],
      text(draft.demo_confidence, "maybe"),
    );
    confidenceWrap.append(confidenceLabel, confidence);
    signalGrid.append(impulseWrap, confidenceWrap);
    fields.append(signalGrid);
  }

  const reactionFieldset = document.createElement("fieldset");
  reactionFieldset.className = "reaction-fieldset";
  const reactionLegend = document.createElement("legend");
  reactionLegend.textContent = "看完这个项目的第一反应";
  reactionFieldset.append(reactionLegend, createReactionGroups(index, draft));
  fields.append(reactionFieldset);

  const commentWrap = document.createElement("div");
  commentWrap.className = "field field-full";
  const commentId = `comment-${index + 1}`;
  const commentLabel = document.createElement("label");
  commentLabel.htmlFor = commentId;
  commentLabel.textContent = "只针对这个项目的自由评论";
  const comment = document.createElement("textarea");
  comment.id = commentId;
  comment.maxLength = 4000;
  comment.rows = 5;
  comment.value = text(draft.comment);
  bindReviewField(comment, index, "comment");
  commentWrap.append(
    commentLabel,
    comment,
    createCharacterNote(commentId, "这段会与本项目绑定，不会混到其他卡。", 4000),
  );
  fields.append(commentWrap);

  section.append(fields);
  return section;
}

function createConceptReviewCard(concept, index, total) {
  const card = document.createElement("article");
  card.id = `concept-card-${index + 1}`;
  card.className = "project-review-card";
  card.tabIndex = -1;
  card.dataset.conceptIndex = String(index);

  const header = document.createElement("header");
  header.className = "project-file-header";
  header.append(
    makeTextElement(
      "span",
      "file-number",
      `${String(index + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}`,
    ),
  );

  const heading = document.createElement("div");
  heading.className = "project-heading";
  const title = makeTextElement("h2", "", conceptTitle(concept));
  title.id = `concept-title-${index + 1}`;
  const hook = fieldText(concept, "hook", "one_sentence_hook", "title");
  const lede =
    hook === conceptTitle(concept)
      ? fieldText(concept, "first_impression", "first_thirty_seconds")
      : hook;
  heading.append(title, makeTextElement("p", "project-hook", lede));

  const binding = document.createElement("div");
  binding.className = "project-binding";
  binding.append(
    makeTextElement("p", "concept-id", conceptRef(concept)),
    makeTextElement(
      "p",
      "territory-label",
      text(concept.primary_territory_ref, text(concept.territory)),
    ),
    makeTextElement("p", "hash-label", `sha256 ${shortHash(conceptHash(concept))}`),
  );
  header.append(heading, binding);
  card.append(header);

  const facts = document.createElement("div");
  facts.className = "project-facts";

  const experience = createFactPanel("体验与 Hook");
  const trace = document.createElement("div");
  trace.className = "experience-trace";
  trace.append(
    createExperienceStep(
      "先看到",
      fieldText(concept, "first_impression", "first_thirty_seconds"),
      "setup",
    ),
    createExperienceStep(
      "观众做什么",
      fieldText(concept, "audience_action", "action"),
      "action",
    ),
    createExperienceStep(
      "Reveal / 余韵",
      fieldText(concept, "reveal", "setup_reveal_aftertaste"),
      "reveal",
    ),
  );
  experience.append(trace);

  const software = createFactPanel("软件 / Demo");
  appendFactCopy(
    software,
    "软件核心与运行入口",
    fieldText(
      concept,
      "software_core_and_runtime",
      "core_mechanism",
      "mechanism",
    ),
  );
  appendFactCopy(
    software,
    "最小 Hackathon Demo",
    fieldText(concept, "minimum_hackathon_demo", "minimum_demo"),
  );

  const share = createFactPanel("分享对象 / 产物");
  appendFactCopy(
    share,
    "分享触发与可转发物",
    fieldText(
      concept,
      "share_trigger_and_artifact",
      "why_someone_may_share_it",
    ),
  );
  appendFactCopy(
    share,
    "一句话 Hook",
    fieldText(concept, "hook", "one_sentence_hook", "title"),
  );
  facts.append(experience, software, share);
  card.append(facts);

  const details = document.createElement("details");
  details.className = "source-details";
  const summary = document.createElement("summary");
  summary.textContent = "查看其余原始材料：机制、先例与风险";
  const detailGrid = document.createElement("div");
  detailGrid.className = "source-detail-grid";
  [
    [
      "真实输入与转换",
      fieldText(concept, "core_mechanism", "mechanism"),
    ],
    [
      "先例与差异",
      fieldText(concept, "novelty", "novelty_and_references"),
    ],
    [
      "尚未解决",
      fieldText(concept, "risks", "assumptions_confusion_and_risks"),
    ],
  ].forEach(([label, value]) => {
    const section = document.createElement("section");
    section.append(
      makeTextElement("h4", "", label),
      makeTextElement("p", "", value),
    );
    detailGrid.append(section);
  });
  details.append(summary, detailGrid);
  card.append(details, createConceptReviewSection(concept, index));
  return card;
}

function renderConceptCards() {
  const target = byId("concept-review-cards");
  target.replaceChildren();
  const concepts = getConcepts();
  concepts.forEach((concept, index) => {
    target.append(createConceptReviewCard(concept, index, concepts.length));
  });
}

function syncConceptReviewFields() {
  if (!state.draft || state.staleDraft) {
    return;
  }
  document.querySelectorAll("[data-review-field]").forEach((element) => {
    const index = Number(element.dataset.conceptIndex);
    const concept = getConcepts()[index];
    if (!concept) {
      return;
    }
    conceptDraft(concept)[element.dataset.reviewField] = element.value;
  });
}

function storeReviewDraft() {
  if (!state.draft || state.staleDraft) {
    return;
  }
  syncConceptReviewFields();
  state.draft.reviewer_name = byId("reviewer-name").value.trim();
  state.draft.overall_comment = byId("overall-comment").value;
  persistProfileName(state.draft.reviewer_name);
  saveDraft();
}

function restoreForm() {
  byId("reviewer-name").value = text(
    state.draft.reviewer_name,
    state.profile.reviewer_name,
  );
  byId("overall-comment").value = text(state.draft.overall_comment);
  updateAllCounts();
}

function updateCount(inputId, countId) {
  const input = byId(inputId);
  const count = byId(countId);
  if (input && count) {
    count.textContent = String(input.value.length);
  }
}

function updateAllCounts() {
  document.querySelectorAll("[data-count-for]").forEach((count) => {
    const input = byId(count.dataset.countFor);
    count.textContent = input ? String(input.value.length) : "0";
  });
  updateCount("overall-comment", "overall-comment-count");
  updateCount("pair-reason", "pair-reason-count");
  updateCount("coverage-override", "coverage-override-count");
}

function updateConceptReviewStatus(index) {
  const concept = getConcepts()[index];
  if (!concept) {
    return;
  }
  const complete = conceptDraftIsComplete(concept);
  const card = byId(`concept-card-${index + 1}`);
  const status = card ? card.querySelector(".concept-review-status") : null;
  if (status) {
    status.dataset.complete = complete ? "true" : "false";
    status.textContent = complete ? "草稿已记" : "可跳过";
  }
  const indexButton = byId("concept-list").querySelector(`[data-index="${index}"]`);
  if (indexButton) {
    indexButton.dataset.complete = complete ? "true" : "false";
  }
  renderRoundMeta();
}

function renderRoundMeta() {
  const round = getRound();
  const status = text(round.status, "open");
  byId("round-status").textContent = status === "closed" ? "本轮已关闭" : "本轮正在接力";
  byId("round-status").dataset.status = status;
  const concepts = getConcepts();
  const isCurator = text(asObject(asObject(state.snapshot).viewer).role) === "curator";
  byId("relay-position").textContent = concepts.length
    ? isCurator
      ? `${String(concepts.length).padStart(2, "0")} 项`
      : `${String(reviewedConceptCount()).padStart(2, "0")} / ${String(
          concepts.length,
        ).padStart(2, "0")}`
    : "00 / 00";
  byId("profile-label").textContent = text(state.profile.reviewer_name, "尚未登记");
  const coverage = asObject(asObject(state.snapshot).coverage_summary);
  const covered = Number(coverage.covered_concept_count || 0);
  const reviewerCount = Number(coverage.reviewer_count || 0);
  byId("coverage-summary").textContent =
    isCurator
      ? `匿名覆盖：${covered}/${concepts.length} 个项目 · ${reviewerCount} 位评审者`
      : `你的草稿：${reviewedConceptCount()}/${concepts.length} 个项目 · 团队已有 ${reviewerCount} 位评审者`;
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
    asArray(entry.concept_reviews).forEach((review) => {
      card.append(
        makeTextElement(
          "strong",
          "",
          `${text(review.concept_ref, "候选")}：${text(
            review.one_sentence_retell,
            "未填写复述",
          )}`,
        ),
      );
      const impulse = text(review.share_impulse);
      const confidence = text(review.demo_confidence);
      card.append(
        makeTextElement(
          "p",
          "human-signal",
          impulse
            ? SHARE_IMPULSE_LABELS[impulse] || impulse
            : "旧版回执：未记录分享冲动",
        ),
      );
      card.append(
        makeTextElement(
          "p",
          "",
          text(review.share_target)
            ? `想到的人：${review.share_target}`
            : "没有填写分享对象",
        ),
      );
      card.append(
        makeTextElement(
          "p",
          "human-signal",
          confidence
            ? DEMO_CONFIDENCE_LABELS[confidence] || confidence
            : "旧版回执：未记录 Demo 信心",
        ),
      );
      if (text(review.comment)) {
        card.append(makeTextElement("p", "", review.comment));
      }
    });
    if (text(entry.overall_comment)) {
      card.append(makeTextElement("p", "", `整体补充：${entry.overall_comment}`));
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
  const isCurator = text(viewer.role) === "curator";
  const showReceipt =
    submitted && !state.editingAfterReveal && !state.pairMode && !isCurator;
  byId("review-form").classList.toggle("is-submitted", showReceipt);
  byId("receipt-signal").hidden = !showReceipt;
  if (!submitted) {
    return;
  }
  const reviewed = getConcepts()
    .map((concept, index) => ({ concept, index, review: conceptDraft(concept) }))
    .filter(({ review }) => text(review.one_sentence_retell).trim());
  byId("receipt-signature").textContent = reviewed.length
    ? `${text(state.profile.reviewer_name, "你")} 已提交 ${reviewed.length} 张项目回执`
    : `${text(state.profile.reviewer_name, "你")} 的本轮回执已提交`;
  const projects = byId("receipt-projects");
  projects.replaceChildren();
  reviewed.forEach(({ concept, index, review }) => {
    const row = document.createElement("article");
    row.className = "receipt-project-row";
    row.append(
      makeTextElement("span", "file-number", String(index + 1).padStart(2, "0")),
    );
    const copy = document.createElement("div");
    copy.append(
      makeTextElement(
        "strong",
        "",
        `${conceptTitle(concept)}：${text(review.one_sentence_retell)}`,
      ),
      makeTextElement(
        "p",
        "",
        text(review.share_target)
          ? `${SHARE_IMPULSE_LABELS[text(review.share_impulse)] || "分享信号"} · 想到：${
              review.share_target
            }`
          : SHARE_IMPULSE_LABELS[text(review.share_impulse)] ||
              "这次没有指定分享对象。",
      ),
    );
    row.append(copy);
    projects.append(row);
  });
  if (!reviewed.length) {
    projects.append(
      makeTextElement(
        "p",
        "",
        "页面刷新后，本轮精确回执仍保存在 append-only ledger；详细文本可在 Team Wall 查看。",
      ),
    );
  }
  const round = getRound();
  byId("receipt-binding").textContent =
    `✓ 每个项目分别绑定 exact revision / hash · ${text(
      round.id,
      text(round.round_id),
    )} / ${shortHash(round.sha256)}`;
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
  renderCuratorFeasibility(curation);
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
      card.append(
        makeTextElement(
          "p",
          "human-signal",
          text(review.share_impulse)
            ? SHARE_IMPULSE_LABELS[review.share_impulse] || review.share_impulse
            : "旧版回执：未记录分享冲动",
        ),
      );
      card.append(
        makeTextElement("p", "", `想到的人：${text(review.share_target, "未填写")}`),
      );
      card.append(
        makeTextElement(
          "p",
          "human-signal",
          text(review.demo_confidence)
            ? DEMO_CONFIDENCE_LABELS[review.demo_confidence] || review.demo_confidence
            : "旧版回执：未记录 Demo 信心",
        ),
      );
      card.append(makeTextElement("p", "", text(review.comment)));
    });
    receiptsTarget.append(card);
  });
}

function renderCuratorFeasibility(curation) {
  const target = byId("curator-feasibility");
  target.replaceChildren();
  const rows = asArray(curation.feasibility_evidence);
  if (!rows.length) {
    target.append(
      makeTextElement(
        "p",
        "",
        "本轮没有 C4F 证据（旧版 waiting run 仍可继续评审）。",
      ),
    );
    return;
  }
  rows.forEach((row) => {
    const card = document.createElement("article");
    card.className = "feasibility-note";
    card.append(makeTextElement("p", "eyebrow", text(row.concept_ref)));
    card.append(
      makeTextElement(
        "strong",
        "",
        `机器 C4F：${text(row.overall_decision, "unknown")}`,
      ),
    );
    asArray(row.dimensions).forEach((dimension) => {
      const reason = text(dimension.reason_code);
      card.append(
        makeTextElement(
          "p",
          "",
          `${text(dimension.dimension)} · ${text(dimension.verdict)}${
            reason ? ` · ${reason}` : ""
          }\n${text(dimension.evidence)}`,
        ),
      );
    });
    target.append(card);
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
  const isCurator = text(asObject(asObject(state.snapshot).viewer).role) === "curator";
  document.body.classList.toggle("is-curator", isCurator);
  byId("concept-index").hidden = !concepts.length || state.pairMode;
  byId("review-form").hidden = !concepts.length || state.pairMode;
  if (!concepts.length) {
    setPageState("本轮没有待审候选；工作流会直接进入零 Idea 报告。");
  } else {
    setPageState(
      state.pairMode
        ? "Pairwise 完全可选；跳过不会被解释为平局或拒绝。"
        : isCurator
          ? "策展模式会显示完整机器证据；候选档案仍保留原始项目上下文。"
          : "每张项目档案的下半部只评这一个 Concept；可跳过其他卡。",
    );
  }
  renderConceptCards();
  renderRoundMeta();
  renderConceptList();
  renderPairMode();
  restoreForm();
  renderTeamWall();
  renderReceiptState();
  renderCurator();
}

function buildReviewPayload() {
  storeReviewDraft();
  const conceptReviews = Object.values(asObject(state.draft.concept_reviews)).filter(
    (review) => text(review.one_sentence_retell).trim(),
  );
  if (!state.profile.reviewer_name) {
    throw new Error("请填写评审人名字。");
  }
  if (!conceptReviews.length) {
    throw new Error("至少为一个候选留下一句话复述。");
  }
  const immediateWithoutTarget =
    reviewSchemaVersion() >= 2 &&
    conceptReviews.find(
      (review) =>
        review.share_impulse === "immediate" && !text(review.share_target).trim(),
    );
  if (immediateWithoutTarget) {
    const index = getConcepts().findIndex(
      (concept) => conceptRef(concept) === immediateWithoutTarget.concept_ref,
    );
    const input = byId(`share-target-${index + 1}`);
    if (input) {
      input.focus();
    }
    throw new Error("选择“会立刻发”时，请在对应项目卡里填写具体分享对象。");
  }
  const pairwise = Object.values(asObject(state.draft.pairwise)).filter((pair) =>
    ["left", "right", "both", "neither", "cannot_compare"].includes(pair.preference),
  );
  const round = getRound();
  const normalizedReviews = conceptReviews.map((review) => {
    const result = { ...review };
    if (reviewSchemaVersion() < 2) {
      delete result.share_impulse;
      delete result.demo_confidence;
    }
    return result;
  });
  const payload = {
    review_id: text(state.draft.review_id),
    run_id: text(asObject(state.snapshot).run_id),
    round_id: text(round.id, text(round.round_id)),
    round_sha256: text(round.sha256),
    reviewer_id: state.profile.reviewer_id,
    reviewer_name: state.profile.reviewer_name,
    concept_reviews: normalizedReviews,
    pairwise,
    overall_comment: text(state.draft.overall_comment),
    supersedes_review_id: state.submittedReviewId,
  };
  if (reviewSchemaVersion() >= 2) {
    payload.schema_version = 2;
  }
  return payload;
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
    state.editingAfterReveal = false;
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
  const cards = byId("concept-review-cards");
  const persistConceptField = (event) => {
    const target = event.target.closest("[data-review-field]");
    if (!target || state.staleDraft) {
      return;
    }
    const index = Number(target.dataset.conceptIndex);
    const concept = getConcepts()[index];
    if (!concept) {
      return;
    }
    conceptDraft(concept)[target.dataset.reviewField] = target.value;
    saveDraft();
    updateAllCounts();
    if (target.dataset.reviewField === "one_sentence_retell") {
      updateConceptReviewStatus(index);
    }
  };
  cards.addEventListener("input", persistConceptField);
  cards.addEventListener("change", persistConceptField);
  cards.addEventListener("click", (event) => {
    const button = event.target.closest(".reaction-chip");
    if (!button || state.staleDraft) {
      return;
    }
    const index = Number(button.dataset.conceptIndex);
    const concept = getConcepts()[index];
    if (!concept) {
      return;
    }
    const draft = conceptDraft(concept);
    draft.reactions[button.dataset.reaction] = button.dataset.value;
    button
      .closest(".reaction-group")
      .querySelectorAll(".reaction-chip")
      .forEach((candidate) => {
        candidate.setAttribute(
          "aria-pressed",
          candidate.dataset.value === button.dataset.value ? "true" : "false",
        );
      });
    saveDraft();
  });

  byId("reviewer-name").addEventListener("input", () => {
    if (!state.draft || state.staleDraft) {
      return;
    }
    state.draft.reviewer_name = byId("reviewer-name").value.trim();
    persistProfileName(state.draft.reviewer_name);
    saveDraft();
  });
  byId("overall-comment").addEventListener("input", () => {
    if (!state.draft || state.staleDraft) {
      return;
    }
    state.draft.overall_comment = byId("overall-comment").value;
    saveDraft();
    updateCount("overall-comment", "overall-comment-count");
  });
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
    storeReviewDraft();
    state.pairMode = true;
    state.currentPairIndex = 0;
    render();
    byId("pair-left").focus();
  });
  byId("leave-pair-mode").addEventListener("click", () => {
    state.pairMode = false;
    render();
    byId("pair-mode-button").focus();
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
    state.editingAfterReveal = true;
    render();
    const firstRetell = byId("retell-1");
    if (firstRetell) {
      firstRetell.focus();
    }
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
    byId("concept-index").hidden = true;
    byId("review-form").hidden = true;
    byId("receipt-signal").hidden = true;
    byId("pair-stage").hidden = true;
    byId("team-wall").hidden = true;
    byId("curator-workbench").hidden = true;
  }
}

boot();
