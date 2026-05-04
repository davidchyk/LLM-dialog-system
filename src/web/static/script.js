const MAX_TEXTAREA_HEIGHT = 210;
const MAX_CHAT_TITLE_LENGTH = 60;

const textareas = document.querySelectorAll("textarea");
const forms = document.querySelectorAll(".message-form, .landing-form");
const searchInput = document.querySelector(".chat-search");
const messagesContainer = document.getElementById("messages");
const messageCount = document.querySelector("[data-message-count]");
const chatHeaderTitle = document.querySelector("[data-chat-title]");
const chatEmptyState = document.getElementById("chat-empty-state");
const generationPresetSelect = document.querySelector("[data-generation-preset]");
const modelState = document.querySelector("[data-model-state]");
const modelName = document.querySelector("[data-model-name]");
const messageSearchResults = document.querySelector("[data-message-search-results]");
const messageSearchList = document.querySelector("[data-message-search-list]");
let isGenerating = false;
let searchTimer = null;

function formatLocalTime(isoTimestamp) {
  if (!isoTimestamp) {
    return "";
  }

  const date = new Date(isoTimestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function formatExistingMessageTimes() {
  document.querySelectorAll(".message-time[data-timestamp]").forEach((time) => {
    const formatted = formatLocalTime(time.dataset.timestamp);
    if (formatted) {
      time.textContent = formatted;
    }
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function highlightCode(code) {
  const tokenPattern =
    /(&quot;[^&]*(?:&(?!quot;)[^&]*)*&quot;|&#039;[^&]*(?:&(?!#039;)[^&]*)*&#039;|\/\/.*|#.*|\b(?:class|def|return|if|else|elif|for|while|try|except|finally|with|from|import|as|const|let|var|function|async|await|return|new|true|false|null|None|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|TABLE|JOIN|LEFT|RIGHT|INNER|ORDER|GROUP|BY|LIMIT)\b|\b\d+(?:\.\d+)?\b)/g;

  return code.replace(tokenPattern, (token) => {
    if (token.startsWith("&quot;") || token.startsWith("&#039;")) {
      return `<span class="code-token string">${token}</span>`;
    }
    if (token.startsWith("//") || token.startsWith("#")) {
      return `<span class="code-token comment">${token}</span>`;
    }
    if (/^\d/.test(token)) {
      return `<span class="code-token number">${token}</span>`;
    }
    return `<span class="code-token keyword">${token}</span>`;
  });
}

function renderAssistantMarkdown(text) {
  const codeBlocks = [];
  let escaped = escapeHtml(text);

  escaped = escaped.replace(/```([\w-]*)\n?([\s\S]*?)```/g, (_match, language, code) => {
    const index = codeBlocks.length;
    const languageClass = language ? ` language-${language}` : "";
    const highlightedCode = highlightCode(code.trim());
    codeBlocks.push(
      `<pre><code class="${languageClass.trim()}">${highlightedCode}</code></pre>`
    );
    return `@@CODE_BLOCK_${index}@@`;
  });

  escaped = escaped.replace(/`([^`\n]+)`/g, "<code>$1</code>");

  const paragraphs = escaped
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => {
      if (/^@@CODE_BLOCK_\d+@@$/.test(paragraph)) {
        return paragraph;
      }
      return `<p>${paragraph.replace(/\n/g, "<br>")}</p>`;
    })
    .join("");

  return paragraphs.replace(/@@CODE_BLOCK_(\d+)@@/g, (_match, index) => {
    return codeBlocks[Number(index)] || "";
  });
}

function renderExistingAssistantMarkdown() {
  document
    .querySelectorAll(".message.assistant .message-content")
    .forEach((content) => {
      if (content.closest(".pending")) {
        return;
      }
      const rawText = content.textContent || "";
      content.innerHTML = renderAssistantMarkdown(rawText);
    });
}

function typesetMath(element) {
  if (!element || !window.MathJax || !window.MathJax.typesetPromise) {
    return;
  }

  window.MathJax.typesetPromise([element]).catch(() => {
    // Math rendering should never block the chat UI.
  });
}

function typesetExistingAssistantMath() {
  document.querySelectorAll(".message.assistant").forEach((message) => {
    typesetMath(message);
  });
}

function showToast(message, type = "error", duration = 3500) {
  const container = document.getElementById("toast-container");
  if (!container || !message) {
    return;
  }

  container.replaceChildren();

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  window.setTimeout(() => {
    toast.classList.add("hide");
    toast.addEventListener("animationend", () => toast.remove(), { once: true });
  }, duration);
}

function resizeTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  textarea.style.overflowY =
    textarea.scrollHeight > MAX_TEXTAREA_HEIGHT ? "auto" : "hidden";
}

function resetTextarea(textarea) {
  textarea.value = "";
  textarea.style.height = "auto";
  resizeTextarea(textarea);
}

function clearEmptyTextarea(textarea) {
  textarea.value = "";
  resetTextarea(textarea);
}

function scrollMessagesToBottom() {
  if (!messagesContainer) {
    return;
  }
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function scheduleScrollToBottom() {
  requestAnimationFrame(scrollMessagesToBottom);
}

function createMessageElement(message) {
  const article = document.createElement("article");
  article.className = `message ${message.role}`;

  const role = document.createElement("div");
  role.className = "message-role";
  role.textContent = message.role;

  const content = document.createElement("div");
  content.className = "message-content";
  if (message.role === "assistant") {
    content.innerHTML = renderAssistantMarkdown(message.content);
  } else {
    content.textContent = message.content;
  }

  const time = document.createElement("time");
  time.className = "message-time";
  if (message.timestamp) {
    time.dataset.timestamp = message.timestamp;
    time.textContent = formatLocalTime(message.timestamp);
  }

  article.append(role, content, time);
  return article;
}

function appendMessage(message) {
  if (!messagesContainer) {
    return null;
  }

  document.querySelector("[data-empty-chat]")?.remove();
  const article = createMessageElement(message);
  messagesContainer.append(article);
  if (message.role === "assistant") {
    typesetMath(article);
  }
  return article;
}

function appendPendingAssistantMessage() {
  if (!messagesContainer) {
    return null;
  }

  document.querySelector("[data-empty-chat]")?.remove();
  const article = document.createElement("article");
  article.className = "message assistant pending";
  article.dataset.pending = "true";

  const role = document.createElement("div");
  role.className = "message-role";
  role.textContent = "assistant";

  const content = document.createElement("div");
  content.className = "message-content";
  content.append(createTypingDots());

  const time = document.createElement("time");
  time.className = "message-time";

  article.append(role, content, time);
  messagesContainer.append(article);
  return article;
}

function createTypingDots() {
  const wrapper = document.createElement("span");
  wrapper.className = "typing-dots";
  wrapper.setAttribute("aria-label", "Generating response");
  for (let index = 0; index < 3; index += 1) {
    wrapper.append(document.createElement("span"));
  }
  return wrapper;
}

function resolvePendingAssistantMessage(pendingElement, message) {
  const target = pendingElement || appendMessage(message);
  if (!target) {
    return;
  }

  target.classList.remove("pending");
  delete target.dataset.pending;

  const content = target.querySelector(".message-content");
  if (content) {
    content.innerHTML = renderAssistantMarkdown(message.content);
  }

  const time = target.querySelector(".message-time");
  if (time) {
    time.dataset.timestamp = message.timestamp;
    time.textContent = formatLocalTime(message.timestamp);
  }
  typesetMath(target);
}

function markPendingAssistantError(pendingElement) {
  if (!pendingElement) {
    return;
  }

  pendingElement.classList.remove("pending");
  pendingElement.classList.add("error");
  delete pendingElement.dataset.pending;

  const content = pendingElement.querySelector(".message-content");
  if (content) {
    content.textContent = "Could not generate a response.";
  }
}

async function postJson(url, payload = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({
    ok: false,
    error: "Unexpected server response.",
  }));

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "Request failed.");
  }

  return data;
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/json",
    },
  });

  const data = await response.json().catch(() => ({
    ok: false,
    error: "Unexpected server response.",
  }));

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "Request failed.");
  }

  return data;
}

function updateModelStateLabel(status) {
  if (!modelState || !status) {
    return;
  }

  const state = status.state || (status.ready ? "ready" : "not_loaded");
  const label = state === "not_loaded" ? "not loaded" : state;
  modelState.textContent = label;
  modelState.title = `${status.service || "LLM service"}: ${label}`;
  modelState.classList.remove("ready", "loading", "error", "not-loaded");
  modelState.classList.add(state.replace("_", "-"));
  if (modelName) {
    modelName.textContent = status.model_display_name || status.model_name || "mock";
    modelName.title = status.model_name || "mock";
  }
  if (generationPresetSelect && status.generation_preset) {
    generationPresetSelect.value = status.generation_preset;
  }
  updateActiveModelButtons(status.model_name);
}

function updateActiveModelButtons(activeModelPath) {
  document.querySelectorAll("[data-model-switch]").forEach((button) => {
    button.classList.toggle("active", button.dataset.modelPath === activeModelPath);
  });
}

function setModelLoading(label = "loading") {
  if (!modelState) {
    return;
  }
  modelState.textContent = label;
  modelState.title = "Model operation is running";
  modelState.classList.remove("ready", "error", "not-loaded");
  modelState.classList.add("loading");
}

async function refreshModelStatus() {
  if (!modelState) {
    return;
  }

  try {
    const data = await getJson("/api/model/status");
    updateModelStateLabel(data.status);
    if (data.status?.state === "error") {
      showToast(data.status.error || "Model failed to load.");
    }
  } catch (error) {
    modelState.textContent = "error";
    modelState.title = error.message;
    modelState.classList.remove("ready", "loading", "not-loaded");
    modelState.classList.add("error");
  }
}

textareas.forEach((textarea) => {
  resizeTextarea(textarea);

  textarea.addEventListener("input", () => {
    resizeTextarea(textarea);
  });

  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (textarea.value.trim() === "") {
        clearEmptyTextarea(textarea);
        return;
      }
      textarea.form?.requestSubmit();
    }
  });
});

forms.forEach((form) => {
  form.addEventListener("submit", async (event) => {
    const textarea = form.querySelector("textarea");
    if (!textarea) {
      event.preventDefault();
      return;
    }

    const jsonAction = form.dataset.jsonAction;
    if (!jsonAction) {
      return;
    }

    event.preventDefault();
    if (isGenerating) {
      return;
    }

    const message = textarea.value.trim();
    if (message === "") {
      clearEmptyTextarea(textarea);
      return;
    }

    const submitButton = form.querySelector("button");
    isGenerating = true;
    submitButton?.setAttribute("disabled", "disabled");

    const optimisticUserMessage = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    appendMessage(optimisticUserMessage);
    const pendingAssistantMessage = appendPendingAssistantMessage();
    resetTextarea(textarea);
    scheduleScrollToBottom();

    try {
      const data = await postJson(jsonAction, { message });
      resolvePendingAssistantMessage(pendingAssistantMessage, data.assistant_message);
      if (messageCount && typeof data.message_count === "number") {
        messageCount.textContent = data.message_count;
      }
      scheduleScrollToBottom();
    } catch (error) {
      markPendingAssistantError(pendingAssistantMessage);
      showToast(error.message);
      scheduleScrollToBottom();
    } finally {
      isGenerating = false;
      submitButton?.removeAttribute("disabled");
      textarea.focus();
    }
  });
});

if (searchInput) {
  searchInput.addEventListener("input", () => {
    updateSidebarSearchState();
    scheduleMessageSearch();
  });
}

generationPresetSelect?.addEventListener("change", async () => {
  const selectedPreset = generationPresetSelect.value;
  generationPresetSelect.setAttribute("disabled", "disabled");

  try {
    await postJson("/api/generation-preset", { preset: selectedPreset });
    showToast(`Generation preset set to ${selectedPreset}.`, "success", 2200);
  } catch (error) {
    showToast(error.message);
  } finally {
    generationPresetSelect.removeAttribute("disabled");
  }
});

document.querySelectorAll("[data-model-switch]").forEach((button) => {
  button.addEventListener("click", async () => {
    const modelPath = button.dataset.modelPath;
    const backend = button.dataset.modelBackend || "transformers";
    const generationPreset = button.dataset.modelPreset || generationPresetSelect?.value || "";
    if (!modelPath && backend !== "mock") {
      return;
    }

    button.setAttribute("disabled", "disabled");
    setModelLoading("loading");
    try {
      const data = await postJson("/api/model/switch", {
        backend,
        model_name: modelPath,
        generation_preset: generationPreset,
      });
      updateModelStateLabel(data.status);
      if (data.status?.state === "error") {
        showToast(data.status.error || "Model failed to load.");
      } else {
        showToast(`Model switched to ${data.status.model_display_name}.`, "success", 2200);
      }
    } catch (error) {
      await refreshModelStatus();
      showToast(error.message);
    } finally {
      button.removeAttribute("disabled");
    }
  });
});

document.querySelector("[data-model-unload]")?.addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.setAttribute("disabled", "disabled");
  setModelLoading("unloading");
  try {
    const data = await postJson("/api/model/unload");
    updateModelStateLabel(data.status);
    showToast("Model unloaded. Mock backend is active.", "success", 2200);
  } catch (error) {
    await refreshModelStatus();
    showToast(error.message);
  } finally {
    button.removeAttribute("disabled");
  }
});

function updateSidebarSearchState() {
  const rows = Array.from(document.querySelectorAll(".sidebar-chat-row"));
  const query = searchInput?.value.trim().toLowerCase() || "";
  let visibleCount = 0;

  rows.forEach((row) => {
    const title = row.dataset.title || "";
    const isVisible = title.includes(query);
    row.classList.toggle("hidden", !isVisible);
    if (isVisible) {
      visibleCount += 1;
    }
  });

  if (!chatEmptyState) {
    return;
  }

  if (rows.length === 0) {
    chatEmptyState.textContent = "No chats yet";
    chatEmptyState.classList.remove("hidden");
  } else if (visibleCount === 0) {
    chatEmptyState.textContent = "No matching chats";
    chatEmptyState.classList.remove("hidden");
  } else {
    chatEmptyState.classList.add("hidden");
  }
}

function renderMessageSearchResults(results) {
  if (!messageSearchResults || !messageSearchList) {
    return;
  }

  messageSearchList.replaceChildren();
  if (!results.length) {
    messageSearchResults.classList.add("hidden");
    return;
  }

  results.forEach((result) => {
    const link = document.createElement("a");
    link.className = "message-search-result";
    link.href = result.url;

    const title = document.createElement("strong");
    title.textContent = result.chat_title;

    const meta = document.createElement("span");
    meta.className = "message-search-meta";
    meta.textContent = result.role;

    const preview = document.createElement("span");
    preview.className = "message-search-preview";
    preview.textContent = result.preview;

    link.append(title, meta, preview);
    messageSearchList.append(link);
  });
  messageSearchResults.classList.remove("hidden");
}

function scheduleMessageSearch() {
  if (!searchInput || !messageSearchResults || !messageSearchList) {
    return;
  }

  window.clearTimeout(searchTimer);
  const query = searchInput.value.trim();
  if (query.length < 2) {
    renderMessageSearchResults([]);
    return;
  }

  searchTimer = window.setTimeout(async () => {
    try {
      const params = new URLSearchParams({ query, limit: "8" });
      const data = await getJson(`/api/messages/search?${params.toString()}`);
      renderMessageSearchResults(data.results || []);
    } catch (error) {
      renderMessageSearchResults([]);
      showToast(error.message);
    }
  }, 220);
}

function updateChatTitleInDom(chatId, title) {
  document.querySelectorAll(`.sidebar-chat-row[data-chat-id="${chatId}"]`).forEach((row) => {
    const link = row.querySelector(".sidebar-chat-link");
    const titleSpan = link?.querySelector("span");
    const renameButton = row.querySelector(".rename-chat");

    if (titleSpan) {
      titleSpan.textContent = title;
    }
    if (link) {
      link.title = title;
    }
    if (renameButton) {
      renameButton.dataset.currentTitle = title;
    }
    row.dataset.title = title.toLowerCase();
  });
  updateSidebarSearchState();

  if (chatHeaderTitle?.dataset.chatId === chatId) {
    chatHeaderTitle.textContent = title;
    chatHeaderTitle.title = title;
    document.title = `${title} - LLM Dialog System`;
  }

  const headerRenameButton = document.querySelector("[data-header-rename]");
  if (headerRenameButton?.dataset.renameChatId === chatId) {
    headerRenameButton.dataset.currentTitle = title;
  }
}

async function commitRename(chatId, oldTitle, nextTitle, renameUrl) {
  const normalizedTitle = nextTitle.trim();

  if (normalizedTitle === oldTitle.trim()) {
    return oldTitle;
  }
  if (normalizedTitle === "") {
    throw new Error("Chat title cannot be empty.");
  }
  if (normalizedTitle.length > MAX_CHAT_TITLE_LENGTH) {
    throw new Error("Chat title must be 60 characters or fewer.");
  }

  const data = await postJson(renameUrl || `/chat/${chatId}/rename`, {
    title: normalizedTitle,
  });
  updateChatTitleInDom(chatId, data.chat.title);
  return data.chat.title;
}

function startInlineRename({ chatId, titleElement, currentTitle, renameUrl, mode, editingContainer }) {
  if (!chatId || !titleElement || titleElement.dataset.editing === "true") {
    return;
  }

  const oldTitle = currentTitle || titleElement.textContent.trim();
  const input = document.createElement("input");
  input.type = "text";
  input.className = `rename-input inline-title-input ${
    mode === "header" ? "chat-rename-input" : "sidebar-title-input"
  }`;
  input.value = oldTitle;
  input.maxLength = MAX_CHAT_TITLE_LENGTH;

  let cancelled = false;
  let finished = false;
  titleElement.dataset.editing = "true";
  editingContainer?.classList.add("is-editing");

  const restoreTitle = (title) => {
    titleElement.textContent = title;
    titleElement.title = title;
    delete titleElement.dataset.editing;
    editingContainer?.classList.remove("is-editing");
  };

  const finish = async () => {
    if (finished || cancelled) {
      return;
    }
    finished = true;

    try {
      const finalTitle = await commitRename(chatId, oldTitle, input.value, renameUrl);
      restoreTitle(finalTitle);
    } catch (error) {
      restoreTitle(oldTitle);
      showToast(error.message);
    }
  };

  const cancel = () => {
    if (finished) {
      return;
    }
    cancelled = true;
    finished = true;
    restoreTitle(oldTitle);
  };

  input.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      input.blur();
    } else if (event.key === "Escape") {
      event.preventDefault();
      cancel();
    }
  });

  input.addEventListener("blur", () => {
    finish();
  });

  titleElement.replaceChildren(input);
  window.requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
}

document.querySelectorAll(".rename-chat").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const row = button.closest(".sidebar-chat-row");
    const titleElement = row?.querySelector(".sidebar-chat-link span");
    if (!row || !titleElement) {
      return;
    }

    startInlineRename({
      chatId: row.dataset.chatId,
      titleElement,
      currentTitle: button.dataset.currentTitle || titleElement.textContent.trim(),
      renameUrl: button.dataset.renameUrl,
      mode: "sidebar",
      editingContainer: row,
    });
  });
});

document.querySelector("[data-header-rename]")?.addEventListener("click", (event) => {
  const button = event.currentTarget;
  const titleRow = button.closest(".chat-title-row");
  startInlineRename({
    chatId: button.dataset.renameChatId,
    titleElement: chatHeaderTitle,
    currentTitle: button.dataset.currentTitle || chatHeaderTitle?.textContent.trim() || "",
    renameUrl: button.dataset.renameUrl,
    mode: "header",
    editingContainer: titleRow,
  });
});

document.querySelectorAll(".delete-chat").forEach((button) => {
  button.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const row = button.closest(".sidebar-chat-row");
    if (!row) {
      return;
    }

    const confirmed = window.confirm(
      "Delete this chat? This action cannot be undone."
    );
    if (!confirmed) {
      return;
    }

    try {
      await postJson(button.dataset.deleteUrl);
      const isActive = row.dataset.active === "true";
      row.remove();
      updateSidebarSearchState();
      if (isActive) {
        window.location.assign("/");
      }
    } catch (error) {
      showToast(error.message);
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  formatExistingMessageTimes();
  renderExistingAssistantMarkdown();
  typesetExistingAssistantMath();
  updateSidebarSearchState();
  refreshModelStatus();

  const initialToasts = window.__INITIAL_TOASTS__ || [];
  if (Array.isArray(initialToasts) && initialToasts.length > 0) {
    showToast(initialToasts[initialToasts.length - 1], "error");
  }
});

document.querySelector(".message-form textarea")?.focus();
scheduleScrollToBottom();
