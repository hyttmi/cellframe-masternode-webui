document.addEventListener("DOMContentLoaded", function () {
    const customView = document.getElementById('custom_view');
    const availableCards = document.getElementById('available_cards');
    const editViewBtn = document.getElementById('edit_view_button');
    const clearStorageBtn = document.getElementById('clear_storage');
    const timestampElements = document.querySelectorAll('[data-timestamp]');

    {% if general_info.websocket_server_port %}
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const host = isLocal ? 'localhost' : window.location.hostname;
    const port = {{ general_info.websocket_server_port }};

    if (port !== 0) {
        const socketUrl = `${protocol}//${host}${window.location.protocol === 'https:' ? '' : `:${port}`}`;
        console.log("Connecting to WebSocket with URL:", socketUrl);
        const socket = new WebSocket(socketUrl);

        socket.onopen = () => console.log("WebSocket connection established.");
        socket.onerror = error => console.error("WebSocket connection error:", error);
        socket.onclose = () => console.log("WebSocket connection closed.");

        socket.onmessage = function (event) {
            let parsed;
            try {
                parsed = JSON.parse(event.data);
            } catch (e) {
                parsed = { type: 'text', data: event.data };
            }

            const message = parsed.type === 'stats_update'
                ? (typeof parsed.data === 'string' ? parsed.data : JSON.stringify(parsed.data, null, 2))
                : parsed.data;

            showToast(message);
        };
    }
    {% endif %}

    const updateLocalStorage = () => {
        const layout = Array.from(customView.children).map(card => card.dataset.id);
        localStorage.setItem('customViewLayout', JSON.stringify(layout));
    };

    const toggleVisibility = () => {
        const isVisible = availableCards.classList.contains('visibility-visible');
        availableCards.classList.toggle('visibility-visible', !isVisible);
        availableCards.classList.toggle('visibility-hidden', isVisible);
        const icon = editViewBtn.querySelector('i');
        icon?.classList.toggle('add_icon', isVisible);
        icon?.classList.toggle('add_icon_disabled', !isVisible);
    };

    const toggleCard = (cardId) => {
        const card = document.querySelector(`[data-id="${cardId}"]`);
        if (!card) return;
        const isInCustomView = card.parentNode === customView;
        const target = isInCustomView ? availableCards : customView;

        card.remove();
        target.appendChild(card);

        const icon = card.querySelector('button i');
        icon?.classList.toggle('fa-plus', isInCustomView);
        icon?.classList.toggle('fa-minus', !isInCustomView);

        updateLocalStorage();
        checkAvailableCards();
        sortCards();
    };

    const checkAvailableCards = () => {
        editViewBtn.style.display = availableCards.children.length === 0 ? 'none' : 'block';
    };

    const initializeSortable = (element, enable) => {
        return new Sortable(element, {
            group: enable ? 'shared' : null,
            animation: 150,
            delay: 150,
            delayOnTouchOnly: true,
            disabled: !enable,
            handle: enable ? '.card-header' : null,
            onEnd: updateLocalStorage
        });
    };

    const savedLayout = JSON.parse(localStorage.getItem('customViewLayout') || "[]");
    savedLayout.forEach(cardId => {
        const card = availableCards.querySelector(`[data-id="${cardId}"]`);
        if (card) customView.appendChild(card);
    });

    initializeSortable(customView, true);
    initializeSortable(availableCards, false);

    editViewBtn.addEventListener('click', toggleVisibility);

    document.querySelectorAll('#custom_view .fa-plus').forEach(icon => {
        icon.classList.replace('fa-plus', 'fa-minus');
    });

    checkAvailableCards();

    function sortCards() {
        const container = document.getElementById('available_cards');
        if (!container) return;
        const cards = Array.from(container.querySelectorAll('.col-12, .col-sm-6, .col-md-4, .col-lg-3'));

        cards.sort((a, b) => {
            const cardA = a.querySelector('.card');
            const cardB = b.querySelector('.card');
            return cardA.clientHeight - cardB.clientHeight;
        });

        cards.forEach(card => container.appendChild(card));
    }

    function formatDate(dateString, short = false) {
        const date = new Date(dateString);
        return short
            ? date.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' })
            : date.toLocaleString(undefined, {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
    }

    timestampElements.forEach(el => {
        const raw = el.getAttribute('data-timestamp');
        if (raw) el.textContent = formatDate(raw);
    });

    const currentVersion = "{{ general_info.current_plugin_version }}";
    const storedVersion = localStorage.getItem("pluginVersion");

    function checkForVersionUpdate() {
        if (!storedVersion) {
            localStorage.setItem("pluginVersion", currentVersion);
            return;
        }
        if (storedVersion !== currentVersion) {
            showChangelogModal();
            localStorage.setItem("pluginVersion", currentVersion);
        }
    }

    function showChangelogModal() {
        const modal = new bootstrap.Modal(document.getElementById("changelogModal"));
        modal.show();
        fetch("https://raw.githubusercontent.com/hyttmi/cellframe-masternode-webui/refs/heads/master/CHANGELOG.md")
            .then(r => r.text())
            .then(data => {
                const rendered = marked.parse(data);
                document.getElementById("changelog").innerHTML = rendered;
            })
            .catch(err => {
                document.getElementById("changelog").innerHTML = `<p>Error loading changelog.</p>`;
                console.error("Failed to load changelog:", err);
            });
    }

    function showToast(message) {
        const toastId = `toast-${Date.now()}`;
        const container = document.getElementById("wsToastContainer");
        container.insertAdjacentHTML("beforeend", `
            <div id="${toastId}" class="toast align-items-center text-center border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body d-flex justify-content-center align-items-center w-100 text-center"><strong>${message}</strong></div>
                </div>
            </div>`);

        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 10000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    clearStorageBtn?.addEventListener("click", () => {
        localStorage.removeItem('customViewLayout');
        localStorage.removeItem('customViewTutorialSeen');
        location.reload();
    });

    checkForVersionUpdate();

    const cliModal = document.getElementById('cli_modal');
    cliModal?.addEventListener('shown.bs.modal', () => {
        document.getElementById('cli_input').focus();
    });

    const tutorialModal = new bootstrap.Modal(document.getElementById("tutorialModal"));
    const tutorialOkBtn = document.getElementById("tutorialOkBtn");
    if (!localStorage.getItem("customViewTutorialSeen")) tutorialModal.show();

    tutorialOkBtn?.addEventListener("click", () => {
        localStorage.setItem("customViewTutorialSeen", "true");
        tutorialModal.hide();
    });

    const restartBtn = document.getElementById("restart_node");
    restartBtn?.addEventListener("click", () => {
        fetch(window.location.href, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'restart' })
        })
        .then(res => res.json())
        .then(data => console.log('Restart Success:', data))
        .catch(err => console.error('Restart Error:', err));
    });

    const cliSendBtn = document.getElementById('cli_send');
    const cliInput = document.getElementById('cli_input');

    cliSendBtn?.addEventListener('click', () => {
        sendCliCommand(cliInput.value);
    });

    async function sendCliCommand(command) {
        if (!command.trim()) return;
        appendCliOutput(command);

        const loadingId = `loading-${Date.now()}`;
        let dotCount = 0;
        let dotInterval = setInterval(() => {
            dotCount = (dotCount + 1) % 4;
            updateCliOutputLine('.'.repeat(dotCount), loadingId);
        }, 500);

        appendCliOutput('', loadingId);

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'cli', command })
            });

            const result = await response.text();
            clearInterval(dotInterval);
            removeCliOutputLine(loadingId);
            appendCliOutput(result);
        } catch (err) {
            clearInterval(dotInterval);
            removeCliOutputLine(loadingId);
            appendCliOutput(`Error: ${err.message}`);
        }
    }

    function appendCliOutput(text, id = null) {
        const output = document.getElementById('cli-output');
        const div = document.createElement('div');
        div.textContent = text;
        if (id) div.id = id;
        output.appendChild(div);
        output.scrollTop = output.scrollHeight;
    }

    function updateCliOutputLine(text, id) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function removeCliOutputLine(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
});