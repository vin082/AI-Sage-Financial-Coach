/**
 * AI Sage Chat Panel — Online Banking Integration
 *
 * Connects to the FastAPI backend (/session/new + /chat endpoints).
 * Falls back to the Streamlit agent via a direct API call.
 *
 * Usage:
 *   openChat(prefillText)  — open panel, optionally pre-fill + send a message
 *   closeChat()            — close panel
 *   sendMessage()          — send the current textarea content
 *   sendSuggestion(text)   — click a suggestion chip
 */

// ---- Configuration ----
const API_BASE   = 'http://localhost:8000';   // FastAPI backend
const DEMO_TOKEN = 'demo-token-alex';          // Matches api/main.py bearer stub
const CUSTOMER_ID = 'CUST_DEMO_002';           // Life Events demo profile

// ---- State ----
let sessionId    = null;
let isTyping     = false;
let messageCount = 0;
let userProfile  = null;   // populated after /session/profile — drives dynamic chips

// ---- Profile cache (localStorage) ----
const PROFILE_CACHE_KEY = `ai_sage_profile_${CUSTOMER_ID}`;

function loadCachedProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveCachedProfile(profile) {
  try { localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(profile)); } catch { /* ignore */ }
}

// ---- Panel open/close ----

function openChat(prefillText = '') {
  document.getElementById('chat-panel').classList.add('open');
  document.getElementById('chat-overlay').classList.add('open');

  // Hide floating badge once opened
  const badge = document.querySelector('#ai-sage-btn .btn-badge');
  if (badge) badge.style.display = 'none';

  // Initialise session if first open
  if (!sessionId) {
    // Render instantly from cache (no API wait) — returning users see chips immediately
    const cached = loadCachedProfile();
    if (cached && cached.conversation_count > 0) {
      userProfile = cached;
      renderInitialChips(cached);
      // No welcome bubble for returning users — they're ready to type
    }

    initSession().then(() => {
      // showWelcome / onboarding handled inside initSession → checkOnboarding
      if (prefillText) {
        setTimeout(() => sendSuggestion(prefillText), 400);
      }
    });
  } else if (prefillText) {
    setTimeout(() => sendSuggestion(prefillText), 200);
  }

  // Focus input
  setTimeout(() => document.getElementById('chat-input')?.focus(), 350);
}

function closeChat() {
  document.getElementById('chat-panel').classList.remove('open');
  document.getElementById('chat-overlay').classList.remove('open');
  // End session on close so summary is persisted for next visit
  if (sessionId && !sessionId.startsWith('demo-')) {
    fetch(`${API_BASE}/session/end?session_id=${sessionId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${DEMO_TOKEN}` },
      keepalive: true,   // fires even if the user navigates away
    }).catch(() => {});  // fire-and-forget
    sessionId = null;    // force fresh session on next open
  }
}

// ---- Session initialisation ----

async function initSession() {
  try {
    const res = await fetch(`${API_BASE}/session/new?customer_id=${CUSTOMER_ID}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${DEMO_TOKEN}` },
    });
    if (res.ok) {
      const data = await res.json();
      sessionId = data.session_id;
      // Check if first visit — show onboarding if so
      await checkOnboarding();
    } else {
      sessionId = 'demo-' + Math.random().toString(36).slice(2, 9);
    }
  } catch {
    // API not running — use mock session
    sessionId = 'offline-' + Math.random().toString(36).slice(2, 9);
  }
}

async function checkOnboarding() {
  // Skip onboarding if offline/mock session
  if (!sessionId || sessionId.startsWith('demo-') || sessionId.startsWith('offline-')) return;
  try {
    const res = await fetch(`${API_BASE}/session/profile?session_id=${sessionId}`, {
      headers: { 'Authorization': `Bearer ${DEMO_TOKEN}` },
    });
    if (res.ok) {
      const profile = await res.json();
      userProfile = profile;
      saveCachedProfile(profile);   // keep cache fresh for next visit

      if (profile.is_first_visit && profile.active_goals.length === 0) {
        showOnboarding();
        return;
      }

      // Return visit — chips already rendered from cache; silently refresh them
      // with latest data but do NOT show a welcome bubble (user is already typing)
      renderInitialChips(profile);
      return;
    }
  } catch { /* silently fall through to generic welcome */ }

  // First visit fallback (no cache, no API) — show generic welcome
  if (!userProfile) {
    showWelcome(null);
    renderInitialChips(null);
  }
}

