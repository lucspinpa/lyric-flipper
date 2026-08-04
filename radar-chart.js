// Web Radar — pinta el mood semanal (valence/energy) como gráfico radar SVG
// Lee mood_history desde stats.json (generado por lyric_flipper.py). Cero dependencias.
(function () {
  const container = document.getElementById('web-radar');
  if (!container) return;

  fetch('stats.json')
    .then((r) => r.json())
    .then((data) => {
      const history = data.mood_history || [];
      if (history.length < 2) {
        container.innerHTML = '<p class="radar-empty">necesito más días de datos para dibujar el radar...</p>';
        return;
      }
      renderRadar(history);
    })
    .catch(() => {
      container.innerHTML = '<p class="radar-empty">no se pudo cargar el mood semanal.</p>';
    });

  function renderRadar(history) {
    const size = 320;
    const center = size / 2;
    const maxRadius = center - 46;
    const n = history.length;

    function pointFor(index, value) {
      const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
      const r = maxRadius * value;
      return [center + r * Math.cos(angle), center + r * Math.sin(angle)];
    }

    function polygonPoints(key) {
      return history.map((d, i) => pointFor(i, d[key]).join(',')).join(' ');
    }

    function gridRing(fraction) {
      return history.map((d, i) => pointFor(i, fraction).join(',')).join(' ');
    }

    const dayLabels = history.map((d) => {
      const dt = new Date(d.date + 'T00:00:00');
      return dt.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase();
    });

    let labelsSvg = '';
    history.forEach((d, i) => {
      const [x, y] = pointFor(i, 1.2);
      labelsSvg += `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" class="radar-label">${dayLabels[i]}</text>`;
    });

    let ringsSvg = '';
    [0.25, 0.5, 0.75, 1].forEach((f) => {
      ringsSvg += `<polygon points="${gridRing(f)}" class="radar-ring" />`;
    });

    container.innerHTML = `
      <svg viewBox="0 0 ${size} ${size}" class="radar-svg">
        ${ringsSvg}
        <polygon points="${polygonPoints('valence')}" class="radar-poly radar-valence" />
        <polygon points="${polygonPoints('energy')}" class="radar-poly radar-energy" />
        ${labelsSvg}
      </svg>
      <div class="radar-legend">
        <span class="radar-legend-item"><i class="radar-dot radar-dot-valence"></i>valence (positividad)</span>
        <span class="radar-legend-item"><i class="radar-dot radar-dot-energy"></i>energy (intensidad)</span>
      </div>
    `;
  }
})();
