const els = {
  status: document.getElementById("status"),
  chatLog: document.getElementById("chatLog")
};

let currentEmailContext = null;

function setStatus(text) {
  els.status.textContent = text;
}

function addBubble(role, text) {
  const article = document.createElement("article");
  article.className = "bubble assistant";

  const roleNode = document.createElement("div");
  roleNode.className = "role";
  roleNode.textContent = role;

  const content = document.createElement("div");
  content.className = "content";
  content.textContent = text;

  article.appendChild(roleNode);
  article.appendChild(content);
  els.chatLog.appendChild(article);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function addFieldBubble(title, value) {
  const article = document.createElement("article");
  article.className = "bubble assistant";

  const roleNode = document.createElement("div");
  roleNode.className = "role";
  roleNode.textContent = "Assistant";

  const fieldNode = document.createElement("div");
  fieldNode.className = "field";
  fieldNode.textContent = title;

  const valueNode = document.createElement("div");
  valueNode.className = "value";
  valueNode.textContent = value || "(empty)";

  article.appendChild(roleNode);
  article.appendChild(fieldNode);
  article.appendChild(valueNode);
  els.chatLog.appendChild(article);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
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

function renderImageBubble(title, attachment, dataUrl) {
  const article = document.createElement("article");
  article.className = "bubble assistant";

  const roleNode = document.createElement("div");
  roleNode.className = "role";
  roleNode.textContent = "Assistant";

  const fieldNode = document.createElement("div");
  fieldNode.className = "field";
  fieldNode.textContent = title;

  const valueNode = document.createElement("div");
  valueNode.className = "value";

  const metaNode = document.createElement("div");
  metaNode.className = "value";
  metaNode.textContent = `${attachment.name || attachment.displayName || "Image"} (${attachment.contentType || "unknown type"})`;

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

  valueNode.appendChild(metaNode);
  valueNode.appendChild(image);
  valueNode.appendChild(link);

  article.appendChild(roleNode);
  article.appendChild(fieldNode);
  article.appendChild(valueNode);
  els.chatLog.appendChild(article);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderFileBubble(title, attachment, content) {
  const article = document.createElement("article");
  article.className = "bubble assistant";

  const roleNode = document.createElement("div");
  roleNode.className = "role";
  roleNode.textContent = "Assistant";

  const fieldNode = document.createElement("div");
  fieldNode.className = "field";
  fieldNode.textContent = title;

  const valueNode = document.createElement("div");
  valueNode.className = "value";

  const metaNode = document.createElement("div");
  metaNode.className = "value";
  metaNode.textContent = `${attachment.name || attachment.displayName || "Attachment"} (${attachment.contentType || "unknown type"})`;

  const contentNode = document.createElement("div");
  contentNode.className = "value";
  contentNode.textContent = content || "(no preview available)";

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

  valueNode.appendChild(metaNode);
  valueNode.appendChild(contentNode);
  valueNode.appendChild(link);

  article.appendChild(roleNode);
  article.appendChild(fieldNode);
  article.appendChild(valueNode);
  els.chatLog.appendChild(article);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
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

  const bodyText = await getBodyText(item);
  const senderName = item.from?.displayName || "Unknown sender";
  const senderEmail = item.from?.emailAddress || "";
  const subject = item.subject || "(no subject)";
  const attachments = await getAttachmentsAsync(item);

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

  addBubble("Assistant", "Selected email loaded.");
  addFieldBubble("Email title", subject);
  addFieldBubble("Email sender", senderEmail ? `${senderName} <${senderEmail}>` : senderName);
  addFieldBubble("Email body", bodyText || "(empty body)");

  if (attachments.length === 0) {
    addFieldBubble("Attachments", "No attachments");
  } else {
    addFieldBubble(
      "Attachments",
      attachments.map((attachment) => `${attachment.name || attachment.displayName || "Unnamed attachment"} (${attachment.contentType || "unknown type"})`).join("\n")
    );

    for (const attachment of attachments) {
      const attachmentContent = await getAttachmentContentAsync(item, attachment.id || attachment.attachmentId);
      const attachmentRecord = {
        id: attachment.id || attachment.attachmentId || "",
        name: attachment.name || attachment.displayName || "Attachment",
        contentType: attachment.contentType || "",
        format: attachmentContent?.format || "",
        content: attachmentContent?.content || ""
      };

      currentEmailContext.attachments.push(attachmentRecord);
      window.salesAgentEmailContext = currentEmailContext;

      if (!attachmentContent) {
        renderFileBubble(attachmentTypeLabel(attachment), attachment, "Attachment content is unavailable in this Outlook context.");
        continue;
      }

      const attachmentName = attachment.name || attachment.displayName || "Attachment";
      const attachmentContentType = String(attachment.contentType || "").toLowerCase();

      if (attachmentContentFormatIsImage(attachmentContent, attachmentContentType)) {
        const dataUrl = buildDataUrl(attachmentContent, attachmentContentType);
        renderImageBubble(attachmentTypeLabel(attachment), attachment, dataUrl);
      } else {
        attachment.downloadUrl = attachmentContent.format === "base64"
          ? toBase64BlobUrl(attachmentContent.content, attachment.contentType)
          : attachmentContent.content || "";

        renderFileBubble(
          attachmentTypeLabel(attachment),
          attachment,
          normalizeAttachmentPreview(attachmentContent, attachmentName)
        );
      }
    }
  }

  setStatus("Email details ready.");
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

  setStatus("Reading selected email...");
  loadEmailContext().catch((error) => {
    addBubble("Assistant", `Read failed: ${error.message}`);
    setStatus("Read failed.");
  });
});
