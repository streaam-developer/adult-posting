document.addEventListener('DOMContentLoaded', function () {
    const postGrid = document.getElementById('post-grid-container');
    const loadingIndicator = document.getElementById('loading');
    let posts = [];
    let page = 1;
    const postsPerPage = 12;

    async function fetchPosts() {
        try {
            const response = await fetch('/posts.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            posts = await response.json();
            loadMorePosts();
        } catch (error) {
            console.error('Error fetching posts:', error);
            postGrid.innerHTML = '<p>Error loading posts. Please try again later.</p>';
        }
    }

    function createPostCard(post) {
        const article = document.createElement('article');
        article.className = 'post-card';

        const link = document.createElement('a');
        link.href = post.page_url;

        const thumbnail = document.createElement('img');
        thumbnail.src = post.thumbnail_url;
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
        meta.textContent = `Uploaded on ${post.human_date}`;

        content.appendChild(title);
        content.appendChild(meta);
        link.appendChild(thumbnail);
        link.appendChild(content);
        article.appendChild(link);

        return article;
    }

    function loadMorePosts() {
        loadingIndicator.style.display = 'block';
        const start = (page - 1) * postsPerPage;
        const end = start + postsPerPage;
        const postsToLoad = posts.slice(start, end);

        postsToLoad.forEach(post => {
            const postCard = createPostCard(post);
            postGrid.appendChild(postCard);
        });

        page++;
        loadingIndicator.style.display = 'none';

        if (end >= posts.length) {
            window.removeEventListener('scroll', handleScroll);
        }
    }

    function handleScroll() {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
            loadMorePosts();
        }
    }

    fetchPosts();
    window.addEventListener('scroll', handleScroll);
});
