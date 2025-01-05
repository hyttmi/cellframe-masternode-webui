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

                    var weightCtx_{{ network_name }} = document.getElementById('weightChart_{{ network_name }}').getContext('2d')
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
                                            ]
                                        }
                                    },
                                    position: 'top',
                                    title: {
                                        display: true,
                                        color: '#DEE2E6',
                                        padding: 10,
                                    }
                                }
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
    </script>
{% endif %}