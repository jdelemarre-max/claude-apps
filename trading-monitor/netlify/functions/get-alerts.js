// netlify/functions/get-alerts.js
import { getStore } from "@netlify/blobs";

export default async (request) => {
  const url = new URL(request.url);
  const ticker = url.searchParams.get('ticker'); // optional filter
  
  try {
    const store = getStore('tv-alerts');
    let alerts = await store.get('recent', { type: 'json' }) || [];
    const tickers = await store.get('tickers', { type: 'json' }) || [];
    
    if (ticker) {
      alerts = alerts.filter(a => a.ticker === ticker.toUpperCase());
    }
    
    return Response.json({ alerts, tickers, count: alerts.length }, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=15',
        'Content-Type': 'application/json'
      }
    });
  } catch (err) {
    return Response.json({ alerts: [], tickers: [], error: err.message }, { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } });
  }
};

export const config = { path: '/api/alerts' };
