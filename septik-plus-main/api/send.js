export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const input = req.body;
  if (!input) {
    return res.status(400).json({ ok: false, error: 'No data' });
  }

  // Credentials from environment variables
  const tgBotToken = process.env.TG_BOT_TOKEN;
  const tgChatIds = process.env.TG_CHAT_IDS ? process.env.TG_CHAT_IDS.split(',') : [];

  if (!tgBotToken || tgChatIds.length === 0) {
    console.error('Missing TG_BOT_TOKEN or TG_CHAT_IDS');
    return res.status(500).json({ ok: false, error: 'Server configuration error' });
  }

  const form = input.form || '';
  let msg = '<b>Новая заявка с сайта Септик-Плюс</b>\n\n';

  if (form === 'calculator') {
    msg += '<b>Калькулятор:</b>\n';
    msg += `Услуга: ${escapeHtml(input.serviceType || '-')}\n`;
    msg += `Объём: ${escapeHtml(input.volume || '-')} м³\n`;
    msg += `Шланг: ${escapeHtml(input.hose || '-')} м\n`;
    if (input.urgent) msg += 'Срочно/Ночь: Да\n';
    if (input.hardAccess) msg += 'Трудный подъезд: Да\n';
    msg += `Цена: ${escapeHtml(input.price || '-')} руб.\n`;
    msg += `Телефон: ${escapeHtml(input.phone || '-')}`;
  } else if (form === 'contact') {
    msg += '<b>Обратная связь:</b>\n';
    msg += `Имя: ${escapeHtml(input.name || '-')}\n`;
    msg += `Орг: ${escapeHtml(input.org || '-')}\n`;
    msg += `Телефон: ${escapeHtml(input.phone || '-')}\n`;
    msg += `Сообщение: ${escapeHtml(input.message || '-')}`;
  } else if (form === 'error' && input.error) {
    console.log('Client JS error:', input.error);
    return res.status(200).json({ ok: true });
  } else {
    msg += `Неизвестная форма: ${JSON.stringify(input)}`;
  }

  // Send to all Telegram chats
  const url = `https://api.telegram.org/bot${tgBotToken}/sendMessage`;
  let allOk = true;

  try {
    for (const chatId of tgChatIds) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: chatId,
            text: msg,
            parse_mode: 'HTML',
            disable_web_page_preview: true
          })
        });

        const result = await response.json();
        if (!response.ok || !result.ok) {
          console.error(`Failed to send to chat ${chatId}:`, result);
          allOk = false;
        }
      } catch (error) {
        console.error(`Error sending to chat ${chatId}:`, error);
        allOk = false;
      }
    }

    if (allOk) {
      return res.status(200).json({ ok: true });
    } else {
      return res.status(500).json({ ok: false, error: 'Failed to send to some chats' });
    }
  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({ ok: false, error: 'Server error' });
  }
}

function escapeHtml(str) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(str).replace(/[&<>"']/g, (char) => map[char]);
}
