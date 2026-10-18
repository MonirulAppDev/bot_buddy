// Bot Buddy Facebook Content Script

console.log("[Bot Buddy] Content script loaded on Facebook page.");

// Listen for commands from Popup or Background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "PING") {
    sendResponse({
      status: "ok",
      url: window.location.href,
      title: document.title
    });
    return true;
  }

  if (request.action === "CLICK_LIKE") {
    handleLikeAction()
      .then(res => sendResponse(res))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }

  if (request.action === "CLICK_LOVE") {
    handleLoveAction()
      .then(res => sendResponse(res))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === "POST_COMMENT") {
    handleCommentAction(request.text)
      .then(res => sendResponse(res))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

// Helper to find Facebook Like button
function findLikeButton() {
  const selectors = [
    'div[aria-label="Like"][role="button"]',
    'div[aria-label="like"][role="button"]',
    'div[aria-label="Like"][tabindex="0"]',
    'div[aria-label="Like, Love, Care, Haha, Wow, Sad, Angry"][role="button"]',
    'div[role="button"][tabindex="0"]:has(span:has-text("Like"))',
    'div[role="button"]:has-text("Like")'
  ];

  for (const sel of selectors) {
    try {
      const el = document.querySelector(sel);
      if (el && el.offsetParent !== null) {
        return el;
      }
    } catch (e) {}
  }

  // Fallback: look through all buttons
  const buttons = document.querySelectorAll('div[role="button"]');
  for (const btn of buttons) {
    const text = btn.innerText || "";
    const aria = btn.getAttribute("aria-label") || "";
    if ((aria.toLowerCase() === "like" || text.trim() === "Like") && btn.offsetParent !== null) {
      return btn;
    }
  }

  return null;
}

// Show visual notification inside Facebook tab
function showFacebookToast(msg, isSuccess = true) {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999999;
    padding: 12px 20px;
    background: ${isSuccess ? '#4f46e5' : '#e11d48'};
    color: white;
    font-size: 14px;
    font-weight: bold;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    transition: all 0.3s ease;
  `;
  toast.innerHTML = `🤖 <span>${msg}</span>`;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-10px)";
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// Handle Like Action
async function handleLikeAction() {
  const likeBtn = findLikeButton();
  if (!likeBtn) {
    showFacebookToast("Like button not found on this view!", false);
    return { success: false, error: "Like button not found. Please make sure the post is visible." };
  }

  // Check if already liked
  const isPressed = likeBtn.getAttribute("aria-pressed") === "true";
  if (isPressed) {
    showFacebookToast("Post is already liked!", true);
    return { success: true, message: "Post was already liked." };
  }

  likeBtn.scrollIntoView({ behavior: "smooth", block: "center" });
  await new Promise(r => setTimeout(r, 400));

  // Native mouse events
  const opts = { bubbles: true, cancelable: true, view: window };
  likeBtn.dispatchEvent(new MouseEvent("mousedown", opts));
  likeBtn.dispatchEvent(new MouseEvent("mouseup", opts));
  likeBtn.click();

  showFacebookToast("Like clicked successfully!");
  return { success: true, message: "Like clicked successfully on Facebook!" };
}

// Handle Love Reaction
async function handleLoveAction() {
  const likeBtn = findLikeButton();
  if (!likeBtn) {
    return { success: false, error: "Reaction button not found." };
  }

  likeBtn.scrollIntoView({ behavior: "smooth", block: "center" });
  await new Promise(r => setTimeout(r, 400));

  // Dispatch hover to trigger reaction tray
  likeBtn.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
  likeBtn.dispatchEvent(new MouseEvent("mouseover", { bubbles: true }));
  await new Promise(r => setTimeout(r, 800));

  // Look for Love reaction button
  const loveBtn = document.querySelector('div[aria-label="Love"][role="button"]');
  if (loveBtn) {
    loveBtn.click();
    showFacebookToast("Love reaction ❤️ added!");
    return { success: true, message: "Love reaction added!" };
  }

  // Fallback to standard like
  likeBtn.click();
  showFacebookToast("Liked successfully (Love tray didn't pop up)!");
  return { success: true, message: "Like clicked successfully." };
}

// Handle Comment Action
async function handleCommentAction(commentText) {
  if (!commentText || !commentText.trim()) {
    return { success: false, error: "Comment text cannot be empty." };
  }

  const commentInput = document.querySelector('div[aria-label*="Write a comment"][role="textbox"]') ||
                       document.querySelector('div[contenteditable="true"][role="textbox"]');

  if (!commentInput) {
    showFacebookToast("Comment box not found!", false);
    return { success: false, error: "Comment box not found on this post." };
  }

  commentInput.scrollIntoView({ behavior: "smooth", block: "center" });
  commentInput.focus();
  await new Promise(r => setTimeout(r, 300));

  // Insert text via document.execCommand for native React input synthetic event handling
  document.execCommand("insertText", false, commentText.trim());
  await new Promise(r => setTimeout(r, 500));

  // Press Enter to submit comment
  const enterEvent = new KeyboardEvent("keydown", {
    bubbles: true,
    cancelable: true,
    keyCode: 13,
    which: 13,
    key: "Enter"
  });
  commentInput.dispatchEvent(enterEvent);

  showFacebookToast("Comment submitted!");
  return { success: true, message: "Comment successfully posted!" };
}
