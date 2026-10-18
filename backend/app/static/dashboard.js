/**
 * Bot Buddy — Vue 3 Reactive Dashboard Controller
 * Facebook & Reel Organic View & Reach Booster Engine
 */

const { createApp, ref, computed, onMounted, onUnmounted } = Vue;

createApp({
  setup() {
    // Reactive Form State
    const targetUrl = ref("https://www.facebook.com/reel/1767246594345288");
    const quantity = ref(50);
    const dwellSeconds = ref(20);
    const concurrency = ref(4);

    // Engine & System State
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

    // Toast Notification State
    const toast = ref({ show: false, message: "", isError: false });
    let pollerTimer = null;

    // Computed Properties
    const progressPercent = computed(() => {
      if (!currentTotal.value) return 0;
      return Math.min(100, Math.round((currentDelivered.value / currentTotal.value) * 100));
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

    const estimatedTimeRemaining = computed(() => {
      const remaining = isRunning.value 
        ? Math.max(0, currentTotal.value - currentDelivered.value)
        : quantity.value;
      const estSec = Math.ceil((remaining / (concurrency.value || 4)) * dwellSeconds.value);
      return formatSeconds(estSec);
    });

    function formatSeconds(sec) {
      if (sec < 60) return `~${sec}s`;
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return `~${m}m ${s}s`;
    }

    function showToast(msg, isError = false) {
      toast.value = { show: true, message: msg, isError };
      setTimeout(() => {
        toast.value.show = false;
      }, 4000);
    }

    function setPreset(qty, dwell) {
      quantity.value = qty;
      if (dwell) dwellSeconds.value = dwell;
      showToast(`Selected preset: ${qty} Views (${dwellSeconds.value}s watch-time)`);
    }

    function resetToReelUrl() {
      targetUrl.value = "https://www.facebook.com/reel/1767246594345288";
      showToast("Loaded your Harry Potter Reel URL!");
    }

    function copyUrl() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(targetUrl.value);
        showToast("URL copied to clipboard!");
      }
    }

    function getDeviceIcon(platform) {
      if (platform === "Windows") return "fa-brands fa-windows text-blue-400";
      if (platform === "macOS" || platform === "iOS") return "fa-brands fa-apple text-slate-300";
      return "fa-brands fa-android text-emerald-400";
    }

    function formatDate(isoStr) {
      if (!isoStr) return "Just now";
      try {
        const d = new Date(isoStr);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } catch (e) {
        return isoStr;
      }
    }

    function triggerConfetti() {
      if (typeof confetti === "function") {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });
      }
    }

    // Launch Real View Campaign
    async function launchCampaign() {
      if (isRunning.value) return;

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
        if (!res.ok) throw new Error(data.detail || "Failed to launch view campaign");

        currentTaskId.value = data.task_id;
        showToast(`Campaign Started: Delivering ${quantity.value} authentic views on Facebook Reel!`);
        startPolling(data.task_id);
      } catch (err) {
        isRunning.value = false;
        showToast(err.message, true);
      }
    }

    // Polling logic
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
            triggerConfetti();
            showToast(`Campaign Completed! ${data.delivered} views delivered across unique devices.`);
            await loadStats();
            await loadOrders();
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 1500);
    }

    // Fetch Device Pool Size
    async function loadPoolInfo() {
      try {
        const res = await fetch("/api/v1/view-booster/pool-info");
        if (res.ok) {
          const data = await res.json();
          if (data.total_unique_devices) poolSize.value = data.total_unique_devices;
        }
      } catch (e) {}
    }

    // Calculate Total Views Delivered from TiDB Cloud
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

    // Fetch History of Past Campaigns
    async function loadOrders() {
      isLoadingHistory.value = true;
      try {
        const res = await fetch("/api/v1/orders?limit=20");
        if (res.ok) {
          const data = await res.json();
          pastOrders.value = data.items || [];
        }
      } catch (e) {
      } finally {
        isLoadingHistory.value = false;
      }
    }

    // Lifecycle Hooks
    onMounted(() => {
      Promise.all([loadPoolInfo(), loadStats(), loadOrders()]);
    });

    onUnmounted(() => {
      if (pollerTimer) clearInterval(pollerTimer);
    });

    return {
      targetUrl,
      quantity,
      dwellSeconds,
      concurrency,
      poolSize,
      totalDeliveredViews,
      isRunning,
      currentDelivered,
      currentTotal,
      logs,
      activeFilter,
      pastOrders,
      isLoadingHistory,
      toast,
      progressPercent,
      filteredLogs,
      mobileLogsCount,
      desktopLogsCount,
      uniqueDevicesUsedCount,
      estimatedTimeRemaining,
      setPreset,
      resetToReelUrl,
      copyUrl,
      getDeviceIcon,
      formatDate,
      launchCampaign,
      loadOrders
    };
  }
}).mount("#app");
