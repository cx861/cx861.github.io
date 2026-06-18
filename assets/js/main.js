/**
 * 考研笔记 - 交互功能模块 v4
 * 支持：深色模式、移动端汉堡菜单、滚动进度条、入场动画、涟漪效果、平滑滚动、TOC侧边栏
 */
(function () {
  'use strict';

  /* ====== 深色模式管理 ====== */
  const SafeStorage = {
    get(key) {
      try {
        return localStorage.getItem(key);
      } catch {
        return null;
      }
    },

    set(key, value) {
      try {
        localStorage.setItem(key, value);
        return true;
      } catch {
        return false;
      }
    }
  };

  const Media = {
    query(query) {
      return window.matchMedia ? window.matchMedia(query) : null;
    },

    onChange(mediaQuery, handler) {
      if (!mediaQuery) return;
      if (typeof mediaQuery.addEventListener === 'function') {
        mediaQuery.addEventListener('change', handler);
      } else if (typeof mediaQuery.addListener === 'function') {
        mediaQuery.addListener(handler);
      }
    }
  };

  const ThemeManager = {
    KEY: 'kaoyan-theme',

    init() {
      const saved = SafeStorage.get(this.KEY);
      const darkQuery = Media.query('(prefers-color-scheme: dark)');
      if (saved) {
        this.apply(saved);
      } else if (darkQuery && darkQuery.matches) {
        this.apply('dark');
      }
      Media.onChange(darkQuery, (e) => {
        if (!SafeStorage.get(this.KEY)) {
          this.apply(e.matches ? 'dark' : 'light');
        }
      });
    },

    toggle() {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      this.apply(next);
      SafeStorage.set(this.KEY, next);
    },

    apply(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      document.querySelectorAll('.theme-toggle-icon').forEach(icon => {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
      });
      document.querySelectorAll('.menu-theme-icon').forEach(icon => {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
      });
    }
  };

  /* ====== 移动端汉堡菜单 ====== */
  const MobileNav = {
    overlay: null, menu: null, hamburger: null, isOpen: false,

    init() {
      this.overlay = document.querySelector('.mobile-nav-overlay');
      this.menu = document.querySelector('.mobile-menu');
      this.hamburger = document.querySelector('.hamburger');
      if (!this.hamburger || !this.menu || !this.overlay) return;
      this.hamburger.addEventListener('click', () => this.toggle());
      this.overlay.addEventListener('click', () => this.close());
      this.menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => this.close());
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen) this.close();
      });
    },

    toggle() { this.isOpen ? this.close() : this.open(); },

    open() {
      this.isOpen = true;
      this.hamburger.classList.add('active');
      this.hamburger.setAttribute('aria-expanded', 'true');
      this.overlay.classList.add('active');
      this.menu.classList.add('active');
      document.body.style.overflow = 'hidden';
    },

    close() {
      this.isOpen = false;
      this.hamburger.classList.remove('active');
      this.hamburger.setAttribute('aria-expanded', 'false');
      this.overlay.classList.remove('active');
      this.menu.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  /* ====== 滚动进度条 ====== */
  const ScrollProgress = {
    init() {
      const bar = document.getElementById('scroll-progress');
      if (!bar) return;
      let ticking = false;
      window.addEventListener('scroll', () => {
        if (!ticking) {
          requestAnimationFrame(() => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.width = (docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0) + '%';
            ticking = false;
          });
          ticking = true;
        }
      }, { passive: true });
    }
  };

  /* ====== 滚动入场动画 ====== */
  const RevealAnimations = {
    init() {
      const reducedMotion = Media.query('(prefers-reduced-motion: reduce)');
      if (reducedMotion && reducedMotion.matches) {
        document.querySelectorAll('.reveal').forEach(el => el.classList.add('revealed'));
        return;
      }
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
      document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    }
  };

  /* ====== 涟漪效果 ====== */
  const RippleEffect = {
    init() {
      document.querySelectorAll('.ripple-container').forEach(container => {
        container.addEventListener('click', (e) => {
          const rect = container.getBoundingClientRect();
          const size = Math.max(rect.width, rect.height);
          const x = e.clientX - rect.left - size / 2;
          const y = e.clientY - rect.top - size / 2;
          const ripple = document.createElement('span');
          ripple.className = 'ripple-effect';
          ripple.style.width = ripple.style.height = size + 'px';
          ripple.style.left = x + 'px';
          ripple.style.top = y + 'px';
          container.appendChild(ripple);
          ripple.addEventListener('animationend', () => ripple.remove());
        });
      });
    }
  };

  /* ====== 仪表板卡片倾斜效果 ====== */
  const TiltCards = {
    init() {
      const canHover = Media.query('(hover: hover) and (pointer: fine)');
      const reducedMotion = Media.query('(prefers-reduced-motion: reduce)');
      if (canHover && !canHover.matches) return;
      if (reducedMotion && reducedMotion.matches) return;
      document.querySelectorAll('.dash-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
          const rect = card.getBoundingClientRect();
          const x = (e.clientX - rect.left) / rect.width - 0.5;
          const y = (e.clientY - rect.top) / rect.height - 0.5;
          card.style.transform = `perspective(800px) rotateX(${-y * 6}deg) rotateY(${x * 6}deg)`;
        });
        card.addEventListener('mouseleave', () => {
          card.style.transform = '';
        });
      });
    }
  };

  /* ====== TOC 侧边栏 — 折叠 + 高亮 ====== */
  const TocSidebar = {
    KEY: 'kaoyan-toc-collapsed',
    tocEl: null,

    init() {
      this.tocEl = document.querySelector('.toc');
      if (!this.tocEl) return;

      // 1. 注入折叠按钮和头部行
      this._injectHeader();
      // 2. 恢复折叠状态
      this._restoreState();
      // 3. 滚动高亮
      this._initScrollSpy();
    },

    _injectHeader() {
      const title = this.tocEl.querySelector('h3');
      const ul = this.tocEl.querySelector('ul');
      if (!title || !ul) return;

      // 创建头部行
      const header = document.createElement('div');
      header.className = 'toc-header-row';

      // 移动标题到头部行
      title.remove();
      header.appendChild(title);

      // 创建折叠按钮
      const toggle = document.createElement('button');
      toggle.className = 'toc-toggle';
      toggle.setAttribute('aria-label', '折叠目录');
      toggle.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6l5 5 5-5"/></svg>';
      toggle.addEventListener('click', () => this._toggle());

      header.appendChild(toggle);

      // 创建滚动容器包裹列表
      const scrollWrap = document.createElement('div');
      scrollWrap.className = 'toc-scroll';
      ul.remove();
      scrollWrap.appendChild(ul);

      // 重组结构
      this.tocEl.innerHTML = '';
      this.tocEl.appendChild(header);
      this.tocEl.appendChild(scrollWrap);
    },

    _toggle() {
      const collapsed = this.tocEl.classList.toggle('collapsed');
      SafeStorage.set(this.KEY, collapsed ? '1' : '0');
    },

    _restoreState() {
      if (SafeStorage.get(this.KEY) === '1') {
        this.tocEl.classList.add('collapsed');
      }
    },

    _initScrollSpy() {
      const links = this.tocEl.querySelectorAll('a');
      if (links.length === 0) return;

      const headings = [];
      links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
          const target = document.getElementById(href.slice(1));
          if (target) headings.push({ link, target });
        }
      });
      if (headings.length === 0) return;

      let ticking = false;
      window.addEventListener('scroll', () => {
        if (!ticking) {
          requestAnimationFrame(() => {
            let current = null;
            const scrollPos = window.scrollY + 120;
            headings.forEach(({ link, target }) => {
              if (target.offsetTop <= scrollPos) current = link;
            });
            links.forEach(l => l.classList.remove('active-chapter'));
            if (current) current.classList.add('active-chapter');
            ticking = false;
          });
          ticking = true;
        }
      }, { passive: true });
    }
  };

  /* ====== 初始化 ====== */
  document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    MobileNav.init();
    ScrollProgress.init();
    RevealAnimations.init();
    RippleEffect.init();
    TiltCards.init();
    TocSidebar.init();

    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => ThemeManager.toggle());
    });
    document.querySelectorAll('.menu-theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => ThemeManager.toggle());
    });
  });
})();
