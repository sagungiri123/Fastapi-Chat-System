let ws = null;
let currentRoom = null;
let oldestMessageId = null;
let oldestMessageTimestamp = null;
let isLoadingMessages = false;
let hasMoreMessages = true;
let token = null;
let currentUser = null;
const seenMessageIds = new Set();
let isSearchMode = false;
let originalMessages = [];

// ---------- SEARCH FUNCTIONS ----------
async function searchMessages() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    alert("Please enter a search term.");
    return;
  }
  const room = document.getElementById("room").value;
  if (!room) {
    alert("Please connect to a room first.");
    return;
  }
  try {
    const response = await fetch(
      `/api/v1/messages/search?q=${encodeURIComponent(query)}&room_id=${encodeURIComponent(room)}&limit=50`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (!response.ok) {
      alert("Search failed.");
      return;
    }
    const messages = await response.json();
    const messagesDiv = document.getElementById("messages");
    if (!isSearchMode) {
      originalMessages = messagesDiv.innerHTML;
    }
    isSearchMode = true;
    messagesDiv.innerHTML = "";
    if (messages.length === 0) {
      messagesDiv.innerHTML =
        '<div class="system">No messages found matching your query.</div>';
    } else {
      messages.forEach((msg) => {
        const p = document.createElement("div");
        p.className = "msg";
        const time = new Date(msg.created_at).toLocaleTimeString();
        const highlightedContent = msg.content.replace(
          new RegExp(query, "gi"),
          (match) => `<mark>${match}</mark>`,
        );
        p.innerHTML = `[${time}] <strong>${msg.username || "Unknown"}</strong>: ${highlightedContent}`;
        messagesDiv.appendChild(p);
      });
    }
    document.getElementById("searchInfo").textContent =
      `Showing ${messages.length} results for "${query}"`;
  } catch (error) {
    console.error("Search error:", error);
    alert("Search failed. Check console for details.");
  }
}

function clearSearch() {
  if (isSearchMode && originalMessages) {
    document.getElementById("messages").innerHTML = originalMessages;
    isSearchMode = false;
    originalMessages = null;
    document.getElementById("searchInfo").textContent = "";
    document.getElementById("searchInput").value = "";
  }
}

// ---------- LOGGING ----------
function logMessage(text, isSystem = true) {
  const div = document.getElementById("messages");
  const p = document.createElement("div");
  p.className = isSystem ? "system" : "msg";
  p.textContent = text;
  div.appendChild(p);
  div.scrollTop = div.scrollHeight;
}

// ---------- AUTH ----------
async function register() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const res = await fetch("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      email: `${username}@test.com`,
      password,
    }),
  });
  if (res.ok) logMessage(`✅ Registered as ${username}`, true);
  else logMessage(`❌ Registration failed: ${await res.text()}`, true);
}

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const formData = new URLSearchParams({ username, password });
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });
  if (res.ok) {
    const data = await res.json();
    token = data.access_token;
    currentUser = username;
    console.log("login token:", token);
    logMessage(`🔑 Logged in as ${username}`, true);
    document.getElementById("msgInput").disabled = false;
    document.getElementById("sendBtn").disabled = false;
  } else {
    logMessage(`❌ Login failed: ${await res.text()}`, true);
  }
}

// ---------- DM SEARCH ----------
async function searchUser() {
  const query = document.getElementById("dmUsername").value.trim();
  if (!query) return;
  const res = await fetch(
    `/api/v1/users/search?username=${encodeURIComponent(query)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok) {
    alert("Search failed");
    return;
  }
  const users = await res.json();
  const resultsDiv = document.getElementById("searchResults");
  resultsDiv.innerHTML = "";
  if (users.length === 0) {
    resultsDiv.innerHTML = "<p>No users found.</p>";
    return;
  }
  users.forEach((user) => {
    const btn = document.createElement("button");
    btn.textContent = `Chat with ${user.username}`;
    btn.onclick = () => startDM(user.id);
    resultsDiv.appendChild(btn);
    resultsDiv.appendChild(document.createElement("br"));
  });
}

async function startDM(targetUserId) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
    ws = null;
  }
  const res = await fetch(`/api/v1/users/${targetUserId}/dm_room`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    alert("Failed to get DM room");
    return;
  }
  const data = await res.json();
  document.getElementById("room").value = data.room_id;
  connectWS();
}

// ---------- EDIT & DELETE ----------
async function editMessage(messageId) {
  const newContent = prompt("Edit your message:");
  if (newContent === null) return;
  if (newContent.trim() === "") {
    alert("Message cannot be empty.");
    return;
  }

  try {
    const response = await fetch(`/api/v1/messages/${messageId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content: newContent.trim() }),
    });

    if (!response.ok) {
      const err = await response.json();
      alert(`Edit failed: ${err.detail || response.status}`);
    } else {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${messageId}"]`,
      );
      if (msgElement) {
        const contentSpan = msgElement.querySelector(".msg-content");
        if (contentSpan) {
          contentSpan.textContent = newContent.trim();
        }

        let editedSpan = msgElement.querySelector(".msg-edited");
        if (!editedSpan) {
          editedSpan = document.createElement("span");
          editedSpan.className = "msg-edited";
          editedSpan.textContent = " (edited)";
          msgElement.appendChild(editedSpan);
        }
      }
    }
  } catch (error) {
    console.error("Edit error:", error);
    alert("Failed to edit message.");
  }
}
async function deleteMessage(messageId) {
  if (!confirm("Are you sure you want to delete this message?")) return;
  try {
    const response = await fetch(`/api/v1/messages/${messageId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const err = await response.json();
      alert(`Delete failed: ${err.detail || response.status}`);
    } else {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${messageId}"]`,
      );
      if (msgElement) {
        msgElement.remove();
      }
    }
  } catch (error) {
    console.error("Delete error:", error);
    alert("Failed to delete message.");
  }
}

