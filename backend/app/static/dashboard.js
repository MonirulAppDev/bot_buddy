// State
let servicesCache = [];
let pollingTimer = null;
let lastSMMOrderId = null;

// Tab switcher
function switchTab(tab) {
  const tabs = ['orders', 'personas', 'smm', 'realfb', 'pagefarm'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    const sec = document.getElementById(`section-${t}`);
    if (!btn || !sec) return;
    if (t === tab) {
      btn.className = "px-4 py-1.5 rounded-lg font-medium transition-all bg-indigo-600 text-white shadow-sm flex items-center gap-2";
      sec.classList.remove('hidden');
    } else {
      btn.className = "px-4 py-1.5 rounded-lg font-medium transition-all text-slate-400 hover:text-white flex items-center gap-2";
      sec.classList.add('hidden');
    }
  });

  if (tab === 'personas') {
    loadPersonas();
  } else if (tab === 'realfb') {
    loadFBAccountsList();
  } else if (tab === 'pagefarm') {
    loadPagesList();
  }
}

// Toast notification
function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toast-msg');
  msg.innerText = message;
  toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-xl shadow-xl transform transition-all duration-300 z-50 text-sm flex items-center gap-2 ${isError ? 'bg-rose-600 text-white' : 'bg-indigo-600 text-white'}`;
  toast.classList.remove('translate-y-20', 'opacity-0');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 3500);
}

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  await loadServices();
  await refreshOrders();
  await loadPersonasCount();
  await loadUserBalance();
  await loadPagesCount();
  
  // Start continuous polling for orders
  startPolling();
});

// Load Services
async function loadServices() {
  try {
    const res = await fetch("/api/v1/services");
    servicesCache = await res.json();
    const select = document.getElementById("order-service");
    select.innerHTML = "";
    servicesCache.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} ($${s.rate_per_1000}/1k)`;
      select.appendChild(opt);
    });
    onServiceChange();
  } catch (err) {
    console.error("Failed to load services", err);
  }
}

function onServiceChange() {
  const select = document.getElementById("order-service");
  const serviceId = parseInt(select.value);
  const service = servicesCache.find(s => s.id === serviceId);
  const commentsBox = document.getElementById("comments-box");

  if (service && service.service_type === "comment") {
    commentsBox.classList.remove("hidden");
  } else {
    commentsBox.classList.add("hidden");
  }

  if (service) {
    const qtyInput = document.getElementById("order-quantity");
    qtyInput.min = service.min_quantity;
    qtyInput.max = service.max_quantity;
    if (parseInt(qtyInput.value) < service.min_quantity) {
      qtyInput.value = service.min_quantity;
    }
  }
}

function toggleIntervalInput() {
  const isDrip = document.getElementById("order-drip").checked;
  const container = document.getElementById("interval-container");
  container.style.opacity = isDrip ? "1" : "0.4";
  container.style.pointerEvents = isDrip ? "auto" : "none";
}

function insertSpintaxPreset(type) {
  const textarea = document.getElementById("order-comments");
  if (type === 1) {
    textarea.value = "{Awesome|Great|Superb|Brilliant} work! {Loved this|Very helpful|Keep sharing} {🔥|👏|❤️}";
  } else {
    textarea.value = "{Interesting|Never thought about this}! {What do you think about next steps?|Could you explain more?} {💡|🤔}";
  }
}

