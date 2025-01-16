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
                return item.isMyNode ? 'MY NODE' : item.nodeAddr;
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
                        backgroundColor: '#B3A3FF',
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
                                color: '#B3A3FF',
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
                                color: '#B3A3FF',
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
                                color: '#B3A3FF',
                                fillStyle: '#B3A3FF',
                                font: {
                                    size: 13,
                                    family: 'Rubik'
                                }
                            },
                            position: 'bottom',
                            title: {
                                display: true,
                                color: '#B3A3FF'
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
            {'data': network.rewards, 'chart_id': 'rewards', 'label': 'Rewards'}
        ] %}

        {% if network.rewards %}
            var rewardsData = {};
            rewardsData['{{ network_name }}'] = {{ network.rewards | tojson }};
            var sovereignRewardsData = {};
            sovereignRewardsData['{{ network_name }}'] = {{ network.rewards | tojson }};
            var rewardsCharts = {};
            var rewardsCtx{{ network_name }} = document.getElementById('rewardsChart_{{ network_name }}').getContext('2d');
            rewardsCharts['{{ network_name }}'] = new Chart(rewardsCtx{{ network_name }}, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Rewards',
                            data: [],
                            backgroundColor: '#B3A3FF',
                            borderColor: '#B3A3FF',
                            borderWidth: 1
                        },
                        {
                            label: 'Sovereign Rewards',
                            data: [],
                            backgroundColor: '#A3B3FF',
                            borderColor: '#A3B3FF',
                            borderWidth: 1
                        }
                    ]
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
                                color: '#B3A3FF',
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
                            beginAtZero: true,
                            ticks: {
                                color: '#B3A3FF',
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
                            display: true
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

            updateChart('rewardsChart', 7, '{{ network_name }}');
        {% endif %}

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
                                    color: '#B3A3FF',
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
                                beginAtZero: true,
                                ticks: {
                                    color: '#B3A3FF',
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
