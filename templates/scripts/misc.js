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

let socketUrl;

if (port !== 0) {
    if (window.location.protocol === 'https:') {
        socketUrl = `${protocol}//${host}`;
    } else {
        socketUrl = `${protocol}//${host}:${port}`;
    }

    console.log("Connecting to WebSocket with URL:", socketUrl);
    const socket = new WebSocket(socketUrl);

    socket.onopen = () => {
        console.log("WebSocket connection established.");
    };
    socket.onerror = (error) => {
        console.error("WebSocket connection error:", error);
    };
    socket.onclose = () => {
        console.log("WebSocket connection closed.");
    };

    socket.onmessage = function (event) {
        const msg = event.data;
        let parsed;
        try {
            parsed = JSON.parse(msg);
        } catch (e) {
            parsed = { type: 'text', data: msg };
        }

        let message;
        if (parsed.type === 'stats_update') {
            message = typeof parsed.data === 'string' ? parsed.data : JSON.stringify(parsed.data, null, 2);
        } else {
            message = parsed.data;
        }

        showToast(message);
    };
}
{% endif %}

const updateLocalStorage = () => {
    const customViewCards = Array.from(customView.children).map(card => card.dataset.id);
    localStorage.setItem('customViewLayout', JSON.stringify(customViewCards));
};

const toggleVisibility = () => {
    const isVisible = availableCards.classList.contains('visibility-visible');
    availableCards.classList.toggle('visibility-visible', !isVisible);
    availableCards.classList.toggle('visibility-hidden', isVisible);

    const icon = editViewBtn.querySelector('i');
    icon.classList.toggle('add_icon', isVisible);
    icon.classList.toggle('add_icon_disabled', !isVisible);
};

const toggleCard = (cardId) => {
    const card = document.querySelector(`[data-id="${cardId}"]`);
    const isInCustomView = card.parentNode === customView;
    const targetContainer = isInCustomView ? availableCards : customView;

    card.parentNode.removeChild(card);
    targetContainer.appendChild(card);

    const icon = card.querySelector('button i');
    icon.classList.toggle('fa-plus', isInCustomView);
    icon.classList.toggle('fa-minus', !isInCustomView);

    updateLocalStorage();
    checkAvailableCards();
    sortCards();
};

const checkAvailableCards = () => {
    editViewBtn.style.display = availableCards.children.length === 0 ? 'none' : 'block';
};

const initializeSortable = (element, enableSorting) => {
    return new Sortable(element, {
        group: enableSorting ? 'shared' : null,
        animation: 150,
        delay: 150,
        delayOnTouchOnly: true,
        disabled: !enableSorting,
        handle: enableSorting ? '.card-header' : null,
        onEnd() {
            updateLocalStorage();
        }
    });
};

const savedLayout = JSON.parse(localStorage.getItem('customViewLayout')) || [];
savedLayout.forEach(cardId => {
    const card = availableCards.querySelector(`[data-id="${cardId}"]`);
    if (card) customView.appendChild(card);
});

const customViewSortable = initializeSortable(customView, true);
initializeSortable(availableCards, false);

editViewBtn.addEventListener('click', toggleVisibility);

document.querySelectorAll('#custom_view .fa-plus').forEach(icon => {
    icon.classList.replace('fa-plus', 'fa-minus');
});

checkAvailableCards();

function formatDate(dateString, short = false) {
    const date = new Date(dateString);
    if (short) {
        return date.toLocaleDateString(undefined, {
            month: 'numeric',
            day: 'numeric'
        });
    } else {
        return date.toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }
}

function setActive(selectedItem) {
    var parentCard = selectedItem.closest('.card');
    var navItems = parentCard.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    selectedItem.classList.add('active');
}

clearStorageBtn.addEventListener("click", () => {
    localStorage.removeItem('customViewLayout');
    localStorage.removeItem('customViewTutorialSeen');
    location.reload();
});

