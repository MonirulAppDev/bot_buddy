// Bot Buddy Popup Script

let activeTab = null;

document.addEventListener("DOMContentLoaded", async () => {
  await checkBackendStatus();
  await detectActiveTab();
  setupEventListeners();
});

// Check if Python FastAPI server is running
async function checkBackendStatus() {
  const statusEl = document.getElementById("backend-status");
  try {
    const res = await fetch("http://127.0.0.1:8000/health");
    if (res.ok) {
      statusEl.className = "badge badge-online";
      statusEl.innerText = "● Backend Online";
      return;
    }
  } catch (err) {}

  statusEl.className = "badge badge-offline";
  statusEl.innerText = "● Backend Offline";
}

// Detect active tab URL
async function detectActiveTab() {
  const urlEl = document.getElementById("detected-url");
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs[0]) {
      activeTab = tabs[0];
      const url = activeTab.url || "";
      if (url.includes("facebook.com")) {
        urlEl.innerText = url;
      } else {
        urlEl.innerText = "Not on Facebook. Open a Facebook post in your active tab!";
        disableActionButtons();
      }
    }
  } catch (err) {
    urlEl.innerText = "Could not detect active tab.";
  }
}

function disableActionButtons() {
  document.getElementById("btn-like").disabled = true;
  document.getElementById("btn-love").disabled = true;
  document.getElementById("btn-comment").disabled = true;
}

function showStatus(msg, isSuccess = true) {
  const box = document.getElementById("status-box");
  box.className = isSuccess ? "status-msg status-success" : "status-msg status-error";
  box.innerText = msg;
  setTimeout(() => {
    box.style.display = "none";
  }, 4000);
}

function setupEventListeners() {
  // 1. Direct Like
  document.getElementById("btn-like").addEventListener("click", async () => {
    if (!activeTab || !activeTab.id) return;
    const btn = document.getElementById("btn-like");
    btn.disabled = true;
    btn.innerText = "Clicking Like...";

    try {
      const response = await chrome.tabs.sendMessage(activeTab.id, { action: "CLICK_LIKE" });
      if (response && response.success) {
        showStatus(response.message || "Liked successfully!", true);
      } else {
        showStatus((response && response.error) || "Could not click like.", false);
      }
    } catch (err) {
      showStatus("Failed to communicate with Facebook tab. Please refresh the FB page and try again.", false);
    } finally {
      btn.disabled = false;
      btn.innerText = "👍 Like This Post (Direct)";
    }
  });

  // 2. Direct Love Reaction
  document.getElementById("btn-love").addEventListener("click", async () => {
    if (!activeTab || !activeTab.id) return;
    const btn = document.getElementById("btn-love");
    btn.disabled = true;
    btn.innerText = "Adding Love React...";

    try {
      const response = await chrome.tabs.sendMessage(activeTab.id, { action: "CLICK_LOVE" });
      if (response && response.success) {
        showStatus(response.message || "Love reaction added!", true);
      } else {
        showStatus((response && response.error) || "Could not add love react.", false);
      }
    } catch (err) {
      showStatus("Failed to communicate with Facebook tab.", false);
    } finally {
      btn.disabled = false;
      btn.innerText = "❤️ Love React (Direct)";
    }
  });

  // 3. Post Smart Comment
  document.getElementById("btn-comment").addEventListener("click", async () => {
    if (!activeTab || !activeTab.id) return;
    const commentText = document.getElementById("comment-preset").value;
    const btn = document.getElementById("btn-comment");
    btn.disabled = true;
    btn.innerText = "Posting comment...";

    try {
      const response = await chrome.tabs.sendMessage(activeTab.id, {
        action: "POST_COMMENT",
        text: commentText
      });
      if (response && response.success) {
        showStatus(response.message || "Comment posted!", true);
      } else {
        showStatus((response && response.error) || "Could not post comment.", false);
      }
    } catch (err) {
      showStatus("Failed to communicate with Facebook tab.", false);
    } finally {
      btn.disabled = false;
      btn.innerText = "💬 Post Smart Comment";
    }
  });

  // 4. 1-Click Cookie Sync to Backend
  document.getElementById("btn-sync-cookies").addEventListener("click", async () => {
    const btn = document.getElementById("btn-sync-cookies");
    btn.disabled = true;
    btn.innerText = "Syncing with backend...";

    try {
      const response = await chrome.runtime.sendMessage({
        action: "SYNC_COOKIES_TO_BACKEND",
        accountName: "Extension Auto-Synced Account"
      });

      if (response && response.success) {
        showStatus(`Synced! Account UID: ${response.fb_user_id || 'Active'} saved to Bot Buddy!`, true);
      } else {
        showStatus((response && response.error) || "Cookie sync failed.", false);
      }
    } catch (err) {
      showStatus("Could not connect to Bot Buddy backend (http://127.0.0.1:8000). Is server running?", false);
    } finally {
      btn.disabled = false;
      btn.innerText = "🔄 1-Click Add Account to Pool";
    }
  });

  // 5. Send Fake Account Likes (Excluding personal profile)
  document.getElementById("btn-send-fake-likes").addEventListener("click", async () => {
    if (!activeTab || !activeTab.url || !activeTab.url.includes("facebook.com")) {
      showStatus("Please open a Facebook post first!", false);
      return;
    }

    const btn = document.getElementById("btn-send-fake-likes");
    const qty = parseInt(document.getElementById("popup-fake-qty").value) || 5;

    btn.disabled = true;
    btn.innerText = "Sending Fake Likes...";

    try {
      // Find my own UID from cookies so we can exclude it
      let myUid = null;
      try {
        const cUserCookie = await chrome.cookies.get({ url: "https://www.facebook.com", name: "c_user" });
        if (cUserCookie) myUid = cUserCookie.value;
      } catch (e) {}

      const res = await fetch("http://127.0.0.1:8000/api/v1/fb-accounts/batch-like", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_url: activeTab.url,
          quantity: qty,
          exclude_fb_user_id: myUid,
          delay_seconds: 2.0,
          headless: true
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Batch like failed");

      showStatus(`Delivered ${data.delivered} / ${data.total_requested} likes from Fake Accounts Pool!`, true);
    } catch (err) {
      showStatus(err.message, false);
    } finally {
      btn.disabled = false;
      btn.innerText = "🚀 Send Fake Likes";
    }
  });
}

