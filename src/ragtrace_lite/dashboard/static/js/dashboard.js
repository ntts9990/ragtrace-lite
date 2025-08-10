        function advancedDashboard() {
            return {
                viewMode: 'overview',
                reports: [],
                filteredReports: [],
                selectedReport: null,
                questions: [],
                abSelection: { a: null, b: null },
                abTestResults: null,
                searchQuery: '',
                expandedQuestion: -1,
                commonIssues: [],
                recommendations: [],
                charts: {},
                dateRange: {
                    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                    end: new Date().toISOString().split('T')[0]
                },
                timeSeriesStats: null,
                
                async init() {
                    console.log('Initializing dashboard...');
                    
                    // Initialize time series on page load
                    await this.updateTimeSeriesStats();
                    
                    await this.loadReports();
                    
                    // Auto-select first report if available
                    if (this.filteredReports.length > 0) {
                        await this.selectReport(this.filteredReports[0]);
                    }
                },
                
                async loadReports() {
                    try {
                        const response = await fetch('/api/reports');
                        this.reports = await response.json();
                        this.filterReports();
                    } catch (error) {
                        console.error('Failed to load reports:', error);
                    }
                },
                
                filterReports() {
                    if (this.searchQuery) {
                        this.filteredReports = this.reports.filter(r => 
                            r.dataset_name.toLowerCase().includes(this.searchQuery.toLowerCase())
                        );
                    } else {
                        this.filteredReports = [...this.reports];
                    }
                },
                
                setViewMode(mode) {
                    this.viewMode = mode;
                    if (mode === 'questions' && this.selectedReport) {
                        this.loadQuestions();
                    } else if (mode === 'overview') {
                        // Load time series when switching to overview
                        this.updateTimeSeriesStats();
                    }
                },
                
                async selectReport(report) {
                    this.selectedReport = report;
                    
                    // Load detailed data
                    try {
                        const response = await fetch(`/api/report/${report.run_id}`);
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        const details = await response.json();
                        this.selectedReport = { ...this.selectedReport, ...details };
                        console.log('Report loaded with statistics:', this.selectedReport.statistics);
                        
                        // Time series stats will be loaded on demand when overview mode is viewed
                        
                        this.$nextTick(() => {
                            if (this.viewMode === 'overview') {
                                this.updateCharts();
                            } else if (this.viewMode === 'questions') {
                                this.loadQuestions();
                            }
                        });
                    } catch (error) {
                        console.error('Failed to load report details:', error);
                        // If statistics calculation failed, calculate it here
                        if (this.selectedReport && !this.selectedReport.statistics) {
                            this.calculateStatistics();
                        }
                    }
                },
                
                async loadQuestions() {
                    if (!this.selectedReport) return;
                    
                    try {
                        const response = await fetch(`/api/questions/${this.selectedReport.run_id}`);
                        this.questions = await response.json();
                        this.analyzeQuestions();
                        this.$nextTick(() => {
                            this.createQuestionHeatmap();
                        });
                    } catch (error) {
                        console.error('Failed to load questions:', error);
                    }
                },
                
                analyzeQuestions() {
                    // Find common issues
                    const issueCounts = {};
                    this.questions.forEach(q => {
                        if (q.issues) {
                            q.issues.forEach(issue => {
                                issueCounts[issue] = (issueCounts[issue] || 0) + 1;
                            });
                        }
                    });
                    
                    this.commonIssues = Object.entries(issueCounts)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 5)
                        .map(([issue]) => issue);
                    
                    // Generate recommendations
                    this.recommendations = [
                        '가장 낮은 점수 문항들부터 개선',
                        '공통 문제점 해결을 위한 시스템 조정',
                        '검색 정확도 향상을 위한 임베딩 모델 검토'
                    ];
                },
                
                selectForAB(report, group) {
                    // Toggle selection - if already selected, deselect
                    if (this.abSelection[group]?.run_id === report.run_id) {
                        this.abSelection[group] = null;
                    } else {
                        this.abSelection[group] = report;
                    }
                },
                
                async performABTest() {
                    if (!this.abSelection.a || !this.abSelection.b) {
                        alert('A그룹과 B그룹을 모두 선택해주세요.');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/ab-test', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                run_id_a: this.abSelection.a.run_id,
                                run_id_b: this.abSelection.b.run_id
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        this.abTestResults = await response.json();
                        
                        if (this.abTestResults.error) {
                            alert('A/B 테스트 실행 중 오류: ' + this.abTestResults.error);
                            return;
                        }
                        
                        // Switch to A/B test view to show results
                        this.viewMode = 'ab-test';
                        
                        this.$nextTick(() => {
                            this.createABCharts();
                        });
                    } catch (error) {
                        console.error('Failed to perform A/B test:', error);
                        alert('A/B 테스트 실행 실패: ' + error.message);
                    }
                },
                
                showQuestionDetail(question) {
                    console.log('Showing question detail:', question);
                    this.selectedQuestion = question;
                    this.showQuestionModal = true;
                    
                    // Ensure the modal gets the right data
                    if (!question.metrics) {
                        question.metrics = {
                            faithfulness: question.faithfulness || 0,
                            answer_relevancy: question.answer_relevancy || 0,
                            context_precision: question.context_precision || 0,
                            context_recall: question.context_recall || 0,
                            answer_correctness: question.answer_correctness || 0
                        };
                    }
                    
                    if (!question.contexts && question.raw_contexts) {
                        question.contexts = question.raw_contexts;
                    }
                    
                    console.log('Modal data prepared:', this.selectedQuestion);
                },
                
                async updateTimeSeriesStats() {
                    if (!this.dateRange.start || !this.dateRange.end) return;
                    
                    try {
                        const response = await fetch('/api/time-series', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                start_date: this.dateRange.start,
                                end_date: this.dateRange.end,
                                run_id: this.selectedReport?.run_id
                            })
                        });
                        
                        if (response.ok) {
                            this.timeSeriesStats = await response.json();
                            console.log('Time series stats loaded:', this.timeSeriesStats);
                            this.createTimeSeriesChart();
                        }
                    } catch (error) {
                        console.error('Failed to load time series stats:', error);
                    }
                },
                
                createTimeSeriesChart() {
                    if (!this.timeSeriesStats || !this.timeSeriesStats.dates) return;
                    
                    const canvas = document.getElementById('timeSeriesChart');
                    if (!canvas) return;
                    
                    // Destroy existing chart
                    if (this.charts.timeSeries) {
                        this.charts.timeSeries.destroy();
                    }
                    
                    const ctx = canvas.getContext('2d');
                    this.charts.timeSeries = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: this.timeSeriesStats.dates,
                            datasets: [
                                {
                                    label: '실제 값',
                                    data: this.timeSeriesStats.values,
                                    borderColor: 'rgb(59, 130, 246)',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    tension: 0.1
                                },
                                {
                                    label: '예측 값',
                                    data: this.timeSeriesStats.forecast_values,
                                    borderColor: 'rgb(239, 68, 68)',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    borderDash: [5, 5],
                                    tension: 0.1
                                },
                                {
                                    label: '이동 평균',
                                    data: this.timeSeriesStats.moving_avg,
                                    borderColor: 'rgb(34, 197, 94)',
                                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                    tension: 0.3
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'RAGAS Score 시계열 분석'
                                },
                                legend: {
                                    position: 'top'
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 1
                                }
                            }
                        }
                    });
                },
                
                calculateStatistics() {
                    // Calculate statistics from available metrics
                    if (!this.selectedReport) return;
                    
                    const metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                                   'context_recall', 'answer_correctness'];
                    const scores = [];
                    
                    for (const metric of metrics) {
                        const value = this.selectedReport[metric];
                        if (value !== null && value !== undefined) {
                            scores.push(value);
                        }
                    }
                    
                    if (scores.length > 0) {
                        scores.sort((a, b) => a - b);
                        const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
                        const std = Math.sqrt(scores.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / scores.length);
                        
                        this.selectedReport.statistics = {
                            mean: mean,
                            std: std,
                            min: Math.min(...scores),
                            max: Math.max(...scores),
                            median: scores[Math.floor(scores.length / 2)],
                            q1: scores[Math.floor(scores.length * 0.25)],
                            q3: scores[Math.floor(scores.length * 0.75)],
                            cv: std / mean
                        };
                        console.log('Calculated statistics:', this.selectedReport.statistics);
                    }
                },
                
                updateCharts() {
                    console.log('Updating charts with data:', this.selectedReport);
                    
                    // Destroy existing charts
                    Object.values(this.charts).forEach(chart => {
                        try {
                            chart?.destroy();
                        } catch(e) {
                            console.error('Error destroying chart:', e);
                        }
                    });
                    this.charts = {};
                    
                    // Wait for DOM to update
                    this.$nextTick(() => {
                        // Create radar chart
                        const radarCtx = document.getElementById('metricsRadar');
                        console.log('Radar canvas element:', radarCtx);
                        
                        if (radarCtx && radarCtx.getContext) {
                            try {
                                const ctx = radarCtx.getContext('2d');
                                this.charts.radar = new Chart(ctx, {
                            type: 'radar',
                            data: {
                                labels: ['충실도', '답변 관련성', '컨텍스트 정밀도', '컨텍스트 재현율', '답변 정확도'],
                                datasets: [{
                                    label: '점수',
                                    data: [
                                        this.selectedReport.faithfulness || 0,
                                        this.selectedReport.answer_relevancy || 0,
                                        this.selectedReport.context_precision || 0,
                                        this.selectedReport.context_recall || 0,
                                        this.selectedReport.answer_correctness || 0
                                    ],
                                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                                    borderColor: 'rgba(99, 102, 241, 1)',
                                    borderWidth: 2
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    r: {
                                        beginAtZero: true,
                                        max: 1
                                    }
                                }
                            }
                        });
                                console.log('Radar chart created successfully');
                            } catch(e) {
                                console.error('Error creating radar chart:', e);
                            }
                        }
                        
                        // Create bar chart
                        const barCtx = document.getElementById('metricsBar');
                        console.log('Bar canvas element:', barCtx);
                        
                        if (barCtx && barCtx.getContext) {
                            try {
                                const ctx = barCtx.getContext('2d');
                                this.charts.bar = new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels: ['충실도', '답변 관련성', '컨텍스트 정밀도', '컨텍스트 재현율', '답변 정확도'],
                                datasets: [{
                                    label: '점수',
                                    data: [
                                        this.selectedReport.faithfulness || 0,
                                        this.selectedReport.answer_relevancy || 0,
                                        this.selectedReport.context_precision || 0,
                                        this.selectedReport.context_recall || 0,
                                        this.selectedReport.answer_correctness || 0
                                    ],
                                    backgroundColor: [
                                        'rgba(99, 102, 241, 0.8)',
                                        'rgba(168, 85, 247, 0.8)',
                                        'rgba(34, 197, 94, 0.8)',
                                        'rgba(251, 146, 60, 0.8)',
                                        'rgba(239, 68, 68, 0.8)'
                                    ]
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        max: 1
                                    }
                                }
                            }
                        });
                                console.log('Bar chart created successfully');
                            } catch(e) {
                                console.error('Error creating bar chart:', e);
                            }
                        }
                    });
                },
                
                createQuestionHeatmap() {
                    // Create heatmap using Plotly
                    const metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                                   'context_recall', 'answer_correctness'];
                    
                    const z = this.questions.map(q => 
                        metrics.map(m => q.metrics?.[m] || 0)
                    );
                    
                    const data = [{
                        z: z,
                        x: ['충실도', '답변 관련성', '컨텍스트 정밀도', '컨텍스트 재현율', '답변 정확도'],
                        y: this.questions.map((_, i) => `문항 ${i + 1}`),
                        type: 'heatmap',
                        colorscale: 'RdYlGn',
                        zmin: 0,
                        zmax: 1
                    }];
                    
                    const layout = {
                        margin: { t: 20, r: 20, b: 40, l: 60 },
                        xaxis: { side: 'bottom' },
                        yaxis: { autorange: 'reversed' }
                    };
                    
                    Plotly.newPlot('questionHeatmap', data, layout);
                },
                
                createABCharts() {
                    console.log('Creating A/B charts with results:', this.abTestResults);
                    
                    // Wait for DOM
                    this.$nextTick(() => {
                        // Create comparison charts
                        const compCtx = document.getElementById('abComparisonChart');
                        console.log('A/B comparison canvas:', compCtx);
                        
                        if (compCtx && compCtx.getContext && this.abTestResults) {
                            try {
                                const ctx = compCtx.getContext('2d');
                        const metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                                       'context_recall', 'answer_correctness'];
                        
                                this.charts.abComparison = new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels: metrics.map(m => this.getMetricLabel(m)),
                                datasets: [
                                    {
                                        label: 'A 그룹',
                                        data: metrics.map(m => this.abTestResults[m]?.mean_a || 0),
                                        backgroundColor: 'rgba(59, 130, 246, 0.8)'
                                    },
                                    {
                                        label: 'B 그룹',
                                        data: metrics.map(m => this.abTestResults[m]?.mean_b || 0),
                                        backgroundColor: 'rgba(34, 197, 94, 0.8)'
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        max: 1
                                    }
                                }
                            }
                        });
                                console.log('A/B comparison chart created successfully');
                            } catch(e) {
                                console.error('Error creating A/B chart:', e);
                            }
                        }
                        
                        // Create confidence interval chart
                        this.createConfidenceIntervalChart();
                    });
                },
                
                createConfidenceIntervalChart() {
                    if (!this.abTestResults) return;
                    
                    const metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                                   'context_recall', 'answer_correctness'];
                    
                    const data = [];
                    
                    metrics.forEach(metric => {
                        const result = this.abTestResults[metric];
                        if (result) {
                            // A group
                            data.push({
                                x: [result.mean_a],
                                y: [this.getMetricLabel(metric) + ' (A)'],
                                error_x: {
                                    type: 'data',
                                    array: [result.std_a],
                                    visible: true
                                },
                                type: 'scatter',
                                mode: 'markers',
                                marker: { color: 'blue', size: 10 },
                                name: 'A'
                            });
                            
                            // B group
                            data.push({
                                x: [result.mean_b],
                                y: [this.getMetricLabel(metric) + ' (B)'],
                                error_x: {
                                    type: 'data',
                                    array: [result.std_b],
                                    visible: true
                                },
                                type: 'scatter',
                                mode: 'markers',
                                marker: { color: 'green', size: 10 },
                                name: 'B'
                            });
                        }
                    });
                    
                    const layout = {
                        margin: { t: 20, r: 20, b: 40, l: 120 },
                        xaxis: { range: [0, 1] },
                        showlegend: false
                    };
                    
                    Plotly.newPlot('confidenceIntervalChart', data, layout);
                },
                
                getBestMetric() {
                    const metrics = {
                        'faithfulness': this.selectedReport?.faithfulness || 0,
                        'answer_relevancy': this.selectedReport?.answer_relevancy || 0,
                        'context_precision': this.selectedReport?.context_precision || 0,
                        'context_recall': this.selectedReport?.context_recall || 0,
                        'answer_correctness': this.selectedReport?.answer_correctness || 0
                    };
                    
                    const best = Object.entries(metrics).reduce((a, b) => a[1] > b[1] ? a : b);
                    return `${this.getMetricLabel(best[0])} (${best[1].toFixed(3)})`;
                },
                
                getWorstMetric() {
                    const metrics = {
                        'faithfulness': this.selectedReport?.faithfulness || 0,
                        'answer_relevancy': this.selectedReport?.answer_relevancy || 0,
                        'context_precision': this.selectedReport?.context_precision || 0,
                        'context_recall': this.selectedReport?.context_recall || 0,
                        'answer_correctness': this.selectedReport?.answer_correctness || 0
                    };
                    
                    const worst = Object.entries(metrics).reduce((a, b) => a[1] < b[1] ? a : b);
                    return `${this.getMetricLabel(worst[0])} (${worst[1].toFixed(3)})`;
                },
                
                getMetricLabel(metric) {
                    const labels = {
                        'faithfulness': '충실도',
                        'answer_relevancy': '답변 관련성',
                        'context_precision': '컨텍스트 정밀도',
                        'context_recall': '컨텍스트 재현율',
                        'answer_correctness': '답변 정확도'
                    };
                    return labels[metric] || metric;
                },
                
                getStatusText(status) {
                    const texts = {
                        'good': '우수',
                        'warning': '주의',
                        'poor': '개선필요'
                    };
                    return texts[status] || status;
                },
                
                async exportCurrentView() {
                    if (this.selectedReport) {
                        window.open(`/api/export/${this.selectedReport.run_id}`, '_blank');
                    }
                }
            }
        }
