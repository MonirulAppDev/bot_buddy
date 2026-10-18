// State
let activeViewBoostTimer = null;

// Toast notification
function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toast-msg');
  msg.innerText = message;
  toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-xl shadow-xl transform transition-all duration-300 z-50 text-sm flex items-center gap-2 ${isError ? 'bg-rose-600 text-white' : 'bg-cyan-600 text-white'}`;
  toast.classList.remove('translate-y-20', 'opacity-0');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 4000);
}

// Preset helper
function setQuantity(val) {
  const input = document.getElementById("view-quantity");
  if (input) input.value = val;
}

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  await loadPoolInfo();
  await loadViewBoosterStats();
  await refreshOrders();
});

// Fetch Device Pool Size & Info from Backend
async function loadPoolInfo() {
  try {
    const res = await fetch("/api/v1/view-booster/pool-info");
    if (!res.ok) return;
    const data = await res.json();
    const count = data.total_unique_devices || 695;

    const navBadge = document.getElementById("nav-pool-size");
    const kpiCount = document.getElementById("kpi-devices-count");
    if (navBadge) navBadge.innerText = `${count} Unique Profiles`;
    if (kpiCount) kpiCount.innerText = `${count} Devices`;
  } catch (err) {
    console.error("Failed to load device pool info", err);
  }
}

// Calculate Total Views Boosted from TiDB Cloud
async function loadViewBoosterStats() {
  try {
    const res = await fetch("/api/v1/orders?limit=100");
    if (!res.ok) return;
    const data = await res.json();
    const orders = data.items || [];

    let totalViews = 0;
    orders.forEach(o => {
      totalViews += (o.delivered_count || 0);
    });

    const kpiViews = document.getElementById("kpi-total-views");
    if (kpiViews) kpiViews.innerText = totalViews;
  } catch (err) {
    console.error("Failed to load view booster stats", err);
  }
}

// Refresh Past Campaigns History Table
async function refreshOrders() {
  const tbody = document.getElementById("orders-table-body");
  if (!tbody) return;

  try {
    const res = await fetch("/api/v1/orders?limit=25");
    const data = await res.json();
    const orders = data.items || [];

    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-6 text-center text-slate-500">No view campaigns recorded yet. Launch your first one above!</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => {
      const isCompleted = o.status === "Completed";
      const badgeClass = isCompleted 
        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";

      const createdDate = o.created_at ? new Date(o.created_at).toLocaleString() : "Just now";

      return `
        <tr class="hover:bg-surface-800/40 transition">
          <td class="px-5 py-3 font-mono text-[11px] text-slate-400">
            <span title="${o.id}">${o.id.substring(0, 8)}...</span>
          </td>
          <td class="px-5 py-3 text-slate-200 truncate max-w-xs" title="${o.target_url}">
            <a href="${o.target_url}" target="_blank" class="hover:text-cyan-400 underline decoration-slate-700">${o.target_url}</a>
          </td>
          <td class="px-5 py-3 text-center font-bold text-white font-mono">
            ${o.delivered_count} / ${o.quantity}
          </td>
          <td class="px-5 py-3 text-center">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeClass}">
              ${o.status}
            </span>
          </td>
          <td class="px-5 py-3 text-slate-400 text-[11px] font-mono">
            ${createdDate}
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-4 text-center text-rose-400">Failed to load history: ${err.message}</td></tr>`;
  }
}

