window.onload = () => {
    // --- 1. CONFIGURATION AND ELEMENTS (No changes) ---
    // --- 1. CONFIGURACIÓN Y ELEMENTOS (Sin cambios) ---
    const elements = {
        html: document.documentElement,
        body: document.body,
        connectionStatus: document.getElementById('connectionStatus'),
        statusContainer: document.getElementById('statusContainer'),
        loading: document.getElementById('loading'),
        guidesSection: document.getElementById('guidesSection'),
        guidesGrid: document.getElementById('guidesGrid'),
        themeSwitch: document.getElementById('theme-switch'),
    };

    const toolInfo = {
        'Java': { link: 'https://adoptium.net/' }, 'Anaconda': { link: 'https://www.anaconda.com/download' },
        'Node.js': { link: 'https://nodejs.org/' }, 'Go': { link: 'https://go.dev/dl/' },
        'Rust': { link: 'https://www.rust-lang.org/tools/install' }, 'Deno': { link: 'https://deno.land/' },
        'Docker': { link: 'https://www.docker.com/products/docker-desktop/' }, 'Kubernetes (k3s)': { link: 'https://k3s.io/' },
        'Vagrant': { link: 'https://developer.hashicorp.com/vagrant/downloads' }, 'WSL': { link: 'https://learn.microsoft.com/en-us/windows/wsl/install' },
        'Godot': { link: 'https://godotengine.org/download/' }, 'Git': { link: 'https://git-scm.com/download' },
        'Terraform': { link: 'https://developer.hashicorp.com/terraform/downloads' }, 'OpenSSL': { link: 'https://slproweb.com/products/Win32OpenSSL.html' }
    };

    const serviceCategories = {
        databases: { titleKey: 'category-databases', services: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Neo4j'] },
        messaging: { titleKey: 'category-messaging', services: ['Kafka', 'RabbitMQ', 'Mosquitto'] },
        api: { titleKey: 'category-api', services: ['Elasticsearch', 'Traefik Proxy'] },
        security: { titleKey: 'category-security', services: ['HashiCorp Vault'] }
    };

    const toolCategories = {
        runtimes: { titleKey: 'category-runtimes', services: ['Java', 'Anaconda', 'Node.js', 'Go', 'Rust', 'Deno'] },
        containers: { titleKey: 'category-containers', services: ['Docker', 'Kubernetes (k3s)', 'Vagrant', 'WSL'] },
        gaming: { titleKey: 'category-gaming', services: ['Godot'] },
        devops: { titleKey: 'category-devops', services: ['Git', 'Terraform', 'OpenSSL'] }
    };

    // --- 2. THEME LOGIC (No changes) ---
    // --- 2. LÓGICA DEL TEMA (Sin cambios) ---
    const currentTheme = localStorage.getItem("theme") || "dark";
    elements.html.setAttribute("data-theme", currentTheme);
    elements.themeSwitch.checked = currentTheme === "dark";
    elements.themeSwitch.addEventListener("change", () => {
        const newTheme = elements.themeSwitch.checked ? "dark" : "light";
        elements.html.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });

    // --- 3. UI RENDERING LOGIC (No changes) ---
    // --- 3. LÓGICA DE RENDERIZADO (Sin cambios) ---
    function getText(key) {
        const formattedKey = key.replace(/[().]/g, '').replace(/\s/g, '-').toLowerCase();
        return elements.body.getAttribute(`data-text-${formattedKey}`) || key;
    }

    function createHr(container, element) {
        const horizontalLine = document.createElement('hr');
        container.insertBefore(horizontalLine, element);
    }

    function createCategoryTable(titleKey, services, statusData) {
        const categoryServices = services.filter(s => statusData[s]);
        if (categoryServices.length === 0) return null;

        const container = document.createDocumentFragment();
        const title = document.createElement('h6');
        title.textContent = getText(titleKey);
        container.appendChild(title);

        const table = document.createElement('table');
        table.setAttribute('role', 'grid');
        table.innerHTML = `
            <thead>
                <tr>
                    <th scope="col">${getText('service')}</th>
                    <th scope="col">${getText('status')}</th>
                    <th scope="col">${getText('details')}</th>
                    <th scope="col" style="text-align: center;">${getText('actions')}</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        const tbody = table.querySelector('tbody');

        for (const serviceName of categoryServices) {
            const service = statusData[serviceName];
            const row = document.createElement('tr');
            const statusClass = service.installed ? 'status-ok' : 'status-fail';
            const statusText = service.installed ? getText('installed') : getText('not-installed');
            
            const actionsCell = !service.installed && toolInfo[serviceName]
                ? `<a href="${toolInfo[serviceName].link}" target="_blank">${getText('official-guide')}</a>`
                : '';

            row.innerHTML = `
                <td><strong>${service.name}</strong></td>
                <td><span class="status-indicator ${statusClass}"></span>${statusText}</td>
                <td><pre>${service.versionDetails || 'N/A'}</pre></td>
                <td class="actions-cell">${actionsCell}</td>
            `;
            tbody.appendChild(row);
        }
        container.appendChild(table);
        return container;
    }

    function updateUI(statusData) {
        elements.loading.style.display = 'none';
        elements.statusContainer.innerHTML = '';

        const managedTitle = document.createElement('h5');
        managedTitle.textContent = getText('category-managed');
        elements.statusContainer.appendChild(managedTitle);
        createHr(elements.statusContainer, managedTitle.nextSibling);

        for (const key in serviceCategories) {
            const category = serviceCategories[key];
            const placeholderData = {};
            category.services.forEach(s => {
                placeholderData[s] = { name: s, installed: false, versionDetails: 'Not implemented yet' };
            });
            const tableFragment = createCategoryTable(category.titleKey, category.services, placeholderData);
            if (tableFragment) {
                elements.statusContainer.appendChild(tableFragment);
            }
        }

        const espaciador = document.createElement('div');
        espaciador.className = 'espaciador';
        elements.statusContainer.appendChild(espaciador);

        const verifiedTitle = document.createElement('h5');
        verifiedTitle.textContent = getText('category-verified');
        elements.statusContainer.appendChild(verifiedTitle);
        createHr(elements.statusContainer, verifiedTitle.nextSibling);
        
        for (const key in toolCategories) {
            const category = toolCategories[key];
            const tableFragment = createCategoryTable(category.titleKey, category.services, statusData);
            if (tableFragment) {
                elements.statusContainer.appendChild(tableFragment);
            }
        }
    }
    
    // --- 4. NEW WEBSOCKET CONNECTION LOGIC ---
    // --- 4. NUEVA LÓGICA DE CONEXIÓN WEBSOCKET ---
    let socket = null;
    let updateInterval = null;

    function connect() {
        const socketUrl = `ws://${window.location.host}/ws`;
        socket = new WebSocket(socketUrl);

        socket.onopen = () => {
            console.log("WebSocket connection established.");
            elements.connectionStatus.textContent = getText('connected');
            elements.connectionStatus.className = 'connection-status connection-ok';
            
            sendCommand('GET_STATUS');

            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(() => sendCommand('GET_STATUS'), 10000);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("Message received:", data);
            
            if (data.status === 'success' && data.payload && data.payload.type === 'ENVIRONMENT_STATUS') {
                updateUI(data.payload.data);
            }
        };

        socket.onclose = (event) => {
            console.log("WebSocket connection closed. Retrying...", event);
            elements.connectionStatus.textContent = `${getText('error')} (${getText('retrying')})`;
            elements.connectionStatus.className = 'connection-status connection-fail';
            if (updateInterval) clearInterval(updateInterval);
            setTimeout(connect, 5000); // Auto-reconnect
        };

        socket.onerror = (error) => {
            console.error("WebSocket Error:", error);
            elements.connectionStatus.textContent = getText('error');
            elements.connectionStatus.className = 'connection-status connection-fail';
        };
    }

    function sendCommand(commandType) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const commandRequest = {
                command: commandType,
                params: {}
            };
            socket.send(JSON.stringify(commandRequest));
        } else {
            console.warn("Could not send command, WebSocket is not open.");
        }
    }

    connect();
};