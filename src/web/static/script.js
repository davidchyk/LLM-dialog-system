const MAX_TEXTAREA_HEIGHT = 210;
const MAX_CHAT_TITLE_LENGTH = 60;

const textareas = document.querySelectorAll("textarea");
const forms = document.querySelectorAll(".message-form, .landing-form");
const searchInput = document.querySelector(".chat-search");
const chatRows = document.querySelectorAll(".sidebar-chat-row");
const messagesContainer = document.getElementById("messages");
const messageCount = document.querySelector("[data-message-count]");
const chatHeaderTitle = document.querySelector("[data-chat-title]");

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

function appendMessage(message) {
  if (!messagesContainer) {
    return;
  }

  document.querySelector("[data-empty-chat]")?.remove();

  const article = document.createElement("article");
  article.className = `message ${message.role}`;

  const role = document.createElement("div");
  role.className = "message-role";
  role.textContent = message.role;

  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = message.content;

  const time = document.createElement("div");
  time.className = "message-time";
  time.textContent = message.timestamp;

  article.append(role, content, time);
  messagesContainer.append(article);
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

    const message = textarea.value.trim();
    if (message === "") {
      event.preventDefault();
      clearEmptyTextarea(textarea);
      return;
    }

    event.preventDefault();
    const submitButton = form.querySelector("button");
    submitButton?.setAttribute("disabled", "disabled");

    try {
      const data = await postJson(jsonAction, { message });
      appendMessage(data.user_message);
      scheduleScrollToBottom();
      appendMessage(data.assistant_message);
      if (messageCount && typeof data.message_count === "number") {
        messageCount.textContent = data.message_count;
      }
      resetTextarea(textarea);
      scheduleScrollToBottom();
    } catch (error) {
      showToast(error.message);
    } finally {
      submitButton?.removeAttribute("disabled");
      textarea.focus();
    }
  });
});

if (searchInput) {
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();

    chatRows.forEach((row) => {
      const title = row.dataset.title || "";
      row.classList.toggle("hidden", !title.includes(query));
    });
  });
}

document.querySelectorAll(".rename-chat").forEach((button) => {
  button.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const row = button.closest(".sidebar-chat-row");
    const link = row?.querySelector(".sidebar-chat-link");
    if (!row || !link) {
      return;
    }

    const currentTitle = button.dataset.currentTitle || link.textContent.trim();
    const nextTitle = window.prompt("Rename chat", currentTitle);
    if (nextTitle === null) {
      return;
    }

    const normalizedTitle = nextTitle.trim();
    if (normalizedTitle === "") {
      showToast("Chat title cannot be empty.");
      return;
    }
    if (normalizedTitle.length > MAX_CHAT_TITLE_LENGTH) {
      showToast("Chat title must be 60 characters or fewer.");
      return;
    }

    try {
      const data = await postJson(button.dataset.renameUrl, {
        title: normalizedTitle,
      });
      const titleSpan = link.querySelector("span");
      titleSpan.textContent = data.chat.title;
      link.title = data.chat.title;
      row.dataset.title = data.chat.title.toLowerCase();
      button.dataset.currentTitle = data.chat.title;

      if (row.dataset.active === "true" && chatHeaderTitle) {
        chatHeaderTitle.textContent = data.chat.title;
        chatHeaderTitle.title = data.chat.title;
      }
    } catch (error) {
      showToast(error.message);
    }
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
      if (isActive) {
        window.location.assign("/");
      }
    } catch (error) {
      showToast(error.message);
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const initialToasts = window.__INITIAL_TOASTS__ || [];
  if (Array.isArray(initialToasts) && initialToasts.length > 0) {
    showToast(initialToasts[initialToasts.length - 1], "error");
  }
});

document.querySelector(".message-form textarea")?.focus();
scheduleScrollToBottom();
