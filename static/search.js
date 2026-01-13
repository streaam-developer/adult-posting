document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const categorySelect = document.getElementById('category-select');
    const searchButton = document.getElementById('search-button');
    const resultsContainer = document.getElementById('search-results');
    const paginationControls = document.getElementById('pagination-controls');

    const POSTS_PER_PAGE = 10; // This should ideally come from config.py or an API endpoint

    let currentPage = 1;

    async function performSearch() {
        const query = searchInput.value;
        const category = categorySelect.value;

        resultsContainer.innerHTML = '<p>Searching...</p>';
        paginationControls.innerHTML = '';

        try {
            const params = new URLSearchParams();
            if (query) params.append('query', query);
            if (category) params.append('category', category);
            params.append('page', currentPage);
            params.append('page_size', POSTS_PER_PAGE);

            const response = await fetch(`/api/search?${params.toString()}`);
            const data = await response.json();

            displayResults(data.posts);
            displayPagination(data.total_results);
        } catch (error) {
            console.error('Error fetching search results:', error);
            resultsContainer.innerHTML = '<p>Error performing search. Please try again later.</p>';
        }
    }

    function displayResults(posts) {
        if (posts.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        const html = posts.map(post => `
            <div class="post-card">
                <a href="${post.page_url}">
                    <img src="${post.thumbnail_url || '/static/placeholder.png'}" alt="Thumbnail for ${post.title}" loading="lazy">
                </a>
                <div class="post-info">
                    <h3><a href="${post.page_url}">${post.title}</a></h3>
                    <p><small>${post.human_date || ''}</small></p>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    function displayPagination(totalResults) {
        paginationControls.innerHTML = ''; // Clear previous pagination
        const totalPages = Math.ceil(totalResults / POSTS_PER_PAGE);

        if (totalPages <= 1) {
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'pagination';

        // Previous button
        const prevLi = document.createElement('li');
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                performSearch();
            }
        });
        prevLi.appendChild(prevButton);
        ul.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            const button = document.createElement('button');
            button.textContent = i;
            button.className = currentPage === i ? 'active' : '';
            button.addEventListener('click', () => {
                currentPage = i;
                performSearch();
            });
            li.appendChild(button);
            ul.appendChild(li);
        }

        // Next button
        const nextLi = document.createElement('li');
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.disabled = currentPage === totalPages;
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                performSearch();
            }
        });
        nextLi.appendChild(nextButton);
        ul.appendChild(nextLi);

        paginationControls.appendChild(ul);
    }

    // Event listeners
    searchButton.addEventListener('click', () => {
        currentPage = 1; // Reset to first page on new search
        performSearch();
    });

    // Optional: Live search on input/category change (can be resource intensive)
    // searchInput.addEventListener('input', () => {
    //     currentPage = 1;
    //     performSearch();
    // });
    // categorySelect.addEventListener('change', () => {
    //     currentPage = 1;
    //     performSearch();
    // });

    // Initial search on page load if query params exist (not implemented here)
});
