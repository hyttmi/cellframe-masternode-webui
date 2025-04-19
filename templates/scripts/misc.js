const customView = document.getElementById('custom_view');
const availableCards = document.getElementById('available_cards');
const editViewBtn = document.getElementById('edit_view_button');
const clearStorageBtn = document.getElementById('clear_storage');

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

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
        month: 'numeric',
        day: 'numeric'
    });
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
            const emojiMap = {
                ':sunglasses:': '😎',
            };

            for (const [shortcode, emoji] of Object.entries(emojiMap)) {
                data = data.replaceAll(shortcode, emoji);
            }

            document.getElementById("changelog").innerHTML = `
                <h6>What's New:</h6>
                <pre>${data}</pre>
            `;
        })
        .catch(error => {
            document.getElementById("changelog").innerHTML = `<p>Error loading changelog.</p>`;
            console.error("Failed to load changelog:", error);
        });
}


document.addEventListener("DOMContentLoaded", function () {
    sortCards();
    checkForVersionUpdate();
    const tutorialModal = new bootstrap.Modal(document.getElementById("tutorialModal"));
    const tutorialOkBtn = document.getElementById("tutorialOkBtn");

    if (!localStorage.getItem("customViewTutorialSeen")) {
        tutorialModal.show();
    }

    tutorialOkBtn.addEventListener("click", function () {
        localStorage.setItem("customViewTutorialSeen", "true");
        tutorialModal.hide();
    });
});
