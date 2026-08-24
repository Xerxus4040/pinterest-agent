try {
  const response = await fetch(`${agentUrl}/api/save_session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      gdrive_url: gdriveUrl,
      pinterest_sess: cookie.value
    })
  });

  // Read response as plain text first to prevent JSON parse crash
  const rawText = await response.text();
  let resData;

  try {
    resData = JSON.parse(rawText);
  } catch (jsonErr) {
    throw new Error(`Server returned non-JSON response. Check your Vercel URL or Logs. (Response: ${rawText.substring(0, 40)}...)`);
  }

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
    throw new Error(resData.message || "Failed to sync with Vercel.");
  }
} catch (err) {
  statusEl.style.color = '#f87171';
  statusEl.innerText = "Failed: " + err.message;
}
