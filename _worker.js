export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        
        // Jika path /bot — handle webhook
        if (url.pathname === '/bot') {
            if (request.method === 'GET') {
                return new Response('⚛️ Quantum Bot is running!', { status: 200 });
            }
            
            if (request.method === 'POST') {
                const BOT_TOKEN = env.BOT_TOKEN;
                const MASTER_SEED = env.MASTER_SEED;
                
                try {
                    const update = await request.json();
                    
                    if (update.message?.text === '/start') {
                        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                chat_id: update.message.chat.id,
                                text: '⚛️ *QUANTUM ENTANGLEMENT IDENTITY GATE*\n\n🖥️ *Cloudflare Worker — JavaScript Murni*\n\n📌 Klik butang di bawah.',
                                parse_mode: 'Markdown',
                                reply_markup: {
                                    keyboard: [[{ text: 'LOG MASUK', request_contact: true }]],
                                    one_time_keyboard: true,
                                    resize_keyboard: true
                                }
                            })
                        });
                        return new Response('OK', { status: 200 });
                    }
                    
                    if (update.message?.contact) {
                        const userId = String(update.message.from.id);
                        const chatId = update.message.chat.id;
                        
                        if (String(update.message.contact.user_id) !== userId) {
                            await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ chat_id: chatId, text: '❌ Entropi tidak sepadan.' })
                            });
                            return new Response('OK', { status: 200 });
                        }
                        
                        // Generate token (ringkas)
                        const seedHex = Array.from({length: 32}, () => Math.floor(Math.random() * 16).toString(16)).join('');
                        const combined = seedHex + ':' + userId;
                        const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(combined));
                        const hash = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
                        
                        const tokenData = {
                            u: userId,
                            s: seedHex,
                            h: hash,
                            exp: Math.floor(Date.now() / 1000) + 600,
                            tid: Array.from({length: 16}, () => Math.floor(Math.random() * 16).toString(16)).join(''),
                            qid: 'QuantumMatrix_' + hash.substring(0, 16)
                        };
                        
                        const tokenSafe = btoa(JSON.stringify(tokenData));
                        const fullUrl = `https://schr-dinger-hash.pages.dev?token=${encodeURIComponent(tokenSafe)}`;
                        
                        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                chat_id: chatId,
                                text: `<b>[⚛️ ENTANGLEMENT HASH]</b>\n\n<b>• User ID:</b> <code>${userId}</code>\n<b>• Hash:</b> <code>${hash.substring(0, 16)}...</code>`,
                                parse_mode: 'HTML'
                            })
                        });
                        
                        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                chat_id: chatId,
                                text: `🔗 <a href="${fullUrl}">🌌 Akses Portal Kuantum</a>`,
                                parse_mode: 'HTML'
                            })
                        });
                        
                        return new Response('OK', { status: 200 });
                    }
                    
                    return new Response('OK', { status: 200 });
                } catch (error) {
                    return new Response('Error: ' + error.message, { status: 500 });
                }
            }
        }
        
        // Untuk semua path lain — serve static files (index.html, dll.)
        return env.ASSETS.fetch(request);
    }
};