// Handle Order Creation
async function handleCreateOrder(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-submit-order");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching...`;

  try {
    const serviceId = parseInt(document.getElementById("order-service").value);
    const targetUrl = document.getElementById("order-target").value.trim();
    const quantity = parseInt(document.getElementById("order-quantity").value);
    const isDrip = document.getElementById("order-drip").checked;
    const interval = parseInt(document.getElementById("order-interval").value);
    const comments = document.getElementById("order-comments").value;

    const payload = {
      service_id: serviceId,
      target_url: targetUrl,
      quantity: quantity,
      drip_feed: isDrip,
      interval_seconds: interval,
      comments: comments || null
    };

    const res = await fetch("/api/v1/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Order submission failed");
    }

    const order = await res.json();
    lastSMMOrderId = order.id;
    showToast(`Simulation launched for ${quantity} actions!`);
    document.getElementById("order-target").value = "";
    await refreshOrders();
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Simulation`;
  }
}

// Refresh Orders & Update KPI Cards
async function refreshOrders() {
  try {
    const res = await fetch("/api/v1/orders?limit=25");
    const data = await res.json();
    const orders = data.items || [];

    // Update KPI
    let inProgressCount = 0;
    let completedCount = 0;
    orders.forEach(o => {
      if (o.status === "In progress") inProgressCount++;
      if (o.status === "Completed") completedCount++;
    });

    document.getElementById("kpi-total-orders").innerText = data.total || 0;
    document.getElementById("kpi-in-progress").innerText = inProgressCount;
    document.getElementById("kpi-completed").innerText = completedCount;

    // Render Table
    const tbody = document.getElementById("orders-table-body");
    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-6 py-8 text-center text-slate-500">No simulation orders yet. Launch your first one above!</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(order => {
      const progressPercent = Math.min(100, Math.round((order.delivered_count / order.quantity) * 100));
      
      let badgeClass = "bg-slate-700/60 text-slate-300 border-slate-600";
      let statusIcon = "fa-clock";
      if (order.status === "In progress") {
        badgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
        statusIcon = "fa-spinner fa-spin";
      } else if (order.status === "Completed") {
        badgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
        statusIcon = "fa-check-circle";
      }

      return `
        <tr class="hover:bg-surface-800/40 transition">
          <td class="px-6 py-4 font-mono text-xs text-slate-400">
            <span title="${order.id}">${order.id.substring(0, 8)}...</span>
          </td>
          <td class="px-6 py-4 font-medium text-white">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-md bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs">
                <i class="fa-brands fa-facebook-f"></i>
              </span>
              <span>${order.service ? order.service.name : 'Engagement Service'}</span>
            </div>
          </td>
          <td class="px-6 py-4">
            <a href="${order.target_url}" target="_blank" class="text-indigo-400 hover:underline max-w-xs truncate block text-xs" title="${order.target_url}">
              ${order.target_url} <i class="fa-solid fa-arrow-up-right-from-square text-[10px] ml-1"></i>
            </a>
          </td>
          <td class="px-6 py-4">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-semibold text-slate-300">${order.delivered_count} / ${order.quantity}</span>
              <span class="text-slate-400 font-mono">${progressPercent}%</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/50">
              <div class="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-300" style="width: ${progressPercent}%"></div>
            </div>
          </td>
          <td class="px-6 py-4">
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeClass}">
              <i class="fa-solid ${statusIcon}"></i> ${order.status}
            </span>
          </td>
          <td class="px-6 py-4 text-right">
            <button onclick="viewOrderLogs('${order.id}')" class="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-slate-700 text-xs font-medium text-slate-300 hover:text-white border border-slate-700 transition">
              <i class="fa-solid fa-terminal text-indigo-400 mr-1"></i> View Logs
            </button>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Orders refresh error", err);
  }
}

function startPolling() {
  if (pollingTimer) clearInterval(pollingTimer);
  pollingTimer = setInterval(async () => {
    await refreshOrders();
  }, 2000);
}

// View Audit Logs Modal
async function viewOrderLogs(orderId) {
  const modal = document.getElementById("logs-modal");
  const modalOrderId = document.getElementById("modal-order-id");
  const modalBody = document.getElementById("modal-logs-body");

  modalOrderId.innerText = `Order ID: ${orderId}`;
  modalBody.innerHTML = `<div class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-lg"></i> Loading audit logs...</div>`;
  modal.classList.remove("hidden");

  try {
    const res = await fetch(`/api/v1/orders/${orderId}/logs?limit=100`);
    const logs = await res.json();

    if (logs.length === 0) {
      modalBody.innerHTML = `<div class="text-slate-500 text-center py-6">No execution logs registered yet. Actions are in queue...</div>`;
      return;
    }

    modalBody.innerHTML = logs.map(l => {
      const time = new Date(l.created_at).toLocaleTimeString();
      return `
        <div class="p-2.5 rounded-lg bg-black/40 border border-slate-800/80 flex items-start justify-between gap-4">
          <div class="space-y-0.5">
            <div class="flex items-center gap-2">
              <span class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">${l.status}</span>
              <span class="font-semibold text-slate-300 text-xs">${l.action_type}</span>
              <span class="text-[10px] text-slate-500">${time}</span>
            </div>
            <div class="text-slate-400 text-xs break-all">${l.details}</div>
          </div>
          <span class="text-indigo-400 font-mono text-[11px] whitespace-nowrap">${l.execution_time_ms} ms</span>
        </div>
      `;
    }).join("");
  } catch (err) {
    modalBody.innerHTML = `<div class="text-rose-400">Failed to fetch logs.</div>`;
  }
}

