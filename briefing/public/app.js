// app.js — fetcht briefing en rendert

const DAYS = ['zondag', 'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag'];
const MONTHS = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'];

function getAccessKey() {
  // Token kan in URL (?key=...) of in localStorage na eerste bezoek
  const url = new URL(window.location.href);
  const fromUrl = url.searchParams.get('key');
  if (fromUrl) {
    localStorage.setItem('briefing_key', fromUrl);
    // strip key uit URL voor schonere look + om te voorkomen dat hij in screenshots staat
    url.searchParams.delete('key');
    window.history.replaceState({}, '', url.toString());
    return fromUrl;
  }
  return localStorage.getItem('briefing_key') || '';
}

function renderDate() {
  const now = new Date();
  const day = DAYS[now.getDay()];
  const date = now.getDate();
  const month = MONTHS[now.getMonth()];
  document.getElementById('date').textContent = `${day} ${date} ${month}`;
}

function renderQuote(quote, error) {
  const el = document.getElementById('quote');
  el.classList.remove('skeleton');
  if (quote) {
    el.textContent = quote;
  } else if (error) {
    el.textContent = '(quote tijdelijk niet beschikbaar)';
    el.style.fontStyle = 'normal';
    el.style.color = 'var(--muted)';
  } else {
    el.textContent = '(geen quote)';
  }
}

function renderTasks(tasks, error) {
  const container = document.getElementById('tasks');
  container.innerHTML = '';

  if (error) {
    const div = document.createElement('div');
    div.className = 'error';
    div.textContent = `Notion-fout: ${error}`;
    container.appendChild(div);
    return;
  }

  if (!tasks || tasks.length === 0) {
    const div = document.createElement('div');
    div.className = 'empty';
    div.textContent = 'Geen 🔴 NU-taken open. Ademen.';
    container.appendChild(div);
    return;
  }

  for (const t of tasks) {
    const a = document.createElement('a');
    a.className = 'task';
    a.href = t.url;
    a.target = '_blank';
    a.rel = 'noopener';

    const dot = document.createElement('div');
    dot.className = `priority-dot priority-${t.priority || 'Normaal'}`;
    a.appendChild(dot);

    const body = document.createElement('div');
    body.className = 'task-body';

    const title = document.createElement('div');
    title.className = 'task-title';
    title.textContent = t.task;
    body.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'task-meta';
    if (t.project) {
      const proj = document.createElement('span');
      proj.className = 'project';
      proj.textContent = t.project;
      meta.appendChild(proj);
    }
    if (t.priority) {
      const pri = document.createElement('span');
      pri.textContent = t.priority;
      meta.appendChild(pri);
    }
    body.appendChild(meta);

    a.appendChild(body);
    container.appendChild(a);
  }
}

function renderFooter(generatedAt) {
  if (!generatedAt) return;
  const time = new Date(generatedAt).toLocaleTimeString('nl-NL', {
    hour: '2-digit', minute: '2-digit'
  });
  document.getElementById('footer').textContent = `gegenereerd ${time}`;
}

function renderFullError(msg) {
  document.getElementById('quote').classList.remove('skeleton');
  document.getElementById('quote').textContent = '';

  const container = document.getElementById('tasks');
  container.innerHTML = '';
  const div = document.createElement('div');
  div.className = 'error';
  div.textContent = msg;
  container.appendChild(div);
}

async function loadBriefing() {
  renderDate();

  const key = getAccessKey();
  if (!key) {
    renderFullError('Geen toegangscode. Open de juiste URL met ?key=...');
    return;
  }

  try {
    const res = await fetch(`/api/briefing?key=${encodeURIComponent(key)}`, {
      cache: 'no-store'
    });

    if (res.status === 403) {
      localStorage.removeItem('briefing_key');
      renderFullError('Verkeerde toegangscode. Open de juiste URL opnieuw.');
      return;
    }

    if (!res.ok) {
      renderFullError(`Server-fout: ${res.status}`);
      return;
    }

    const data = await res.json();
    renderQuote(data.quote, data.quoteError);
    renderTasks(data.tasks, data.tasksError);
    renderFooter(data.generatedAt);
  } catch (err) {
    renderFullError(`Netwerkfout: ${err.message}`);
  }
}

document.getElementById('refresh').addEventListener('click', () => {
  // reset skeletons
  document.getElementById('quote').className = 'quote skeleton';
  document.getElementById('quote').textContent = 'Quote laden...';
  document.getElementById('tasks').innerHTML =
    '<div class="task skeleton"><div class="priority-dot"></div><div class="task-body"><div class="task-title">&nbsp;</div></div></div>'.repeat(3);
  loadBriefing();
});

// Service worker registratie
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

loadBriefing();
