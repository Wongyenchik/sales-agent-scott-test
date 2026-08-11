const els = {
  chatLog: document.getElementById("chatLog"),
  backendUrl: document.getElementById("backendUrl"),
  senderName: document.getElementById("senderName"),
  senderEmail: document.getElementById("senderEmail"),
  subject: document.getElementById("subject"),
  message: document.getElementById("message"),
  sendBtn: document.getElementById("sendBtn"),
  clearBtn: document.getElementById("clearBtn"),
  status: document.getElementById("backendStatus"),
  bubbleTemplate: document.getElementById("bubbleTemplate")
};

function getBackendBaseUrl() {
  return (els.backendUrl.value || "http://localhost:8080").trim().replace(/\/$/, "");
}

function appendBubble({ role, text, meta }) {
  const node = els.bubbleTemplate.content.firstElementChild.cloneNode(true);
  node.classList.add(role === "You" ? "user" : "agent");
  node.querySelector(".bubble-role").textContent = role;
  node.querySelector(".bubble-body").textContent = text;

  const details = node.querySelector(".bubble-meta-wrap");
  const metaNode = node.querySelector(".bubble-meta");
  if (meta) {
    metaNode.textContent = JSON.stringify(meta, null, 2);
  } else {
    details.remove();
  }

  els.chatLog.appendChild(node);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function buildPayload() {
  const message = els.message.value.trim();
  const subject = els.subject.value.trim();

  return {
    messageId: `web-${Date.now()}`,
    subject: subject || "Order inquiry",
    sender: {
      name: els.senderName.value.trim() || "Customer",
      email: els.senderEmail.value.trim() || "customer@example.com"
    },
    recipients: [],
    bodyText: message,
    conversationId: "web-chat",
    userAction: "generate_reply"
  };
}

function setSending(sending) {
  els.sendBtn.disabled = sending;
  els.sendBtn.textContent = sending ? "Sending..." : "Send";
}

async function checkHealth() {
  const baseUrl = getBackendBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/health`);
    const json = await res.json();

    els.status.classList.remove("error");
    els.status.classList.add("ok");
    els.status.textContent = `Backend online (${json.sapApiMode} mode)`;
  } catch {
    els.status.classList.remove("ok");
    els.status.classList.add("error");
    els.status.textContent = "Backend offline";
  }
}

async function sendMessage() {
  const message = els.message.value.trim();
  if (!message) {
    appendBubble({
      role: "System",
      text: "Please type a message before sending."
    });
    return;
  }

  const payload = buildPayload();
  appendBubble({
    role: "You",
    text: `Subject: ${payload.subject}\n\n${payload.bodyText}`
  });

  setSending(true);
  try {
    const baseUrl = getBackendBaseUrl();
    const response = await fetch(`${baseUrl}/api/agent/generate-reply`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (!response.ok) {
      appendBubble({
        role: "Agent",
        text: result.error || result.message || "Backend request failed.",
        meta: result
      });
      return;
    }

    const answer = [
      `Status: ${result.status}`,
      "",
      result.draftReply || "No draft returned"
    ].join("\n");

    appendBubble({
      role: "Agent",
      text: answer,
      meta: {
        requestId: result.requestId,
        detectedIntent: result.detectedIntent,
        extractedParameters: result.extractedParameters,
        missingParameters: result.missingParameters,
        sapRetrieval: result.sapRetrieval
      }
    });
  } catch (error) {
    appendBubble({
      role: "Agent",
      text: "Could not reach backend.",
      meta: { error: error.message }
    });
  } finally {
    setSending(false);
    els.message.value = "";
    els.message.focus();
  }
}

els.sendBtn.addEventListener("click", sendMessage);
els.backendUrl.addEventListener("change", checkHealth);
els.message.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    sendMessage();
  }
});
els.clearBtn.addEventListener("click", () => {
  els.chatLog.innerHTML = "";
});

checkHealth();
appendBubble({
  role: "System",
  text: "Web chat ready. Enter an email message and press Send."
});