// ---- Welcome message ----

function showWelcome(profile = null) {
  // Generic first-time welcome (fallback)
  if (!profile || profile.conversation_count === 0) {
    appendAgentMessage(
      "Hi Alex! I'm **AI Sage**, your personal financial coach. 👋\n\n" +
      "I can see your accounts and recent transactions, so I can give you " +
      "personalised insights — no need to explain your situation from scratch.\n\n" +
      "What would you like to explore today?"
    );
    return;
  }

  // Return visit — build a memory-aware greeting
  const firstName = (profile.customer_name || 'Alex').split(' ')[0];
  const count = profile.conversation_count;

  // Goals line
  let goalsLine = '';
  if (profile.active_goals && profile.active_goals.length > 0) {
    const goalDescs = profile.active_goals
      .slice(0, 2)
      .map(g => {
        let txt = `**${g.description}**`;
        if (g.target_amount) txt += ` (£${Number(g.target_amount).toLocaleString('en-GB')})`;
        return txt;
      })
      .join(' and ');
    const more = profile.active_goals.length > 2 ? ` and ${profile.active_goals.length - 2} more` : '';
    goalsLine = `\n\nYou're working toward ${goalDescs}${more}. Want to check your progress?`;
  }

  // Topics line
  let topicsLine = '';
  if (profile.preferences && profile.preferences.preferred_topics.length > 0) {
    topicsLine = `\n\nI know you're interested in **${profile.preferences.preferred_topics.join(', ')}** — I'll keep that in mind.`;
  }

  const greeting = count === 1
    ? `Welcome back, ${firstName}! 👋 Great to see you again.`
    : `Welcome back, ${firstName}! 👋 This is your session #${count + 1} with me.`;

  appendAgentMessage(`${greeting}${goalsLine}${topicsLine}\n\nWhat would you like to explore today?`);
}

// ---- Dynamic suggestion chips ----

function renderInitialChips(profile) {
  const el = document.getElementById('chat-suggestions');
  if (!el) return;

  const hasGoals   = profile && profile.active_goals && profile.active_goals.length > 0;
  const hasPrefs   = profile && profile.preferences && profile.preferences.preferred_topics.length > 0;
  const returning  = profile && profile.conversation_count > 0;
  const multiVisit = profile && profile.conversation_count > 1;

  const chips = [];

  // Goal-aware chip
  if (hasGoals) {
    chips.push({ icon: '📊', label: 'Check my goal progress',  msg: 'What are my financial goals and how am I progressing?' });
  } else {
    chips.push({ icon: '🎯', label: 'Set a savings goal',      msg: 'I want to set a savings goal' });
  }

  // Preferences chip
  if (!hasPrefs) {
    chips.push({ icon: '⚙️', label: 'Personalise my coaching', msg: 'I want to personalise how you coach me' });
  } else {
    chips.push({ icon: '💰', label: 'My spending this month',  msg: 'How much am I spending each month?' });
  }

  // Session recap chip (only for multi-session users)
  if (multiVisit) {
    chips.push({ icon: '📋', label: 'Recap last session',      msg: 'Can you recap what we discussed last time?' });
  } else {
    chips.push({ icon: '🏥', label: 'My health score',         msg: "What's my financial health score?" });
  }

  // Always include a couple of standard useful chips
  chips.push({ icon: '🏠', label: 'Mortgage check',            msg: 'Can I afford a £300,000 mortgage?' });
  chips.push({ icon: '💡', label: 'Save money',                msg: 'Where can I save money?' });

  el.innerHTML = chips.map(c =>
    `<button class="suggestion-chip" onclick="sendSuggestion('${c.msg.replace(/'/g, "\\'")}')">${c.icon} ${c.label}</button>`
  ).join('');
  el.style.display = 'flex';
}

// ---- Onboarding flow ----

// Onboarding state
const ob = {
  // structured goals: [{ key, description, amount, date }]
  selectedGoals: [],
  customGoal: '',
  selectedStyle: 'balanced',
  selectedTopics: [],
};

