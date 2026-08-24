document.addEventListener('DOMContentLoaded', async () => {
  const urlInput = document.getElementById('vercelUrl');
  const stored = await chrome.storage.local.get(['vercelUrl']);
  if (stored.vercelUrl) {
    urlInput.value = stored.vercelUrl;
  }
});

document.getElementById('syncBtn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  const rawUrl = document.getElementById('vercelUrl').value.trim();
  const urlInput = rawUrl.replace(/\/$/, '');

  if (!urlInput) {
    statusEl.style.color = '#f87171';
    statusEl.innerText = "Please enter your live Vercel URL!";
    return;
  }

  await chrome.storage.local.set({ vercelUrl: urlInput });

  statusEl.style.color = '#38bdf8';
  statusEl.innerText = "Extracting session cookie...";

  chrome.cookies.get({ url: 'https://www.pinterest.com', name: '_pinterest_sess' }, async (cookie) => {
    if (!cookie) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Error: Pinterest cookie not found. Please log in first.";
      return;
    }

    statusEl.innerText = "Connecting to Vercel Cloud Agent...";

    try {
      const response = await fetch(`${urlInput}/api/save_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: "group_member_1",
          pinterest_sess: cookie.value
        })
      });

      const resData = await response.json();
      if (response.ok && resData.status === 'success') {
        statusEl.style.color = '#4ade80';
        statusEl.innerText = "Connected to Vercel Agent! ✅";
      } else {
        throw new Error(resData.message || "Failed to sync session token.");
      }
    } catch (err) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Failed: " + err.message;
    }
  });
});
