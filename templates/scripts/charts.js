{% if general_info.template == "cpunk" %}
    let primaryColor = '#F97834';
    let secondaryColor = '#FF9A4D';
{% else %}
    let primaryColor = '#9079FF';
    let secondaryColor = '#B3A3FF';
{% endif %}

{% if network_info and network_info.items() %}
    {% for network_name, network in network_info.items() %}
    {% if "backbone" in network_name | lower %}
        {% set network_name = "BB" %}
    {% elif "kelvpn" in network_name | lower %}
        {% set network_name = "KV" %}
    {% endif %}

        {% if network.node_data.nodes %}
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

            var myNode = nodeData.filter(function(item) {
                return item.isMyNode;
            });

            var otherNodes = nodeData.filter(function(item) {
                return !item.isMyNode;
            });

            otherNodes.sort(function(a, b) {
                return b.effectiveWeight - a.effectiveWeight;
            });

            var topNodes = otherNodes.slice(0, 15).concat(myNode);

            var nodeLabels = topNodes.map(function(item) {
                return item.isMyNode ? 'MY NODE' : item.nodeAddr
            });

            var effectiveWeights = topNodes.map(function(item) {
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
                        backgroundColor: topNodes.map(function(item) {
                            return item.isMyNode ? secondaryColor : primaryColor;
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
                    indexAxis: 'x',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            grid: {
                                display: false
                            },
                            ticks: {
                                display: false,
                                color: primaryColor,
                                font: {
                                    size: 13,
                                    family: 'Rubik'
                                  }
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                display: true,
                                color: primaryColor,
                                autoSkip: false,
                                maxRotation: 0,
                                minRotation: 0,
                                font: {
                                    size: 13,
                                    family: 'Rubik'
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false,
                            labels: {
                                color: primaryColor,
                                fillStyle: primaryColor,
                                font: {
                                  size: 13,
                                  family: 'Rubik'
                                }
                            },
                            position: 'bottom',
                            title: {
                                display: true,
                                color: primaryColor
                            }
                        },
                        tooltip: {
                            enabled: true,
                            titleFont: {
                                size: 13,
                                family: 'Rubik'
                            },
                            bodyFont: {
                                size: 13,
                                family: 'Rubik'
                            },
                            callbacks: {
                                label: function(tooltipItem) {
                                    return tooltipItem.raw;
                                }
                            }
                        }
                    }
                }
            });
        {% endif %}

        {% set chartTypes = [
            {'data': network.all_signed_blocks_dict, 'chart_id': 'signedBlocks', 'label': 'Blocks'},
            {'data': network.first_signed_blocks_dict, 'chart_id': 'firstSignedBlocks', 'label': 'First Signed Blocks'},
            {'data': network.rewards, 'chart_id': 'rewards', 'label': 'Rewards'},
            {'data': network.sovereign_rewards, 'chart_id': 'sovereignRewards', 'label': 'Sovereign Rewards'}
        ] %}

        function updateChart(chart, daysToShow, networkName) {
            const chartMapping = {
                {% for chart in chartTypes %}
                    {% if chart.data %}
                        {{ chart.chart_id }}Chart: {
                            data: {{ chart.chart_id }}Data,
                            chart: {{ chart.chart_id }}Charts
                        },
                    {% endif %}
                {% endfor %}
            };

            if (chart in chartMapping) {
                const { data, chart: chartObject, mapValues } = chartMapping[chart];
                const days = Object.keys(data[networkName]).slice(-daysToShow);
                const values = Object.values(data[networkName]).slice(-daysToShow);

                const sortedDays = days.map(day => formatDate(day, true));
                const sortedValues = mapValues ? values.map(mapValues) : values;

                chartObject[networkName].data.labels = sortedDays;
                chartObject[networkName].data.datasets[0].data = sortedValues;
                chartObject[networkName].update();
            }
        }

        {% for chart in chartTypes %}
            {% if chart.data %}
                var {{ chart.chart_id }}Data = {};
                {{ chart.chart_id }}Data['{{ network_name }}'] = {{ chart.data | tojson }};
                var {{ chart.chart_id }}Charts = {};
                var {{ chart.chart_id }}Ctx{{ network_name }} = document.getElementById('{{ chart.chart_id }}Chart_{{ network_name }}').getContext('2d');
                {{ chart.chart_id }}Charts['{{ network_name }}'] = new Chart({{ chart.chart_id }}Ctx{{ network_name }}, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: '{{ chart.label }}',
                            data: [],
                            backgroundColor: primaryColor,
                            borderColor: primaryColor,
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
                                    color: primaryColor,
                                    font: {
                                        size: 13,
                                        family: 'Rubik'
                                    },
                                }
                            },
                            y: {
                                grid: {
                                    display: false
                                },
                                beginAtZero: true,
                                ticks: {
                                    color: primaryColor,
                                    precision: 0,
                                    font: {
                                        size: 13,
                                        family: 'Rubik'
                                    }
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
                                },
                                titleFont: {
                                    size: 13,
                                    family: 'Rubik'
                                },
                                bodyFont: {
                                    size: 13,
                                    family: 'Rubik'
                                }
                            }
                        }
                    }
                });
                updateChart('{{ chart.chart_id }}Chart', 7, '{{ network_name }}');
            {% endif %}
        {% endfor %}
    {% endfor %}
{% endif %}