function closeLogsModal() {
  document.getElementById("logs-modal").classList.add("hidden");
}

// Personas Management
async function loadPersonasCount() {
  try {
    const res = await fetch("/api/v1/personas?limit=1");
    const data = await res.json();
    document.getElementById("kpi-personas").innerText = data.total || 0;
    document.getElementById("nav-persona-count").innerText = data.total || 0;
  } catch (err) {}
}

async function loadUserBalance() {
  try {
    const res = await fetch("/api/v2?key=bb_live_master_api_key_778899&action=balance");
    const data = await res.json();
    if (data.balance) {
      document.getElementById("nav-user-balance").innerText = `$${parseFloat(data.balance).toFixed(2)}`;
    }
  } catch (e) {}
}

async function quickAddFunds() {
  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "admin", password: "admin123456" })
    });
    const authData = await res.json();
    if (authData.access_token) {
      await fetch("/api/v1/auth/add-funds", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authData.access_token}`
        },
        body: JSON.stringify({ amount: 50.0 })
      });
      showToast("Credited +$50.00 demo funds to wallet!");
      await loadUserBalance();
    }
  } catch (err) {
    showToast("Failed to add funds", true);
  }
}

async function loadPersonas() {
  const grid = document.getElementById("personas-grid");
  grid.innerHTML = `<div class="col-span-4 text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-lg"></i> Loading accounts pool...</div>`;

  try {
    const res = await fetch("/api/v1/personas?limit=24");
    const data = await res.json();
    const personas = data.items || [];

    if (personas.length === 0) {
      grid.innerHTML = `<div class="col-span-4 text-center py-8 text-slate-500">No dummy personas in database. Click 'Generate' above to seed profiles!</div>`;
      return;
    }

    grid.innerHTML = personas.map(p => {
      let meta = {};
      try { meta = JSON.parse(p.extra_metadata); } catch(e){}

      return `
        <div class="bg-surface-900 border border-slate-800 rounded-2xl p-4 shadow-sm hover:border-slate-700 transition flex items-start gap-3">
          <img src="${p.avatar_url}" alt="Avatar" class="w-12 h-12 rounded-xl bg-slate-800 object-cover border border-slate-700 shadow" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=${p.username}'">
          <div class="flex-1 min-w-0">
            <h4 class="font-bold text-sm text-white truncate">${p.display_name}</h4>
            <p class="text-xs text-indigo-400 font-mono truncate">@${p.username}</p>
            <div class="flex items-center gap-2 mt-2 text-[11px] text-slate-400">
              <span><i class="fa-solid fa-bolt text-amber-400 text-[10px]"></i> ${p.total_actions} actions</span>
              <span>•</span>
              <span><i class="fa-solid fa-location-dot text-slate-500 text-[10px]"></i> ${meta.country || 'Global'}</span>
            </div>
          </div>
        </div>
      `;
    }).join("");

    await loadPersonasCount();
  } catch (err) {
    grid.innerHTML = `<div class="col-span-4 text-rose-400 text-center py-4">Failed to load personas.</div>`;
  }
}

async function handleGeneratePersonas() {
  const btn = document.getElementById("btn-generate-personas");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

  const count = parseInt(document.getElementById("persona-count").value);
  const locale = document.getElementById("persona-locale").value;

  try {
    const res = await fetch("/api/v1/personas/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count, locale, platform: "facebook" })
    });
    if (!res.ok) throw new Error("Failed to generate personas");

    showToast(`Successfully generated ${count} dummy personas!`);
    await loadPersonas();
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Generate`;
  }
}

