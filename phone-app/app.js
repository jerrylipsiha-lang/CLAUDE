/* app.js — управление чатом: офлайн-движок + «живой режим» через Claude API. */
(() => {
  'use strict';

  const $ = (s) => document.querySelector(s);
  const chatEl = $('#chat');
  const chipsEl = $('#chips');
  const inputEl = $('#input');
  const formEl = $('#composer');
  const sendBtn = $('#send');

  const LS_MSGS = 'bz_msgs_v1';
  const LS_CFG = 'bz_cfg_v1';

  const NAMES = { budko: 'Иван Будько', pozov: 'Дмитрий Позов' };

  // --- состояние ---
  let messages = load(LS_MSGS, []);          // [{speaker, text}]
  let settings = load(LS_CFG, { live: false, apiKey: '', model: 'claude-opus-4-8' });
  let liveHistory = [];                       // контекст для API (в памяти)
  let busy = false;
  const recentlyUsed = {};                    // антиповтор реплик в офлайне

  // ---------- утилиты хранения ----------
  function load(key, def) {
    try { return JSON.parse(localStorage.getItem(key)) ?? def; } catch { return def; }
  }
  function save(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch {} }

  // ---------- рендер ----------
  function scrollDown() { chatEl.scrollTop = chatEl.scrollHeight; }

  function renderMessage({ speaker, text }) {
    const wrap = document.createElement('div');
    wrap.className = `msg from-${speaker}`;
    if (speaker === 'budko' || speaker === 'pozov') {
      const name = document.createElement('div');
      name.className = 'name';
      name.textContent = NAMES[speaker];
      wrap.appendChild(name);
    }
    const bub = document.createElement('div');
    bub.className = 'bubble';
    bub.textContent = text;
    wrap.appendChild(bub);
    chatEl.appendChild(wrap);
    scrollDown();
    return wrap;
  }

  function addMessage(msg, { persist = true } = {}) {
    renderMessage(msg);
    if (persist) { messages.push(msg); save(LS_MSGS, messages); }
  }

  function showTyping(speaker) {
    const wrap = document.createElement('div');
    wrap.className = `msg from-${speaker} typing`;
    wrap.id = 'typing';
    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = NAMES[speaker] + ' печатает';
    wrap.appendChild(name);
    const bub = document.createElement('div');
    bub.className = 'bubble';
    bub.innerHTML = '<span></span><span></span><span></span>';
    wrap.appendChild(bub);
    chatEl.appendChild(wrap);
    scrollDown();
  }
  function hideTyping() { const t = $('#typing'); if (t) t.remove(); }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const typingTime = (text) => Math.min(2200, 480 + (text ? text.length : 0) * 16);

  // проигрываем последовательность реплик с индикатором «печатает»
  async function playTurns(turns) {
    for (const t of turns) {
      showTyping(t.speaker);
      await sleep(typingTime(t.text));
      hideTyping();
      addMessage({ speaker: t.speaker, text: t.text });
    }
  }

  // ---------- офлайн-движок ----------
  const D = window.DIALOGUE;

  function pick(arr, key) {
    if (!arr || !arr.length) return '';
    if (arr.length === 1) return arr[0];
    const used = recentlyUsed[key] || -1;
    let i;
    do { i = Math.floor(Math.random() * arr.length); } while (i === used);
    recentlyUsed[key] = i;
    return arr[i];
  }

  const GREET_RE = /\b(привет|здоров|здрав|добр(ый|ое|ого)|хай|hi|hello|кто вы|кто ты|представ|это кто)/i;

  function generateOffline(userText) {
    const turns = [];
    const budkoFirst = Math.random() < 0.55;
    const order = budkoFirst ? ['budko', 'pozov'] : ['pozov', 'budko'];

    if (GREET_RE.test(userText)) {
      for (const sp of order) turns.push({ speaker: sp, text: pick(D.GREETING[sp], 'greet_' + sp) });
      return turns;
    }

    const topic = D.findTopic(userText);
    if (topic) {
      for (const sp of order) turns.push({ speaker: sp, text: pick(topic[sp], topic.id + '_' + sp) });
    } else {
      for (const sp of order) turns.push({ speaker: sp, text: pick(D.GENERIC[sp], 'gen_' + sp) });
    }

    // иногда — финальная подколка для живости
    if (Math.random() < 0.33) {
      const b = pick(D.BANTER.map((x) => x.text), 'banter');
      const sp = D.BANTER.find((x) => x.text === b).speaker;
      if (sp !== turns[turns.length - 1].speaker) turns.push({ speaker: sp, text: b });
    }
    return turns;
  }

  // ---------- живой режим (Claude API) ----------
  const SYSTEM_PROMPT = `Ты ведёшь застольный разговор от лица ДВУХ персонажей сразу:

1) ИВАН БУДЬКО — сельский дядька, хитрый и добродушный. Говорит ПО-РУССКИ, просторечно и образно, с народными присказками (без суржика и украинских слов). Любит чарку самогона, сало, огород, рыбалку, кума; работать не любит, жену Валю слушается. Простая житейская мудрость, юмор, образы из деревенской жизни.
2) ДМИТРИЙ ПОЗОВ — городской циник и ироник. Говорит по-русски, сухо, метко, «по факту», без иллюзий. Сарказм, лёгкий снобизм, отсылки к деньгам, политике, технологиям. Подкалывает Будько за наивность, но по-доброму.

Они отвечают пользователю «обо всём подряд», прямо и без купюр: режут правду-матку, шутят грубовато, спорят между собой и друг друга подкалывают. Это пародия и юмор.

Правила:
- Отвечай ТОЛЬКО на русском языке, в характере персонажей (Будько — просторечно, но по-русски).
- Всего 2–4 коротких реплики за ответ, персонажи чередуются и реагируют и на пользователя, и друг на друга. Каждая реплика — 1–3 предложения, живая разговорная речь.
- Будь смелым и прямым в оценках и юморе, но без настоящей жестокости: без оскорблений по национальности/религии/полу, без разжигания вражды, без сексуальной откровенности, без инструкций к чему-то опасному или противоправному. Резкость — через остроумие, а не через мерзость.
- Не ломай образ, не упоминай, что ты ИИ или модель.`;

  const TURNS_SCHEMA = {
    type: 'object',
    properties: {
      turns: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            speaker: { type: 'string', enum: ['budko', 'pozov'] },
            text: { type: 'string' }
          },
          required: ['speaker', 'text'],
          additionalProperties: false
        }
      }
    },
    required: ['turns'],
    additionalProperties: false
  };

  async function callLive(userText) {
    const key = (settings.apiKey || '').trim();
    if (!key) throw new Error('no-key');
    const model = settings.model || 'claude-opus-4-8';

    const body = {
      model,
      max_tokens: 800,
      system: SYSTEM_PROMPT,
      messages: liveHistory.concat([{ role: 'user', content: userText }]),
      output_config: { format: { type: 'json_schema', schema: TURNS_SCHEMA } }
    };

    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      let detail = '';
      try { detail = (await res.json()).error?.message || ''; } catch {}
      throw new Error(`http-${res.status}${detail ? ': ' + detail : ''}`);
    }

    const data = await res.json();
    if (data.stop_reason === 'refusal') throw new Error('refusal');

    const block = (data.content || []).find((b) => b.type === 'text');
    let turns = null;
    try { turns = JSON.parse(block.text).turns; } catch {}
    if (!Array.isArray(turns) || !turns.length) {
      turns = [{ speaker: 'pozov', text: block ? block.text : 'Что-то связь барахлит. Попробуй ещё раз.' }];
    }
    turns = turns.filter((t) => t && t.text && (t.speaker === 'budko' || t.speaker === 'pozov'));

    // обновляем контекст для следующего хода
    liveHistory.push({ role: 'user', content: userText });
    liveHistory.push({ role: 'assistant', content: turns.map((t) => NAMES[t.speaker] + ': ' + t.text).join('\n') });
    if (liveHistory.length > 16) liveHistory = liveHistory.slice(-16);

    return turns;
  }

  // ---------- основной поток отправки ----------
  async function handleSend(text) {
    text = (text || '').trim();
    if (!text || busy) return;
    busy = true; sendBtn.disabled = true;

    addMessage({ speaker: 'user', text });
    inputEl.value = '';
    autosize();

    try {
      let turns;
      if (settings.live && (settings.apiKey || '').trim()) {
        showTyping('budko');
        await sleep(220);
        hideTyping();
        turns = await callLive(text);
      } else {
        turns = generateOffline(text);
      }
      await playTurns(turns);
    } catch (err) {
      hideTyping();
      addMessage({ speaker: 'system', text: liveErrorText(err) }, { persist: false });
    } finally {
      busy = false; sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  function liveErrorText(err) {
    const m = String(err && err.message || err);
    if (m === 'no-key') return 'Включён живой режим, но не вписан ключ API. Зайди в ⚙️ настройки или выключи живой режим — офлайн работает и без ключа.';
    if (m === 'refusal') return 'Тут даже Будько с Позовым прикусили языки — на такое отвечать не будем. Спроси иначе.';
    if (m.startsWith('http-401')) return 'Ключ API не принят (401). Проверь его в настройках.';
    if (m.startsWith('http-429')) return 'Слишком часто — лимит запросов (429). Подожди чуть-чуть.';
    if (m.startsWith('http-')) return 'Сервер ответил ошибкой (' + m + '). Можно пока перейти в офлайн-режим.';
    return 'Не получилось дозвониться до ИИ (похоже, сеть). Офлайн-режим работает без интернета — выключи живой режим в ⚙️.';
  }

  // ---------- чипсы тем ----------
  function buildChips() {
    chipsEl.innerHTML = '';
    const surprise = document.createElement('button');
    surprise.className = 'chip special';
    surprise.textContent = '🎲 Подкинь тему';
    surprise.addEventListener('click', () => {
      const t = D.TOPICS[Math.floor(Math.random() * D.TOPICS.length)];
      handleSend(randomPrompt(t));
    });
    chipsEl.appendChild(surprise);

    for (const t of D.TOPICS) {
      const b = document.createElement('button');
      b.className = 'chip';
      b.textContent = `${t.emoji} ${t.label}`;
      b.addEventListener('click', () => handleSend(randomPrompt(t)));
      chipsEl.appendChild(b);
    }
  }
  function randomPrompt(topic) {
    const lead = ['А что насчёт', 'Скажите про', 'Давайте о', 'Ваше мнение про', 'Что думаете о'];
    const tail = topic.label.replace(/^О /, '').toLowerCase();
    return `${lead[Math.floor(Math.random() * lead.length)]} ${tail}?`;
  }

  // ---------- приветственное вступление ----------
  function bootstrapIntro() {
    if (messages.length) {
      messages.forEach((m) => renderMessage(m));
      scrollDown();
      return;
    }
    addMessage({ speaker: 'system', text: 'Кухня. На столе — сало, чарка и телефон. Иван и Дмитрий уже спорят.' });
    const intro = [
      { speaker: 'budko', text: 'О, человек пришёл! Садись, не стесняйся. Тут у нас без цензуры: что думаем, то и говорим. Спрашивай о чём хочешь.' },
      { speaker: 'pozov', text: 'Привет. Иван — за народную мудрость, я — за здравый смысл. Между нами где-то правда. Что обсудим: деньги, власть, бабы, жизнь?' }
    ];
    intro.forEach((m) => addMessage(m));
  }

  // ---------- настройки (шторка) ----------
  const sheetBackdrop = $('#sheetBackdrop');
  const liveToggle = $('#liveToggle');
  const liveOpts = $('#liveOpts');
  const apiKeyEl = $('#apiKey');
  const modelEl = $('#model');

  function openSheet() {
    liveToggle.checked = !!settings.live;
    apiKeyEl.value = settings.apiKey || '';
    modelEl.value = settings.model || 'claude-opus-4-8';
    liveOpts.hidden = !settings.live;
    sheetBackdrop.hidden = false;
  }
  function closeSheet() { sheetBackdrop.hidden = true; }

  function persistSettings() {
    settings.live = liveToggle.checked;
    settings.apiKey = apiKeyEl.value.trim();
    settings.model = modelEl.value;
    liveOpts.hidden = !settings.live;
    save(LS_CFG, settings);
  }

  $('#settingsBtn').addEventListener('click', openSheet);
  $('#closeSheet').addEventListener('click', closeSheet);
  sheetBackdrop.addEventListener('click', (e) => { if (e.target === sheetBackdrop) closeSheet(); });
  liveToggle.addEventListener('change', persistSettings);
  apiKeyEl.addEventListener('change', persistSettings);
  modelEl.addEventListener('change', persistSettings);
  $('#clearChat').addEventListener('click', () => {
    messages = []; liveHistory = []; save(LS_MSGS, messages);
    chatEl.innerHTML = '';
    closeSheet();
    bootstrapIntro();
  });

  // ---------- ввод ----------
  function autosize() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
  }
  inputEl.addEventListener('input', autosize);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(inputEl.value); }
  });
  formEl.addEventListener('submit', (e) => { e.preventDefault(); handleSend(inputEl.value); });

  // ---------- старт ----------
  buildChips();
  bootstrapIntro();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
  }
})();
