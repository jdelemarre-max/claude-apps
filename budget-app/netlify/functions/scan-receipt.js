// Receipt OCR via Anthropic Claude vision
// POST { image: "data:image/jpeg;base64,..." }
// Returns { amount, date, vendor, categoryId } or { error }

export default async (req) => {
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({error:'Method not allowed'}), {
      status: 405, headers: {'content-type':'application/json'}
    });
  }

  const apiKey = Netlify.env.get('ANTHROPIC_API_KEY');
  if (!apiKey) {
    return new Response(JSON.stringify({error:'ANTHROPIC_API_KEY niet gezet'}), {
      status: 500, headers: {'content-type':'application/json'}
    });
  }

  let body;
  try { body = await req.json(); } catch(e) {
    return new Response(JSON.stringify({error:'Invalid JSON'}), {
      status: 400, headers: {'content-type':'application/json'}
    });
  }
  if (!body.image || typeof body.image !== 'string') {
    return new Response(JSON.stringify({error:'image (base64 data URL) required'}), {
      status: 400, headers: {'content-type':'application/json'}
    });
  }

  const m = body.image.match(/^data:(image\/[a-z]+);base64,(.+)$/);
  if (!m) {
    return new Response(JSON.stringify({error:'Verwacht data:image/...;base64 URL'}), {
      status: 400, headers: {'content-type':'application/json'}
    });
  }
  const mediaType = m[1];
  const base64 = m[2];

  const prompt = `Analyseer deze foto van een Nederlandse bon/factuur en extract de info.

Output STRIKT in JSON, zonder markdown, zonder uitleg:
{
  "amount": 12.34,
  "date": "2026-05-04",
  "vendor": "Albert Heijn",
  "categoryId": "food"
}

Regels:
- amount: EINDtotaal in euro's als decimal (geen euroteken). Bij twijfel: het grootste totaalbedrag onderaan.
- date: ISO YYYY-MM-DD. Onleesbaar? Gebruik vandaag.
- vendor: bedrijfsnaam kort (zonder BV/NV).
- categoryId: kies EEN ID:
  food (supermarkt: AH, Jumbo, Lidl, Plus, Aldi, Dirk)
  eating (restaurant, cafe, bar, take-away, snackbar)
  transport (NS, OV, taxi, parkeren)
  fuel (Shell, BP, Esso, Tinq, tankstation)
  home (huur, hypotheek, meubels, IKEA, Karwei, Praxis)
  utilities (Vattenfall, Eneco, Essent, water, internet, KPN)
  subscriptions (Netflix, Spotify, abonnementen)
  health (apotheek, dokter, fysio, tandarts)
  leisure (bioscoop, sport, museum, hobby)
  clothing (kleding, schoenen, H&M, Zara)
  gifts (cadeaus, bloemen)
  other (alles wat niet past)

Geen bon zichtbaar? Return: {"error": "geen bon zichtbaar"}.`;

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-5',
        max_tokens: 500,
        messages: [{
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type: mediaType, data: base64 } },
            { type: 'text', text: prompt }
          ]
        }]
      })
    });

    const data = await resp.json();
    if (!resp.ok) {
      return new Response(JSON.stringify({error:'Claude API error', detail: data}), {
        status: 502, headers: {'content-type':'application/json'}
      });
    }

    const text = data.content?.[0]?.text || '';
    const clean = text.replace(/```json\s*/g,'').replace(/```\s*/g,'').trim();
    let parsed;
    try { parsed = JSON.parse(clean); } catch(e) {
      return new Response(JSON.stringify({error:'Kon Claude output niet parsen', raw: text}), {
        status: 500, headers: {'content-type':'application/json'}
      });
    }

    if (parsed.error) {
      return new Response(JSON.stringify(parsed), {
        status: 200, headers: {'content-type':'application/json'}
      });
    }

    return new Response(JSON.stringify({
      amount: Number(parsed.amount) || 0,
      date: parsed.date || new Date().toISOString().split('T')[0],
      vendor: parsed.vendor || '',
      categoryId: parsed.categoryId || 'other'
    }), {
      status: 200, headers: {'content-type':'application/json'}
    });
  } catch(e) {
    return new Response(JSON.stringify({error:'Fetch failed: ' + e.message}), {
      status: 500, headers: {'content-type':'application/json'}
    });
  }
};
