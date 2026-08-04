// Spiderweb cursor trail — canvas overlay, cero dependencias
(function () {
  const canvas = document.createElement('canvas');
  canvas.id = 'web-cursor-canvas';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const MAX_POINTS = 18;      // cuántos puntos guarda el hilo
  const points = [];
  let mouseX = -100, mouseY = -100;

  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    points.push({ x: mouseX, y: mouseY });
    if (points.length > MAX_POINTS) points.shift();
  });

  // "disparo" de red al hacer click
  const shots = [];
  window.addEventListener('mousedown', (e) => {
    shots.push({ x: e.clientX, y: e.clientY, r: 0, alpha: 1 });
  });

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // hilo que sigue al cursor
    ctx.strokeStyle = 'rgba(220, 38, 38, 0.5)'; // --accent-red
    ctx.lineWidth = 1;
    for (let i = 1; i < points.length; i++) {
      const p1 = points[i - 1];
      const p2 = points[i];
      const alpha = i / points.length;
      ctx.beginPath();
      ctx.strokeStyle = `rgba(220, 38, 38, ${alpha * 0.6})`;
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }

    // anillos de "disparo" al hacer click
    for (let i = shots.length - 1; i >= 0; i--) {
      const s = shots[i];
      ctx.beginPath();
      ctx.strokeStyle = `rgba(29, 78, 216, ${s.alpha})`; // --accent-blue
      ctx.lineWidth = 2;
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.stroke();
      s.r += 4;
      s.alpha -= 0.04;
      if (s.alpha <= 0) shots.splice(i, 1);
    }

    requestAnimationFrame(draw);
  }
  draw();
})();

// Cursor custom que sigue al ratón
(function () {
  const cursor = document.createElement('div');
  cursor.id = 'custom-cursor';
  document.body.appendChild(cursor);

  window.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });

  window.addEventListener('mousedown', () => cursor.classList.add('click'));
  window.addEventListener('mouseup', () => cursor.classList.remove('click'));

  // hover automático sobre elementos interactivos
  const interactiveSelector = 'a, button, .card, [role="button"]';
  document.addEventListener('mouseover', (e) => {
    if (e.target.closest(interactiveSelector)) cursor.classList.add('hover');
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(interactiveSelector)) cursor.classList.remove('hover');
  });
})();