// Map chip key → base description used when building the goal message
const OB_GOAL_DESCRIPTIONS = {
  deposit:    'save for a house deposit',
  emergency:  'build a 3-month emergency fund',
  debt:       'pay off my credit card debt',
  holiday:    'save for a family holiday',
  car:        'save for a new car',
  retirement: 'retire early',
};

function showOnboarding() {
  document.getElementById('onboarding-panel').style.display = 'block';
  document.getElementById('chat-messages').style.display = 'none';
  document.getElementById('chat-suggestions').style.display = 'none';
  document.getElementById('chat-input-area') && (document.querySelector('.chat-input-area').style.display = 'none');
}

function hideOnboarding() {
  document.getElementById('onboarding-panel').style.display = 'none';
  document.getElementById('chat-messages').style.display = 'flex';
  document.querySelector('.chat-input-area').style.display = 'flex';
}

function obSetStep(step) {
  [1, 2, 3].forEach(n => {
    document.getElementById(`ob-step-${n}`).style.display = n === step ? 'block' : 'none';
    const dot = document.getElementById(`ob-dot-${n}`);
    dot.classList.toggle('active', n <= step);
    dot.classList.toggle('done', n < step);
  });
}

// Toggle goal chip + expand/collapse inline detail card
function obToggleGoal(chip) {
  const key = chip.dataset.key;
  const isSelected = chip.classList.contains('selected');
  const card = document.getElementById(`ob-detail-${key}`);

  if (isSelected) {
    // Deselect — collapse card and remove from state
    chip.classList.remove('selected');
    if (card) {
      card.style.display = 'none';
      // Clear inputs
      card.querySelectorAll('input').forEach(i => i.value = '');
    }
  } else {
    // Select — expand card
    chip.classList.add('selected');
    if (card) {
      card.style.display = 'block';
      // Focus the amount input
      setTimeout(() => card.querySelector('.ob-amount')?.focus(), 50);
    }
  }
}

// Topic chips (step 3) still use simple toggle — no detail card
document.addEventListener('click', function (e) {
  const chip = e.target.closest('#ob-topic-chips .ob-chip');
  if (!chip) return;
  chip.classList.toggle('selected');
});

function obNext(step) {
  if (step === 1) {
    // Collect structured goals from selected chips + their detail cards
    ob.selectedGoals = [];
    document.querySelectorAll('#ob-goal-chips .ob-chip.selected').forEach(chip => {
      const key = chip.dataset.key;
      const card = document.getElementById(`ob-detail-${key}`);
      const amountInput = card ? card.querySelector('.ob-amount') : null;
      const dateInput   = card ? card.querySelector('.ob-date')   : null;
      ob.selectedGoals.push({
        key,
        description: OB_GOAL_DESCRIPTIONS[key] || key,
        amount: amountInput && amountInput.value ? parseFloat(amountInput.value) : null,
        date:   dateInput   && dateInput.value   ? dateInput.value + '-01'       : null,
      });
    });
    ob.customGoal = document.getElementById('ob-goal-custom').value.trim();
    obSetStep(2);
  } else if (step === 2) {
    obSetStep(3);
  }
}

function obBack(step) {
  obSetStep(step - 1);
}

function obSkip(step) {
  if (step === 1) obSetStep(2);
}