// SMM API v2 Quick Tester
async function testSMM(type) {
  const output = document.getElementById("smm-response");
  const timeSpan = document.getElementById("smm-time");
  output.innerText = "Requesting /api/v2 ...";
  const startTime = Date.now();

  try {
    let url = "/api/v2";
    let options = { method: "POST" };
    const formData = new FormData();
    formData.append("key", "bb_live_master_api_key_778899"); // Master admin API key

    if (type === "services") {
      formData.append("action", "services");
    } else if (type === "balance") {
      formData.append("action", "balance");
    } else if (type === "add_sample") {
      const firstService = servicesCache[0] ? servicesCache[0].id : 1;
      formData.append("action", "add");
      formData.append("service", firstService);
      formData.append("link", "https://facebook.com/example/post/987654");
      formData.append("quantity", 15);
    } else if (type === "status_sample") {
      const orderIdToTest = lastSMMOrderId || "sample-order-id";
      formData.append("action", "status");
      formData.append("order", orderIdToTest);
    }

    options.body = formData;
    const res = await fetch(url, options);
    const data = await res.json();
    
    if (type === "add_sample" && data.order) {
      lastSMMOrderId = data.order;
    }

    output.innerText = JSON.stringify(data, null, 2);
    timeSpan.innerText = `${Date.now() - startTime} ms response`;
    await loadUserBalance();
  } catch (err) {
    output.innerText = `Error: ${err.message}`;
  }
}

// Handle Real Facebook Playwright Like Action
async function handleRealFBLike(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-realfb-like");
  const url = document.getElementById("realfb-url").value.trim();
  const cookies = document.getElementById("realfb-cookies").value.trim();
  const visible = document.getElementById("realfb-visible").checked;

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching Browser & Clicking...`;

  const resultDiv = document.getElementById("realfb-result");
  const titleSpan = document.getElementById("realfb-result-title");
  const timeSpan = document.getElementById("realfb-exec-time");
  const img = document.getElementById("realfb-screenshot");

  resultDiv.classList.remove("hidden");
  titleSpan.innerHTML = `<span class="text-amber-400"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Opening stealth browser, navigating to post...</span>`;
  timeSpan.innerText = "";
  img.src = "";

  const startTime = Date.now();

  try {
    const res = await fetch("/api/v1/fb-accounts/execute-like", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        post_url: url,
        cookie_data: cookies,
        headless: !visible
      })
    });

    const data = await res.json();
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    timeSpan.innerText = `${duration}s execution`;

    if (data.success) {
      titleSpan.innerHTML = `<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check-circle mr-1"></i> ${data.message || 'Successfully clicked Like on Facebook!'}</span>`;
      showToast("Like successfully clicked on Facebook!");
    } else {
      titleSpan.innerHTML = `<span class="text-rose-400 font-bold"><i class="fa-solid fa-circle-exclamation mr-1"></i> ${data.error || 'Failed to like post'}</span>`;
      showToast(data.error || "Failed to like post", true);
    }

    if (data.screenshot) {
      img.src = data.screenshot + "?t=" + Date.now();
    }
  } catch (err) {
    titleSpan.innerHTML = `<span class="text-rose-400 font-bold"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Error: ${err.message}</span>`;
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-thumbs-up"></i> Click Real Like on Facebook`;
  }
}

// Load Fake FB Accounts Pool
async function loadFBAccountsList() {
  const container = document.getElementById("fb-accounts-table-body");
  const countBadge = document.getElementById("realfb-accounts-count");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/fb-accounts");
    const accounts = await res.json();
    countBadge.innerText = accounts.length;

    if (accounts.length === 0) {
      container.innerHTML = `<div class="text-slate-500 text-center py-3 text-xs">No fake accounts in pool yet. Paste cookies on the right to import!</div>`;
      return;
    }

    container.innerHTML = accounts.map((acc, idx) => `
      <div class="p-2.5 rounded-lg bg-surface-950 border border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-[10px]">${idx + 1}</span>
          <div>
            <div class="font-bold text-white text-xs">${acc.account_name}</div>
            <div class="text-[10px] text-slate-500 font-mono">UID: ${acc.fb_user_id || 'N/A'} • ${acc.total_likes_given} likes given</div>
          </div>
        </div>
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="text-rose-400 text-xs">Failed to load account pool.</div>`;
  }
}

