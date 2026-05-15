// netlify/functions/briefing.js
// Backend voor DCA Briefing PWA.
// Parallel calls naar Notion (top 3 NU-taken) + Anthropic (quote in jop-voice).

const NOTION_VERSION = "2022-06-28";
const NOTION_DB_ACTION_BOARD = "56a334ea9e874ec1ade0d1ee073d4528";
const ANTHROPIC_MODEL = "claude-sonnet-4-6";

const QUOTE_SYSTEM = `Je bent Jop's eigen stem: Nederlands Jeugdkampioen U20 1994, IM, fulltime schaaktrainer sinds 2004 (DCA Oegstgeest), biotech-trader op pro-niveau. Schrijf één quote (max 25 woorden) in Jop's stijl: direct, concreet, geen platitudes, scherp of contra-intuïtief. Onderwerp: schaak, biotech/markten, of stoïcijns. Bekende denker (Capablanca, Tartakower, Lasker, Aurelius, Munger, Taleb) of origineel. Geen aanhalingstekens, geen attributie, alleen de zin. Geen emoji.`;

const QUOTE_USER = `Geef vandaag's quote. Vermijd: "geloof in jezelf", "elke dag een nieuwe kans", "alles is mogelijk", "je kunt het". Wel: scherp, contra-intuïtief, mooi precies, of pijnlijk waar.`;

async function fetchNotionTasks(token) {
  const res = await fetch(
    `https://api.notion.com/v1/databases/${NOTION_DB_ACTION_BOARD}/query`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        filter: {
          property: "Status",
          select: { equals: "🔴 NU" },
        },
        sorts: [{ property: "Priority", direction: "ascending" }],
        page_size: 3,
      }),
    }
  );

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Notion API ${res.status}: ${text.slice(0, 300)}`);
  }

  const data = await res.json();
  return data.results.map((page) => {
    const titleProp = page.properties.Task?.title || [];
    const priorityProp = page.properties.Priority?.select?.name || "";
    const projectProp = page.properties.Project?.select?.name || "";
    return {
      id: page.id,
      task: titleProp.map((t) => t.plain_text).join("") || "(zonder titel)",
      priority: priorityProp,
      project: projectProp,
      url: page.url,
    };
  });
}

async function fetchQuote(apiKey) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: ANTHROPIC_MODEL,
      max_tokens: 150,
      system: QUOTE_SYSTEM,
      messages: [{ role: "user", content: QUOTE_USER }],
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Anthropic API ${res.status}: ${text.slice(0, 300)}`);
  }

  const data = await res.json();
  const text = (data.content || [])
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join(" ")
    .trim();

  // strip aanhalingstekens als het model er toch een produceert
  return text.replace(/^["'""'']|["'""'']$/g, "").trim();
}

export default async (req) => {
  const url = new URL(req.url);
  const providedKey = url.searchParams.get("key");
  const expectedKey = process.env.ACCESS_KEY;
  const notionToken = process.env.NOTION_TOKEN;
  const anthropicKey = process.env.ANTHROPIC_API_KEY;

  if (!expectedKey || !notionToken || !anthropicKey) {
    return new Response(
      JSON.stringify({ error: "Server niet geconfigureerd" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  if (providedKey !== expectedKey) {
    return new Response(JSON.stringify({ error: "Forbidden" }), {
      status: 403,
      headers: { "Content-Type": "application/json" },
    });
  }

  // parallel — slowest wins
  const [tasksResult, quoteResult] = await Promise.allSettled([
    fetchNotionTasks(notionToken),
    fetchQuote(anthropicKey),
  ]);

  const tasks =
    tasksResult.status === "fulfilled"
      ? tasksResult.value
      : { _error: tasksResult.reason?.message || "Notion failed" };

  const quote =
    quoteResult.status === "fulfilled"
      ? quoteResult.value
      : null;

  return new Response(
    JSON.stringify({
      quote,
      quoteError: quoteResult.status === "rejected"
        ? quoteResult.reason?.message
        : null,
      tasks: Array.isArray(tasks) ? tasks : [],
      tasksError: tasks._error || null,
      generatedAt: new Date().toISOString(),
    }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    }
  );
};
