// Enhanced Index/Homepage JavaScript
class QuizHomepage {
    constructor() {
        this.categories = [];
        this.stats = {
            totalQuizzes: 0,
            totalQuestions: 0,
            totalPlayers: 0,
            avgRating: 4.8
        };
        this.isLoading = true;
        this.animationObserver = null;

        this.init();
    }

    async init() {
        try {
            await this.showLoadingScreen();
            await this.loadData();
            this.setupAnimations();
            this.setupEventListeners();
            this.setupAccessibility();
            await this.hideLoadingScreen();
            this.startAnimations();
        } catch (error) {
            console.error('Initialization error:', error);
            this.hideLoadingScreen();
        }
    }

    // Loading Screen
    async showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
        }

        // Simulate loading time
        return new Promise(resolve => setTimeout(resolve, 1500));
    }

    async hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }

        // Start main animations
        document.body.classList.add('loaded');
    }

    // Data Loading
    async loadData() {
        try {
            // Load categories and stats
            await Promise.all([
                this.loadCategories(),
                this.loadStats()
            ]);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    async loadCategories() {
        try {
            // Categories werden bereits vom Flask-Template gerendert
            const categoryElements = document.querySelectorAll('.category-card');
            this.categories = Array.from(categoryElements).map((el, index) => ({
                id: index,
                name: el.querySelector('.category-title')?.textContent || 'Unknown',
                element: el
            }));

            console.log('Categories loaded:', this.categories.length);
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async loadStats() {
        try {
            // Simulate API call - in real app would fetch from backend
            this.stats = {
                totalQuizzes: this.categories.length,
                totalQuestions: this.categories.length * 10, // Estimate
                totalPlayers: Math.floor(Math.random() * 1000) + 500,
                avgRating: 4.8
            };

            this.updateStatsDisplay();
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStatsDisplay() {
        const statElements = {
            quizzes: document.querySelector('[data-stat="quizzes"] .stat-number'),
            questions: document.querySelector('[data-stat="questions"] .stat-number'),
            players: document.querySelector('[data-stat="players"] .stat-number'),
            rating: document.querySelector('[data-stat="rating"] .stat-number')
        };

        if (statElements.quizzes) {
            this.animateNumber(statElements.quizzes, 0, this.stats.totalQuizzes, 1000);
        }
        if (statElements.questions) {
            this.animateNumber(statElements.questions, 0, this.stats.totalQuestions, 1200);
        }
        if (statElements.players) {
            this.animateNumber(statElements.players, 0, this.stats.totalPlayers, 1500);
        }
        if (statElements.rating) {
            this.animateNumber(statElements.rating, 0, this.stats.avgRating, 800, 1);
        }
    }

    // Animations
    animateNumber(element, start, end, duration, decimals = 0) {
        const startTime = performance.now();
        const difference = end - start;

        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = start + (difference * easeOutQuart);

            element.textContent = current.toFixed(decimals);

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                element.textContent = end.toFixed(decimals);
            }
        };

        requestAnimationFrame(step);
    }

    setupAnimations() {
        // Intersection Observer for scroll animations
        this.animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;

                    if (element.classList.contains('stat-card')) {
                        element.style.animationDelay = `${Math.random() * 0.3}s`;
                        element.classList.add('fade-in');
                    } else if (element.classList.contains('category-card')) {
                        const index = Array.from(document.querySelectorAll('.category-card')).indexOf(element);
                        element.style.animationDelay = `${index * 0.1}s`;
                        element.classList.add('slide-up');
                    }

                    this.animationObserver.unobserve(element);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        // Observe elements
        document.querySelectorAll('.stat-card, .category-card').forEach(el => {
            this.animationObserver.observe(el);
        });
    }

    startAnimations() {
        // Create particles
        this.createParticles();

        // Start floating orbs
        this.animateOrbs();

        // Logo hover effect
        this.setupLogoEffects();

        // Category card effects
        this.setupCategoryEffects();
    }

    createParticles() {
        const particlesContainer = document.getElementById('particles-container');
        if (!particlesContainer) return;

        // Clear existing particles
        particlesContainer.innerHTML = '';

        const particleCount = window.innerWidth > 768 ? 50 : 25;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';

            // Random properties
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 25 + 's';
            particle.style.animationDuration = (Math.random() * 15 + 15) + 's';

            // Random size
            const size = Math.random() * 3 + 2;
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';

            particlesContainer.appendChild(particle);
        }
    }

    animateOrbs() {
        const orbs = document.querySelectorAll('.orb');
        orbs.forEach((orb, index) => {
            // Random animation delays and durations
            orb.style.animationDelay = `${index * -3}s`;
            orb.style.animationDuration = `${20 + Math.random() * 10}s`;
        });
    }

    setupLogoEffects() {
        const logo = document.querySelector('.logo');
        if (!logo) return;

        // 3D tilt effect
        logo.addEventListener('mousemove', (e) => {
            const rect = logo.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            const deltaX = (e.clientX - centerX) / (rect.width / 2);
            const deltaY = (e.clientY - centerY) / (rect.height / 2);

            const rotateX = deltaY * -15;
            const rotateY = deltaX * 15;

            logo.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.1)`;
        });

        logo.addEventListener('mouseleave', () => {
            logo.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)';
        });

        // Click effect
        logo.addEventListener('click', () => {
            logo.style.animation = 'none';
            setTimeout(() => {
                logo.style.animation = 'logoFloat 4s ease-in-out infinite alternate';
            }, 100);

            this.createClickEffect(logo);
        });
    }

    createClickEffect(element) {
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            top: 50%;
            left: 50%;
            width: 200px;
            height: 200px;
            margin-left: -100px;
            margin-top: -100px;
        `;

        element.style.position = 'relative';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    setupCategoryEffects() {
        const categoryCards = document.querySelectorAll('.category-card');

        categoryCards.forEach((card, index) => {
            // 3D hover effect
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;

                const deltaX = (e.clientX - centerX) / (rect.width / 2);
                const deltaY = (e.clientY - centerY) / (rect.height / 2);

                const rotateX = deltaY * -5;
                const rotateY = deltaX * 5;

                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-15px) scale(1.02)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px) scale(1)';
            });

            // Click animation
            card.addEventListener('click', (e) => {
                if (e.target.closest('.play-button')) return;

                this.createClickEffect(card);
                this.playClickSound();

                // Navigate after animation
                setTimeout(() => {
                    const href = card.getAttribute('href');
                    if (href) {
                        window.location.href = href;
                    }
                }, 200);
            });

            // Play button effect
            const playButton = card.querySelector('.play-button');
            if (playButton) {
                playButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();

                    this.playStartSound();
                    this.animatePlayButton(playButton);

                    setTimeout(() => {
                        const href = card.getAttribute('href');
                        if (href) {
                            window.location.href = href;
                        }
                    }, 300);
                });
            }
        });
    }

    animatePlayButton(button) {
        button.style.transform = 'scale(0.95)';
        button.style.boxShadow = '0 5px 15px rgba(99, 102, 241, 0.6)';

        setTimeout(() => {
            button.style.transform = 'scale(1.05)';
            button.style.boxShadow = '0 20px 40px rgba(99, 102, 241, 0.4)';
        }, 100);

        setTimeout(() => {
            button.style.transform = '';
            button.style.boxShadow = '';
        }, 200);
    }

    // Event Listeners
    setupEventListeners() {
        // Resize handler
        window.addEventListener('resize', this.debounce(() => {
            this.createParticles();
        }, 250));

        // Scroll effects
        window.addEventListener('scroll', this.throttle(() => {
            this.updateScrollEffects();
        }, 16));

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        // Focus management
        document.addEventListener('focusin', (e) => {
            if (e.target.classList.contains('category-card')) {
                e.target.style.outline = '2px solid var(--primary-color)';
                e.target.style.outlineOffset = '4px';
            }
        });

        document.addEventListener('focusout', (e) => {
            if (e.target.classList.contains('category-card')) {
                e.target.style.outline = '';
                e.target.style.outlineOffset = '';
            }
        });

        // Admin panel shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                window.location.href = '/admin';
            }
        });
    }

    updateScrollEffects() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;

        // Parallax effect for orbs
        const orbs = document.querySelectorAll('.orb');
        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.1;
            orb.style.transform = `translateY(${scrolled * speed}px)`;
        });

        // Header parallax
        const header = document.querySelector('.header-section');
        if (header) {
            header.style.transform = `translateY(${rate}px)`;
        }
    }

    handleKeyboardNavigation(e) {
        const categoryCards = Array.from(document.querySelectorAll('.category-card'));
        const currentFocus = document.activeElement;
        const currentIndex = categoryCards.indexOf(currentFocus);

        switch(e.key) {
            case 'ArrowDown':
            case 'ArrowRight':
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % categoryCards.length;
                categoryCards[nextIndex]?.focus();
                break;

            case 'ArrowUp':
            case 'ArrowLeft':
                e.preventDefault();
                const prevIndex = currentIndex <= 0 ? categoryCards.length - 1 : currentIndex - 1;
                categoryCards[prevIndex]?.focus();
                break;

            case 'Enter':
            case ' ':
                if (currentFocus && currentFocus.classList.contains('category-card')) {
                    e.preventDefault();
                    currentFocus.click();
                }
                break;
        }
    }

    // Accessibility
    setupAccessibility() {
        // Reduce motion for users who prefer it
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--transition', 'none');

            // Disable animations
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            `;
            document.head.appendChild(style);
        }

        // High contrast mode
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.body.classList.add('high-contrast');
        }

        // Keyboard focus indicators
        document.addEventListener('keydown', () => {
            document.body.classList.add('keyboard-nav');
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-nav');
        });
    }

    // Sound Effects
    initAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Audio not supported');
            this.audioEnabled = false;
        }
    }

    playSound(frequency, duration = 200, type = 'sine') {
        if (!this.audioContext || !this.audioEnabled) return;

        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            oscillator.frequency.value = frequency;
            oscillator.type = type;

            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);

            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + duration / 1000);
        } catch (e) {
            console.log('Sound playback failed');
        }
    }

    playClickSound() {
        this.playSound(440, 100); // A4
    }

    playStartSound() {
        this.playSound(523.25, 200); // C5
    }

    // Utility Functions
    debounce(func, wait) {
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

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Cleanup
    destroy() {
        if (this.animationObserver) {
            this.animationObserver.disconnect();
        }

        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('scroll', this.handleScroll);
    }
}

// Smooth scroll polyfill for older browsers
if (!('scrollBehavior' in document.documentElement.style)) {
    const script = document.createElement('script');
    script.src = 'https://cdn.polyfill.io/v2/polyfill.min.js?features=smoothscroll';
    document.head.appendChild(script);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quizHomepage = new QuizHomepage();
    });
} else {
    window.quizHomepage = new QuizHomepage();
}

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.code);
    if (konamiCode.length > konamiSequence.length) {
        konamiCode.shift();
    }

    if (JSON.stringify(konamiCode) === JSON.stringify(konamiSequence)) {
        // Easter egg activated!
        document.body.style.filter = 'hue-rotate(180deg)';
        setTimeout(() => {
            document.body.style.filter = '';
        }, 3000);

        // Show secret message
        const msg = document.createElement('div');
        msg.textContent = '🎉 Konami Code aktiviert! 🎉';
        msg.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--primary-color);
            color: white;
            padding: 2rem;
            border-radius: 1rem;
            font-size: 1.5rem;
            font-weight: bold;
            z-index: 9999;
            box-shadow: var(--shadow-xl);
        `;
        document.body.appendChild(msg);

        setTimeout(() => msg.remove(), 3000);
        konamiCode = [];
    }
});

// Export for potential use in other scripts
window.QuizHomepage = QuizHomepage;