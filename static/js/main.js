// Smart Blog AI - JavaScript principal

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Gestion du temps de lecture
    trackReadingTime();
    
    // Gestion des interactions HTMX
    initHTMX();
    
    // Gestion du mode sombre (optionnel)
    initDarkMode();
});

function trackReadingTime() {
    const articles = document.querySelectorAll('article[data-article-id]');
    
    articles.forEach(article => {
        const articleId = article.dataset.articleId;
        const startTime = Date.now();
        
        window.addEventListener('beforeunload', function() {
            const duration = Math.floor((Date.now() - startTime) / 1000);
            if (duration > 10) { // Envoyer seulement si > 10s de lecture
                sendReadingTime(articleId, duration);
            }
        });
    });
}

function sendReadingTime(articleId, duration) {
    fetch(`/api/v1/track-reading/${articleId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ duration: duration })
    }).catch(error => console.log('Erreur tracking lecture:', error));
}

function initHTMX() {
    // Configuration HTMX globale
    htmx.config.globalViewTransitions = true;
    
    // Gestion des erreurs HTMX
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('Erreur HTMX:', evt.detail);
        showToast('Une erreur est survenue', 'error');
    });
    
    // Gestion du succès
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.detail.successful) {
            // Animation de succès pour les boutons
            const target = evt.detail.target;
            if (target && target.classList.contains('btn')) {
                target.classList.add('btn-success');
                setTimeout(() => {
                    target.classList.remove('btn-success');
                }, 1000);
            }
        }
    });
}

function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return;
    
    // Vérifier la préférence sauvegardée
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
    
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDark);
    });
}

// Utilitaires
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    // Créer un toast simple (pourrait utiliser une librairie plus avancée)
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-suppression après 5 secondes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Gestion du partage
function shareArticle(title, url) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(err => console.log('Erreur partage:', err));
    } else {
        // Fallback: copier dans le presse-papier
        navigator.clipboard.writeText(url).then(() => {
            showToast('Lien copié dans le presse-papier !', 'success');
        });
    }
}

// Infinite scroll (pour l'avenir)
function initInfiniteScroll() {
    const nextPageLink = document.querySelector('.pagination .next');
    if (!nextPageLink) return;
    
    let loading = false;
    
    window.addEventListener('scroll', function() {
        if (loading) return;
        
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
            loading = true;
            
            fetch(nextPageLink.href)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newArticles = doc.querySelectorAll('.card');
                    const container = document.querySelector('.row');
                    
                    newArticles.forEach(article => {
                        container.appendChild(article);
                    });
                    
                    // Mettre à jour le lien de la page suivante
                    const newNextLink = doc.querySelector('.pagination .next');
                    if (newNextLink) {
                        nextPageLink.href = newNextLink.href;
                    } else {
                        nextPageLink.remove();
                    }
                    
                    loading = false;
                })
                .catch(error => {
                    console.error('Erreur infinite scroll:', error);
                    loading = false;
                });
        }
    });
}

// Recherche en temps réel (pour l'avenir)
function initLiveSearch() {
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    let timeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(timeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            // Afficher tous les articles
            return;
        }
        
        timeout = setTimeout(() => {
            fetch(`/api/v1/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // Mettre à jour l'interface avec les résultats
                    updateSearchResults(data.results);
                })
                .catch(error => console.error('Erreur recherche:', error));
        }, 300);
    });
}

function updateSearchResults(results) {
    const container = document.querySelector('.row');
    if (!container) return;
    
    // Vider et repeupler avec les résultats
    container.innerHTML = '';
    
    results.forEach(article => {
        const card = createArticleCard(article);
        container.appendChild(card);
    });
}

function createArticleCard(article) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-4';
    
    col.innerHTML = `
        <div class="card h-100">
            ${article.cover ? `<img src="${article.cover}" class="card-img-top" alt="${article.title}">` : ''}
            <div class="card-body">
                <h5 class="card-title">
                    <a href="${article.url}" class="text-decoration-none text-dark">${article.title}</a>
                </h5>
                <p class="card-text text-muted">${article.excerpt}</p>
                <small class="text-muted">
                    <i class="bi bi-clock"></i> ${article.read_time} min • 
                    <i class="bi bi-eye"></i> ${article.view_count}
                </small>
            </div>
        </div>
    `;
    
    return col;
}
