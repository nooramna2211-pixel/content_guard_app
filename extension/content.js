(() => {
  const MAX_URL_LENGTH = 8192;
  let lastCheckedUrl = "";
  const pendingForms = new WeakSet();
  const allowNextSubmit = new WeakSet();

  function showBlocked(reason) {
    const target = new URL(chrome.runtime.getURL("blocked.html"));
    target.searchParams.set("reason", reason || "This request matches a Content Guard rule.");
    target.searchParams.set("source", location.hostname);
    location.replace(target.href);
  }

  function checkKeyword(query) {
    if (!query || query.length > MAX_URL_LENGTH) {
      return Promise.resolve({ blocked: false, reason: "" });
    }
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { type: "CONTENT_GUARD_CHECK_KEYWORD", query },
        (result) => {
          if (chrome.runtime.lastError || !result) {
            console.warn("Content Guard keyword check is unavailable.");
            resolve({ blocked: false, reason: "" });
            return;
          }
          resolve(result);
        }
      );
    });
  }

  function searchEngine(url) {
    const host = url.hostname.toLowerCase();
    const google = [
      "google.com",
      "google.co.uk",
      "google.ca",
      "google.com.au",
      "google.co.in",
      "google.de",
      "google.fr",
      "google.com.pk"
    ].some((domain) => host === domain || host.endsWith(`.${domain}`));
    if (google && url.pathname === "/search") return "google";
    if (
      (host === "youtube.com" || host.endsWith(".youtube.com")) &&
      url.pathname === "/results"
    ) {
      return "youtube";
    }
    return "";
  }

  function searchQuery(url, engine) {
    const parameter = engine === "google" ? "q" : "search_query";
    return url.searchParams.get(parameter) || "";
  }

  function enforceGoogleSafeSearch(url, engine) {
    if (engine !== "google" || url.searchParams.get("safe") === "active") {
      return false;
    }
    url.searchParams.set("safe", "active");
    return true;
  }

  async function checkCurrentPage() {
    if (location.protocol !== "http:" && location.protocol !== "https:") return;
    const pageUrl = new URL(location.href);
    const engine = searchEngine(pageUrl);
    if (!engine) {
      lastCheckedUrl = location.href;
      return;
    }
    const query = searchQuery(pageUrl, engine).trim();
    if (!query) {
      lastCheckedUrl = location.href;
      return;
    }
    if (enforceGoogleSafeSearch(pageUrl, engine)) {
      location.replace(pageUrl.href);
      return;
    }
    if (lastCheckedUrl === location.href) return;
    const checkedUrl = location.href;
    lastCheckedUrl = checkedUrl;
    const result = await checkKeyword(query);
    if (location.href !== checkedUrl) return;
    if (result.blocked) showBlocked(result.reason);
  }

  function searchFormDetails(form) {
    const action = new URL(form.action || location.href, location.href);
    const engine = searchEngine(action);
    if (!engine) return null;

    const queryParameter = engine === "google" ? "q" : "search_query";
    const queryValues = [];
    for (const [name, value] of new FormData(form).entries()) {
      if (typeof value === "string" && name.toLowerCase() === queryParameter) {
        queryValues.push(value);
      }
    }
    if (!queryValues.length) return null;

    if (engine === "google") {
      enforceGoogleSafeSearch(action, engine);
      const safeInputs = form.querySelectorAll('input[name="safe" i]');
      if (safeInputs.length) {
        safeInputs.forEach((input) => {
          input.value = "active";
        });
      } else {
        const safeInput = document.createElement("input");
        safeInput.type = "hidden";
        safeInput.name = "safe";
        safeInput.value = "active";
        form.appendChild(safeInput);
      }
      form.action = action.href;
    }
    return { query: queryValues.join(" "), engine };
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (allowNextSubmit.has(form)) {
      allowNextSubmit.delete(form);
      return;
    }
    const details = searchFormDetails(form);
    if (!details) return;
    if (pendingForms.has(form)) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }

    const submitter = event.submitter;
    const submittedFrom = location.href;
    event.preventDefault();
    event.stopImmediatePropagation();
    pendingForms.add(form);
    const result = await checkKeyword(details.query.trim());
    pendingForms.delete(form);
    if (location.href !== submittedFrom) return;
    if (result.blocked) {
      showBlocked(result.reason);
      return;
    }
    allowNextSubmit.add(form);
    if (submitter && form.requestSubmit) {
      form.requestSubmit(submitter);
    } else if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }, true);

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === "CONTENT_GUARD_CHECK_CURRENT") {
      checkCurrentPage();
    }
  });

  window.addEventListener("popstate", checkCurrentPage);
  checkCurrentPage();
})();
