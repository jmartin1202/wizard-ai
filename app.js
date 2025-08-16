(function () {
  const root = document.documentElement;
  const messagesEl = document.getElementById('messages');
  const formEl = document.getElementById('composer-form');
  const textareaEl = document.getElementById('prompt-input');
  const attachBtn = document.getElementById('attach-btn');
  const fileInput = document.getElementById('file-input');
  const attachmentsEl = document.getElementById('attachments');
  const clearBtn = document.getElementById('clear-btn');
  const newChatBtn = document.getElementById('new-chat-btn');
  const themeToggle = document.getElementById('theme-toggle');

  function setTheme(theme) {
    const isDark = theme === 'dark';
    root.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }

  function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') {
      setTheme(saved);
      return;
    }
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(prefersDark ? 'dark' : 'light');
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight + 1000;
  }

  function createMessage({ role, html }) {
    const row = document.createElement('div');
    row.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = role === 'assistant' ? '🤖' : '🧑';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    const meta = document.createElement('div');
    meta.className = 'meta';

    const roleSpan = document.createElement('span');
    roleSpan.className = 'role';
    roleSpan.textContent = role === 'assistant' ? 'Assistant' : 'You';

    const time = document.createElement('time');
    time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    meta.appendChild(roleSpan);
    meta.appendChild(time);

    const content = document.createElement('div');
    content.className = 'content';
    content.innerHTML = html;

    bubble.appendChild(meta);
    bubble.appendChild(content);

    if (role === 'assistant') {
      const actions = document.createElement('div');
      actions.className = 'actions';

      const copyBtn = document.createElement('button');
      copyBtn.className = 'tiny-button copy';
      copyBtn.textContent = 'Copy';
      actions.appendChild(copyBtn);

      const upBtn = document.createElement('button');
      upBtn.className = 'tiny-button';
      upBtn.title = 'Good response';
      upBtn.textContent = '👍';
      actions.appendChild(upBtn);

      const downBtn = document.createElement('button');
      downBtn.className = 'tiny-button';
      downBtn.title = 'Bad response';
      downBtn.textContent = '👎';
      actions.appendChild(downBtn);

      bubble.appendChild(actions);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    return row;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function toHtmlFromMarkdownish(text) {
    const parts = text.split(/```[\s\S]*?```/g);
    const codeBlocks = [...text.matchAll(/```([\s\S]*?)```/g)].map(m => m[1]);
    let html = '';
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i].trim();
      if (p) {
        const paragraphs = p.split(/\n{2,}/).map(x => `<p>${escapeHtml(x).replace(/\n/g, '<br>')}</p>`).join('');
        html += paragraphs;
      }
      if (i < codeBlocks.length) {
        html += `<pre><code>${escapeHtml(codeBlocks[i])}</code></pre>`;
      }
    }
    if (!html) {
      html = `<p>${escapeHtml(text)}</p>`;
    }
    return html;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const raw = textareaEl.value;
    const text = raw.trim();
    if (!text) return;

    const userMessage = createMessage({ role: 'user', html: toHtmlFromMarkdownish(text) });
    messagesEl.appendChild(userMessage);

    textareaEl.value = '';
    autoResize(textareaEl);
    scrollToBottom();

    const loading = createMessage({ role: 'assistant', html: '<p>Thinking…</p>' });
    loading.classList.add('loading');
    messagesEl.appendChild(loading);
    scrollToBottom();

    setTimeout(() => {
      loading.remove();
      const replyText = `You said:\n\n${text}\n\n(This is a stub response. Wire this up to your backend to get real answers.)`;
      const assistantMessage = createMessage({ role: 'assistant', html: toHtmlFromMarkdownish(replyText) });
      messagesEl.appendChild(assistantMessage);
      scrollToBottom();
    }, 700);
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      formEl.requestSubmit();
    }
  }

  function handleAttachClick() {
    fileInput.click();
  }

  function renderAttachments(files) {
    attachmentsEl.innerHTML = '';
    Array.from(files).forEach(file => {
      const chip = document.createElement('span');
      chip.className = 'attachment-chip';
      const sizeKb = Math.max(1, Math.round(file.size / 1024));
      chip.textContent = `${file.name} · ${sizeKb} KB`;
      attachmentsEl.appendChild(chip);
    });
  }

  function handleCopyClick(target) {
    const bubble = target.closest('.bubble');
    if (!bubble) return;
    const content = bubble.querySelector('.content');
    if (!content) return;
    const text = content.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const original = target.textContent;
      target.textContent = 'Copied';
      setTimeout(() => (target.textContent = original), 900);
    }).catch(() => {});
  }

  function clearChat() {
    messagesEl.innerHTML = '';
  }

  // Event bindings
  initTheme();
  themeToggle.addEventListener('click', () => {
    const nowDark = !root.classList.contains('dark');
    setTheme(nowDark ? 'dark' : 'light');
  });

  autoResize(textareaEl);
  textareaEl.addEventListener('input', () => autoResize(textareaEl));
  textareaEl.addEventListener('keydown', handleKeydown);

  formEl.addEventListener('submit', handleSubmit);
  attachBtn.addEventListener('click', handleAttachClick);
  fileInput.addEventListener('change', () => renderAttachments(fileInput.files));
  clearBtn.addEventListener('click', clearChat);
  newChatBtn.addEventListener('click', () => {
    clearChat();
    textareaEl.focus();
  });

  // Delegate copy buttons
  messagesEl.addEventListener('click', (e) => {
    const target = e.target;
    if (target && target.classList && target.classList.contains('copy')) {
      handleCopyClick(target);
    }
  });
})();