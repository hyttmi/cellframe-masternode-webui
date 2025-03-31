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

window.onload = function() {
    sortCards();
};
