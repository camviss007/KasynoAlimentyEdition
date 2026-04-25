const env = process.env;

function normalizeWebhook(url) {
  let u = String(url || "").trim().replace(/^['"]|['"]$/g, "");
  u = u.replace("https://discord.com/api/webhooks/", "https://discord.com/api/v10/webhooks/");
  u = u.replace("https://discordapp.com/api/webhooks/", "https://discord.com/api/v10/webhooks/");
  return u.replace(/\/+$/, "");
}

function buildPayload(rows) {
  const medals = ["🥇", "🥈", "🥉"];
  const lines = rows.length
    ? rows.map(([nick, cash], i) => `${medals[i] || "•"} ${nick} — ${Math.floor(cash)}$`)
    : ["Brak danych leaderboardu."];
  return {
    embeds: [
      {
        title: "💰 Leaderboard",
        description: lines.join("\n"),
        color: 0x2ecc71,
        timestamp: new Date().toISOString(),
        footer: { text: "Auto refresh (GitHub Actions)" }
      }
    ]
  };
}

async function readLeaderboard(dbUrl) {
  const resp = await fetch(`${dbUrl.replace(/\/+$/, "")}/leaderboard.json`, {
    headers: { "Accept": "application/json", "User-Agent": "KasynoTopkaBot/2.0" }
  });
  if (!resp.ok) throw new Error(`Firebase GET ${resp.status}: ${await resp.text()}`);
  const data = (await resp.json()) || {};
  const rows = Object.entries(data)
    .map(([nick, cash]) => [String(nick || "").trim(), Number(cash) || 0])
    .filter(([nick]) => nick && nick.toLowerCase() !== "gracz")
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  return rows;
}

async function discordRequest(url, method, payload) {
  const resp = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "User-Agent": "KasynoTopkaBot/2.0"
    },
    body: JSON.stringify(payload)
  });
  if (resp.ok) {
    const txt = await resp.text();
    try { return txt ? JSON.parse(txt) : {}; } catch { return {}; }
  }
  const body = await resp.text();
  throw new Error(`Discord ${method} ${resp.status}: ${body}`);
}

async function main() {
  const dbUrl = String(env.FIREBASE_DB_URL || "").trim();
  const webhookUrl = normalizeWebhook(env.DISCORD_WEBHOOK_URL || "");
  const messageId = String(env.DISCORD_MESSAGE_ID || "").trim();

  if (!dbUrl || !webhookUrl) {
    throw new Error("Brak FIREBASE_DB_URL lub DISCORD_WEBHOOK_URL.");
  }
  if (!webhookUrl.includes("/api/v10/webhooks/")) {
    throw new Error("DISCORD_WEBHOOK_URL nie jest poprawnym webhookiem Discord API.");
  }

  const payload = buildPayload(await readLeaderboard(dbUrl));

  if (messageId) {
    try {
      await discordRequest(`${webhookUrl}/messages/${encodeURIComponent(messageId)}`, "PATCH", payload);
      console.log("OK: PATCH leaderboard success");
      return;
    } catch (e) {
      console.log(`PATCH failed -> fallback POST: ${e.message}`);
    }
  }

  const created = await discordRequest(`${webhookUrl}?wait=true`, "POST", payload);
  const newId = String((created && created.id) || "").trim();
  if (!newId) throw new Error("POST ok, ale brak id wiadomosci w odpowiedzi.");
  console.log(`OK: stworzono nowa wiadomosc. Ustaw DISCORD_MESSAGE_ID=${newId}`);
}

main().catch((err) => {
  console.error(err.message || String(err));
  process.exit(1);
});
