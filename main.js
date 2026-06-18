document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    const currentTheme = localStorage.getItem('theme');
    if (currentTheme == 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        if (themeToggle) themeToggle.textContent = '☀️';
    } else if (currentTheme == 'light') {
        document.body.setAttribute('data-theme', 'light');
        if (themeToggle) themeToggle.textContent = '🌙';
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            let theme = 'light';
            if (document.body.getAttribute('data-theme') === 'light') {
                document.body.setAttribute('data-theme', 'dark');
                theme = 'dark';
                themeToggle.textContent = '☀️';
            } else {
                document.body.setAttribute('data-theme', 'light');
                theme = 'light';
                themeToggle.textContent = '🌙';
            }
            localStorage.setItem('theme', theme);
        });
    }

    // Mobile Menu
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }

    // AI Chat
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        const chatInput = document.getElementById('chat-message');
        const chatMessages = document.getElementById('chat-messages');

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, 'user');
            chatInput.value = '';

            // Simulate AI delay
            addMessage('Thinking...', 'ai', true);

            try {
                const response = await fetch('/ai-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();

                // Remove loading and add response
                const loadingMsg = document.querySelector('.message.loading');
                if (loadingMsg) loadingMsg.remove();

                addMessage(data.response, 'ai');

            } catch (error) {
                console.error('Error:', error);
                // Remove loading
                const loadingMsg = document.querySelector('.message.loading');
                if (loadingMsg) loadingMsg.remove();
                addMessage('Sorry, I could not reach the server.', 'ai');
            }
        });
    }

    function addMessage(text, sender, isLoading = false) {
        const chatMessages = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        if (isLoading) msgDiv.classList.add('loading');
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

async function toggleTask(taskId) {
    try {
        const response = await fetch(`/toggle_task/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();

        if (data.success) {
            const label = document.getElementById(`label-${taskId}`);
            if (data.new_status) {
                label.style.textDecoration = 'line-through';
                label.style.color = 'var(--text-secondary)';
            } else {
                label.style.textDecoration = 'none';
                label.style.color = 'var(--text-color)';
            }
        }
    } catch (error) {
        console.error('Error toggling task:', error);
    }
}