function obSelectStyle(btn) {
  document.querySelectorAll('.ob-style-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  ob.selectedStyle = btn.dataset.value;
}

// Build a fully-formed natural language goal message from a structured goal object
function obBuildGoalMessage(goal) {
  // goal = { description, amount, date }  e.g. "save for a house deposit", 20000, "2027-06-01"
  let msg = `I want to ${goal.description}`;
  if (goal.amount) {
    msg += ` of £${Number(goal.amount).toLocaleString('en-GB')}`;
  }
  if (goal.date) {
    const d = new Date(goal.date);
    const month = d.toLocaleString('en-GB', { month: 'long' });
    const year  = d.getFullYear();
    msg += ` by ${month} ${year}`;
  }
  return msg;  // e.g. "I want to save for a house deposit of £20,000 by June 2027"
}

async function obFinish() {
  // Collect topics
  ob.selectedTopics = [...document.querySelectorAll('#ob-topic-chips .ob-chip.selected')]
    .map(c => c.dataset.value);

  hideOnboarding();
  showWelcome();

  // Build fully-formed goal messages (no chat refinement needed later)
  const goalMessages = ob.selectedGoals.map(obBuildGoalMessage);
  if (ob.customGoal) goalMessages.push(ob.customGoal);

  // Save goals silently in sequence
  for (const msg of goalMessages) {
    await silentChat(msg);
  }

  // Save preferences
  if (ob.selectedStyle !== 'balanced' || ob.selectedTopics.length > 0) {
    let prefMsg = '';
    if (ob.selectedStyle === 'concise')  prefMsg = 'Please keep your answers brief and to the point.';
    if (ob.selectedStyle === 'detailed') prefMsg = 'Please give me detailed explanations with examples.';
    if (ob.selectedTopics.length > 0)
      prefMsg += (prefMsg ? ' ' : '') + `I am interested in these topics: ${ob.selectedTopics.join(', ')}.`;
    if (prefMsg) await silentChat(prefMsg);
  }

  // Build confirmation message showing what was saved with full details
  let goalSummary = '';
  if (goalMessages.length > 0) {
    const lines = ob.selectedGoals.map(g => {
      let line = `**${g.description.replace(/^[a-z]/, c => c.toUpperCase())}**`;
      if (g.amount) line += ` — £${Number(g.amount).toLocaleString('en-GB')}`;
      if (g.date)   { const d = new Date(g.date); line += ` by ${d.toLocaleString('en-GB', {month:'long'})} ${d.getFullYear()}`; }
      return `• ${line}`;
    });
    if (ob.customGoal) lines.push(`• **${ob.customGoal}**`);
    goalSummary = `\n\nI've saved your goal${goalMessages.length > 1 ? 's' : ''}:\n${lines.join('\n')}`;
  }
  const topicSummary = ob.selectedTopics.length > 0
    ? `\n\nI'll focus on **${ob.selectedTopics.join(', ')}** in my coaching.`
    : '';

  appendAgentMessage(
    `All set! 🎉${goalSummary}${topicSummary}\n\nWhat would you like to explore first?`,
    false, []
  );

  // Update userProfile so chips immediately reflect what was just set
  if (!userProfile) userProfile = { active_goals: [], preferences: { preferred_topics: [] }, conversation_count: 0 };
  userProfile.active_goals = ob.selectedGoals.map((g, i) => ({ goal_id: `GOAL_${i+1}`, description: g.description }));
  if (ob.customGoal) userProfile.active_goals.push({ goal_id: `GOAL_custom`, description: ob.customGoal });
  if (ob.selectedTopics.length > 0) userProfile.preferences.preferred_topics = ob.selectedTopics;
  userProfile.conversation_count = 1;   // mark as no longer first visit
  saveCachedProfile(userProfile);        // persist so next open is instant
  renderInitialChips(userProfile);
}

// Send a message to the agent without showing it in the chat UI (for onboarding saves)
async function silentChat(text) {
  if (!sessionId || sessionId.startsWith('demo-') || sessionId.startsWith('offline-')) return;
  try {
    await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
  } catch { /* ignore */ }
}

// ---- Send message ----

function sendMessage() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text || isTyping) return;

  input.value = '';
  autoResize(input);
  hideSuggestions();
  sendToAgent(text);
}

function sendSuggestion(text) {
  hideSuggestions();
  sendToAgent(text);
}

