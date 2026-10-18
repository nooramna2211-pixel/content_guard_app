const API_BASE = "http://127.0.0.1:5000/api";
const DOMAIN_RULE_ID_START = 10000;
const MAX_DOMAIN_RULES = 5000;
const API_TIMEOUT_MS = 2500;
const ALWAYS_ACCESSIBLE_DOMAINS = [
  "google.com",
  "google.co.uk",
  "google.ca",
  "google.com.au",
  "google.co.in",
  "google.de",
  "google.fr",
  "google.com.pk",
  "youtube.com",
  "youtu.be"
];

async function isEnabled() {
  const { enabled = true } = await chrome.storage.local.get("enabled");
  return enabled;
}

async function fetchJson(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      method: options.method || "GET",
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal
    });
    if (!response.ok) {
      throw new Error(`Content Guard API returned HTTP ${response.status}.`);
    }
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function checkKeyword(query) {
  if (!(await isEnabled())) return { blocked: false, reason: "" };
  try {
    const result = await fetchJson("/check-keywords", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    if (typeof result.blocked !== "boolean" || typeof result.reason !== "string") {
      throw new Error("Content Guard keyword API returned an invalid response.");
    }
    return result;
  } catch (error) {
    console.error("Content Guard could not check this search query:", error);
    return { blocked: false, reason: "" };
  }
}

function isAlwaysAccessibleDomain(domain) {
  return ALWAYS_ACCESSIBLE_DOMAINS.some(
    (root) =>
      domain === root ||
      domain.endsWith(`.${root}`) ||
      root.endsWith(`.${domain}`)
  );
}

async function syncBlockedDomains() {
  if (!(await isEnabled())) {
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    const ownedIds = existing
      .filter((rule) => rule.id >= DOMAIN_RULE_ID_START)
      .map((rule) => rule.id);
    if (ownedIds.length) {
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: ownedIds
      });
    }
    await chrome.storage.local.set({ lastRuleSync: Date.now(), syncedDomainCount: 0 });
    return;
  }
  const result = await fetchJson("/rules");
  if (!Array.isArray(result.domains)) {
    throw new Error("Content Guard rules API returned an invalid domain list.");
  }
  const domains = [...new Set(
    result.domains.filter((domain) =>
      typeof domain === "string" &&
      domain.length > 0 &&
      domain.length <= 253 &&
      /^[a-z0-9.-]+$/i.test(domain) &&
      !isAlwaysAccessibleDomain(domain.toLowerCase())
    )
  )].slice(0, MAX_DOMAIN_RULES);
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const ownedRules = existing.filter((rule) => rule.id >= DOMAIN_RULE_ID_START);
  const addRules = domains.map((domain, index) => ({
    id: DOMAIN_RULE_ID_START + index,
    priority: 10,
    action: {
      type: "redirect",
      redirect: {
        extensionPath: `/blocked.html?reason=${encodeURIComponent(`Blocked domain: ${domain}`)}`
      }
    },
    condition: {
      requestDomains: [domain],
      resourceTypes: ["main_frame"]
    }
  }));
  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: ownedRules.map((rule) => rule.id),
    addRules
  });
  await chrome.storage.local.set({
    lastRuleSync: Date.now(),
    syncedDomainCount: domains.length
  });
}

function supportedUrl(value) {
  try {
    const host = new URL(value).hostname.toLowerCase();
    return [
      "google.com",
      "google.co.uk",
      "google.ca",
      "google.com.au",
      "google.co.in",
      "google.de",
      "google.fr",
      "google.com.pk",
      "youtube.com"
    ].some((domain) => host === domain || host.endsWith(`.${domain}`));
  } catch {
    return false;
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (
    message?.type === "CONTENT_GUARD_CHECK_KEYWORD" &&
    typeof message.query === "string"
  ) {
    checkKeyword(message.query).then(sendResponse);
    return true;
  }
  return false;
});

chrome.webNavigation.onHistoryStateUpdated.addListener(
  (details) => {
    if (details.frameId !== 0 || !supportedUrl(details.url)) return;
    chrome.tabs.sendMessage(
      details.tabId,
      { type: "CONTENT_GUARD_CHECK_CURRENT" },
      () => void chrome.runtime.lastError
    );
  },
  {
    url: [
      { hostSuffix: "google.com" },
      { hostSuffix: "google.co.uk" },
      { hostSuffix: "google.ca" },
      { hostSuffix: "google.com.au" },
      { hostSuffix: "google.co.in" },
      { hostSuffix: "google.de" },
      { hostSuffix: "google.fr" },
      { hostSuffix: "google.com.pk" },
      { hostSuffix: "youtube.com" }
    ]
  }
);

chrome.alarms.create("content-guard-rule-sync", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "content-guard-rule-sync") {
    syncBlockedDomains().catch((error) =>
      console.error("Could not synchronize Content Guard domains:", error)
    );
  }
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get("enabled").then(({ enabled }) => {
    if (enabled === undefined) return chrome.storage.local.set({ enabled: true });
  }).then(syncBlockedDomains).catch((error) =>
    console.error("Content Guard extension setup failed:", error)
  );
});

chrome.runtime.onStartup.addListener(() => {
  syncBlockedDomains().catch((error) =>
    console.error("Could not synchronize Content Guard domains:", error)
  );
});