// ---------- CREATE MESSAGE ELEMENT ----------
function createMessageElement(msg, currentUsername) {
  const div = document.createElement("div");
  div.className = "msg";
  div.dataset.messageId = msg.id;

  const time = new Date(msg.created_at).toLocaleTimeString();
  const isOwn = msg.username === currentUsername;

  if (isOwn) {
    div.classList.add("me");
  }

  let contentHtml = `<span class="msg-content">${msg.content}</span>`;
  if (msg.updated_at) {
    contentHtml += ` <span class="msg-edited">(edited)</span>`;
  }

  let actionsHtml = "";
  if (isOwn) {
    actionsHtml = `
            <span class="msg-actions">
              <button class="edit-btn" onclick="editMessage(${msg.id})">✏️ Edit</button>
              <button class="delete-btn" onclick="deleteMessage(${msg.id})">🗑️ Delete</button>
            </span>
          `;
  }

  div.innerHTML = `
          <span class="msg-user">${msg.username || "Unknown"}</span>
          <span class="msg-time">[${time}]</span>
          ${contentHtml}
          ${actionsHtml}
        `;
  return div;
}

function updateRoomHeader(roomName = "general") {
  const cleanedRoom = roomName || "general";
  document.getElementById("currentRoomDisplay").textContent = cleanedRoom;
  document.getElementById("roomAvatar").textContent = cleanedRoom.charAt(0).toUpperCase();
}

function updateOnlineCount(users) {
  const names = Array.from(new Set(users || []));
  const countEl = document.getElementById("onlineCount");
  countEl.textContent = `${names.length} online`;

  const userListEl = document.getElementById("userList");
  if (!names.length) {
    userListEl.innerHTML = '<span class="empty-state">Nobody here yet.</span>';
    return;
  }

  userListEl.innerHTML = names
    .map((user) => `<span class="user-badge">${user}</span>`)
    .join(" ");
}

// ---------- WEBSOCKET ----------
function connectWS() {
  if (!token) {
    alert("Please login first");
    return;
  }
  // Close existing connection if any
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
    ws = null;
  }

  const room = document.getElementById("room").value;
  updateRoomHeader(room);
  const wsUrl = `ws://${window.location.host}/ws/${room}?token=${token}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    logMessage(`🔗 Connected to room: ${room}`, true);
    currentRoom = room;
    oldestMessageId = null;
    oldestMessageTimestamp = null;
    hasMoreMessages = true;
    isLoadingMessages = false;
    seenMessageIds.clear();
    LoadMessages(room);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "typing") {
      document.getElementById("typingStatus").textContent =
        `${data.username} is typing...`;
      clearTimeout(window.typingTimeout);
      window.typingTimeout = setTimeout(() => {
        document.getElementById("typingStatus").textContent = "";
      }, 2000);
    } else if (data.type === "edit") {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${data.message_id}"]`,
      );
      if (msgElement) {
        const contentSpan = msgElement.querySelector(".msg-content");
        if (contentSpan) {
          contentSpan.textContent = data.content;
        }
        // Add (edited) badge if not present
        let editedSpan = msgElement.querySelector(".msg-edited");
        if (!editedSpan) {
          editedSpan = document.createElement("span");
          editedSpan.className = "msg-edited";
          editedSpan.textContent = " (edited)";
          msgElement.appendChild(editedSpan);
        }
      }
    } else if (data.type === "delete") {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${data.message_id}"]`,
      );
      if (msgElement) {
        msgElement.remove();
      }
    } else if (data.type === "presence") {
      logMessage(`👤 ${data.username} ${data.status}`, true);
    } else if (data.type === "online_list") {
      updateOnlineCount(data.users || []);
    } else if (data.type === "message") {
      const messagesDiv = document.getElementById("messages");
      if (data.id && seenMessageIds.has(data.id)) return;
      if (data.id) seenMessageIds.add(data.id);

      const placeholder = messagesDiv.querySelector(".system");
      if (placeholder && placeholder.textContent.includes("No messages yet")) {
        messagesDiv.innerHTML = "";
      }

      const p = createMessageElement(data, currentUser);
      messagesDiv.appendChild(p);

      const isAtBottom =
        messagesDiv.scrollHeight -
          messagesDiv.scrollTop -
          messagesDiv.clientHeight <
        10;
      if (isAtBottom) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      }
    } else if (data.type === "edit") {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${data.message_id}"]`,
      );
      if (msgElement) {
        const contentSpan = msgElement.querySelector(".msg-content");
        if (contentSpan) {
          contentSpan.textContent = data.content;
        }
        let editedSpan = msgElement.querySelector(".msg-edited");
        if (!editedSpan) {
          editedSpan = document.createElement("span");
          editedSpan.className = "msg-edited";
          editedSpan.textContent = " (edited)";
          msgElement.appendChild(editedSpan);
        }
      }
    } else if (data.type === "delete") {
      const msgElement = document.querySelector(
        `.msg[data-message-id="${data.message_id}"]`,
      );
      if (msgElement) {
        msgElement.remove();
      }
    }
  };

  ws.onclose = () => {
    logMessage("🔌 Disconnected", true);
    document.getElementById("typingStatus").textContent = "";
    console.log("WebSocket closed");
  };

  ws.onerror = (err) => {
    logMessage(`⚠️ WebSocket Error`, true);
    console.error("WebSocket error", err);
  };
}

