document.getElementById('syncBtn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  statusEl.style.color = '#38bdf8';
  statusEl.innerText = "Extracting cookie...";

  chrome.cookies.get({ url: 'https://www.pinterest.com', name: '_pinterest_sess' }, async (cookie) => {
    if (!cookie) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Error: Pinterest cookie not found. Pehle log in karein.";
      return;
    }

    statusEl.innerText = "Sending session to Vercel Cloud...";

    try {
      const response = await fetch('https://your-project-name.vercel.app/api/save_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: "group_member_1",
          pinterest_sess: cookie.value
        })
      });

      const resData = await response.json();
      if (resData.status === 'success') {
        statusEl.style.color = '#4ade80';
        statusEl.innerText = "Connected to Vercel Agent! ✅";
      } else {
        throw new Error(resData.message);
      }
    } catch (err) {
      statusEl.style.color = '#f87171';
      statusEl.innerText = "Failed: " + err.message;
    }
  });
});
