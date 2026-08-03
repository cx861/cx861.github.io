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
    overlay: null,
    menu: null,
    hamburger: null,
    previousFocus: null,
    isOpen: false,

    init() {
      this.overlay = document.querySelector('.mobile-nav-overlay');
      this.menu = document.querySelector('.mobile-menu');
      this.hamburger = document.querySelector('.hamburger');
      if (!this.hamburger || !this.menu || !this.overlay) return;
      this.menu.setAttribute('aria-hidden', 'true');
      this.menu.setAttribute('inert', '');
      this.hamburger.addEventListener('click', () => this.toggle());
      this.overlay.addEventListener('click', () => this.close());
      this.menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => this.close(false));
      });
      document.addEventListener('keydown', (e) => {
        if (!this.isOpen) return;
        if (e.key === 'Escape') this.close();
        if (e.key === 'Tab') this._trapFocus(e);
      });
    },

    toggle() { this.isOpen ? this.close() : this.open(); },

    open() {
      this.isOpen = true;
      this.previousFocus = document.activeElement;
      this.hamburger.classList.add('active');
      this.hamburger.setAttribute('aria-expanded', 'true');
      this.hamburger.setAttribute('aria-label', '关闭导航菜单');
      this.overlay.classList.add('active');
      this.menu.classList.add('active');
      this.menu.removeAttribute('inert');
      this.menu.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      const firstControl = this.menu.querySelector('a, button');
      if (firstControl) {
        window.setTimeout(() => {
          if (this.isOpen) firstControl.focus();
        }, 50);
      }
    },

    close(restoreFocus = true) {
      if (!this.isOpen) return;
      this.isOpen = false;
      this.hamburger.classList.remove('active');
      this.hamburger.setAttribute('aria-expanded', 'false');
      this.hamburger.setAttribute('aria-label', '打开导航菜单');
      this.overlay.classList.remove('active');
      this.menu.classList.remove('active');
      this.menu.setAttribute('aria-hidden', 'true');
      this.menu.setAttribute('inert', '');
      document.body.style.overflow = '';
      if (restoreFocus && this.previousFocus instanceof HTMLElement) {
        this.previousFocus.focus();
      }
      this.previousFocus = null;
    },

    _trapFocus(event) {
      const controls = Array.from(
        this.menu.querySelectorAll('a[href], button:not([disabled])')
      );
      if (controls.length === 0) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
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
    toggleButton: null,
    mobileQuery: null,

    init() {
      this.tocEl = document.querySelector('.toc');
      if (!this.tocEl) return;
      this.mobileQuery = Media.query('(max-width: 768px)');

      if (!this._injectHeader()) return;
      this._restoreState();
      this._initScrollSpy();
      Media.onChange(this.mobileQuery, () => this._restoreState());
    },

    _injectHeader() {
      const title = this.tocEl.querySelector('h3, .toc-header');
      const list = this.tocEl.querySelector('ul, .toc-list');
      if (!title || !list) return false;

      // 创建头部行
      const header = document.createElement('div');
      header.className = 'toc-header-row';

      // 移动标题到头部行
      title.remove();
      header.appendChild(title);

      // 创建折叠按钮
      const toggle = document.createElement('button');
      toggle.className = 'toc-toggle';
      toggle.type = 'button';
      toggle.setAttribute('aria-controls', 'page-toc-content');
      toggle.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6l5 5 5-5"/></svg>';
      toggle.addEventListener('click', () => this._toggle());
      this.toggleButton = toggle;

      header.appendChild(toggle);

      // 创建滚动容器包裹列表
      const scrollWrap = document.createElement('div');
      scrollWrap.className = 'toc-scroll';
      scrollWrap.id = 'page-toc-content';
      list.remove();
      scrollWrap.appendChild(list);

      // 重组结构
      this.tocEl.innerHTML = '';
      this.tocEl.appendChild(header);
      this.tocEl.appendChild(scrollWrap);
      return true;
    },

    _toggle() {
      const collapsed = !this.tocEl.classList.contains('collapsed');
      this._setCollapsed(collapsed);
      SafeStorage.set(this._storageKey(), collapsed ? '1' : '0');
    },

    _restoreState() {
      const saved = SafeStorage.get(this._storageKey());
      const collapsed = saved === null ? this._isMobile() : saved === '1';
      this._setCollapsed(collapsed);
    },

    _setCollapsed(collapsed) {
      this.tocEl.classList.toggle('collapsed', collapsed);
      this.toggleButton.setAttribute('aria-expanded', String(!collapsed));
      this.toggleButton.setAttribute(
        'aria-label',
        collapsed ? '展开章节目录' : '折叠章节目录'
      );
    },

    _isMobile() {
      return Boolean(this.mobileQuery && this.mobileQuery.matches);
    },

    _storageKey() {
      return `${this.KEY}-${this._isMobile() ? 'mobile' : 'desktop'}`;
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
        link.addEventListener('click', () => {
          if (this._isMobile()) {
            this._setCollapsed(true);
            SafeStorage.set(this._storageKey(), '1');
          }
        });
      });
      if (headings.length === 0) return;

      let ticking = false;
      const updateCurrentChapter = () => {
        let current = null;
        const scrollPos = window.scrollY + 120;
        headings.forEach(({ link, target }) => {
          if (target.offsetTop <= scrollPos) current = link;
        });
        links.forEach(link => link.classList.remove('active-chapter'));
        if (current) current.classList.add('active-chapter');
        ticking = false;
      };
      window.addEventListener('scroll', () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(updateCurrentChapter);
      }, { passive: true });
      updateCurrentChapter();
    }
  };

  /* ====== 跳到正文 ====== */
  const SkipToContent = {
    init() {
      const link = document.querySelector('.skip-link');
      const target = document.getElementById('main-content');
      if (!link || !target) return;
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      link.addEventListener('click', () => {
        requestAnimationFrame(() => target.focus({ preventScroll: true }));
      });
    }
  };

  /* ====== 回到顶部按钮 ====== */
  const BackToTop = {
    init() {
      const btn = document.getElementById('backTop');
      if (!btn) return;
      btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
      window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 300);
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
    SkipToContent.init();
    BackToTop.init();

    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => ThemeManager.toggle());
    });
    document.querySelectorAll('.menu-theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => ThemeManager.toggle());
    });
  });
})();
