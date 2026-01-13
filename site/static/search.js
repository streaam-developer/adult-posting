document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    let posts = [];

    // Fetch the search index
    fetch('/search_index.json')
        .then(response => response.json())
        .then(data => {
            posts = data;
        })
        .catch(error => {
            console.error('Error fetching search index:', error);
            resultsContainer.innerHTML = '<p>Error loading search data. Please try again later.</p>';
        });

    function performSearch(query) {
        if (!query || query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }

        const lowerCaseQuery = query.toLowerCase();
        const filteredPosts = posts.filter(post => {
            const titleMatch = post.title.toLowerCase().includes(lowerCaseQuery);
            const descriptionMatch = post.description.toLowerCase().includes(lowerCaseQuery);
            return titleMatch || descriptionMatch;
        });

        displayResults(filteredPosts);
    }

    function displayResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        const html = results.map(post => `
            <div class="search-result-item" style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #eee;">
                <h3><a href="${post.url}">${post.title}</a></h3>
                <p>${post.description.substring(0, 150)}...</p>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
    });
});
