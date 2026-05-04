// netlify/functions/get-data.js
// Reads positions/scenarios per ticker from Notion. Filters on Ticker property.

const cache = new Map();
const TTL = 30000;

export default async (request) => {
  const url = new URL(request.url);
  const type = url.searchParams.get('type') || 'positions';
  const ticker = (url.searchParams.get('ticker') || '').toUpperCase();
  
  const cacheKey = `${type}:${ticker}`;
  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.t < TTL) {
    return Response.json(cached.data, { headers: cors() });
  }
  
  const dbId = type === 'positions'
    ? Netlify.env.get('NOTION_POSITIONS_DB')
    : type === 'catalysts'
    ? Netlify.env.get('NOTION_CATALYSTS_DB')
    : type === 'scenarios'
    ? Netlify.env.get('NOTION_SCENARIOS_DB')
    : null;
  
  const apiKey = Netlify.env.get('NOTION_API_KEY');
  
  if (!dbId || !apiKey) {
    return Response.json({ data: [], error: 'Notion env not configured', source: 'fallback' }, { headers: cors() });
  }
  
  try {
    const filter = ticker ? { property: 'Ticker', select: { equals: ticker } } : undefined;
    const r = await fetch(`https://api.notion.com/v1/databases/${dbId}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(filter ? { filter, page_size: 100 } : { page_size: 100 })
    });
    
    if (!r.ok) throw new Error(`Notion ${r.status}`);
    const j = await r.json();
    const data = j.results.map(p => simplifyProps(p.properties));
    const result = { data, source: 'notion', ticker };
    cache.set(cacheKey, { t: Date.now(), data: result });
    return Response.json(result, { headers: cors() });
  } catch (err) {
    return Response.json({ data: [], error: err.message, source: 'error' }, { status: 500, headers: cors() });
  }
};

function simplifyProps(props) {
  const out = {};
  for (const [k, v] of Object.entries(props)) {
    if (v.type === 'title') out[k] = v.title.map(t => t.plain_text).join('');
    else if (v.type === 'rich_text') out[k] = v.rich_text.map(t => t.plain_text).join('');
    else if (v.type === 'number') out[k] = v.number;
    else if (v.type === 'select') out[k] = v.select?.name || null;
    else if (v.type === 'multi_select') out[k] = v.multi_select.map(s => s.name);
    else if (v.type === 'date') out[k] = v.date?.start || null;
    else if (v.type === 'checkbox') out[k] = v.checkbox;
    else if (v.type === 'url') out[k] = v.url;
  }
  return out;
}

function cors() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'public, max-age=30',
    'Content-Type': 'application/json'
  };
}

export const config = { path: '/api/data' };
