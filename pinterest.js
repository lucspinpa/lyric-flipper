// ==========================================
// PINTEREST BOARDS MODULE
// Lyric sh0p1t & Control Center
// ==========================================

let PINTEREST_DATA = {
  boards: [],
  filteredBoards: [],
  currentBoard: null,
  username: 'lucasdancesthrough' // ← CAMBIAR CON TU USERNAME DE PINTEREST
};

// ==========================================
// INICIALIZACIÓN
// ==========================================

async function initPinterestPage() {
  const today = new Date();
  const dt = new Date();
  document.getElementById('header-date').textContent = dt.toLocaleDateString('es-ES', { 
    day: 'numeric', 
    month: 'long', 
    year: 'numeric' 
  });
  
  // Cargar datos del lunar si existen
  updateLunarData();
  
  // Intentar cargar tableros desde caché local primero
  loadBoardsFromCache();
  
  // Luego sincronizar con Pinterest
  if (shouldRefreshData()) {
    await fetchPinterestBoards();
  }
}

// ==========================================
// FETCH PINTEREST DATA
// ==========================================

async function fetchPinterestBoards() {
  const container = document.getElementById('boards-container');
  
  try {
    // Opción 1: Si tienes un backend que maneja la autenticación de Pinterest
    const response = await fetch('api/pinterest/boards', {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    PINTEREST_DATA.boards = await response.json();
    PINTEREST_DATA.filteredBoards = [...PINTEREST_DATA.boards];
    
    saveBoardsToCache();
    renderBoards();
    
  } catch (error) {
    console.error('Error fetching Pinterest boards:', error);
    // Mostrar interfaz con instrucciones
    showPinterestSetupGuide();
  }
}

// ==========================================
// RENDER BOARDS
// ==========================================

function renderBoards() {
  const container = document.getElementById('boards-container');
  
  if (PINTEREST_DATA.filteredBoards.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📌</div>
        <p>No se encontraron tableros</p>
        <small>Intenta ajustar tus filtros</small>
      </div>
    `;
    return;
  }
  
  const boardsHTML = PINTEREST_DATA.filteredBoards.map(board => createBoardCard(board)).join('');
  container.innerHTML = boardsHTML;
}

function createBoardCard(board) {
  const bgImage = board.image_url || 'linear-gradient(135deg, var(--accent), var(--surface))';
  const imageStyle = bgImage.startsWith('http') 
    ? `background-image: url('${escapeHtml(bgImage)}');` 
    : `background: ${bgImage};`;
  
  return `
    <div class="board-card" onclick="openBoardDetails('${escapeHtml(board.id)}')">
      <div class="board-cover" style="${imageStyle}">
        <div class="board-overlay">
          <span class="pin-icon">📌</span>
        </div>
      </div>
      <div class="board-info">
        <h3 class="board-title">${escapeHtml(board.name)}</h3>
        <p class="board-description">${escapeHtml(board.description || 'Sin descripción')}</p>
        <div class="board-meta">
          <span class="meta-item">
            <span class="meta-icon">📍</span>
            <span>${board.pin_count || 0} pins</span>
          </span>
          <span class="meta-item">
            <span class="meta-icon">👥</span>
            <span>${board.collaborators_count || 1} colaborador${(board.collaborators_count || 1) !== 1 ? 'es' : ''}</span>
          </span>
        </div>
      </div>
    </div>
  `;
}

// ==========================================
// BOARD DETAILS MODAL
// ==========================================

async function openBoardDetails(boardId) {
  const board = PINTEREST_DATA.boards.find(b => b.id === boardId);
  if (!board) return;
  
  PINTEREST_DATA.currentBoard = board;
  const modal = document.getElementById('board-modal');
  const modalBody = document.getElementById('modal-body');
  
  // Contenido mientras carga
  modalBody.innerHTML = `
    <div class="modal-loading">
      <div class="spinner"></div>
      <p>Cargando tablero...</p>
    </div>
  `;
  
  modal.classList.add('active');
  
  // Cargar pins del tablero
  await loadBoardPins(boardId);
}

async function loadBoardPins(boardId) {
  try {
    const response = await fetch(`api/pinterest/boards/${boardId}/pins`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Error loading pins');
    }
    
    const pins = await response.json();
    renderBoardModal(pins);
    
  } catch (error) {
    console.error('Error loading board pins:', error);
    document.getElementById('modal-body').innerHTML = `
      <div class="error-state">
        <p>Error al cargar los pins</p>
        <small>Intenta de nuevo más tarde</small>
      </div>
    `;
  }
}

function renderBoardModal(pins) {
  const board = PINTEREST_DATA.currentBoard;
  const modalBody = document.getElementById('modal-body');
  
  const pinsGrid = pins.length > 0 
    ? pins.map(pin => `
        <a href="${escapeHtml(pin.url)}" target="_blank" class="pin-item">
          <img src="${escapeHtml(pin.image)}" alt="${escapeHtml(pin.title)}" loading="lazy">
          <div class="pin-overlay">
            <p class="pin-title">${escapeHtml(pin.title)}</p>
          </div>
        </a>
      `).join('')
    : '<p class="no-pins">Este tablero no tiene pins aún</p>';
  
  modalBody.innerHTML = `
    <div class="board-modal-header">
      <h2>${escapeHtml(board.name)}</h2>
      <p class="board-modal-desc">${escapeHtml(board.description || '')}</p>
    </div>
    <div class="pins-grid">
      ${pinsGrid}
    </div>
  `;
}

function closeBoardModal() {
  document.getElementById('board-modal').classList.remove('active');
  PINTEREST_DATA.currentBoard = null;
}

// ==========================================
// FILTER & SEARCH
// ==========================================

function filterBoards() {
  const searchTerm = document.getElementById('search-input').value.toLowerCase();
  const showSaved = document.getElementById('filter-saved').checked;
  const showCollaborated = document.getElementById('filter-collaborated').checked;
  
  PINTEREST_DATA.filteredBoards = PINTEREST_DATA.boards.filter(board => {
    const matchesSearch = board.name.toLowerCase().includes(searchTerm) || 
                         (board.description && board.description.toLowerCase().includes(searchTerm));
    
    const isSaved = board.is_owner || board.is_owned;
    const isCollaborated = !isSaved;
    
    const matchesFilter = (showSaved && isSaved) || (showCollaborated && isCollaborated);
    
    return matchesSearch && matchesFilter;
  });
  
  renderBoards();
}

function toggleFilterPanel() {
  const panel = document.getElementById('filter-panel');
  panel.classList.toggle('visible');
}

// ==========================================
// REFRESH & CACHE
// ==========================================

async function refreshBoards() {
  const btn = document.getElementById('btn-refresh-boards');
  btn.disabled = true;
  btn.textContent = 'SYNCING...';
  
  try {
    await fetchPinterestBoards();
    // Guardar timestamp
    localStorage.setItem('pinterest_last_sync', Date.now().toString());
  } finally {
    btn.disabled = false;
    btn.textContent = 'SYNC_BOARDS';
  }
}

function saveBoardsToCache() {
  try {
    localStorage.setItem('pinterest_boards_cache', JSON.stringify(PINTEREST_DATA.boards));
    localStorage.setItem('pinterest_cache_time', Date.now().toString());
  } catch (e) {
    console.warn('Could not save to localStorage:', e);
  }
}

function loadBoardsFromCache() {
  try {
    const cached = localStorage.getItem('pinterest_boards_cache');
    if (cached) {
      PINTEREST_DATA.boards = JSON.parse(cached);
      PINTEREST_DATA.filteredBoards = [...PINTEREST_DATA.boards];
      renderBoards();
    }
  } catch (e) {
    console.warn('Could not load from localStorage:', e);
  }
}

function shouldRefreshData() {
  const lastSync = parseInt(localStorage.getItem('pinterest_cache_time') || '0');
  const oneHourAgo = Date.now() - (60 * 60 * 1000);
  return lastSync < oneHourAgo;
}

// ==========================================
// SETUP GUIDE (Si no hay autenticación)
// ==========================================

function showPinterestSetupGuide() {
  const container = document.getElementById('boards-container');
  container.innerHTML = `
    <div class="setup-guide">
      <div class="setup-icon">📌</div>
      <h2>Integración de Pinterest</h2>
      <p>Para mostrar tus tableros públicos de Pinterest, necesitas:</p>
      <ol class="setup-steps">
        <li>
          <strong>Opción 1: API REST de Pinterest</strong>
          <ul>
            <li>Crear una aplicación en <a href="https://developers.pinterest.com" target="_blank">Pinterest Developers</a></li>
            <li>Obtener tu <code>access_token</code></li>
            <li>Crear un endpoint en tu backend: <code>GET /api/pinterest/boards</code></li>
          </ul>
        </li>
        <li>
          <strong>Opción 2: Web Scraping (Sin API)</strong>
          <ul>
            <li>Usar Python con librerías como <code>requests</code> y <code>BeautifulSoup</code></li>
            <li>Generar JSON con tus tableros públicos</li>
            <li>Guardar en <code>pinterest_data.json</code></li>
          </ul>
        </li>
        <li>
          <strong>Opción 3: Cargar JSON manualmente</strong>
          <ul>
            <li>Crear archivo <code>pinterest_data.json</code> con estructura de tableros</li>
            <li>Los datos se cargarán automáticamente desde el archivo</li>
          </ul>
        </li>
      </ol>
      
      <div class="setup-example">
        <h3>Estructura JSON esperada:</h3>
        <pre><code>[
  {
    "id": "board_id_1",
    "name": "Nombre del Tablero",
    "description": "Descripción opcional",
    "image_url": "https://...",
    "pin_count": 42,
    "collaborators_count": 1,
    "is_owner": true,
    "url": "https://pinterest.com/..."
  }
]</code></pre>
      </div>
      
      <div class="setup-actions">
        <button class="action-btn" onclick="tryLoadPinterestJSON()">
          CARGAR DESDE pinterest_data.json
        </button>
        <a href="https://developers.pinterest.com" target="_blank" class="action-btn">
          DOCUMENTACIÓN API
        </a>
      </div>
    </div>
  `;
}

async function tryLoadPinterestJSON() {
  try {
    const response = await fetch('pinterest_data.json?t=' + Date.now());
    if (response.ok) {
      PINTEREST_DATA.boards = await response.json();
      PINTEREST_DATA.filteredBoards = [...PINTEREST_DATA.boards];
      saveBoardsToCache();
      renderBoards();
    } else {
      alert('No se encontró pinterest_data.json');
    }
  } catch (e) {
    alert('Error al cargar pinterest_data.json: ' + e.message);
  }
}

// ==========================================
// LUNAR PHASE SYNC
// ==========================================

function updateLunarData() {
  const lunarIcon = document.getElementById('lunar-icon');
  const lunarText = document.getElementById('lunar-text');
  
  if (!lunarIcon || !lunarText) return;
  
  const today = new Date();
  const lunar = calculateLunarPhase(today);
  
  lunarIcon.textContent = lunar.icon;
  lunarText.textContent = `${lunar.phaseName} (${lunar.illumination}%)`;
}

function calculateLunarPhase(date) {
  const lunarPhaseDate = new Date(2000, 0, 6);
  const millisecondsPerDay = 1000 * 60 * 60 * 24;
  const lunarCycle = 29.53058867;
  const daysSincePhase = (date - lunarPhaseDate) / millisecondsPerDay;
  const lunarPhaseNumber = daysSincePhase % lunarCycle;
  const illumination = Math.round((1 - Math.cos((2 * Math.PI * lunarPhaseNumber) / lunarCycle)) / 2 * 100);
  
  let phaseName = '', icon = '';
  if (lunarPhaseNumber < 1.84) { phaseName = 'Luna Nueva'; icon = '🌑'; }
  else if (lunarPhaseNumber < 7.38) { phaseName = 'Cuarto Creciente'; icon = '🌒'; }
  else if (lunarPhaseNumber < 14.77) { phaseName = 'Luna Llena'; icon = '🌕'; }
  else if (lunarPhaseNumber < 22.15) { phaseName = 'Cuarto Menguante'; icon = '🌘'; }
  else { phaseName = 'Luna Nueva'; icon = '🌑'; }
  
  return { phaseName, icon, illumination, age: Math.round(lunarPhaseNumber) };
}

// ==========================================
// UTILITIES
// ==========================================

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Exportar funciones globales
window.openBoardDetails = openBoardDetails;
window.closeBoardModal = closeBoardModal;
window.refreshBoards = refreshBoards;
window.filterBoards = filterBoards;
window.toggleFilterPanel = toggleFilterPanel;
window.tryLoadPinterestJSON = tryLoadPinterestJSON;
