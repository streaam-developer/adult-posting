document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    let searchTimeout;

    function performSearch(query) {
        if (!query || query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }

        // Clear the previous timeout
        clearTimeout(searchTimeout);

        // Set a new timeout to avoid sending too many requests
        searchTimeout = setTimeout(() => {
            fetch(`/api/search?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    resultsContainer.innerHTML = '<p>Error performing search. Please try again later.</p>';
                });
        }, 300); // 300ms delay
    }

    function displayResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        const html = results.map(post => `
            <div class="search-result-item" style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #eee;">
                <h3><a href="${post.page_url}">${post.title}</a></h3>
                <p>${post.description.substring(0, 150)}...</p>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
    });
});
