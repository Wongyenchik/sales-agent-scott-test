const els = {
  status: document.getElementById("status"),
  chatLog: document.getElementById("chatLog")
};

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

function getAttachmentNames(item) {
  const attachments = Array.isArray(item.attachments) ? item.attachments : [];
  if (attachments.length === 0) {
    return ["No attachments"];
  }

  return attachments.map((attachment) => {
    const name = attachment.name || attachment.displayName || "Unnamed attachment";
    const type = attachment.contentType ? ` (${attachment.contentType})` : "";
    return `${name}${type}`;
  });
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
  const attachments = getAttachmentNames(item);

  addBubble("Assistant", "Selected email loaded.");
  addFieldBubble("Email title", subject);
  addFieldBubble("Email sender", senderEmail ? `${senderName} <${senderEmail}>` : senderName);
  addFieldBubble("Email body", bodyText || "(empty body)");
  addFieldBubble("Attachments", attachments.join("\n"));

  setStatus("Email details ready.");
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
