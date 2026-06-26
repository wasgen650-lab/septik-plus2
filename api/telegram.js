/**
 * Telegram-OpenHands Bridge - Vercel Serverless Version
 * Endpoint: /api/telegram
 */

const https = require('https');

const TELEGRAM_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '8888279961:AAFy9JV_1-wziF5kSYabn_Jtr-UX6vxi4NQ';
const OPENHANDS_API_KEY = process.env.OPENHANDS_API_KEY;
const ALLOWED_USER_ID = process.env.ALLOWED_USER_ID || null;

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(200).send('OK');
    }

    try {
        const { message } = req.body;

        if (!message || !message.text) {
            return res.status(200).send('OK');
        }

        const chatId = message.chat.id;
        const text = message.text;
        const userId = message.from.id;
        const userName = message.from.first_name || 'User';

        // Check access
        if (ALLOWED_USER_ID && userId.toString() !== ALLOWED_USER_ID) {
            await sendTelegram(chatId, '⛔ Доступ запрещён');
            return res.status(200).send('OK');
        }

        // Handle commands
        if (text.startsWith('/')) {
            if (text === '/start') {
                await sendTelegram(chatId, 
                    `👋 Привет, ${userName}!\n\n` +
                    `Я бот-связующее звено с OpenHands AI.\n\n` +
                    `Напишите мне сообщение - передам AI ассистенту.`
                );
            } else if (text === '/status') {
                await sendTelegram(chatId, 
                    `📋 Проверьте статус на:\nhttps://app.all-hands.dev`
                );
            }
            return res.status(200).send('OK');
        }

        console.log(`📩 From ${userName}: ${text.substring(0, 50)}...`);

        // Create OpenHands conversation
        await sendTelegram(chatId, '🤔 Создаю задачу для AI...');

        const result = await createConversation(text);

        if (result.error) {
            await sendTelegram(chatId, `❌ Ошибка: ${result.error}`);
        } else {
            const convId = result.conversation_id;
            await sendTelegram(chatId, 
                `✅ Задача создана!\n\n` +
                `📋 ID: \`${convId}\`\n\n` +
                `⏳ AI обрабатывает запрос (1-2 мин)\n\n` +
                `🔗 https://app.all-hands.dev/conversations/${convId}`
            );
        }

        return res.status(200).send('OK');

    } catch (error) {
        console.error('Error:', error);
        return res.status(500).send('Error');
    }
}

async function sendTelegram(chatId, text) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            chat_id: chatId,
            text,
            parse_mode: 'Markdown'
        });

        const options = {
            hostname: 'api.telegram.org',
            port: 443,
            path: `/bot${TELEGRAM_TOKEN}/sendMessage`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => resolve(body));
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function createConversation(message) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            initial_message: {
                content: [{ type: 'text', text: message }]
            }
        });

        const options = {
            hostname: 'app.all-hands.dev',
            port: 443,
            path: '/api/v1/app-conversations',
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENHANDS_API_KEY}`,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(body);
                    const convId = result.app_conversation_id || result.id;
                    if (convId) {
                        resolve({ conversation_id: convId });
                    } else {
                        resolve({ error: body.substring(0, 200) });
                    }
                } catch (e) {
                    resolve({ error: e.message });
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}
