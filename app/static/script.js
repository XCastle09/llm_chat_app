let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');
let currentChatId = null;

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function apiCall(url, options = {}) {
    if (!options.headers) options.headers = {};
    if (accessToken) options.headers['Authorization'] = `Bearer ${accessToken}`;
    let res = await fetch(url, options);
    if (res.status === 401 && refreshToken) {
        const refreshRes = await fetch('/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (refreshRes.ok) {
            const data = await refreshRes.json();
            accessToken = data.access_token;
            localStorage.setItem('access_token', accessToken);
            options.headers['Authorization'] = `Bearer ${accessToken}`;
            res = await fetch(url, options);
        } else {
            logout();
        }
    }
    return res;
}

async function loadChats() {
    if (!accessToken) return;
    const res = await apiCall('/chats/');
    if (res.ok) {
        const chats = await res.json();
        const chatList = document.getElementById('chatList');
        chatList.innerHTML = '';
        chats.forEach((chat, index) => {
            const li = document.createElement('li');
            // Используем индекс для отображения (виртуальный номер чата для пользователя)
            li.textContent = `Chat ${index + 1}: ${escapeHtml(chat.title)}`;
            li.className = 'chat-item';
            li.onclick = () => selectChat(chat.id);
            chatList.appendChild(li);
        });
    }
}

async function selectChat(chatId) {
    currentChatId = chatId;
    // Получаем номер чата для отображения
    const displayNumber = await getChatDisplayNumber(chatId);
    document.getElementById('chatHeader').innerHTML = `<h3>Chat ${displayNumber}</h3>`;
    
    const res = await apiCall(`/chats/${chatId}/messages`);
    if (res.ok) {
        const messages = await res.json();
        const container = document.getElementById('messages');
        container.innerHTML = '';
        messages.forEach(msg => {
            const div = document.createElement('div');
            div.className = `message ${msg.role}`;
            div.innerHTML = `
                <strong>${msg.role === 'user' ? 'You' : 'Assistant'}</strong>
                <div class="message-content">${escapeHtml(msg.content)}</div>
            `;
            container.appendChild(div);
        });
        container.scrollTop = container.scrollHeight;
        document.getElementById('userInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
    }
}

// Функция для получения отображаемого номера чата для пользователя
async function getChatDisplayNumber(chatId) {
    const res = await apiCall('/chats/');
    if (res.ok) {
        const chats = await res.json();
        const index = chats.findIndex(c => c.id === chatId);
        return index + 1;
    }
    return chatId;
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text || !currentChatId) return;
    input.value = '';
    const container = document.getElementById('messages');
    
    // Добавляем сообщение пользователя
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `
        <strong>You</strong>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    container.appendChild(userDiv);
    container.scrollTop = container.scrollHeight;
    
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    
    const res = await apiCall(`/ask/?chat_id=${currentChatId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    });
    
    sendBtn.disabled = false;
    
    if (res.ok) {
        const data = await res.json();
        const assistantDiv = document.createElement('div');
        assistantDiv.className = 'message assistant';
        assistantDiv.innerHTML = `
            <strong>Assistant</strong>
            <div class="message-content">${escapeHtml(data.answer || 'No response')}</div>
        `;
        container.appendChild(assistantDiv);
        container.scrollTop = container.scrollHeight;
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant';
        errorDiv.innerHTML = `
            <strong>Assistant</strong>
            <div class="message-content" style="background:#ffebee; color:#c62828;">Error sending message. Please try again.</div>
        `;
        container.appendChild(errorDiv);
        container.scrollTop = container.scrollHeight;
    }
}

async function login() {
    const login = document.getElementById('login').value.trim();
    const password = document.getElementById('password').value;
    
    if (!login || !password) {
        alert('Please enter both login and password!');
        return;
    }
    
    const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password })
    });
    if (res.ok) {
        const data = await res.json();
        accessToken = data.access_token;
        refreshToken = data.refresh_token;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        document.getElementById('logoutBtn').style.display = 'inline-block';
        document.getElementById('loginBtn').style.display = 'none';
        document.getElementById('registerBtn').style.display = 'none';
        document.getElementById('chatHeader').innerHTML = 'Select a chat to start';
        document.getElementById('messages').innerHTML = '';
        loadChats();
    } else {
        const error = await res.json();
        alert('Login failed: ' + (error.detail || 'Invalid credentials'));
    }
}

async function register() {
    const login = document.getElementById('login').value.trim();
    const password = document.getElementById('password').value;
    
    if (!login) {
        alert('Login cannot be empty!');
        return;
    }
    if (!password) {
        alert('Password cannot be empty!');
        return;
    }
    if (login.length < 3) {
        alert('Login must be at least 3 characters!');
        return;
    }
    if (password.length < 3) {
        alert('Password must be at least 3 characters!');
        return;
    }
    
    const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password })
    });
    if (res.ok) {
        alert('Registered! Now login.');
        document.getElementById('login').value = login;
        document.getElementById('password').value = '';
    } else {
        const error = await res.json();
        alert('Register failed: ' + (error.detail || 'Unknown error'));
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    accessToken = null;
    refreshToken = null;
    currentChatId = null;
    
    // Очищаем интерфейс
    document.getElementById('messages').innerHTML = '';
    document.getElementById('chatList').innerHTML = '';
    document.getElementById('chatHeader').innerHTML = 'Select a chat to start';
    document.getElementById('userInput').disabled = true;
    document.getElementById('sendBtn').disabled = true;
    
    // Показываем кнопки входа
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('loginBtn').style.display = 'inline-block';
    document.getElementById('registerBtn').style.display = 'inline-block';
    
    // Очищаем поля
    document.getElementById('login').value = '';
    document.getElementById('password').value = '';
}

// Обработчики событий
document.getElementById('loginBtn').onclick = login;
document.getElementById('registerBtn').onclick = register;
document.getElementById('logoutBtn').onclick = logout;
document.getElementById('sendBtn').onclick = sendMessage;

// Отправка по Enter
document.getElementById('userInput').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        if (!this.disabled && currentChatId) {
            sendMessage();
        }
    }
});

document.getElementById('newChatBtn').onclick = async () => {
    if (!accessToken) {
        alert('Please login first!');
        return;
    }
    const title = prompt('Chat title:');
    if (!title) return;
    const res = await apiCall('/chats/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
    });
    if (res.ok) {
        loadChats();
    } else {
        alert('Failed to create chat');
    }
};

// При загрузке страницы
if (accessToken) {
    document.getElementById('logoutBtn').style.display = 'inline-block';
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('registerBtn').style.display = 'none';
    loadChats();
} else {
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('loginBtn').style.display = 'inline-block';
    document.getElementById('registerBtn').style.display = 'inline-block';
}

// Обработка OAuth callback (когда возвращаемся с GitHub)
const urlParams = new URLSearchParams(window.location.search);
const ghAccessToken = urlParams.get('access_token');
const ghRefreshToken = urlParams.get('refresh_token');

if (ghAccessToken && ghRefreshToken) {
    localStorage.setItem('access_token', ghAccessToken);
    localStorage.setItem('refresh_token', ghRefreshToken);
    window.history.replaceState({}, document.title, "/");
    accessToken = ghAccessToken;
    refreshToken = ghRefreshToken;
    document.getElementById('logoutBtn').style.display = 'inline-block';
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('registerBtn').style.display = 'none';
    loadChats();
}