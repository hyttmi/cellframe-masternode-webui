const customView = document.getElementById('custom_view');
const availableCards = document.getElementById('available_cards');
const editViewBtn = document.getElementById('edit_view_button');
const clearStorageBtn = document.getElementById('clear_storage')

const updateLocalStorage = () => {
    const customViewCards = Array.from(customView.children).map(card => card.dataset.id);
    localStorage.setItem('customViewLayout', JSON.stringify(customViewCards));
};

const toggleVisibility = () => {
    const isVisible = availableCards.classList.contains('visibility-visible');
    availableCards.classList.toggle('visibility-visible', !isVisible);
    availableCards.classList.toggle('visibility-hidden', isVisible);
    availableCardsSortable.option('disabled', isVisible);

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

const initializeSortable = (element, disabled = false) => {
    return new Sortable(element, {
        group: 'shared',
        animation: 150,
        delay: 150,
        delayOnTouchOnly: true,
        onStart(evt) {
        },
        onAdd(evt) {
            const cardId = evt.item.dataset.id;
            toggleCard(cardId);
            updateLocalStorage();
            checkAvailableCards();
        },
        onRemove(evt) {
            const cardId = evt.item.dataset.id;
            toggleCard(cardId);
            updateLocalStorage();
            checkAvailableCards();
        },
        onEnd() {
            updateLocalStorage();
            checkAvailableCards();
        },
        disabled: disabled,
        handle: '.card-header',
        filter: '.available_cards_heading',
    });
};

const savedLayout = JSON.parse(localStorage.getItem('customViewLayout')) || [];
savedLayout.forEach(cardId => {
    const card = availableCards.querySelector(`[data-id="${cardId}"]`);
    if (card) customView.appendChild(card);
});

const customViewSortable = initializeSortable(customView);
const availableCardsSortable = initializeSortable(availableCards, true);

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
    navItems.forEach(function (item) {
        item.classList.remove('active');
    });
    selectedItem.classList.add('active');
}

clearStorageBtn.addEventListener("click", function (event) {
    localStorage.removeItem('customViewLayout');
    location.reload();
});