function disconnectWS() {
  if (ws) {
    ws.close();
    ws = null;
    currentRoom = null;
  }
  document.getElementById("typingStatus").textContent = "";
  document.getElementById("onlineCount").textContent = "0 online";
  document.getElementById("userList").innerHTML = '<span class="empty-state">Nobody here yet.</span>';
  updateRoomHeader(document.getElementById("room").value || "general");
}

function sendMessage() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    alert("Not connected");
    return;
  }
  const input = document.getElementById("msgInput");
  const content = input.value.trim();
  if (!content) return;
  ws.send(JSON.stringify({ type: "message", content }));
  input.value = "";
}

// Typing detection
document.getElementById("msgInput").addEventListener("input", function () {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "typing", is_typing: true }));
    clearTimeout(window.typingSendTimeout);
    window.typingSendTimeout = setTimeout(() => {
      ws.send(JSON.stringify({ type: "typing", is_typing: false }));
    }, 1500);
  }
});

// ---------- LOAD MESSAGES (Pagination) ----------
async function LoadMessages(roomId, beforeId = null, beforeTimestamp = null) {
  if (isLoadingMessages) return;
  if (!hasMoreMessages && beforeId !== null) return;

  isLoadingMessages = true;

  let url = `/api/v1/messages/${roomId}?limit=20`;
  if (beforeId && beforeTimestamp) {
    url += `&before_id=${beforeId}&before_timestamp=${encodeURIComponent(beforeTimestamp)}`;
  }

  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      console.error("Failed to load messages:", response.status);
      return;
    }

    const messages = await response.json();

    if (messages.length < 20 && beforeId !== null) {
      hasMoreMessages = false;
    }

    if (messages.length === 0) {
      if (beforeId === null) {
        document.getElementById("messages").innerHTML =
          '<div class="system">No messages yet. Say hello!</div>';
      }
      hasMoreMessages = false;
      return;
    }

    const messagesDiv = document.getElementById("messages");

    if (beforeId === null) {
      // Initial load
      messagesDiv.innerHTML = "";
      messages.forEach((msg) => {
        if (msg.id) seenMessageIds.add(msg.id);
        const p = createMessageElement(msg, currentUser);
        messagesDiv.appendChild(p);
      });

      if (messages.length > 0) {
        const oldest = messages[0];
        oldestMessageId = oldest.id;
        oldestMessageTimestamp = oldest.created_at;
      }

      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } else {
      // Loading older messages
      const oldScrollHeight = messagesDiv.scrollHeight;
      const fragment = document.createDocumentFragment();

      messages.forEach((msg) => {
        if (msg.id && seenMessageIds.has(msg.id)) return;
        if (msg.id) seenMessageIds.add(msg.id);
        const p = createMessageElement(msg, currentUser);
        fragment.appendChild(p);
      });

      messagesDiv.prepend(fragment);

      if (messages.length > 0) {
        const oldest = messages[0];
        oldestMessageId = oldest.id;
        oldestMessageTimestamp = oldest.created_at;
      }

      const newScrollHeight = messagesDiv.scrollHeight;
      const addedHeight = newScrollHeight - oldScrollHeight;
      messagesDiv.scrollTop = addedHeight;
    }
  } catch (error) {
    console.error("Error loading messages:", error);
  } finally {
    isLoadingMessages = false;
  }
}

// ---------- INFINITE SCROLL LISTENER ----------
document.getElementById("messages").addEventListener("scroll", function () {
  if (
    this.scrollTop === 0 &&
    hasMoreMessages &&
    !isLoadingMessages &&
    currentRoom
  ) {
    LoadMessages(currentRoom, oldestMessageId, oldestMessageTimestamp);
  }
});
