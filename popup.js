document.addEventListener('DOMContentLoaded', async () => {
  const stored = await chrome.storage.local.get(['agentUrl', 'gdriveUrl', 'syncStatus']);
  if (stored.agentUrl) document.getElementById('agentUrl').value = stored.agentUrl;
  if (stored.gdriveUrl) document.getElementById('gdriveUrl').value = stored.gdriveUrl;
  
  if (stored.syncStatus) {
    const statusEl = document.getElementById('status');
    statusEl.style.color = '#4ade80';
    statusEl.innerText = stored.syncStatus;
  }
});

document.getElementById('syncBtn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  const agentUrl = document.getElementById('agentUrl').value.trim().replace(/\/$/, '');
  const gdriveUrl = document.getElementById('gdriveUrl').value.trim();

  if (!agentUrl || !gdriveUrl) {
    statusEl.style.color = '#f87171';
    statusEl.innerText = "Error: Fill in both Agent Domain and Drive URL!";
    return;
  }

  statusEl.style.color = '#38bdf8';
  statusEl.innerText = "Checking Pinterest Session...";

  chrome.cookies.get({ url: 'https://www.pinterest.com', name: '_pinterest_sess' }, async (cookie) => {
    if (!cookie) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Error: Pinterest cookie not found. Please log in on Pinterest first.";
      return;
    }

    statusEl.innerText = "Syncing with Cloud Agent...";

    try {
      const response = await fetch(`${agentUrl}/api/save_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gdrive_url: gdriveUrl,
          pinterest_sess: cookie.value
        })
      });

      const resData = await response.json();
      if (response.ok && resData.status === 'success') {
        const successMsg = "Agent Connected & Drive Synced! ✅";
        statusEl.style.color = '#4ade80';
        statusEl.innerText = successMsg;

        await chrome.storage.local.set({ 
          agentUrl, 
          gdriveUrl, 
          syncStatus: successMsg 
        });
      } else {
        throw new Error(resData.message || "Failed to sync.");
      }
    } catch (err) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Failed: " + err.message;
    }
  });
});
