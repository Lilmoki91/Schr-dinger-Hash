// ============================================================
// ⚛️ QUANTUM ENTANGLEMENT BOT — Cloudflare Pages Function
// ============================================================

// ============================================================
// SHA-256 (JavaScript Murni)
// ============================================================
async function sha256(message) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// ============================================================
// FIBONACCI TTL
// ============================================================
function getFibonacciTTL(count) {
    const fib = [1, 1, 2, 3, 5, 8, 13, 21];
    const idx = Math.min(count - 1, fib.length - 1);
    const ttl = fib[idx] * 30;
    return Math.min(ttl, 600);
}

// ============================================================
// QUANTUM MATRIX ID
// ============================================================
async function generateQuantumMatrixId(userId, MASTER_SEED) {
    const combined = `${MASTER_SEED}:${userId}`;
    const hashHex = await sha256(combined);
    return `QuantumMatrix_${hashHex.substring(0, 16)}`;
}

// ============================================================
// ⚛️ ENTANGLEMENT HASH — FORMULA SAMA DENGAN FRONTEND
// ============================================================
async function calculateEntanglementHash(userId, seedHex) {
    const combined = `${seedHex}:${userId}`;
    const hash1 = await sha256(combined);
    
    const qubits = [];
    for (let i = 0; i < 8; i++) {
        const hexVal = parseInt(hash1[i], 16);
        qubits.push(hexVal % 2 === 1 ? 1 : 0);
    }
    
    for (let i = 0; i < 8; i++) {
        if (parseInt(hash1[i + 8], 16) > 7) qubits[i] ^= 1;
    }
    
    qubits[1] ^= qubits[0];
    qubits[3] ^= qubits[2];
    qubits[5] ^= qubits[4];
    qubits[7] ^= qubits[6];
    qubits[3] ^= qubits[0];
    qubits[5] ^= qubits[2];
    qubits[7] ^= qubits[4];
    qubits[6] ^= qubits[1];
    
    const stateStr = JSON.stringify(qubits);
    return await sha256(stateStr);
}

// ============================================================
// RANDOM HEX
// ============================================================
function randomHex(length) {
    const chars = 'abcdef0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars[Math.floor(Math.random() * 16)];
    }
    return result;
}

// ============================================================
// GENERATE TOKEN
// ============================================================
async function generateToken(userId, count, MASTER_SEED) {
    const ttlSeconds = getFibonacciTTL(count);
    const expiry = Math.floor(Date.now() / 1000) + ttlSeconds;
    const tokenId = randomHex(16);
    const seedHex = randomHex(32);
    
    const quantumHash = await calculateEntanglementHash(userId, seedHex);
    const quantumMatrixId = await generateQuantumMatrixId(userId, MASTER_SEED);
    
    const qStateVisual = quantumHash.substring(0, 8).split('').map(c =>
        parseInt(c, 16) % 2 === 0 ? '|0⟩' : '|1⟩'
    ).join(' ');
    
    const tokenData = {
        u: userId,
        s: seedHex,
        h: quantumHash,
        exp: expiry,
        tid: tokenId,
        qid: quantumMatrixId
    };
    
    const tokenStr = JSON.stringify(tokenData);
    const tokenSafe = btoa(tokenStr);
    const fullUrl = `https://schr-dinger-hash.pages.dev?token=${encodeURIComponent(tokenSafe)}`;
    
    const msg = 
        `<b>[⚛️ ENTANGLEMENT HASH TERKUNCI]</b>\n\n` +
        `<b>🖥️ Platform:</b> <i>Cloudflare Pages Function</i>\n` +
        `<b>🔬 Formula:</b> <i>Quantum Entanglement (JS Murni)</i>\n\n` +
        `<b>• User ID:</b> <code>${userId}</code>\n` +
        `<b>• Quantum Matrix ID:</b> <code>${quantumMatrixId}</code>\n` +
        `<b>• Akses ke-:</b> <code>${count}</code>\n` +
        `<b>• Token sah:</b> <code>${ttlSeconds} saat (${(ttlSeconds/60).toFixed(1)} minit)</code>\n` +
        `<b>• Seed:</b> <code>${seedHex.substring(0, 12)}...</code>\n` +
        `<b>• State 8-Qubit:</b> <code>${qStateVisual}</code>\n` +
        `<b>• Hash Kuantum:</b> <code>${quantumHash.substring(0, 16)}...</code>\n\n` +
        `<i>🌀 Hash dari Cloudflare Pages Function</i>`;
    
    return { msg, fullUrl };
}

// ============================================================
// TELEGRAM API
// ============================================================
async function sendTelegram(chatId, text, BOT_TOKEN, replyMarkup = null) {
    const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;
    
    const body = { chat_id: chatId, text: text, parse_mode: 'HTML' };
    if (replyMarkup) body.reply_markup = replyMarkup;
    
    await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
}

// ============================================================
// USER ACCESS COUNT (In-Memory)
// ============================================================
const userAccessCount = {};

// ============================================================
// HANDLER: POST
// ============================================================
export async function onRequestPost(context) {
    // ✅ Ambil dari environment variables — BUKAN hardcoded!
    const BOT_TOKEN = context.env.BOT_TOKEN;
    const MASTER_SEED = context.env.MASTER_SEED;
    
    try {
        const update = await context.request.json();
        
        if (update.message && update.message.text === '/start') {
            await sendTelegram(update.message.chat.id,
                '⚛️ *QUANTUM ENTANGLEMENT IDENTITY GATE*\n\n' +
                '🖥️ *Cloudflare Pages Function — JavaScript Murni*\n' +
                '🔬 Formula: *Entanglement Matematik Tulen*\n\n' +
                '📌 Klik butang *LOG MASUK* di bawah untuk verifikasi.',
                BOT_TOKEN,
                {
                    keyboard: [[{ text: 'LOG MASUK', request_contact: true }]],
                    one_time_keyboard: true,
                    resize_keyboard: true
                }
            );
            return new Response('OK', { status: 200 });
        }
        
        if (update.message && update.message.contact) {
            const contact = update.message.contact;
            const userId = String(update.message.from.id);
            const chatId = update.message.chat.id;
            
            if (String(contact.user_id) !== userId) {
                await sendTelegram(chatId, '❌ <b>Ralat:</b> Entropi fizikal tidak sepadan.', BOT_TOKEN);
                return new Response('OK', { status: 200 });
            }
            
            const count = (userAccessCount[userId] || 0) + 1;
            userAccessCount[userId] = count;
            
            const { msg, fullUrl } = await generateToken(userId, count, MASTER_SEED);
            
            await sendTelegram(chatId, msg, BOT_TOKEN);
            await sendTelegram(chatId, `🔗 <a href="${fullUrl}">🌌 Akses Portal Kuantum</a>`, BOT_TOKEN);
            
            return new Response('OK', { status: 200 });
        }
        
        return new Response('OK', { status: 200 });
        
    } catch (error) {
        console.error('Error:', error);
        return new Response('Error: ' + error.message, { status: 500 });
    }
}

// ============================================================
// HANDLER: GET
// ============================================================
export async function onRequestGet(context) {
    return new Response('⚛️ Quantum Bot is running!', { status: 200 });
}
