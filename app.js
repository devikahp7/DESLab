const $ = (id) => document.getElementById(id);
let lastCipher = null;

async function api(path, payload) {
    const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || 'The request failed.');
    }

    return result;
}

async function getJson(path) {
    const response = await fetch(path);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || 'The request failed.');
    }

    return result;
}

let estimateChart = null;
let runsChart = null;

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`;
    if (seconds < 86400) return `${(seconds / 3600).toFixed(0)}h`;
    if (seconds < 31557600) return `${(seconds / 86400).toFixed(0)}d`;
    return `${(seconds / 31557600).toFixed(1)}y`;
}

async function updateEstimateChart() {
    const note = $('estimateNote');

    try {
        const rate = $('rate').value || '10000';
        const estimate = await getJson(`/api/estimate?rate=${encodeURIComponent(rate)}`);

        if (typeof Chart === 'undefined') {
            throw new Error('Chart.js could not be loaded. Check your network connection and reload.');
        }

        const data = {
            labels: estimate.rows.map((row) => `${row.bits} bits`),
            datasets: [
                {
                    label: 'Average search time',
                    data: estimate.rows.map((row) => row.average_seconds),
                    borderColor: '#19a7a1',
                    backgroundColor: '#19a7a1',
                    tension: 0.25
                },
                {
                    label: 'Worst-case search time',
                    data: estimate.rows.map((row) => row.worst_seconds),
                    borderColor: '#db634e',
                    backgroundColor: '#db634e',
                    tension: 0.25
                }
            ]
        };

        if (estimateChart) {
            estimateChart.data = data;
            estimateChart.update();
        } else {
            estimateChart = new Chart($('estimateChart'), {
                type: 'line',
                data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'logarithmic',
                            title: { display: true, text: 'Time' },
                            ticks: { callback: (value) => formatDuration(Number(value)) }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: (context) =>
                                    `${context.dataset.label}: ${formatDuration(context.parsed.y)}`
                            }
                        }
                    }
                }
            });
        }

        note.textContent = estimate.note;
    } catch (error) {
        note.textContent = `ERROR: ${error.message}`;
    }
}

async function updateRunsChart() {
    try {
        const runs = await getJson('/api/results');

        if (typeof Chart === 'undefined') {
            throw new Error('Chart.js could not be loaded.');
        }

        const data = {
            labels: runs.map((_, index) => `Run ${index + 1}`),
            datasets: [{
                label: 'Search attempts',
                data: runs.map((run) => run.attempts),
                backgroundColor: '#d7a441',
                borderColor: '#b48120',
                borderWidth: 1
            }]
        };

        if (runsChart) {
            runsChart.data = data;
            runsChart.update();
        } else {
            runsChart = new Chart($('runsChart'), {
                type: 'bar',
                data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, title: { display: true, text: 'Attempts' } } }
                }
            });
        }
    } catch (error) {
        $('runsChart').setAttribute('aria-label', `Unable to load measured runs: ${error.message}`);
    }
}

$('estimateBtn').onclick = updateEstimateChart;
updateEstimateChart();
updateRunsChart();

$('encryptBtn').onclick = async () => {
    const key = $('key').value.trim();
    const output = $('cipherOut');

    if (key !== '' && !/^[0-9a-fA-F]{16}$/.test(key)) {
        lastCipher = null;
        output.textContent =
            'ERROR: Enter exactly 16 hexadecimal characters for the DES key, or leave the field blank.';
        return;
    }

    try {
        const result = await api('/api/encrypt', {
            message: $('message').value,
            key_hex: key
        });

        lastCipher = result;
        $('key').value = result.key_hex;

        output.textContent =
            `KEY (hex): ${result.key_hex}\n` +
            `IV (base64): ${result.iv_b64}\n` +
            `CIPHERTEXT (base64): ${result.ciphertext_b64}\n\n` +
            result.note;
    } catch (error) {
        output.textContent = 'ERROR: ' + error.message;
    }
};

$('decryptBtn').onclick = async () => {
    const output = $('cipherOut');

    if (!lastCipher) {
        output.textContent = 'ERROR: Encrypt a message before decrypting it.';
        return;
    }

    try {
        const result = await api('/api/decrypt', {
            key_hex: lastCipher.key_hex,
            iv_b64: lastCipher.iv_b64,
            ciphertext_b64: lastCipher.ciphertext_b64
        });

        output.textContent = `PLAINTEXT:\n${result.plaintext}`;
    } catch (error) {
        output.textContent = 'ERROR: ' + error.message;
    }
};

$('runBtn').onclick = async () => {
    const output = $('experimentOut');

    try {
        const result = await api('/api/experiment', {
            target: $('target').value,
            space: $('space').value
        });

        output.textContent =
            `Search ${result.success ? 'found' : 'did not find'} target index ` +
            `${result.target_index} in ${result.attempts} attempts ` +
            `(${result.elapsed_seconds} seconds).`;
        $('runCount').textContent = result.total_runs;

        const row = $('resultsBody').insertRow(0);
        [
            result.total_runs,
            result.key_space,
            result.attempts,
            result.elapsed_seconds,
            result.attempts_per_second ?? 'N/A',
            result.found_index ?? 'Not found'
        ].forEach((value) => {
            row.insertCell().textContent = value;
        });
    } catch (error) {
        output.textContent = 'ERROR: ' + error.message;
    }
};