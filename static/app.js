document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const urlInput = document.getElementById("url-input");
    const pasteBtn = document.getElementById("paste-btn");
    const downloadBtn = document.getElementById("download-btn");
    const loadingDiv = document.getElementById("loading");
    const errorDiv = document.getElementById("error-message");
    const resultContainer = document.getElementById("result-container");

    // SERVER_DICT and SERVER_LANG are injected by Jinja in base.html
    const dict = window.SERVER_DICT || {};
    const currentLang = window.SERVER_LANG || 'en';

    // Paste from clipboard
    if (pasteBtn) {
        pasteBtn.addEventListener("click", async () => {
            try {
                const text = await navigator.clipboard.readText();
                urlInput.value = text;
            } catch (err) {
                console.error("Failed to read clipboard:", err);
            }
        });
    }

    function showError(msgKey) {
        if (errorDiv) {
            errorDiv.textContent = dict[msgKey] || msgKey;
            errorDiv.classList.remove("hidden");
        }
        if (loadingDiv) loadingDiv.classList.add("hidden");
        if (resultContainer) resultContainer.classList.add("hidden");
    }

    function hideError() {
        if (errorDiv) errorDiv.classList.add("hidden");
    }

    // Process Download
    if (downloadBtn) {
        downloadBtn.addEventListener("click", async () => {
            const url = urlInput.value.trim();
            const formatInput = document.querySelector('input[name="format"]:checked');
            const format = formatInput ? formatInput.value : 'video';

            hideError();
            if (!url) {
                showError("errorEmpty");
                return;
            }

            // Show loading state
            loadingDiv.classList.remove("hidden");
            resultContainer.classList.add("hidden");
            downloadBtn.disabled = true;

            try {
                const response = await fetch("/api/download", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url, format })
                });

                const data = await response.json();

                if (!response.ok) {
                    showError(data.detail || "errorGeneral");
                    return;
                }

                renderResults(data);
            } catch (error) {
                console.error(error);
                showError("errorGeneral");
            } finally {
                loadingDiv.classList.add("hidden");
                downloadBtn.disabled = false;
            }
        });
    }

    function renderResults(data) {
        let dlsHTML = '';
        let mediaTag = '';

        if (data.downloads && data.downloads.length > 0) {
            const ext = data.type === 'audio' ? 'mp3' : 'mp4';
            const dl = data.downloads[0]; // just grab the best one
            const safeTitle = encodeURIComponent(data.title || 'media_download');
            const safeUrl = encodeURIComponent(dl.url);
            const proxyUrl = `/api/proxy_download?url=${safeUrl}&ext=${ext}&title=${safeTitle}`;

            dlsHTML = `
                <a href="${proxyUrl}" class="primary-btn" style="margin-top: 1rem;" download>
                    <i class="fa-solid fa-download"></i> <span>${dict.downloadBtn || 'Download'}</span>
                </a>
            `;

            const fallbackImg = 'https://via.placeholder.com/300x300.png?text=No+Thumbnail';
            const tb = data.thumbnail || fallbackImg;

            if (data.type === 'video') {
                mediaTag = `<video controls playsinline poster="${tb}" style="width: 100%; height: auto; border-radius: 12px; display: block;">
                                <source src="${dl.url}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>`;
            } else {
                mediaTag = `<img src="${tb}" alt="Thumbnail" onerror="this.src='${fallbackImg}'" style="width: 100%; height: 100%; object-fit: cover; display: block;">`;
            }
        }

        resultContainer.innerHTML = `
            <h2 style="margin-bottom: 1.5rem; text-align: center;">${dict.resultsTitle || 'Download Ready'}</h2>
            <div class="result-card" style="flex-direction: column; align-items: center;">
                <div class="result-img" style="width: 100%; max-width: 400px; border-radius: 12px; overflow: hidden; position: relative; border: 1px solid var(--glass-border);">
                    ${mediaTag}
                </div>
                <div class="result-info" style="width: 100%; text-align: center; margin-top: 1rem;">
                    <h3>${data.title}</h3>
                    <p><i class="fa-solid fa-user"></i> ${data.author || dict.authorUnknown}</p>
                    <div class="download-options" style="display: flex; justify-content: center; width: 100%; max-width: 300px; margin: 0 auto;">
                        ${dlsHTML}
                    </div>
                </div>
            </div>
        `;

        resultContainer.classList.remove("hidden");
        // Scroll into view safely handling ad rails layout
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});
