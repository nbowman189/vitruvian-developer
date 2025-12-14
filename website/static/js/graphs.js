document.addEventListener('DOMContentLoaded', function() {
    // Use shared navigation logic similar to script.js
    const projectTitleNav = document.getElementById('project-title-nav');
    const fileList = document.getElementById('file-list');
    const backToProjectLink = document.getElementById('back-to-project');

    const projectName = 'Health_and_Fitness';

    // Custom title mappings for specific files
    const customTitles = {
        'check-in-log.md': 'Metrics Log',
        'progress-check-in-log.md': 'Exercise Progress Log'
    };

    // Function to get display title for a file
    function getFileDisplayTitle(filename) {
        return customTitles[filename] || filenameToTitle(filename);
    }

    // Populate project navigation bar
    if (projectTitleNav && fileList) {
        projectTitleNav.textContent = projectToTitle(projectName);

        // Fetch files for the project
        fetch(`/api/project/${projectName}/files`)
            .then(response => response.json())
            .then(files => {
                fileList.innerHTML = '';

                // Add Graphs link (currently active)
                const graphsLi = document.createElement('li');
                const graphsLink = document.createElement('a');
                graphsLink.href = '/health-and-fitness/graphs';
                graphsLink.textContent = 'Graphs';
                graphsLink.classList.add('active');
                graphsLi.appendChild(graphsLink);
                fileList.appendChild(graphsLi);

                // Add file links
                files.forEach(file => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = '#';
                    a.textContent = getFileDisplayTitle(file);
                    a.addEventListener('click', (e) => {
                        e.preventDefault();
                        // Navigate back to main page and load the file
                        // Store the file to load in sessionStorage so the main page can pick it up
                        sessionStorage.setItem('loadProject', projectName);
                        sessionStorage.setItem('loadFile', file);
                        window.location.href = '/';
                    });
                    li.appendChild(a);
                    fileList.appendChild(li);
                });

                // Add GEMINI link at the end
                const geminiLi = document.createElement('li');
                const geminiLink = document.createElement('a');
                geminiLink.href = '#';
                geminiLink.textContent = 'GEMINI';
                geminiLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    sessionStorage.setItem('loadProject', projectName);
                    sessionStorage.removeItem('loadFile');
                    window.location.href = '/';
                });
                geminiLi.appendChild(geminiLink);
                fileList.appendChild(geminiLi);
            })
            .catch(error => console.error('Error fetching project files:', error));
    }

    // Handle back to project link
    if (backToProjectLink) {
        backToProjectLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Store project to load in sessionStorage
            sessionStorage.setItem('loadProject', projectName);
            sessionStorage.removeItem('loadFile');
            window.location.href = '/';
        });
    }

    // Create and populate charts
    const weightChartCanvas = document.getElementById('weightChart');
    const bodyfatChartCanvas = document.getElementById('bodyfatChart');

    if (weightChartCanvas && bodyfatChartCanvas) {
        fetch('/api/health-and-fitness/health_data')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching health data:', data.error);
                    return;
                }

                if (data.weight && data.weight.length > 0) {
                    createChart('weightChart', 'Weight', data.weight, 'Weight (lbs)');
                }

                if (data.bodyfat && data.bodyfat.length > 0) {
                    createChart('bodyfatChart', 'Body Fat %', data.bodyfat, 'Body Fat %');
                }
            })
            .catch(error => console.error('Error fetching health data:', error));
    }

    function createChart(canvasId, chartTitle, data, yAxisLabel) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: chartTitle,
                    data: data,
                    borderColor: 'rgba(90, 103, 216, 1)',
                    backgroundColor: 'rgba(90, 103, 216, 0.05)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: 'rgba(90, 103, 216, 1)',
                    pointBorderColor: 'rgba(255, 255, 255, 1)',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            font: { size: 12 },
                            padding: 15
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                month: 'MMM yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date',
                            font: { size: 12, weight: 'bold' }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: yAxisLabel,
                            font: { size: 12, weight: 'bold' }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
    }
});
