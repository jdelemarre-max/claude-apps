// netlify/functions/tv-webhook.js
import { getStore } from "@netlify/blobs";

export default async (request) => {
  if (request.method === 'OPTIONS') return new Response(null, { headers: cors() });
  if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });
  
  try {
    const body = await request.json();
    const expected = Netlify.env.get('TV_WEBHOOK_SECRET');
    if (expected && body.secret !== expected) return new Response('Unauthorized', { status: 401 });
    if (!body.ticker || body.price === undefined) return new Response('Missing ticker or price', { status: 400 });
    
    const store = getStore('tv-alerts');
    const existing = await store.get('recent', { type: 'json' }) || [];
    
    const alert = {
      id: Date.now().toString(36),
      ticker: body.ticker.toUpperCase(),
      price: parseFloat(body.price),
      alert_name: body.alert_name || 'Trigger hit',
      tv_time: body.time || null,
      received_at: new Date().toISOString()
    };
    existing.unshift(alert);
    existing.splice(100); // keep 100 across all tickers
    await store.setJSON('recent', existing);
    
    // Track unique tickers seen
    const tickers = await store.get('tickers', { type: 'json' }) || [];
    if (!tickers.includes(alert.ticker)) {
      tickers.push(alert.ticker);
      await store.setJSON('tickers', tickers);
    }
    
    return Response.json({ received: true, id: alert.id }, { headers: cors() });
  } catch (err) {
    return new Response(`Error: ${err.message}`, { status: 500, headers: cors() });
  }
};

function cors() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
}

export const config = { path: '/api/tv-webhook' };
