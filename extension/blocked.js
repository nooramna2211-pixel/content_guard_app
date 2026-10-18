const parameters = new URLSearchParams(location.search);
const reason = parameters.get("reason");
const source = parameters.get("source");

document.getElementById("reason").textContent =
  reason || "This request matches an active Content Guard rule.";
document.getElementById("source").textContent = source ? `Requested site: ${source}` : "";
