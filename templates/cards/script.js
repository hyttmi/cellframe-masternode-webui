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

{% if network_info and network_info.items() %}
<script>
    {% for network_name, network in network_info.items() %}
    {% if network.node_data.nodes %}
    document.addEventListener("DOMContentLoaded", function() {
        var weightChart = weightChart || {};

            var nodeData = [
                {% for node in network.node_data.nodes %}
                {
                    nodeAddr: "{{ node.node_addr }}",
                    effectiveWeight: {{ node.effective_value | float }},
                    isMyNode: {{ node.is_my_node | tojson }},
                    isSovereign: {{ node.is_sovereign | tojson }}
                }
                {% if not loop.last %},{% endif %}
                {% endfor %}
                ];

                nodeData.sort(function(a, b) {
                    return b.effectiveWeight - a.effectiveWeight;
                });

                var nodeLabels = nodeData.map(function(item) {
                    return item.isMyNode ? 'MY NODE' : item.nodeAddr.substring(0,4);
                });

                var effectiveWeights = nodeData.map(function(item) {
                    return item.effectiveWeight;
                });

                var chartData = {
                    labels: nodeLabels,
                    datasets: [
                        {
                            categoryPercentage: 0.9,
                            barPercentage: 0.9,
                            label: 'Effective weight',
                            data: effectiveWeights,
                            backgroundColor: nodeData.map(function(item) {
                                return item.isMyNode
                                ? '#B3A3FF'
                                : item.isSovereign
                                ? '#4751D3'
                                : '#DEE2E6';
                            }),
                            borderWidth: 0
                        }
                    ]
                };

                var weightCtx_{{ network_name }} = document.getElementById('weightChart_{{ network_name }}').getContext('2d');

                weightChart['{{ network_name }}'] = new Chart(weightCtx_{{ network_name }}, {
                    type: 'bar',
                    data: chartData,
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                beginAtZero: true,
                                grid: {
                                    display: true,
                                    color: '#2B2B2B'
                                },
                                ticks: {
                                    color: '#DEE2E6'
                                },
                            },
                            y: {
                                grid: {
                                    display: true,
                                    color: '#2B2B2B'
                                },
                                ticks: {
                                    display: true,
                                    color: '#DEE2E6',
                                    autoSkip: false,
                                    maxRotation: 0,
                                    minRotation: 0
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: true,
                                labels: {
                                    generateLabels: (chart) => {
                                        return [
                                            {
                                                text: 'Effective weight'.toUpperCase(),
                                                fillStyle: '#DEE2E6',
                                                hidden: false,
                                            },
                                            {
                                                text: 'My node'.toUpperCase(),
                                                fillStyle: '#B3A3FF',
                                                hidden: false,
                                            },
                                            {
                                                text: 'Sovereign node'.toUpperCase(),
                                                fillStyle: '#4751D3',
                                                hidden: false,
                                            },
                                        ];
                                    }
                                },
                                position: 'top',
                                title: {
                                    display: true,
                                    color: '#DEE2E6',
                                    padding: 10,
                                }
                            },
                            tooltip: {
                                enabled: true,
                                callbacks: {
                                    label: function(tooltipItem) {
                                    return tooltipItem.raw;
                                }
                            }
                        }
                    }
                }
            });
        });
{% endif %}

                {% if network.all_signed_blocks_dict %}
                    var signedBlocksData = {};
                    signedBlocksData['{{ network_name }}'] = {{ network.all_signed_blocks_dict | tojson }};
                    let signedBlocksKeys = Object.keys(signedBlocksData['{{ network_name }}']);
                    let signedBlocksLastKey = signedBlocksKeys[signedBlocksKeys.length - 1];
                    delete signedBlocksData['{{ network_name }}'][signedBlocksLastKey];
                    var signedBlocksCharts = {};
                    var signedBlocksCtx{{ network_name }} = document.getElementById('signedBlocksChart_{{ network_name }}').getContext('2d');
                    signedBlocksCharts['{{ network_name }}'] = new Chart(signedBlocksCtx{{ network_name }}, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Blocks',
                                data: [],
                                backgroundColor: '#B3A3FF',
                                borderColor: '#B3A3FF',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    grid: {
                                        display: false
                                    },
                                    ticks: {
                                        color: '#B3A3FF'
                                    }
                                },
                                y: {
                                    grid: {
                                        display: false
                                    },
                                    beginAtZero: true,
                                    ticks: {
                                        color: '#B3A3FF'
                                    },
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                }
                            }
                        }
                    });
                    updateChart('signedBlocksChart', 7, '{{ network_name }}');
                {% endif %}

                {% if network.first_signed_blocks_dict %}
                    var firstSignedBlocksData = {};
                    firstSignedBlocksData['{{ network_name }}'] = {{ network.all_signed_blocks_dict | tojson }};
                    let firstSignedBlocksKeys = Object.keys(firstSignedBlocksData['{{ network_name }}']);
                    let firstSignedBlocksLastKey = firstSignedBlocksKeys[firstSignedBlocksKeys.length - 1];
                    delete firstSignedBlocksData['{{ network_name }}'][firstSignedBlocksLastKey];
                    var firstSignedBlocksCharts = {};
                    var firstSignedBlocksCtx{{ network_name }} = document.getElementById('firstSignedBlocksChart_{{ network_name }}').getContext('2d');
                    firstSignedBlocksCharts['{{ network_name }}'] = new Chart(firstSignedBlocksCtx{{ network_name }}, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Blocks',
                                data: [],
                                backgroundColor: '#B3A3FF',
                                borderColor: '#B3A3FF',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    grid: {
                                        display: false
                                    },
                                    ticks: {
                                        color: '#B3A3FF'
                                    }
                                },
                                y: {
                                    grid: {
                                        display: false
                                    },
                                    beginAtZero: true,
                                    ticks: {
                                        color: '#B3A3FF'
                                    },
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                }
                            }
                        }
                    });
                    updateChart('firstSignedBlocksChart', 7, '{{ network_name }}');
                {% endif %}

                {% if network.rewards %}
                    var rewardsData = {};
                    rewardsData['{{ network_name }}'] = {{ network.rewards | tojson }};

                    let rewardsKeys = Object.keys(rewardsData['{{ network_name }}']);
                    let rewardsLastKey = rewardsKeys[rewardsKeys.length - 1];

                    delete rewardsData['{{ network_name }}'][rewardsLastKey];

                    var rewardsCharts = {};
                    var rewardsCtx{{ network_name }} = document.getElementById('rewardsChart_{{ network_name }}').getContext('2d');

                    rewardsCharts['{{ network_name }}'] = new Chart(rewardsCtx{{ network_name }}, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Rewards',
                                data: [],
                                backgroundColor: '#B3A3FF',
                                borderColor: '#B3A3FF',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    grid: {
                                        display: false
                                    },
                                    ticks: {
                                        color: '#B3A3FF'
                                    }
                                },
                                y: {
                                    grid: {
                                        display: false
                                    },
                                    beginAtZero: true,
                                    ticks: {
                                        color: '#B3A3FF'
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(tooltipItem) {
                                            return tooltipItem.raw;
                                        }
                                    }
                                }
                            }
                        }
                    });

                    updateChart('rewardsChart', 7, '{{ network_name }}');
                {% endif %}
            {% endfor %}
    </script>
    {% endif %}