// Handle Launching Real View Campaign
async function handleLaunchViewBoost(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-launch-views");
  const postUrl = document.getElementById("view-target-url").value.trim();
  const quantity = parseInt(document.getElementById("view-quantity").value);
  const dwellSeconds = parseFloat(document.getElementById("view-dwell-time").value);
  const concurrency = parseInt(document.getElementById("view-concurrency").value) || 4;

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Initializing Stealth Workers...`;

  const progressBox = document.getElementById("view-progress-box");
  const heading = document.getElementById("view-progress-heading");
  const badge = document.getElementById("view-status-badge");
  const bar = document.getElementById("view-progress-bar");
  const logsTable = document.getElementById("view-logs-table");

  progressBox.classList.remove("hidden");
  heading.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-cyan-400"></i> Delivering Real Views & Video Watch-Time...`;
  badge.className = "px-3 py-1 rounded-xl text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono";
  badge.innerText = `0 / ${quantity} Delivered (0%)`;
  bar.style.width = "0%";
  logsTable.innerHTML = `<div class="text-slate-400 text-center py-6"><i class="fa-solid fa-satellite-dish fa-spin mr-2 text-cyan-400"></i> Spawning ${concurrency} parallel stealth Playwright browsers with 0 device duplicate...</div>`;

  try {
    const res = await fetch("/api/v1/view-booster/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        post_url: postUrl,
        quantity: quantity,
        dwell_seconds: dwellSeconds,
        concurrency: concurrency
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to launch view campaign");

    showToast(`Campaign launched: ${quantity} real views on Facebook Reel!`);
    pollViewBoostProgress(data.task_id, quantity);
  } catch (err) {
    badge.className = "px-3 py-1 rounded-xl text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono";
    badge.innerText = "Failed";
    heading.innerText = "View booster encountered an error";
    logsTable.innerHTML = `<div class="text-rose-400 p-3">${err.message}</div>`;
    showToast(err.message, true);
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Real Views Campaign`;
  }
}

// Live Status Poller
function pollViewBoostProgress(taskId, totalRequested) {
  if (activeViewBoostTimer) clearInterval(activeViewBoostTimer);

  const btn = document.getElementById("btn-launch-views");
  const heading = document.getElementById("view-progress-heading");
  const badge = document.getElementById("view-status-badge");
  const bar = document.getElementById("view-progress-bar");
  const logsTable = document.getElementById("view-logs-table");

  activeViewBoostTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/view-booster/status/${taskId}`);
      if (!res.ok) return;
      const data = await res.json();

      const delivered = data.delivered || 0;
      const percent = Math.min(100, Math.round((delivered / totalRequested) * 100));

      bar.style.width = `${percent}%`;
      badge.innerText = `${delivered} / ${totalRequested} Delivered (${percent}%)`;

      // Render live stream logs
      if (data.logs && data.logs.length > 0) {
        logsTable.innerHTML = data.logs.slice().reverse().map(log => {
          let deviceIcon = "fa-mobile-screen-button";
          if (log.platform === "Windows") deviceIcon = "fa-desktop";
          else if (log.platform === "macOS") deviceIcon = "fa-laptop";
          else if (log.platform === "iOS") deviceIcon = "fa-apple";

          const isSuccess = log.status === "SUCCESS";
          const statusBadge = isSuccess 
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
            : "bg-rose-500/10 text-rose-400 border-rose-500/20";

          return `
            <div class="p-3 rounded-xl bg-surface-900 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition">
              <div class="flex items-center gap-3">
                <span class="w-7 h-7 rounded-lg bg-cyan-500/15 text-cyan-400 flex items-center justify-center font-bold text-xs">#${log.view_idx}</span>
                <div>
                  <div class="font-bold text-white text-xs flex items-center gap-2">
                    <i class="fa-solid ${deviceIcon} text-slate-400 text-xs"></i>
                    <span>${log.device}</span>
                    <span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">${log.viewport}</span>
                  </div>
                  <div class="text-[11px] text-slate-400 mt-1">
                    Referrer: <strong class="text-pink-400 font-sans">${log.referrer || 'Direct'}</strong> 
                    • Dwell Watch: <strong class="text-emerald-400 font-sans">${log.dwell_seconds}s</strong>
                    ${log.is_video ? `• Video Stream: <strong class="text-cyan-400 font-sans">${log.video_streamed_sec}s</strong>` : ''}
                  </div>
                </div>
              </div>
              <div class="text-right">
                <span class="px-2.5 py-1 rounded-lg text-[10px] font-bold border ${statusBadge}">
                  ${isSuccess ? 'Impression OK' : 'Failed'}
                </span>
                <div class="text-[10px] text-slate-500 mt-1 font-mono">${log.timestamp}</div>
              </div>
            </div>
          `;
        }).join("");
      }

      if (data.status === "COMPLETED") {
        clearInterval(activeViewBoostTimer);
        activeViewBoostTimer = null;
        badge.className = "px-3 py-1 rounded-xl text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono";
        heading.innerHTML = `<i class="fa-solid fa-check-circle text-emerald-400"></i> Campaign Completed! Delivered ${delivered} Real Views on Facebook Reel!`;
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Real Views Campaign`;
        showToast(`Campaign Completed! ${delivered} views delivered across unique devices.`);
        await loadViewBoosterStats();
        await refreshOrders();
      }
    } catch (err) {
      console.error("View booster poll error", err);
    }
  }, 1500);
}
