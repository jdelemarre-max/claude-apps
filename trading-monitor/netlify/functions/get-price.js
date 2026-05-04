// netlify/functions/get-price.js
// Fetches live price for any ticker from Yahoo Finance.
// Cache 60s per ticker.

const cache = new Map();
const TTL = 60000;

export default async (request) => {
  const url = new URL(request.url);
  const ticker = (url.searchParams.get('ticker') || 'ALT').toUpperCase();
  
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(ticker)) {
    return Response.json({ error: 'Invalid ticker' }, { status: 400 });
  }
  
  const cached = cache.get(ticker);
  if (cached && Date.now() - cached.t < TTL) {
    return Response.json(cached.data, { headers: corsHeaders() });
  }
  
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=1d`, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    if (!r.ok) throw new Error(`Yahoo ${r.status}`);
    const j = await r.json();
    const result = j.chart?.result?.[0];
    if (!result) throw new Error('No data');
    
    const meta = result.meta;
    const data = {
      ticker,
      price: meta.regularMarketPrice,
      previousClose: meta.previousClose || meta.chartPreviousClose,
      change: meta.regularMarketPrice - (meta.previousClose || meta.chartPreviousClose),
      changePercent: ((meta.regularMarketPrice - (meta.previousClose || meta.chartPreviousClose)) / (meta.previousClose || meta.chartPreviousClose)) * 100,
      currency: meta.currency || 'USD',
      marketState: meta.marketState,
      timestamp: new Date().toISOString()
    };
    
    cache.set(ticker, { t: Date.now(), data });
    return Response.json(data, { headers: corsHeaders() });
  } catch (err) {
    return Response.json({ error: err.message, ticker }, { status: 500, headers: corsHeaders() });
  }
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'public, max-age=60',
    'Content-Type': 'application/json'
  };
}

export const config = { path: '/api/price' };