// Handle Bulk Import of Fake Accounts
async function handleBulkImport(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-bulk-import");
  const textarea = document.getElementById("bulk-import-data");
  const rawData = textarea.value.trim();

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Importing...`;

  try {
    const res = await fetch("/api/v1/fb-accounts/bulk-import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_data: rawData })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Import failed");

    showToast(`Successfully imported ${data.total_imported} fake accounts!`);
    textarea.value = "";
    await loadFBAccountsList();
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-file-import"></i> Save Fake Accounts to Pool`;
  }
}

// Handle Batch Liking across Fake Accounts Pool
async function handleBatchLike(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-batch-like");
  const url = document.getElementById("batch-url").value.trim();
  const quantity = parseInt(document.getElementById("batch-quantity").value);
  const excludeUid = document.getElementById("batch-exclude-uid").value.trim();
  const visible = document.getElementById("batch-visible").checked;

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sending Fake Likes...`;

  const resultsDiv = document.getElementById("batch-results");
  const statusPill = document.getElementById("batch-status-pill");
  const logsList = document.getElementById("batch-logs-list");

  resultsDiv.classList.remove("hidden");
  statusPill.className = "px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20";
  statusPill.innerText = "Running multi-account simulation...";
  logsList.innerHTML = `<div class="text-slate-400 text-center py-2"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Cycling through fake accounts...</div>`;

  try {
    const res = await fetch("/api/v1/fb-accounts/batch-like", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        post_url: url,
        quantity: quantity,
        exclude_fb_user_id: excludeUid || null,
        delay_seconds: 2.0,
        headless: !visible
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Batch like failed");

    statusPill.className = "px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    statusPill.innerText = `Delivered ${data.delivered} / ${data.total_requested} Likes`;

    logsList.innerHTML = data.logs.map(log => `
      <div class="p-2 rounded bg-surface-900 border border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full ${log.status === 'SUCCESS' ? 'bg-emerald-400' : 'bg-rose-400'}"></span>
          <span class="text-white font-bold">${log.account_name}</span>
        </div>
        <span class="${log.status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'}">${log.message}</span>
      </div>
    `).join("");

    showToast(`Batch completed: ${data.delivered} fake likes delivered!`);
    await loadFBAccountsList();
  } catch (err) {
    statusPill.className = "px-2 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20";
    statusPill.innerText = "Failed";
    logsList.innerHTML = `<div class="text-rose-400 p-2">${err.message}</div>`;
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Send Likes From Fake Accounts`;
  }
}

// -------------------------------------------------------------
// PAGE FARM & SWARM FUNCTIONS (TiDB Cloud Backed)
// -------------------------------------------------------------

// Load count of pages for badges and KPIs
async function loadPagesCount() {
  try {
    const res = await fetch("/api/v1/fb-pages?limit=1");
    if (!res.ok) return;
    const data = await res.json();
    const count = data.total || 0;

    const navBadge = document.getElementById("nav-pages-count");
    const kpiCount = document.getElementById("kpi-farm-pages-count");
    if (navBadge) navBadge.innerText = count;
    if (kpiCount) kpiCount.innerText = `${count} Pages`;
  } catch (err) {
    console.error("Failed to load pages count", err);
  }
}

