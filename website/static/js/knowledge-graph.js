// Knowledge Graph Visualization

let graphData = null;
let disciplineMap = null;
let allNodes = [];
let allEdges = [];

document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('knowledge-graph-canvas');
    const loading = document.getElementById('kg-loading');
    const filterDiscipline = document.getElementById('filter-discipline');
    const filterType = document.getElementById('filter-type');

    // Load graph data
    Promise.all([
        fetch('/api/content/graph').then(r => r.json()),
        fetch('/api/content/disciplines').then(r => r.json())
    ]).then(([graph, disciplines]) => {
        graphData = graph;
        disciplineMap = disciplines;
        allNodes = graph.nodes || [];
        allEdges = graph.edges || [];

        loading.style.display = 'none';

        // Update statistics
        updateStatistics(graph);

        // Load discipline overview
        loadDisciplineOverview(disciplines);

        // Draw initial graph
        drawGraph(allNodes, allEdges);

        // Setup filter listeners
        filterDiscipline.addEventListener('change', filterGraph);
        filterType.addEventListener('change', filterGraph);

        // Setup canvas resize listener
        window.addEventListener('resize', debounce(() => drawGraph(getFilteredNodes(), getFilteredEdges()), 250));
    })
    .catch(error => {
        console.error('Error loading knowledge graph:', error);
        loading.innerHTML = '<p style="color: #d32f2f;">Error loading knowledge graph. Please try again later.</p>';
    });

    function filterGraph() {
        const discipline = filterDiscipline.value;
        const type = filterType.value;

        const filteredNodes = allNodes.filter(node => {
            // Filter by type
            if (type && node.type !== type) return false;
            // Filter by discipline
            if (discipline && !node.disciplines.includes(discipline)) return false;
            return true;
        });

        const filteredEdges = allEdges.filter(edge => {
            const sourceInFiltered = filteredNodes.some(n => n.id === edge.source);
            const targetInFiltered = filteredNodes.some(n => n.id === edge.target);
            return sourceInFiltered && targetInFiltered;
        });

        drawGraph(filteredNodes, filteredEdges);
    }

    function getFilteredNodes() {
        const discipline = filterDiscipline.value;
        const type = filterType.value;

        return allNodes.filter(node => {
            if (type && node.type !== type) return false;
            if (discipline && !node.disciplines.includes(discipline)) return false;
            return true;
        });
    }

    function getFilteredEdges() {
        const filteredNodes = getFilteredNodes();
        return allEdges.filter(edge => {
            const sourceInFiltered = filteredNodes.some(n => n.id === edge.source);
            const targetInFiltered = filteredNodes.some(n => n.id === edge.target);
            return sourceInFiltered && targetInFiltered;
        });
    }

    function drawGraph(nodes, edges) {
        // Transform data for visualization
        const visNodes = new vis.DataSet(nodes.map(node => ({
            id: node.id,
            label: node.title,
            title: node.title,
            color: getNodeColor(node),
            shape: node.type === 'blog-post' ? 'dot' : 'box',
            size: node.type === 'blog-post' ? 25 : 35,
            font: { size: 12, face: 'Arial', color: '#000' },
            physics: true
        })));

        const visEdges = new vis.DataSet(edges.map(edge => ({
            from: edge.source,
            to: edge.target,
            color: getEdgeColor(edge.type),
            width: getEdgeWidth(edge.strength),
            title: formatEdgeTitle(edge),
            smooth: { enabled: true, type: 'continuous' }
        })));

        const container = document.getElementById('knowledge-graph-canvas');
        const data = { nodes: visNodes, edges: visEdges };
        const options = {
            physics: {
                enabled: true,
                stabilization: {
                    iterations: 200
                },
                barnesHut: {
                    gravitationalConstant: -26000,
                    centralGravity: 0.3,
                    springLength: 200,
                    springConstant: 0.04
                }
            },
            nodes: {
                borderWidth: 2,
                borderWidthSelected: 3
            },
            edges: {
                arrows: 'to',
                smooth: true
            },
            interaction: {
                navigationButtons: true,
                keyboard: true
            }
        };

        const network = new vis.Network(container, data, options);

        // Click event for nodes
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.find(n => n.id === nodeId);
                if (node) {
                    if (node.type === 'blog-post') {
                        window.location.href = `/blog/${node.slug}`;
                    } else if (node.type === 'project') {
                        // Navigate to project demo
                        const project = graphData.nodes.find(n => n.id === nodeId);
                        if (project) {
                            // Could navigate to project page or featured section
                            console.log('Clicked project:', project);
                        }
                    }
                }
            }
        });
    }

    function getNodeColor(node) {
        if (node.type === 'blog-post') {
            const primaryDiscipline = node.disciplines[0];
            return getDisciplineColor(primaryDiscipline);
        } else {
            // Projects get a slightly different shade
            const primaryDiscipline = node.disciplines[0];
            return getDisciplineColor(primaryDiscipline, true);
        }
    }

    function getDisciplineColor(discipline, isProject = false) {
        const colors = {
            'code': '#1a237e',
            'ai': '#7c3aed',
            'fitness': '#ff8a3d',
            'meta': '#06b6d4'
        };
        const color = colors[discipline] || '#666';

        if (isProject) {
            // Make project colors slightly lighter
            return color + 'CC';
        }
        return color;
    }

    function getEdgeColor(type) {
        const colors = {
            'related-project': '#ff8a3d',
            'shared-discipline': '#7c3aed',
            'shared-tag': '#a0aec0'
        };
        return colors[type] || '#999';
    }

    function getEdgeWidth(strength) {
        const widths = {
            'strong': 3,
            'medium': 2,
            'weak': 1
        };
        return widths[strength] || 1;
    }

    function formatEdgeTitle(edge) {
        let title = `Connection: ${edge.type}`;
        if (edge.disciplines) {
            title += `\nDisciplines: ${edge.disciplines.join(', ')}`;
        }
        if (edge.tags) {
            title += `\nTags: ${edge.tags.join(', ')}`;
        }
        return title;
    }

    function updateStatistics(graph) {
        document.getElementById('stat-nodes').textContent = graph.stats.total_nodes;
        document.getElementById('stat-edges').textContent = graph.stats.total_edges;
        document.getElementById('stat-posts').textContent = graph.stats.posts;
        document.getElementById('stat-projects').textContent = graph.stats.projects;
    }

    function loadDisciplineOverview(disciplines) {
        const grid = document.getElementById('discipline-grid');
        grid.innerHTML = '';

        Object.entries(disciplines).forEach(([key, data]) => {
            const card = document.createElement('div');
            card.className = 'discipline-card';
            card.setAttribute('data-discipline', key);

            const header = document.createElement('div');
            header.className = `discipline-card-header badge-${key}`;
            header.textContent = formatDisciplineName(key);
            card.appendChild(header);

            const content = document.createElement('div');
            content.className = 'discipline-card-content';

            // Add posts
            if (data.posts.length > 0) {
                const postsDiv = document.createElement('div');
                postsDiv.className = 'discipline-section';
                const postsLabel = document.createElement('h4');
                postsLabel.textContent = 'Articles';
                postsDiv.appendChild(postsLabel);
                data.posts.forEach(post => {
                    const link = document.createElement('a');
                    link.href = `/blog/${post.slug}`;
                    link.className = 'discipline-link';
                    link.textContent = post.title;
                    postsDiv.appendChild(link);
                });
                content.appendChild(postsDiv);
            }

            // Add projects
            if (data.projects.length > 0) {
                const projDiv = document.createElement('div');
                projDiv.className = 'discipline-section';
                const projLabel = document.createElement('h4');
                projLabel.textContent = 'Projects';
                projDiv.appendChild(projLabel);
                data.projects.forEach(proj => {
                    const item = document.createElement('div');
                    item.className = 'discipline-item';
                    item.textContent = proj.title;
                    projDiv.appendChild(item);
                });
                content.appendChild(projDiv);
            }

            // Add connection count
            const connDiv = document.createElement('div');
            connDiv.className = 'discipline-connections';
            connDiv.innerHTML = `<strong>${data.connections}</strong> cross-discipline connections`;
            content.appendChild(connDiv);

            card.appendChild(content);
            grid.appendChild(card);
        });
    }

    function formatDisciplineName(key) {
        const names = {
            'code': 'Code & Engineering',
            'ai': 'AI & Learning',
            'fitness': 'Fitness & Discipline',
            'meta': 'Philosophy & Meta'
        };
        return names[key] || key;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
