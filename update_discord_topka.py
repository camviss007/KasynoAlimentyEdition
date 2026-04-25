import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def http_json(url, method="GET", payload=None, timeout=20):
    data = None
    headers = {
        "User-Agent": "KasynoTopkaBot/1.0 (+GitHubActions)",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))


def build_rows(leaderboard):
    if not isinstance(leaderboard, dict):
        return []
    rows = []
    for nick, cash in leaderboard.items():
        nick = str(nick or "").strip()
        if not nick or nick.lower() == "gracz":
            continue
        try:
            cash_n = float(cash)
        except (TypeError, ValueError):
            continue
        rows.append((nick, cash_n))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:10]


def build_payload(rows):
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (nick, cash) in enumerate(rows):
        prefix = medals[i] if i < 3 else "•"
        lines.append(f"{prefix} {nick} — {int(cash)}$")
    if not lines:
        lines = ["Brak danych leaderboardu."]
    return {
        "embeds": [
            {
                "title": "💰 Leaderboard",
                "description": "\n".join(lines),
                "color": 0x2ECC71,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Auto refresh (GitHub Actions)"},
            }
        ]
    }


def main():
    db_url = (os.environ.get("FIREBASE_DB_URL") or "").strip().rstrip("/")
    webhook_url = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip().strip("\"'").rstrip("/")
    message_id = (os.environ.get("DISCORD_MESSAGE_ID") or "").strip()

    if not db_url or not webhook_url:
        raise RuntimeError("Brak sekretow: FIREBASE_DB_URL / DISCORD_WEBHOOK_URL")
    if "/api/webhooks/" not in webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL nie wyglada na poprawny webhook Discord API (musi zawierac /api/webhooks/).")
    # Wymuszenie wersjonowanego endpointu API.
    webhook_url = webhook_url.replace("https://discord.com/api/webhooks/", "https://discord.com/api/v10/webhooks/")
    webhook_url = webhook_url.replace("https://discordapp.com/api/webhooks/", "https://discord.com/api/v10/webhooks/")

    leaderboard_url = f"{db_url}/leaderboard.json"
    leaderboard = http_json(leaderboard_url, method="GET")
    rows = build_rows(leaderboard)
    payload = build_payload(rows)

    if message_id:
        edit_url = f"{webhook_url}/messages/{urllib.parse.quote(message_id)}"
        try:
            http_json(edit_url, method="PATCH", payload=payload)
            print(f"OK: zaktualizowano topke (PATCH), wiersze={len(rows)}")
            return
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"PATCH nieudany ({exc.code}). Sprobuje POST nowej wiadomosci. Szczegoly: {body}")

    # Fallback: tworzy nowa wiadomosc i zwraca jej ID do ustawienia jako DISCORD_MESSAGE_ID.
    post_url = f"{webhook_url}?wait=true"
    try:
        created = http_json(post_url, method="POST", payload=payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Discord POST error {exc.code}: {body}") from exc

    new_id = str((created or {}).get("id", "")).strip()
    if not new_id:
        raise RuntimeError("Wyslano nowa wiadomosc, ale brak ID w odpowiedzi Discord.")

    print(f"OK: utworzono nowa wiadomosc topki. Ustaw DISCORD_MESSAGE_ID = {new_id}")


if __name__ == "__main__":
    main()
