Discord Topka Bot (GitHub Actions, darmowe)

Co to robi:
- co 5 minut pobiera leaderboard z Firebase Realtime Database
- edytuje jedna wiadomosc webhooka Discord
- dziala 24/7 bez wlaczonego komputera

Wymagane sekrety w GitHub repo (Settings -> Secrets and variables -> Actions):
1) FIREBASE_DB_URL
   Przyklad: https://twoj-projekt-default-rtdb.europe-west1.firebasedatabase.app
2) DISCORD_WEBHOOK_URL
   Przyklad: https://discord.com/api/webhooks/xxx/yyy
3) DISCORD_MESSAGE_ID
   ID wiadomosci Discord, ktora ma byc edytowana
   (moze byc puste na pierwszy run; skrypt utworzy nowa wiadomosc i wypisze ID)

Wersja workflow:
- teraz uruchamia Node.js skrypt: update_discord_topka.mjs
- jesli PATCH nie dziala, robi fallback POST i poda nowe ID do ustawienia

Jak uruchomic:
1) wrzuc folder "discord-topka-bot" do repo na GitHub
2) dodaj 3 sekrety powyzej
3) w Actions odpal workflow "Discord Topka Refresh" recznie (Run workflow)
4) potem bedzie lecial automatycznie co 5 minut

Uwaga:
- jesli chcesz szybciej, zmien cron w .github/workflows/discord-topka.yml
- darmowo i stabilnie najlepiej zostawic co 5 minut