function sortCards() {
    let cardsContainer = document.getElementById('available_cards');
    let cardDivs = Array.from(cardsContainer.querySelectorAll('.col-12, .col-sm-6, .col-md-4, .col-lg-3'));

    cardDivs.sort((a, b) => {
        let cardA = a.querySelector('.card');
        let cardB = b.querySelector('.card');
        return cardA.clientHeight - cardB.clientHeight;
    });

    cardDivs.forEach(div => {
        cardsContainer.appendChild(div);
    });
}

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
        .then(response => response.text())
        .then(data => {
            const renderedHtml = marked.parse(data);

            document.getElementById("changelog").innerHTML = `
                ${renderedHtml}
            `;
        })
        .catch(error => {
            document.getElementById("changelog").innerHTML = `<p>Error loading changelog.</p>`;
            console.error("Failed to load changelog:", error);
        });
}

function showToast(message) {
    const toastId = `toast-${Date.now()}`;
    const container = document.getElementById("wsToastContainer");
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-center border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex justify-content-center align-items-center w-100 text-center"><strong>${message}</strong></div>
            </div>
        </div>`;
    container.insertAdjacentHTML("beforeend", toastHTML);

    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 10000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
document.addEventListener("DOMContentLoaded", function () {
    sortCards();
    checkForVersionUpdate();

    timestampElements.forEach(el => {
        const raw = el.getAttribute('data-timestamp');
        if (raw) {
            el.textContent = formatDate(raw);
        }
    });

    const tutorialModal = new bootstrap.Modal(document.getElementById("tutorialModal"));
    const tutorialOkBtn = document.getElementById("tutorialOkBtn");

    if (!localStorage.getItem("customViewTutorialSeen")) {
        tutorialModal.show();
    }

    tutorialOkBtn.addEventListener("click", function () {
        localStorage.setItem("customViewTutorialSeen", "true");
        tutorialModal.hide();
    });

    const restartBtn = document.getElementById("restart_node");
    const cliOutput = document.getElementById('cli_output');
    const cliInput = document.getElementById('cli_input');
    const cliSendBtn = document.getElementById('cli_send');

    if (restartBtn) {
        restartBtn.addEventListener("click", function () {
            fetch(window.location.href, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'restart' })
            })
            .then(response => response.json())
            .then(data => console.log('Restart Success:', data))
            .catch(error => console.error('Restart Error:', error));
        });
    }

    function appendCliOutput(text) {
        const line = document.createElement('div');
        line.textContent = text;
        cliOutput.appendChild(line);
        cliOutput.scrollTop = cliOutput.scrollHeight;
    }

    async function sendCliCommand(command) {
        if (!command.trim()) return;

        appendCliOutput(`${command}`);

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'cli', command })
            });

            const text = await response.text();
            let data = null;

            try {
                data = JSON.parse(text);
            } catch (err) {
                console.error('Failed to parse response as JSON:', err);
            }

            if (!response.ok) {
                const errorMessage = (data && data.error) || text || `${response.status} ${response.statusText}`;
                appendCliOutput(`Error: ${errorMessage}`);
                return;
            }

            if (data && data.output) {
                appendCliOutput(data.output);
            } else if (data && data.error) {
                appendCliOutput(`Error: ${data.error}`);
            } else if (text && !data) {
                appendCliOutput(text);
            } else {
                appendCliOutput('(no output)');
            }

        } catch (error) {
            appendCliOutput(`Fetch error: ${error.message}`);
        }
    }

    if (cliSendBtn) {
        cliSendBtn.addEventListener('click', () => {
            sendCliCommand(cliInput.value);
            cliInput.value = '';
            cliInput.focus();
        });
    }

    if (cliInput) {
        cliInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                e.preventDefault();
                cliSendBtn.click();
            }
        });
    }

    const cliModal = document.getElementById('cli_modal');
    cliModal.addEventListener('shown.bs.modal', function () {
        document.getElementById('cli_input').focus();
    });
});