async function sendToAgent(text) {
  if (isTyping) return;
  messageCount++;

  appendUserMessage(text);
  showTyping();
  isTyping = true;
  document.getElementById('send-btn').disabled = true;

  let response = null;
  let toolsUsed = [];
  let isLive = false;

  try {
    // Try FastAPI backend first
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEMO_TOKEN}`,
      },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });

    if (res.ok) {
      const data = await res.json();
      response = data.response;
      toolsUsed = data.tools_used || [];
      isLive = true;
    } else {
      response = getMockResponse(text);
    }
  } catch {
    // API offline — use intelligent mock responses for demo
    response = getMockResponse(text);
  }

  hideTyping();
  isTyping = false;
  document.getElementById('send-btn').disabled = false;

  appendAgentMessage(response, isLive, toolsUsed);

  // Show context-sensitive follow-up suggestions after 2nd+ message
  if (messageCount >= 2) {
    showContextSuggestions(text);
  }
}

// ---- Mock responses for offline demo ----

function getMockResponse(userText) {
  const t = userText.toLowerCase();

  if (t.includes('baby') || t.includes('nursery') || t.includes('childcare')) {
    return "I can see from your recent transactions that you've started paying nursery fees at **Busy Bees Nursery** (£850/month), along with baby equipment purchases at Mamas and Papas totalling £649. It looks like you may have recently had a baby — congratulations! 🎉\n\nIs that right?\n\nI can help you:\n• Review your budget to accommodate childcare costs\n• Check whether you qualify for **Tax-Free Childcare** (save up to £2,000/year)\n• Ensure your emergency fund is adequate for a growing family\n\nWhat would you like to start with?";
  }

  if (t.includes('spending') || t.includes('spend') || t.includes('much am i')) {
    return "Based on your last 3 months of transactions:\n\n💰 **Average monthly income:** £3,800\n💸 **Average monthly spend:** £2,068\n✅ **Monthly surplus:** £1,732\n\nYour **top spending categories** are:\n1. Other / Nursery — £1,230/month\n2. Groceries — £720/month\n3. Shopping — £589/month\n\nYour spending trend is **stable** — and your income increased recently which has improved your surplus significantly. Would you like me to identify where you could save more?";
  }

  if (t.includes('health score') || t.includes('financial health')) {
    return "Here's your financial health score:\n\n🏆 **Overall: 74/100 — Grade B (Good)**\n\n**Pillar breakdown:**\n• Savings Rate: 18% ✅ (target 20%)\n• Spend Stability: Good — consistent patterns\n• Essentials Balance: 52% of spend ✅\n• Emergency Buffer: 1.8 months ⚠️ (target 3)\n• Subscription Load: Moderate\n\n**Key insight:** Your main opportunity is building your emergency fund. With your current surplus of £1,732/month, you could reach a 3-month buffer in about **4 months** by setting aside £500/month.";
  }

  if (t.includes('mortgage') || t.includes('afford') || t.includes('house') || t.includes('borrow')) {
    return "Based on your verified income of £3,800/month, here's your mortgage picture:\n\n🏠 **Max loan by income (4.5× rule):** ~£205,200\n📊 **Stress-tested monthly payment** (at +3%): £1,142\n💰 **Surplus after mortgage:** ~£590/month\n\n**Deposit needed:**\n• 5% LTV: £10,800 on a £216k property\n• 10% LTV: £21,600\n\n⚠️ These are indicative figures for guidance only — not a mortgage offer. For a formal Decision in Principle, I can connect you with a mortgage adviser.\n\nWould you like me to model a specific property price?";
  }

  if (t.includes('save') || t.includes('savings') || t.includes('saving')) {
    return "Here are your top savings opportunities based on your actual spending:\n\n💡 **1. Eating out — £340/month**\nYou're spending 28% above the typical benchmark. Cutting back by £80/month = **£960/year**.\n\n💡 **2. Subscriptions — £68/month**\nYou have 6 active subscriptions. Worth reviewing which you use regularly.\n\n💡 **3. Emergency fund**\nYou have £3,250 saved but your buffer is only 1.8 months. Consider a standing order of £300/month to your saver account.\n\nTotal potential annual saving: **£1,920+**. Want me to build a budget plan around these goals?";
  }

  if (t.includes('income') || t.includes('pay rise') || t.includes('salary')) {
    return "I can see your salary increased from **£3,200 to £3,800** recently — that's an 18.75% rise. Well done! 🎉\n\nWith an extra **£600/month**, here's how I'd suggest allocating it:\n\n• **£200/month** → Emergency fund (reach 3-month buffer in ~6 months)\n• **£200/month** → ISA or savings account (tax-efficient growth)\n• **£100/month** → Extra mortgage/debt overpayment\n• **£100/month** → Discretionary / lifestyle upgrade\n\nWould you like me to build a detailed budget plan around your new income?";
  }

  // Default fallback
  return "That's a great question. To give you an accurate answer, let me pull up your transaction data...\n\nBased on your recent transactions and account activity, I can see you have a **monthly surplus of approximately £1,732** after all expenses. Would you like me to dive deeper into any specific area of your finances?";
}

// ---- DOM helpers ----

function appendUserMessage(text) {
  const now  = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div class="msg user">
      <div class="msg-avatar">AJ</div>
      <div>
        <div class="msg-bubble">${escapeHtml(text)}</div>
      </div>
    </div>
    <div class="msg-time">${now}</div>
  `;
  getMessagesEl().appendChild(wrap);
  scrollToBottom();
}

