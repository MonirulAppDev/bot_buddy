/**
 * Bot Buddy — Premium SaaS Social Performance & Campaign Studio
 * Vue 3 Reactive Frontend Controller
 * Enterprise analytics, real-time campaign planner, and distributed edge delivery.
 */

const { createApp, ref, computed, onMounted, onUnmounted } = Vue;

createApp({
  setup() {
    // ----------------------------------------------------
    // Campaign Planning State
    // ----------------------------------------------------
    const targetUrl = ref("https://www.facebook.com/reel/1767246594345288");
    const quantity = ref(50);
    const dwellSeconds = ref(20);
    const concurrency = ref(6);

    // ----------------------------------------------------
    // System & Data State
    // ----------------------------------------------------
    const poolSize = ref(695);
    const totalDeliveredViews = ref(0);
    const isRunning = ref(false);
    const currentTaskId = ref(null);
    const currentDelivered = ref(0);
    const currentTotal = ref(0);
    const logs = ref([]);
    const activeFilter = ref("all");
    const pastOrders = ref([]);
    const isLoadingHistory = ref(false);

    // Table search & filter
    const historySearchQuery = ref("");
    const historyStatusFilter = ref("all");
    const activeChartPeriod = ref("30d");

    // Network & Gateway State
    const proxyStats = ref({
      mode: "auto",
      auto_proxies_count: 0,
      custom_proxies_count: 0,
      total_available: 0,
      is_fetching: false,
      sample_proxies: []
    });
    const proxyMode = ref("auto");
    const customProxiesText = ref("");
    const isImportingProxies = ref(false);
    const isRefreshingProxies = ref(false);
    const showGatewayModal = ref(false);

    // Toast notification state
    const toast = ref({ show: false, message: "", isError: false });
    let pollerTimer = null;
    let proxyStatsTimer = null;

    // ----------------------------------------------------
    // Computed Properties
    // ----------------------------------------------------
    const progressPercent = computed(() => {
      if (!currentTotal.value) return 0;
      return Math.min(100, Math.round((currentDelivered.value / currentTotal.value) * 100));
    });

    const averageRetentionSeconds = computed(() => {
      if (!pastOrders.value.length) return 20;
      const valid = pastOrders.value.filter(o => o.interval_seconds);
      if (!valid.length) return 20;
      const sum = valid.reduce((acc, o) => acc + (o.interval_seconds || 20), 0);
      return Math.round(sum / valid.length);
    });

    const completionRatePercent = computed(() => {
      if (!pastOrders.value.length) return 100;
      const completed = pastOrders.value.filter(o => o.status === "Completed").length;
      return Math.round((completed / pastOrders.value.length) * 100);
    });

    const activeCampaignsCount = computed(() => {
      return pastOrders.value.length;
    });

    const filteredLogs = computed(() => {
      if (activeFilter.value === "mobile") {
        return logs.value.filter(l => l.platform === "Android" || l.platform === "iOS");
      }
      if (activeFilter.value === "desktop") {
        return logs.value.filter(l => l.platform === "Windows" || l.platform === "macOS");
      }
      return logs.value;
    });

    const mobileLogsCount = computed(() => {
      return logs.value.filter(l => l.platform === "Android" || l.platform === "iOS").length;
    });

    const desktopLogsCount = computed(() => {
      return logs.value.filter(l => l.platform === "Windows" || l.platform === "macOS").length;
    });

    const uniqueDevicesUsedCount = computed(() => {
      const set = new Set(logs.value.map(l => l.device));
      return set.size;
    });

    const uniqueNodesUsedCount = computed(() => {
      const set = new Set(logs.value.map(l => l.proxy).filter(p => p && !p.includes("Direct")));
      return set.size;
    });

    const estimatedTimeRemaining = computed(() => {
      const remaining = isRunning.value
        ? Math.max(0, currentTotal.value - currentDelivered.value)
        : quantity.value;
      const estSec = Math.ceil((remaining / (concurrency.value || 4)) * dwellSeconds.value);
      return formatDuration(estSec);
    });

    const totalEstimatedWatchSeconds = computed(() => {
      return quantity.value * dwellSeconds.value;
    });

    const detectedContentType = computed(() => {
      const url = targetUrl.value.toLowerCase();
      if (url.includes("/reel/")) return "Facebook Reel";
      if (url.includes("/watch") || url.includes("video")) return "Facebook Video";
      if (url.includes("/photo") || url.includes("/post")) return "Facebook Post";
      return "Facebook Content Asset";
    });

    // History Table Filtering
    const filteredOrders = computed(() => {
      return pastOrders.value.filter(order => {
        const matchesStatus = historyStatusFilter.value === "all" ||
          order.status.toLowerCase() === historyStatusFilter.value.toLowerCase();

        const query = historySearchQuery.value.trim().toLowerCase();
        const matchesQuery = !query ||
          order.id.toLowerCase().includes(query) ||
          order.target_url.toLowerCase().includes(query);

        return matchesStatus && matchesQuery;
      });
    });

    // Chart SVG Data generation with smooth cubic bezier curve & Y-axis ticks
    const chartData = computed(() => {
      const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Today"];
      const counts = [18, 28, 42, 55, 68, 85, Math.max(98, totalDeliveredViews.value)];
      const maxVal = Math.ceil(Math.max(...counts, 100) / 25) * 25;

      // 940 width, 220 height coordinate space with left margin for Y-axis
      const points = counts.map((val, idx) => {
        const x = Math.round(60 + (idx / (counts.length - 1)) * 880);
        const y = Math.round(200 - (val / maxVal) * 165);
        return { x, y, val, label: days[idx] };
      });

      // Smooth Cubic Bezier Curve
      let curvePath = `M ${points[0].x} ${points[0].y}`;
      for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i];
        const p1 = points[i + 1];
        const cpX = Math.round((p0.x + p1.x) / 2);
        curvePath += ` C ${cpX} ${p0.y}, ${cpX} ${p1.y}, ${p1.x} ${p1.y}`;
      }

      const areaPath = `${curvePath} L ${points[points.length - 1].x} 210 L ${points[0].x} 210 Z`;

      const yTicks = [
        { label: `${maxVal}`, y: 35 },
        { label: `${Math.round(maxVal * 0.75)}`, y: 76 },
        { label: `${Math.round(maxVal * 0.5)}`, y: 118 },
        { label: `${Math.round(maxVal * 0.25)}`, y: 159 },
        { label: "0", y: 200 }
      ];

      return { points, curvePath, areaPath, maxVal, yTicks };
    });

    // ----------------------------------------------------
    // Helper & Utility Methods
    // ----------------------------------------------------
    function formatDuration(sec) {
      if (sec < 60) return `~${sec}s`;
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return s > 0 ? `~${m}m ${s}s` : `~${m}m`;
    }

    function formatNumber(num) {
      return new Intl.NumberFormat().format(num || 0);
    }

    function showToast(msg, isError = false) {
      toast.value = { show: true, message: msg, isError };
      setTimeout(() => {
        toast.value.show = false;
      }, 4500);
    }

    function setPreset(qty, dwell) {
      quantity.value = qty;
      if (dwell) dwellSeconds.value = dwell;
      showToast(`Selected configuration: ${qty} impressions with ${dwellSeconds.value}s target dwell.`);
    }

    function resetToDemoUrl() {
      targetUrl.value = "https://www.facebook.com/reel/1767246594345288";
      showToast("Loaded sample Facebook Reel asset URL.");
    }

    function copyToClipboard(text, label = "Item") {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
        showToast(`${label} copied to clipboard!`);
      }
    }

    function getPlatformIcon(platform) {
      if (platform === "Windows") return "fa-brands fa-windows text-slate-400";
      if (platform === "macOS" || platform === "iOS") return "fa-brands fa-apple text-slate-400";
      return "fa-brands fa-android text-slate-400";
    }

    function formatDate(isoStr) {
      if (!isoStr) return "Just now";
      try {
        const d = new Date(isoStr);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
          " • " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      } catch (e) {
        return isoStr;
      }
    }

    function scrollToSection(id) {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }

    // ----------------------------------------------------
    // Launch Campaign & Polling
    // ----------------------------------------------------
    async function launchCampaign() {
      if (isRunning.value) return;

      if (!targetUrl.value.trim() || !targetUrl.value.includes("facebook.com")) {
        showToast("Please provide a valid Facebook Reel or Post URL", true);
        return;
      }

      isRunning.value = true;
      currentDelivered.value = 0;
      currentTotal.value = quantity.value;
      logs.value = [];

      try {
        const res = await fetch("/api/v1/view-booster/launch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            post_url: targetUrl.value.trim(),
            quantity: quantity.value,
            dwell_seconds: dwellSeconds.value,
            concurrency: concurrency.value
          })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to launch campaign");

        currentTaskId.value = data.task_id;
        showToast(`Campaign initiated: ${quantity.value} impressions scheduled with ${concurrency.value} distribution nodes.`);
        startPolling(data.task_id);
      } catch (err) {
        isRunning.value = false;
        showToast(err.message, true);
      }
    }

    function startPolling(taskId) {
      if (pollerTimer) clearInterval(pollerTimer);

      pollerTimer = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/view-booster/status/${taskId}`);
          if (!res.ok) return;
          const data = await res.json();

          currentDelivered.value = data.delivered || 0;
          if (data.logs) {
            logs.value = data.logs.slice().reverse();
          }

          if (data.status === "COMPLETED") {
            clearInterval(pollerTimer);
            pollerTimer = null;
            isRunning.value = false;
            showToast(`Campaign completed successfully! ${data.delivered} impressions recorded.`);
            await loadStats();
            await loadOrders();
            await loadProxyStats();
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 1500);
    }

    // ----------------------------------------------------
    // Data Loading & Gateway Management
    // ----------------------------------------------------
    async function loadPoolInfo() {
      try {
        const res = await fetch("/api/v1/view-booster/pool-info");
        if (res.ok) {
          const data = await res.json();
          if (data.total_unique_devices) poolSize.value = data.total_unique_devices;
        }
      } catch (e) {}
    }

    async function loadProxyStats() {
      try {
        const res = await fetch("/api/v1/view-booster/proxy-stats");
        if (res.ok) {
          const data = await res.json();
          proxyStats.value = data;
          proxyMode.value = data.mode || "auto";
        }
      } catch (e) {}
    }

    async function updateProxyMode(newMode) {
      try {
        const res = await fetch("/api/v1/view-booster/proxy-mode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: newMode })
        });
        if (res.ok) {
          const data = await res.json();
          proxyMode.value = newMode;
          proxyStats.value = data.stats;
          showToast(`Distribution Gateway switched to: ${newMode.toUpperCase()}`);
        }
      } catch (e) {
        showToast("Failed to switch gateway mode", true);
      }
    }

    async function refreshPublicProxies() {
      isRefreshingProxies.value = true;
      try {
        const res = await fetch("/api/v1/view-booster/proxy-refresh", { method: "POST" });
        if (res.ok) {
          showToast("Refreshed distributed edge endpoints in background.");
          setTimeout(loadProxyStats, 3000);
          setTimeout(loadProxyStats, 8000);
        }
      } catch (e) {
        showToast("Gateway refresh request failed", true);
      } finally {
        isRefreshingProxies.value = false;
      }
    }

    async function importCustomProxies() {
      if (!customProxiesText.value.trim()) {
        showToast("Please provide at least one valid gateway endpoint", true);
        return;
      }
      isImportingProxies.value = true;
      try {
        const res = await fetch("/api/v1/view-booster/proxy-import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ proxies_text: customProxiesText.value })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Imported ${data.imported_count} dedicated gateway endpoints.`);
          proxyStats.value = data.stats;
          proxyMode.value = "custom";
          customProxiesText.value = "";
          showGatewayModal.value = false;
        } else {
          showToast(data.detail || "Failed to import endpoints", true);
        }
      } catch (e) {
        showToast("Error importing endpoints", true);
      } finally {
        isImportingProxies.value = false;
      }
    }

    async function loadStats() {
      try {
        const res = await fetch("/api/v1/orders?limit=100");
        if (res.ok) {
          const data = await res.json();
          let sum = 0;
          (data.items || []).forEach(o => {
            sum += (o.delivered_count || 0);
          });
          totalDeliveredViews.value = sum;
        }
      } catch (e) {}
    }

    async function loadOrders() {
      isLoadingHistory.value = true;
      try {
        const res = await fetch("/api/v1/orders?limit=30");
        if (res.ok) {
          const data = await res.json();
          pastOrders.value = data.items || [];
        }
      } catch (e) {
      } finally {
        isLoadingHistory.value = false;
      }
    }

    // ----------------------------------------------------
    // Lifecycle
    // ----------------------------------------------------
    onMounted(() => {
      Promise.all([loadPoolInfo(), loadProxyStats(), loadStats(), loadOrders()]);
      proxyStatsTimer = setInterval(loadProxyStats, 20000);
    });

    onUnmounted(() => {
      if (pollerTimer) clearInterval(pollerTimer);
      if (proxyStatsTimer) clearInterval(proxyStatsTimer);
    });

    return {
      targetUrl,
      quantity,
      dwellSeconds,
      concurrency,
      poolSize,
      totalDeliveredViews,
      averageRetentionSeconds,
      completionRatePercent,
      activeCampaignsCount,
      isRunning,
      currentDelivered,
      currentTotal,
      logs,
      activeFilter,
      pastOrders,
      isLoadingHistory,
      historySearchQuery,
      historyStatusFilter,
      activeChartPeriod,
      proxyStats,
      proxyMode,
      customProxiesText,
      isImportingProxies,
      isRefreshingProxies,
      showGatewayModal,
      toast,
      progressPercent,
      filteredLogs,
      filteredOrders,
      mobileLogsCount,
      desktopLogsCount,
      uniqueDevicesUsedCount,
      uniqueNodesUsedCount,
      estimatedTimeRemaining,
      totalEstimatedWatchSeconds,
      detectedContentType,
      chartData,
      formatNumber,
      formatDuration,
      setPreset,
      resetToDemoUrl,
      copyToClipboard,
      getPlatformIcon,
      formatDate,
      scrollToSection,
      launchCampaign,
      loadOrders,
      updateProxyMode,
      refreshPublicProxies,
      importCustomProxies
    };
  }
}).mount("#app");
