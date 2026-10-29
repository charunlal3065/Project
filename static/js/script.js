/* ─── Animated Particle Background ─────────────────── */
function initCanvas() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function randBetween(a, b) { return a + Math.random() * (b - a); }

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x  = randBetween(0, W);
      this.y  = randBetween(0, H);
      this.r  = randBetween(0.8, 2.2);
      this.vx = randBetween(-0.18, 0.18);
      this.vy = randBetween(-0.18, 0.18);
      this.alpha = randBetween(0.2, 0.55);
      const hues = [260, 280, 190, 200];
      this.hue = hues[Math.floor(Math.random() * hues.length)];
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < -10 || this.x > W+10 || this.y < -10 || this.y > H+10) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue},80%,75%,${this.alpha})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < 120; i++) particles.push(new Particle());

  // draw connecting lines between nearby particles
  function drawLines() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 90) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(108,99,255,${0.12 * (1 - dist/90)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    drawLines();
    requestAnimationFrame(loop);
  }
  loop();
}

/* ─── Sticky Nav scroll effect ──────────────────────── */
function initNav() {
  const nav = document.querySelector('.land-nav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  });
}

/* ─── Scroll Reveal ─────────────────────────────────── */
function initScrollReveal() {
  const els = document.querySelectorAll('.feat-card, .step, .stat-card, .card');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(28px)';
    el.style.transition = `opacity 0.55s ${i * 0.07}s ease, transform 0.55s ${i * 0.07}s ease`;
    io.observe(el);
  });
}

/* ─── Animated Counter ──────────────────────────────── */
function animateCounter(el, target, suffix='') {
  let current = 0;
  const step  = Math.ceil(target / 40);
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current + suffix;
    if (current >= target) clearInterval(timer);
  }, 30);
}

function initCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const io = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        animateCounter(el, +el.dataset.count, el.dataset.suffix || '');
        io.disconnect();
      }
    });
    io.observe(el);
  });
}

/* ─── Stat Card: animate stat values on dashboard ───── */
function initStatValues() {
  document.querySelectorAll('.stat-value[data-val]').forEach(el => {
    const target  = parseFloat(el.dataset.val);
    const suffix  = el.dataset.suffix || '';
    const isFloat = el.dataset.float === '1';
    let current   = 0;
    const steps   = 40;
    const inc     = target / steps;
    let step      = 0;
    const timer   = setInterval(() => {
      step++;
      current = Math.min(current + inc, target);
      el.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
      if (step >= steps) clearInterval(timer);
    }, 25);
  });
}

/* ─── Password Toggle ───────────────────────────────── */
function initPasswordToggle() {
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.field, .password-wrapper').querySelector('input');
      if (!input) return;
      const isPass = input.type === 'password';
      input.type = isPass ? 'text' : 'password';
      btn.innerHTML = isPass
        ? `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    });
  });
}

/* ─── Button Loading State ──────────────────────────── */
function initFormLoading() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('.btn-primary, .btn-predict');
      if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
      }
    });
  });
}

/* ─── Range Slider Live Display ─────────────────────── */
function initRangeSliders() {
  document.querySelectorAll('.form-range').forEach(input => {
    const display = document.getElementById(input.id + '-val');
    if (display) {
      display.textContent = input.value;
      input.addEventListener('input', () => {
        display.textContent = input.value;
      });
    }
    // Update gradient fill
    function updateFill() {
      const min = +input.min || 0;
      const max = +input.max || 10;
      const pct = ((+input.value - min) / (max - min)) * 100;
      input.style.background = `linear-gradient(to right, #6c63ff ${pct}%, rgba(255,255,255,0.1) ${pct}%)`;
    }
    updateFill();
    input.addEventListener('input', updateFill);
  });
}

/* ─── Score Ring Animation ──────────────────────────── */
function initScoreRing() {
  const ring = document.querySelector('.ring-fill');
  if (!ring) return;
  const score   = parseFloat(ring.dataset.score || 0);
  const circumf = 314; // 2*pi*50
  const offset  = circumf - (score / 100) * circumf;

  // Color by performance
  let color = '#6c63ff';
  if (score >= 75) color = '#34d399';
  else if (score < 60) color = '#f87171';
  ring.style.stroke = color;

  setTimeout(() => {
    ring.style.strokeDashoffset = offset;
  }, 100);

  // Animate the number
  const numEl = document.querySelector('.score-number');
  if (numEl) {
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + 1.5, score);
      numEl.textContent = current.toFixed(1);
      if (current >= score) { numEl.textContent = score.toFixed(2); clearInterval(timer); }
    }, 20);
  }
}

/* ─── Input ripple effect ───────────────────────────── */
function initInputRipple() {
  document.querySelectorAll('.form-input, .field input').forEach(input => {
    input.addEventListener('focus', function() {
      this.style.transition = 'all 0.3s cubic-bezier(0.4,0,0.2,1)';
    });
  });
}

/* ─── Tooltip on table score pills ─────────────────── */
function initTooltips() {
  const tips = {
    'pill-high':   'High Performance ≥ 75%',
    'pill-medium': 'Moderate Risk 60–74%',
    'pill-low':    'Academic Risk < 60%',
  };
  document.querySelectorAll('.score-pill').forEach(el => {
    const cls = [...el.classList].find(c => tips[c]);
    if (cls) el.title = tips[cls];
  });
}

/* ─── Init all ──────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initCanvas();
  initNav();
  initScrollReveal();
  initCounters();
  initStatValues();
  initPasswordToggle();
  initFormLoading();
  initRangeSliders();
  initScoreRing();
  initInputRipple();
  initTooltips();
});
