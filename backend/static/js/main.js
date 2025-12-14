document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('voteForm');
  const status = document.getElementById('voteStatus');

  form && form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const candidate = document.getElementById('candidate').value;
    const privateKey = document.getElementById('voter_private_key').value;

    const payload = new URLSearchParams();
    payload.append('candidate', candidate);
    if (privateKey) payload.append('voter_private_key', privateKey);

    const res = await fetch('/vote', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: payload
    });
    const data = await res.json();
    if (res.ok) {
      status.innerHTML = `<div class="alert alert-success">Vote sent! Tx: ${data.tx_hash}</div>`;
    } else {
      status.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
    }
  });

  let chart;
  async function fetchResultsAndUpdate() {
    const r = await fetch('/api/results');
    const items = await r.json();
    const labels = items.map(i => i.name);
    const counts = items.map(i => i.count);

    const ctx = document.getElementById('resultsChart') && document.getElementById('resultsChart').getContext('2d');
    if (!ctx) return;
    if (!chart) {
      chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Votes',
            data: counts
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    } else {
      chart.data.labels = labels;
      chart.data.datasets[0].data = counts;
      chart.update();
    }
  }

  fetchResultsAndUpdate();
  setInterval(fetchResultsAndUpdate, 5000);
});
