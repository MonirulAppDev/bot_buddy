// Bot Buddy Background Service Worker

const BACKEND_URL = "http://127.0.0.1:8000";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "SYNC_COOKIES_TO_BACKEND") {
    syncFacebookCookies(request.accountName || "My Extension Account")
      .then(res => sendResponse(res))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep channel open
  }

  if (request.action === "GET_BACKEND_STATUS") {
    checkBackendHealth()
      .then(res => sendResponse(res))
      .catch(err => sendResponse({ online: false, error: err.message }));
    return true;
  }
});

// Check if Bot Buddy Python server is running
async function checkBackendHealth() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (res.ok) {
      return { online: true };
    }
    return { online: false };
  } catch (err) {
    return { online: false, error: err.message };
  }
}

// Extract Facebook cookies and sync to backend
async function syncFacebookCookies(accountName) {
  try {
    const cookies = await chrome.cookies.getAll({ domain: "facebook.com" });
    if (!cookies || cookies.length === 0) {
      return { success: false, error: "No Facebook cookies found. Please ensure you are logged into facebook.com in this browser!" };
    }

    const cUser = cookies.find(c => c.name === "c_user");
    const xs = cookies.find(c => c.name === "xs");

    if (!cUser || !xs) {
      return { success: false, error: "Could not find active 'c_user' or 'xs' cookies. Please log into Facebook first." };
    }

    // Format standard cookie string
    const cookieString = cookies.map(c => `${c.name}=${c.value}`).join("; ");

    // Send to Bot Buddy backend
    const res = await fetch(`${BACKEND_URL}/api/v1/fb-accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_name: `${accountName} (${cUser.value})`,
        cookie_data: cookieString
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Backend sync failed");
    }

    const data = await res.json();
    return {
      success: true,
      message: "Facebook session cookies synced to Bot Buddy backend successfully!",
      fb_user_id: cUser.value
    };
  } catch (err) {
    return { success: false, error: err.message };
  }
}
