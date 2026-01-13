document.addEventListener('DOMContentLoaded', function () {
    const postGrid = document.getElementById('post-grid-container');
    const loadingIndicator = document.getElementById('loading');
    let page = 1;
    const postsPerPage = 12;
    let isLoading = false;

    async function fetchPosts() {
        if (isLoading) return;
        isLoading = true;
        loadingIndicator.style.display = 'block';
        try {
            const response = await fetch(`/api/posts?page=${page}&page_size=${postsPerPage}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const newPosts = await response.json();
            if (newPosts.length > 0) {
                newPosts.forEach(post => {
                    const postCard = createPostCard(post);
                    postGrid.appendChild(postCard);
                });
                page++;
            } else {
                // No more posts to load
                window.removeEventListener('scroll', handleScroll);
            }
        } catch (error) {
            console.error('Error fetching posts:', error);
            postGrid.innerHTML = '<p>Error loading posts. Please try again later.</p>';
        } finally {
            isLoading = false;
            loadingIndicator.style.display = 'none';
        }
    }

    function createPostCard(post) {
        const article = document.createElement('article');
        article.className = 'post-card';

        const link = document.createElement('a');
        link.href = post.telegram_link; // Use telegram_link from API

        const thumbnail = document.createElement('img');
        thumbnail.src = post.thumbnail_local_path; // Use thumbnail_local_path from API
        thumbnail.alt = post.title;
        thumbnail.className = 'post-thumbnail';
        thumbnail.loading = 'lazy';

        const content = document.createElement('div');
        content.className = 'post-content';

        const title = document.createElement('h3');
        title.className = 'post-title';
        title.textContent = post.title;

        const meta = document.createElement('p');
        meta.className = 'post-meta';
        // Format the date from the 'processed_at' timestamp
        const date = new Date(post.processed_at * 1000);
        meta.textContent = `Uploaded on ${date.toLocaleDateString()}`;


        content.appendChild(title);
        content.appendChild(meta);
        link.appendChild(thumbnail);
        link.appendChild(content);
        article.appendChild(link);

        return article;
    }

    function handleScroll() {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
            fetchPosts();
        }
    }

    fetchPosts();
    window.addEventListener('scroll', handleScroll);
});