// Load and render child pages in Page Farm grid
async function loadPagesList() {
  const grid = document.getElementById("pages-grid");
  if (!grid) return;

  grid.innerHTML = `<div class="col-span-full py-8 text-center text-slate-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading Page Farm from TiDB Cloud...</div>`;

  try {
    const res = await fetch("/api/v1/fb-pages?limit=60");
    const data = await res.json();
    const pages = data.items || [];

    const navBadge = document.getElementById("nav-pages-count");
    const kpiCount = document.getElementById("kpi-farm-pages-count");
    const total = data.total || pages.length;
    if (navBadge) navBadge.innerText = total;
    if (kpiCount) kpiCount.innerText = `${total} Pages`;

    if (pages.length === 0) {
      grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-500">No pages in farm yet. Click "+ Spawn 5 New Pages" above to generate child identities!</div>`;
      return;
    }

    grid.innerHTML = pages.map((page, idx) => `
      <div class="bg-surface-900 border border-slate-800 rounded-2xl p-4 hover:border-slate-700 transition flex items-start gap-3 relative group">
        <img src="${page.avatar_url}" alt="${page.page_name}" class="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex-shrink-0 object-cover shadow-sm">
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-1">
            <h4 class="font-bold text-white text-xs truncate" title="${page.page_name}">${page.page_name}</h4>
            <span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>
          </div>
          <div class="text-[11px] text-pink-400 mt-0.5 flex items-center gap-1 font-medium">
            <i class="fa-solid fa-tag text-[9px]"></i> ${page.category}
          </div>
          <div class="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono">
            <span>Parent: <strong class="text-slate-300 font-sans">${page.parent_account}</strong></span>
            <span class="text-amber-400 font-bold"><i class="fa-solid fa-thumbs-up mr-0.5"></i> ${page.total_likes_given}</span>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<div class="col-span-full text-rose-400 text-center py-4">Failed to load pages: ${err.message}</div>`;
  }
}

// Spawn new child pages under parent account
async function handleSpawnPages(count = 5) {
  const btn = document.getElementById("btn-spawn-pages");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Spawning ${count} Pages...`;
  }

  try {
    const res = await fetch("/api/v1/fb-pages/spawn-pages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: count })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to spawn pages");

    showToast(data.message || `Successfully spawned ${count} pages!`);
    await loadPagesList();
    await loadPagesCount();
  } catch (err) {
    showToast(err.message, true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> + Spawn 5 New Pages`;
    }
  }
}

// Launch Swarm Like Order across Page Farm
async function handleSwarmLike(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-swarm-like");
  const postUrl = document.getElementById("swarm-url").value.trim();
  const quantity = parseInt(document.getElementById("swarm-quantity").value);

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Swarm Delivering Likes...`;

  const resultsDiv = document.getElementById("swarm-results");
  const heading = document.getElementById("swarm-result-heading");
  const badge = document.getElementById("swarm-status-badge");
  const logsList = document.getElementById("swarm-logs-list");

  resultsDiv.classList.remove("hidden");
  badge.className = "px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold";
  badge.innerText = "Swarming...";
  heading.innerText = `Engaging ${quantity} Child Pages from Bot Farm...`;
  logsList.innerHTML = `<div class="text-slate-400 text-center py-3"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Running Page Farm swarm...</div>`;

  try {
    const res = await fetch("/api/v1/fb-pages/swarm-like", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        post_url: postUrl,
        quantity: quantity,
        delay_seconds: 0.5
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Swarm like request failed");

    badge.className = "px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold";
    badge.innerText = `Delivered ${data.delivered} / ${data.total_requested}`;
    heading.innerText = `Swarm Completed Successfully! Delivered ${data.delivered} Likes`;

    logsList.innerHTML = data.logs.map(log => `
      <div class="p-2 rounded bg-surface-950 border border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center font-bold text-[10px]">${log.step}</span>
          <span class="text-white font-semibold text-xs">${log.entity_name}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${log.category}</span>
        </div>
        <span class="text-emerald-400 font-semibold text-xs flex items-center gap-1">
          <i class="fa-solid fa-check"></i> Liked
        </span>
      </div>
    `).join("");

    showToast(`Swarm completed! ${data.delivered} likes delivered across Page Farm.`);
    await loadPagesList();
    await loadPagesCount();
  } catch (err) {
    badge.className = "px-2 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold";
    badge.innerText = "Failed";
    heading.innerText = "Swarm delivery encountered an error";
    logsList.innerHTML = `<div class="text-rose-400 p-2">${err.message}</div>`;
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Swarm Likes Order`;
  }
}


