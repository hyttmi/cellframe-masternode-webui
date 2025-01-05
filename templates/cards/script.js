<script>
    document.addEventListener('DOMContentLoaded', function () {

        function removeIconEffect(element) {
            element.classList.remove('icon-effect'); // Remove the bouncing effect on click
        }

        function setActive(selectedItem) {
            var parentCard = selectedItem.closest('.card');
            var navItems = parentCard.querySelectorAll('.nav-item');
            navItems.forEach(function(item) {
                item.classList.remove('active');
            });
            selectedItem.classList.add('active');
        }

        var clearStorageBtn = document.getElementById("clearstorage");

        function toggleLocalStorageBtn() {
            var hasCardsHidden = localStorage.getItem('cfclosed');
            if (!hasCardsHidden) {
                clearStorageBtn.style.display = 'none';
            } else {
                clearStorageBtn.style.display = 'block';
            }
        }

        toggleLocalStorageBtn();

        clearStorageBtn.addEventListener('click', function() {
            localStorage.removeItem('cfclosed');
            location.reload();
        });

        var closedCards = JSON.parse(localStorage.getItem('cfclosed')) || [];
        closedCards.forEach(function (closedId) {
            var closedCard = document.querySelector(`.col-12[data-id="${closedId}"]`);
            if (closedCard) {
                closedCard.remove();
            }
        });

        var sortableElements = document.querySelectorAll('.is_sortable');

        sortableElements.forEach(function (el, index) {
            Sortable.create(el, {
                handle: ".card-header",
                animation: 250,
                easing: "cubic-bezier(1, 0, 0, 1)",
                ghostClass: "ghost",
                group: "cfcards-" + index,
                dataIdAttr: "data-id",
                delay: 100,
                store: {
                    get: function (sortable) {
                        var order = localStorage.getItem(sortable.options.group.name);
                        return order ? order.split('|') : [];
                    },
                    set: function (sortable) {
                        var order = sortable.toArray();
                        localStorage.setItem(sortable.options.group.name, order.join('|'));
                    }
                }
            });
        });

        document.querySelectorAll('.btn-close').forEach(function (button) {
            button.addEventListener('click', function (event) {
                var card = event.target.closest('.col-12');
                if (card) {
                    var cardId = card.getAttribute("data-id");
                    card.classList.add('hidden');

                    card.addEventListener('transitionend', function () {
                        card.remove();
                        var closedCards = JSON.parse(localStorage.getItem('cfclosed')) || [];
                        if (!closedCards.includes(cardId)) {
                            closedCards.push(cardId);
                            localStorage.setItem('cfclosed', JSON.stringify(closedCards));
                        }
                        toggleLocalStorageBtn();
                    }, { once: true });
                }
            });
        });

        function formatDate(dateString) {
            var date = new Date(dateString);
            return date.toLocaleDateString(undefined, {
                month: 'numeric',
                day: 'numeric'
            });
        }

        function updateChart(chart, daysToShow, networkName) {
            if (chart === 'signedBlocksChart') {
                var block_days = Object.keys(signedBlocksData[networkName]).slice(-daysToShow);
                var blocks = Object.values(signedBlocksData[networkName]).slice(-daysToShow);

                var sortedDays = block_days.map(formatDate);
                var sortedBlocks = blocks;

                signedBlocksCharts[networkName].data.labels = sortedDays;
                signedBlocksCharts[networkName].data.datasets[0].data = sortedBlocks;
                signedBlocksCharts[networkName].update();
            } else if (chart === 'rewardsChart') {
                var reward_days = Object.keys(rewardsData[networkName]).slice(-daysToShow);
                var rewards = Object.values(rewardsData[networkName]).slice(-daysToShow);

                var sortedRewardDays = reward_days.map(formatDate);
                var sortedRewards = rewards.map(reward => reward.toString());

                rewardsCharts[networkName].data.labels = sortedRewardDays;
                rewardsCharts[networkName].data.datasets[0].data = sortedRewards;
                rewardsCharts[networkName].update();
            } else if (chart === 'firstSignedBlocksChart') {
                var block_days = Object.keys(firstSignedBlocksData[networkName]).slice(-daysToShow);
                var blocks = Object.values(firstSignedBlocksData[networkName]).slice(-daysToShow);

                var sortedDays = block_days.map(formatDate);
                var sortedBlocks = blocks;

                firstSignedBlocksCharts[networkName].data.labels = sortedDays;
                firstSignedBlocksCharts[networkName].data.datasets[0].data = sortedBlocks;
                firstSignedBlocksCharts[networkName].update();
        }
</script>