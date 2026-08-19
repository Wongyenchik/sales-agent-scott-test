const els = {
  status: document.getElementById("status"),
  chatLog: document.getElementById("chatLog"),
  assistantThread: document.getElementById("assistantThread"),
  promptForm: document.getElementById("promptForm"),
  promptInput: document.getElementById("promptInput"),
  sendButton: document.getElementById("sendButton")
};

const API_BASE_URL = "http://localhost:8000";

let currentEmailContext = null;

function setStatus(text) {
  els.status.textContent = text;
}

function scrollChatToBottom() {
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function clearAssistantThread() {
  els.assistantThread.replaceChildren();
}

function clearUserRows() {
  const userRows = els.chatLog.querySelectorAll(".user-row");
  userRows.forEach((row) => row.remove());
}

function appendLine(text, className = "line") {
  const node = document.createElement("div");
  node.className = className;
  node.textContent = text;
  els.assistantThread.appendChild(node);
  scrollChatToBottom();
}

function appendField(title, value) {
  appendLine(title, "line line-title");
  appendLine(value || "(empty)", "line line-meta");
}

function appendUserBubble(text) {
  const row = document.createElement("article");
  row.className = "message-row user-row";

  const bubble = document.createElement("div");
  bubble.className = "user-bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  els.chatLog.appendChild(row);
  scrollChatToBottom();
}

function setSending(sending) {
  els.sendButton.disabled = sending;
  els.sendButton.textContent = sending ? "Sending..." : "Send";
}

function buildEmailRequest() {
  if (!currentEmailContext) {
    throw new Error("Email details are not ready yet.");
  }

  const senderEmail = currentEmailContext.sender?.email || "";
  const subject = currentEmailContext.subject || "";
  const body = currentEmailContext.bodyText || "";

  if (!senderEmail || !subject || !body) {
    throw new Error("Sender email, subject, and body are required before running the agent.");
  }

  return {
    sender_email: senderEmail,
    subject,
    body
  };
}

function appendWorkflowResult(result) {
  clearAssistantThread();
  appendField("Workflow status", result.status || "unknown");

  if (result.understanding) {
    appendField("Detected intent", result.understanding.intent || "unknown");
    appendField(
      "Purchase orders",
      (result.understanding.purchase_order_numbers || []).join("\n") || "None found"
    );
    appendField(
      "Sales orders",
      (result.understanding.sales_order_numbers || []).join("\n") || "None found"
    );
    appendField("Requested language", result.understanding.requested_language || "unknown");
  }

  if (result.customer_validation) {
    appendField(
      "Customer validation",
      result.customer_validation.is_known_customer ? "Known customer" : "Needs review"
    );
  }

  if (result.draft) {
    appendField("Draft subject", result.draft.subject || "(no subject)");
    appendField("Draft reply", result.draft.body || "(empty draft)");
  }

  if (Array.isArray(result.errors) && result.errors.length > 0) {
    appendField("Errors", result.errors.join("\n"));
  }

  appendField("Correlation ID", result.correlation_id || "not returned");
}

async function runSalesAgent() {
  const payload = buildEmailRequest();
  const response = await fetch(`${API_BASE_URL}/api/v1/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  const result = await response.json();

  if (!response.ok) {
    throw new Error((result.errors || []).join("\n") || "Agent request failed.");
  }

  return result;
}

function toBase64BlobUrl(base64, contentType) {
  if (!base64) {
    return "";
  }

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  const blob = new Blob([bytes], { type: contentType || "application/octet-stream" });
  return URL.createObjectURL(blob);
}

function getAttachmentsAsync(item) {
  return new Promise((resolve, reject) => {
    if (typeof item.getAttachmentsAsync !== "function") {
      resolve([]);
      return;
    }

    item.getAttachmentsAsync((result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || []);
      } else {
        reject(new Error(result.error?.message || "Could not read attachments"));
      }
    });
  });
}

function normalizeAttachment(attachment) {
  if (!attachment) {
    return null;
  }

  return {
    id: attachment.id || attachment.attachmentId || "",
    name: attachment.name || attachment.displayName || "Unnamed attachment",
    contentType: attachment.contentType || "",
    attachmentType: attachment.attachmentType || ""
  };
}

function dedupeAttachments(attachments) {
  const seen = new Set();
  const deduped = [];

  for (const attachment of attachments) {
    const key = `${attachment.id}|${attachment.name}|${attachment.contentType}`;
    if (!seen.has(key)) {
      seen.add(key);
      deduped.push(attachment);
    }
  }

  return deduped;
}

async function collectAttachments(item) {
  const fromItemArray = (Array.isArray(item.attachments) ? item.attachments : [])
    .map(normalizeAttachment)
    .filter(Boolean);

  let fromAsyncApi = [];
  try {
    fromAsyncApi = (await getAttachmentsAsync(item)).map(normalizeAttachment).filter(Boolean);
  } catch {
    fromAsyncApi = [];
  }

  return dedupeAttachments([...fromItemArray, ...fromAsyncApi]);
}

function getAttachmentContentAsync(item, attachmentId) {
  return new Promise((resolve, reject) => {
    if (typeof item.getAttachmentContentAsync !== "function") {
      resolve(null);
      return;
    }

    item.getAttachmentContentAsync(attachmentId, (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || null);
      } else {
        reject(new Error(result.error?.message || "Could not read attachment content"));
      }
    });
  });
}

function appendImageAttachment(title, attachment, dataUrl) {
  appendLine(title, "line line-title");
  appendLine(`${attachment.name || attachment.displayName || "Image"} (${attachment.contentType || "unknown type"})`, "line line-meta");

  const wrap = document.createElement("div");
  wrap.className = "image-wrap";

  const image = document.createElement("img");
  image.src = dataUrl;
  image.alt = attachment.name || attachment.displayName || "Attachment image";
  image.className = "attachment-image";

  const link = document.createElement("a");
  link.href = dataUrl;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.className = "attachment-link";
  link.textContent = "Open image";

  wrap.appendChild(image);
  wrap.appendChild(link);
  els.assistantThread.appendChild(wrap);
  scrollChatToBottom();
}

function appendFileAttachment(title, attachment, content) {
  appendLine(title, "line line-title");
  appendLine(`${attachment.name || attachment.displayName || "Attachment"} (${attachment.contentType || "unknown type"})`, "line line-meta");
  appendLine(content || "(no preview available)", "line line-meta");

  const link = document.createElement("a");
  link.className = "attachment-link";
  link.target = "_blank";
  link.rel = "noreferrer";

  if (attachment.downloadUrl) {
    link.href = attachment.downloadUrl;
    link.textContent = "Open file";
  } else {
    link.href = "#";
    link.textContent = "File preview unavailable";
  }

  els.assistantThread.appendChild(link);
  scrollChatToBottom();
}

function getBodyText(item) {
  return new Promise((resolve, reject) => {
    if (!item.body || typeof item.body.getAsync !== "function") {
      resolve("");
      return;
    }

    item.body.getAsync(Office.CoercionType.Text, (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || "");
      } else {
        reject(new Error(result.error?.message || "Could not read email body"));
      }
    });
  });
}

function attachmentTypeLabel(attachment) {
  const contentType = String(attachment.contentType || "").toLowerCase();
  if (contentType.startsWith("image/")) {
    return "Image attachment";
  }
  return "File attachment";
}

async function loadEmailContext() {
  const item = Office.context?.mailbox?.item;
  if (!item) {
    throw new Error("No Outlook email item is currently available.");
  }

  clearUserRows();
  clearAssistantThread();

  const bodyText = await getBodyText(item);
  const senderName = item.from?.displayName || "Unknown sender";
  const senderEmail = item.from?.emailAddress || "";
  const subject = item.subject || "(no subject)";
  const attachments = await collectAttachments(item);

  currentEmailContext = {
    messageId: item.itemId || `outlook-${Date.now()}`,
    subject,
    sender: {
      name: senderName,
      email: senderEmail
    },
    bodyText,
    attachments: []
  };

  window.salesAgentEmailContext = currentEmailContext;

  appendField("Email title", subject);
  appendField("Email sender", senderEmail ? `${senderName} <${senderEmail}>` : senderName);
  appendField("Email body", bodyText || "(empty body)");

  if (attachments.length === 0) {
    appendField("Attachments", "No attachments");
  } else {
    appendField("Attachment count", String(attachments.length));
    appendField(
      "Attachments",
      attachments.map((attachment) => `${attachment.name || "Unnamed attachment"} (${attachment.contentType || "unknown type"})`).join("\n")
    );

    for (const attachment of attachments) {
      if (!attachment.id) {
        appendFileAttachment(
          attachmentTypeLabel(attachment),
          attachment,
          "Attachment ID is not available in this Outlook host, so raw content cannot be fetched here."
        );
        continue;
      }

      let attachmentContent;
      try {
        attachmentContent = await getAttachmentContentAsync(item, attachment.id);
      } catch {
        attachmentContent = null;
      }

      const attachmentRecord = {
        id: attachment.id || "",
        name: attachment.name || "Attachment",
        contentType: attachment.contentType || "",
        format: attachmentContent?.format || "",
        content: attachmentContent?.content || ""
      };

      currentEmailContext.attachments.push(attachmentRecord);
      window.salesAgentEmailContext = currentEmailContext;

      if (!attachmentContent) {
        appendFileAttachment(
          attachmentTypeLabel(attachment),
          attachment,
          "Attachment content is unavailable in this Outlook context."
        );
        continue;
      }

      const attachmentName = attachment.name || "Attachment";
      const attachmentContentType = String(attachment.contentType || "").toLowerCase();

      if (attachmentContentFormatIsImage(attachmentContent, attachmentContentType)) {
        const dataUrl = buildDataUrl(attachmentContent, attachmentContentType);
        appendImageAttachment(attachmentTypeLabel(attachment), attachment, dataUrl);
      } else {
        attachment.downloadUrl = attachmentContent.format === "base64"
          ? toBase64BlobUrl(attachmentContent.content, attachment.contentType)
          : attachmentContent.content || "";

        appendFileAttachment(
          attachmentTypeLabel(attachment),
          attachment,
          normalizeAttachmentPreview(attachmentContent, attachmentName)
        );
      }
    }
  }

  setStatus("Email details ready.");
}

async function handlePromptSubmit(event) {
  event.preventDefault();
  const prompt = (els.promptInput.value || "").trim();
  if (!prompt) {
    return;
  }

  appendUserBubble(prompt);

  if (currentEmailContext) {
    currentEmailContext.userPrompt = prompt;
    window.salesAgentEmailContext = currentEmailContext;
  }

  els.promptInput.value = "";
  setSending(true);
  setStatus("Running sales agent...");

  try {
    const result = await runSalesAgent();
    appendWorkflowResult(result);
    setStatus("Draft ready for review.");
  } catch (error) {
    appendField("Agent request failed", error.message);
    setStatus("Agent request failed.");
  } finally {
    setSending(false);
  }
}

function attachmentContentFormatIsImage(attachmentContent, attachmentContentType) {
  if (attachmentContentType.startsWith("image/")) {
    return true;
  }

  const format = String(attachmentContent.format || "").toLowerCase();
  return format === "base64" && attachmentContentType.startsWith("image/");
}

function buildDataUrl(attachmentContent, attachmentContentType) {
  const mimeType = attachmentContentType || "image/png";
  const format = String(attachmentContent.format || "").toLowerCase();

  if (format === "base64" && attachmentContent.content) {
    return `data:${mimeType};base64,${attachmentContent.content}`;
  }

  if (attachmentContent.content) {
    return attachmentContent.content;
  }

  return "";
}

function normalizeAttachmentPreview(attachmentContent, attachmentName) {
  const format = String(attachmentContent.format || "").toLowerCase();
  const content = attachmentContent.content || "";

  if (format === "base64") {
    return `Base64 content loaded for ${attachmentName}. Length: ${content.length}`;
  }

  if (format === "url") {
    return `Attachment URL: ${content}`;
  }

  return `Attachment content format: ${attachmentContent.format || "unknown"}`;
}

Office.onReady((info) => {
  if (info.host !== Office.HostType.Outlook) {
    setStatus("This page must run inside Outlook.");
    return;
  }

  if (els.promptForm) {
    els.promptForm.addEventListener("submit", handlePromptSubmit);
  }

  setStatus("Reading selected email...");
  loadEmailContext().catch((error) => {
    clearAssistantThread();
    appendLine(`Read failed: ${error.message}`);
    setStatus("Read failed.");
  });
});