function appendAgentMessage(text, isLive = false, toolsUsed = []) {
  const now  = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

  // Source badge: green = live API + tools, amber = live API no tools, grey = mock
  let badge = '';
  if (isLive && toolsUsed.length > 0) {
    const toolList = toolsUsed.map(t => t.replace(/_tool$/, '').replace(/_/g, ' ')).join(', ');
    badge = `<div class="msg-source live-tools" title="Tools used: ${toolList}">⚡ Live · Tools: ${toolList}</div>`;
  } else if (isLive) {
    badge = `<div class="msg-source live-no-tools" title="Response from live API">⚡ Live · No tool call</div>`;
  } else {
    badge = `<div class="msg-source mock" title="API offline — showing demo response">🔌 Demo mode (API offline)</div>`;
  }

  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div class="msg agent">
      <div class="msg-avatar">AI</div>
      <div>
        <div class="msg-bubble">${renderMarkdown(text)}</div>
        ${badge}
      </div>
    </div>
    <div class="msg-time">${now}</div>
  `;
  getMessagesEl().appendChild(wrap);
  scrollToBottom();
}

function showTyping() {
  const el = document.createElement('div');
  el.id = 'typing-msg';
  el.innerHTML = `
    <div class="msg agent">
      <div class="msg-avatar">AI</div>
      <div class="msg-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  getMessagesEl().appendChild(el);
  scrollToBottom();
}

function hideTyping() {
  document.getElementById('typing-msg')?.remove();
}

function hideSuggestions() {
  const el = document.getElementById('chat-suggestions');
  if (el) el.style.display = 'none';
}

function showContextSuggestions(lastMessage) {
  const el = document.getElementById('chat-suggestions');
  if (!el) return;
  const t = lastMessage.toLowerCase();
  const hasGoals = userProfile && userProfile.active_goals && userProfile.active_goals.length > 0;

  let chips = [];

  if (t.includes('baby') || t.includes('nursery')) {
    chips = ['Build a childcare budget', 'Check Tax-Free Childcare', 'Review emergency fund'];
  } else if (t.includes('mortgage')) {
    chips = ['Model £250,000 mortgage', 'How much deposit do I need?', 'Speak to a mortgage adviser'];
  } else if (t.includes('spending') || t.includes('spend')) {
    chips = hasGoals
      ? ['Show savings opportunities', 'Check my goal progress', 'Build a budget plan']
      : ['Show savings opportunities', 'Set a savings goal', 'Build a budget plan'];
  } else if (t.includes('goal')) {
    chips = ['How much am I saving each month?', 'Build a budget plan', 'Where can I save money?'];
  } else if (t.includes('health') || t.includes('score')) {
    chips = hasGoals
      ? ['Check my goal progress', 'Where can I save money?', 'Build a budget plan']
      : ['Set a savings goal', 'Where can I save money?', 'Build a budget plan'];
  } else {
    chips = hasGoals
      ? ['Check my goal progress', 'How much am I spending?', 'Can I afford a mortgage?']
      : ['Set a savings goal', 'How much am I spending?', 'Can I afford a mortgage?'];
  }

  el.innerHTML = chips.map(c =>
    `<button class="suggestion-chip" onclick="sendSuggestion('${c.replace(/'/g, "\\'")}')">${c}</button>`
  ).join('');
  el.style.display = 'flex';
}

function getMessagesEl() {
  return document.getElementById('chat-messages');
}

function scrollToBottom() {
  const el = getMessagesEl();
  el.scrollTop = el.scrollHeight;
}

// ---- Minimal markdown renderer ----
function renderMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')   // bold
    .replace(/\*(.+?)\*/g, '<em>$1</em>')               // italic
    .replace(/\n/g, '<br/>');                            // newlines
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---- Input helpers ----

function handleInputKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 80) + 'px';
}
