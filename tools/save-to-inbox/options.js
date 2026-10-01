const DEFAULT_ENDPOINT = "http://127.0.0.1:27123";

function load() {
  chrome.storage.local.get(["apiKey", "endpoint"], (d) => {
    document.getElementById("apiKey").value = (d && d.apiKey) || "";
    document.getElementById("endpoint").value = (d && d.endpoint) || DEFAULT_ENDPOINT;
  });
}

document.getElementById("save").addEventListener("click", () => {
  const apiKey = document.getElementById("apiKey").value.trim();
  const endpoint = (document.getElementById("endpoint").value.trim() || DEFAULT_ENDPOINT).replace(/\/+$/, "");
  chrome.storage.local.set({ apiKey, endpoint }, () => {
    const ok = document.getElementById("ok");
    ok.textContent = "✅ Хадгалагдлаа";
    setTimeout(() => { ok.textContent = ""; }, 2000);
  });
});

load();
