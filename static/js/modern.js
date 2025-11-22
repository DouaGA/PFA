// modern.js - Interactions modernes et améliorations UX

class ModernUI {
    constructor() {
        this.init();
    }

    init() {
        this.initializeAnimations();
        this.initializeInteractiveElements();
        this.initializePerformanceOptimizations();
    }

    // Animations au défilement
    initializeAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observer les éléments à animer
        document.querySelectorAll('.card, .stats-card, .project-card').forEach(el => {
            observer.observe(el);
        });
    }

    // Éléments interactifs
    initializeInteractiveElements() {
        this.initializeTooltips();
        this.initializeCopyButtons();
        this.initializeLazyLoading();
    }

    // Tooltips personnalisés
    initializeTooltips() {
        const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
        
        tooltipTriggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', this.showTooltip);
            trigger.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(e) {
        const tooltipText = this.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = tooltipText;
        
        document.body.appendChild(tooltip);
        
        const rect = this.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    }

    hideTooltip() {
        const tooltip = document.querySelector('.custom-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // Boutons de copie
    initializeCopyButtons() {
        document.querySelectorAll('[data-copy]').forEach(button => {
            button.addEventListener('click', async (e) => {
                const textToCopy = button.getAttribute('data-copy');
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    this.showToast('Texte copié !', 'success');
                } catch (err) {
                    this.showToast('Erreur lors de la copie', 'error');
                }
            });
        });
    }

    // Chargement paresseux des images
    initializeLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img.lazy').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // Optimisations des performances
    initializePerformanceOptimizations() {
        this.debounceScrollEvents();
        this.throttleResizeEvents();
    }

    debounceScrollEvents() {
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.handleScroll();
            }, 100);
        });
    }

    throttleResizeEvents() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            if (!resizeTimeout) {
                resizeTimeout = setTimeout(() => {
                    resizeTimeout = null;
                    this.handleResize();
                }, 250);
            }
        });
    }

    handleScroll() {
        // Implémentation du header qui rétrécit au scroll
        const header = document.getElementById('mainNav');
        if (window.scrollY > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }

    handleResize() {
        // Ajustements responsive
        console.log('Window resized - perform responsive adjustments');
    }

    // Toasts personnalisés
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `custom-toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;

        document.body.appendChild(toast);

        // Animation d'entrée
        setTimeout(() => toast.classList.add('show'), 100);

        // Fermeture automatique
        setTimeout(() => {
            this.hideToast(toast);
        }, 5000);

        // Fermeture manuelle
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.hideToast(toast);
        });
    }

    hideToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Recherche en temps réel
    initializeLiveSearch(inputSelector, resultsSelector) {
        const searchInput = document.querySelector(inputSelector);
        const resultsContainer = document.querySelector(resultsSelector);

        if (!searchInput || !resultsContainer) return;

        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value, resultsContainer);
            }, 300);
        });
    }

    async performSearch(query, resultsContainer) {
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }

        try {
            // Implémentez votre logique de recherche ici
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            
            this.displaySearchResults(results, resultsContainer);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    displaySearchResults(results, container) {
        container.innerHTML = results.map(result => `
            <div class="search-result-item">
                <h6>${result.title}</h6>
                <p class="text-muted">${result.description}</p>
            </div>
        `).join('');
    }
}

// Initialisation lorsque le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.modernUI = new ModernUI();
});

// Utilitaires supplémentaires
const UIUtils = {
    // Formatage de nombres
    formatNumber: (number) => {
        return new Intl.NumberFormat('fr-FR').format(number);
    },

    // Formatage de dates
    formatDate: (dateString) => {
        return new Date(dateString).toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Formatage de durées
    formatDuration: (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    },

    // Désactivation sécurisée du HTML
    escapeHtml: (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Génération d'ID unique
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ModernUI, UIUtils };
}