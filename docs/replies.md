# Replies of the bot

Every sentence the bot can send, in English and Italian, from `caccometro/i18n.py`. Written by `tools/write_replies.py`: do not edit by hand. `{name}`, `{count}` and the other words in braces are filled in when the bot answers; `*bold*` and `_italic_` are Telegram formatting. Where a section has several sentences for the same moment, the bot picks one at random.

## `/start`

| English | Italian |
| --- | --- |
| Hi, I am 🤖 *Caccometro* 🤖.<br>Send 💩 when you have done your duty.<br>Within 15 minutes send a location to conquer its tile 🚩.<br>/leaderboard\_month, /records and /app for leaderboards, records and the map.<br>_Version {version}_<br><br>🇮🇹 Italiano: /lingua it | Ciao, sono 🤖 *Caccometro* 🤖.<br>Manda 💩 quando hai fatto il tuo dovere.<br>Entro 15 minuti manda una posizione per conquistare la sua zona 🚩.<br>/classifica\_mese, /record e /app per classifiche, record e mappa.<br>_Versione {version}_<br><br>🇬🇧 English: /language en |

## `/leaderboard_month` (`/classifica_mese`), `/leaderboard_year` (`/classifica_anno`)

| English | Italian |
| --- | --- |
| No 💩 was counted in the month {date}. | Nel mese {date} non sono state contate 💩. |
| No 💩 was counted in the year {date}. | Nell'anno {date} non sono state contate 💩. |
| 🏆 *Leaderboard of the month {date}* | 🏆 *Classifica del mese {date}* |
| 🏆 *Leaderboard of the year {date}* | 🏆 *Classifica dell'anno {date}* |
| _💩 so far → forecast at the end of the month_ | _💩 finora → previsione a fine mese_ |
| _💩 so far → forecast at the end of the year_ | _💩 finora → previsione a fine anno_ |

## `/stats_month` (`/statistiche_mese`), `/stats_year` (`/statistiche_anno`)

| English | Italian |
| --- | --- |
| 🤷 No statistics available for the month {date}. | 🤷 Nessuna statistica disponibile per il mese {date}. |
| 🤷 No statistics available for the year {date}. | 🤷 Nessuna statistica disponibile per l'anno {date}. |
| 📊 *Statistics of the month {date}* | 📊 *Statistiche del mese {date}* |
| 📊 *Statistics of the year {date}* | 📊 *Statistiche dell'anno {date}* |
| 💩 per day: mean · median · variance | 💩 al giorno: media · mediana · varianza |

## `/records` (`/record`) of one person

| English | Italian |
| --- | --- |
| Records of {name} | Record per {name} |
| 🔥 it is the record! | 🔥 è il record! |
| 🔥 already beyond the monthly record! | 🔥 già oltre il record mensile! |
| 🔥 monthly record equalled! | 🔥 record mensile eguagliato! |
| 🔥 already beyond the record! | 🔥 già oltre il record! |
| (until yesterday) | (fino a ieri) |
| 🥵 Most 💩 in a day: {value} {times} on {count} different days (the latest: {days}). | 🥵 Più 💩 in un giorno: {value} {times} in {count} giorni diversi (gli ultimi: {days}). |
| 🥵 Most 💩 in a day: {value} {times} on {days}. | 🥵 Più 💩 in un giorno: {value} {times} il {days}. |
| ↳ Today: {count} 💩 | ↳ Oggi: {count} 💩 |
| 🤩 Best month: {value} 💩 {label} {months}. | 🤩 Mese migliore: {value} 💩 {label} {months}. |
| 😭 Worst month: only {value} 💩 {label} {months}. | 😭 Mese peggiore: solo {value} 💩 {label} {months}. |
| 🗓️ The monthly record will be available after the first complete month. | 🗓️ Il record mensile sarà disponibile dopo il primo mese completo. |
| 🗓️ The worst month will be available after at least two months of data. | 🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati. |
| ↳ This month: {count} 💩 so far | ↳ Questo mese: {count} 💩 finora |
| 🥳 Longest streak: {days} ({when}). | 🥳 Serie più lunga: {days} ({when}). |
| ↳ Now: {count} {days} in a row | ↳ In corso: {count} {days} di fila |
| ↳ Now: no streak | ↳ In corso: nessuna serie |
| 🫣 Most 💩 in a streak: {value} {times} ({when}). | 🫣 Più 💩 in una serie: {value} {times} ({when}). |
| ↳ Now: {count} 💩 in the streak | ↳ In corso: {count} 💩 nella serie |
| 🤢 Longest pause: {days} ({when}). | 🤢 Pausa più lunga: {days} ({when}). |
| 🤢 There are no days without 💩 yet between the first and the last record. | 🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione. |
| ↳ Now: 💩 done today, no pause | ↳ In corso: 💩 fatta oggi, nessuna pausa |
| ↳ Now: {count} {days} without 💩 | ↳ In corso: {count} {days} senza 💩 |

## `/records` (`/record`) of the group

| English | Italian |
| --- | --- |
| 🏆 *Group records* 🏆 | 🏆 *Record del gruppo* 🏆 |
| 🥵 Most 💩 in a day: {value} — {holders} | 🥵 Più 💩 in un giorno: {value} — {holders} |
| 🤩 Most 💩 in a month: {value} — {holders} | 🤩 Più 💩 in un mese: {value} — {holders} |
| 😭 Fewest 💩 in a month: {value} — {holders} | 😭 Meno 💩 in un mese: {value} — {holders} |
| 🥳 Longest streak: {value} — {holders} | 🥳 Serie più lunga: {value} — {holders} |
| 🫣 Most 💩 in a streak: {value} — {holders} | 🫣 Più 💩 in una serie: {value} — {holders} |
| 🤢 Longest pause: {value} — {holders} | 🤢 Pausa più lunga: {value} — {holders} |
| 📍 *Now* | 📍 *Adesso* |
| 💩 Today: {value} — {holders} | 💩 Oggi: {value} — {holders} |
| 🔥 Longest streak in progress: {value} — {holders} | 🔥 Serie in corso più lunga: {value} — {holders} |
| 🐢 Longest pause in progress: {value} — {holders} | 🐢 Pausa in corso più lunga: {value} — {holders} |
| Yours: /records me — somebody else's: /records @username (or reply to one of their messages) | Il tuo: /record io — di un altro: /record @username (o rispondi a un suo messaggio) |

## `/trophies` (`/trofei`)

| English | Italian |
| --- | --- |
| 🔥 *New trophy!* {days} days in a row with at least one 💩! | 🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩! |
| 🏆 *Trophy board* 🏆 | 🏆 *Bacheca dei trofei* 🏆 |
| 🤷 No trophy yet: it takes {days} days in a row with at least one 💩, or winning a month. | 🤷 Ancora nessun trofeo: servono {days} giorni di fila con almeno una 💩, oppure vincere un mese. |
| 👑 💩 of the year · 🏅 💩 of the month · 🔥 {days} days in a row | 👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {days} giorni di fila |
| Yours: /trophies me — somebody else's: /trophies @username (or reply to one of their messages) | I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio) |
| 🚩 season conqueror · ⛰️ season king | 🚩 conquistatore della stagione · ⛰️ re della stagione |
| 🚩 Season conqueror: {seasons} | 🚩 Conquistatore della stagione: {seasons} |
| ⛰️ Season king: {seasons} | ⛰️ Re della stagione: {seasons} |
| 🚩 Season {season}: conqueror {conquerors} ({n}), king {king} | 🚩 Stagione {season}: conquistatore {conquerors} ({n}), re {king} |
| Trophies of {name} | Trofei di {name} |
| 🤷 No trophy yet. | 🤷 Ancora nessun trofeo. |
| 👑 💩 of the year: {years} | 👑 💩 dell'anno: {years} |
| 🏅 💩 of the month ({count}): {months} | 🏅 💩 del mese ({count}): {months} |
| 🔥 Streaks: {n} trophy | 🔥 Serie: {n} trofeo |
| 🔥 Streaks: {n} trophies | 🔥 Serie: {n} trofei |
| ↳ {days} days: {period} | ↳ {days} giorni: {period} |
| ↳ and {extra} more streaks | ↳ e altre {extra} serie |
| 📍 Streak in progress: {count} {days} in a row, 1 more to the next trophy | 📍 Serie in corso: {count} {days} di fila, ne manca 1 al prossimo trofeo |
| 📍 Streak in progress: {count} {days} in a row, {missing} more to the next trophy | 📍 Serie in corso: {count} {days} di fila, ne mancano {missing} al prossimo trofeo |
| 📍 No streak in progress: today is the right day to start one! | 📍 Nessuna serie in corso: oggi è il giorno buono per iniziarne una! |

## `/conquests` (`/conquiste`)

| English | Italian |
| --- | --- |
| First the 💩, then the conquest 😏 | Prima la 💩, poi la conquista 😏 |
| 📍 Send your location within 15 minutes to conquer the tile! | 📍 Manda la posizione entro 15 minuti per conquistare la zona! |
| 🚩 {name} conquers a new tile! Tiles: {total} | 🚩 {name} conquista una nuova zona! Zone: {total} |
| 🏠 {name} defends their tile. Tiles: {total} | 🏠 {name} difende la sua zona. Zone: {total} |
| ⚔️ {name} steals a tile from {owner}! Tiles: {total} | ⚔️ {name} ruba una zona a {owner}! Zone: {total} |
| 👑 {name} is the new king of the hill! | 👑 {name} è il nuovo re della collina! |
| /conquests [@username \| me] | /conquiste [@username \| io] |
| 🗺️ {name}: {held} tiles held, {visited} visited. | 🗺️ {name}: {held} zone tenute, {visited} visitate. |
| 👑 King of the hill! | 👑 Re della collina! |
| No tile conquered yet. After the 💩 send a location within 15 minutes. | Nessuna zona conquistata. Dopo la 💩 manda una posizione entro 15 minuti. |
| 🗺️ *Conquests* | 🗺️ *Conquiste* |
| Tile conquered | Zona conquistata |
| Conquests around the world | Conquiste nel mondo |
| Conquests in Lombardy | Conquiste in Lombardia |
| Conquests in Italy | Conquiste in Italia |
| latest conquest | ultima conquista |
| tiles lost: {n} | zone perse: {n} |
| Tiles of {name} | Zona di {name} |
| Tiles of the group | Zone del gruppo |

## `/day_count` (`/conto_giorno`)

| English | Italian |
| --- | --- |
| on {date} | il giorno {date} |
| today | oggi |
| {name} did no 💩 {day}: on strike? | {name} {day} non ha fatto 💩: giornata di sciopero? |
| {name} {day}: zero 💩. The record is empty. | {name} {day}: zero 💩. Il registro è vuoto. |
| {name} {day} did 💩 {count} time: normal. | {name} {day} ha fatto 💩 {count} volta: nella norma. |
| {name} {day} did 💩 {count} times: normal. | {name} {day} ha fatto 💩 {count} volte: nella norma. |
| {name} {day}: {count} 💩, regular as clockwork. | {name} {day}: {count} 💩, regolare come un orologio. |
| {name} {day}: {count} 💩. What did they eat? | {name} {day}: {count} 💩. Che cosa ha mangiato? |
| {name} {day}: {count} 💩, record-breaking day. | {name} {day}: {count} 💩, giornata da record. |

## `/last_poop` (`/ultima_cacca`)

| English | Italian |
| --- | --- |
| No data on the last 💩 of {name}: it starts today. | Nessun dato sull'ultima 💩 di {name}: si comincia oggi. |
| {name} already did 💩 today: duty done. | {name} oggi ha già fatto 💩: il dovere è compiuto. |
| {name} already delivered 💩 today. Resting. | {name} oggi ha già dato 💩. Riposa. |
| {name} did 💩 yesterday: all under control. | {name} ha fatto 💩 ieri: tutto sotto controllo. |
| The last 💩 of {name} was yesterday: today is the day. | L'ultima 💩 di {name} è di ieri: oggi è il giorno giusto. |
| {name} has had no 💩 for {days} days: it starts to show. | {name} non fa 💩 da {days} giorni: inizia a farsi sentire. |
| {name} has had no 💩 for {days} days: a prune is needed. | {name} non fa 💩 da {days} giorni: serve una prugna. |
| {name} has had no 💩 for {days} days: time for an intervention. | {name} non fa 💩 da {days} giorni: serve un intervento. |
| {name} has had no 💩 for {days} days?! The bathroom is waiting, and worried. | {name} non fa 💩 da {days} giorni?! Il bagno lo aspetta, ed è preoccupato. |

## `/add_poop` (`/aggiungi_cacca`)

| English | Italian |
| --- | --- |
| 🔒 Only the group admins can change the counts of somebody else. | 🔒 Solo gli admin del gruppo possono modificare i conteggi degli altri. |
| Done: {name} goes up to {count} 💩 on {date}. History rewritten. | Fatto: {name} il {date} sale a {count} 💩. La storia è riscritta. |
| {name} now has {count} 💩 on {date}. Better late than never. | {name} il {date} ora ha {count} 💩. Meglio tardi che mai. |
| Recorded: {name} reaches {count} 💩 on {date}. | Registrato: {name} il {date} arriva a {count} 💩. |

## `/remove_poop` (`/togli_cacca`)

| English | Italian |
| --- | --- |
| ⚠️ The count of {name} on {date} cannot be changed: it was already 0 💩. | ⚠️ Il conteggio di {name} nel giorno {date} non può essere aggiornato poiché era già 0 💩. |
| Erased: {name} drops to {count} 💩 on {date}. Nobody saw anything. | Cancellata: {name} il {date} scende a {count} 💩. Nessuno ha visto niente. |
| {name} now has {count} 💩 on {date}. The past has been flushed. | {name} il {date} ora ha {count} 💩. Tirato lo sciacquone sul passato. |
| Removed: {name} is left with {count} 💩 on {date}. | Tolta: {name} il {date} resta con {count} 💩. |

## `/language` (`/lingua`)

| English | Italian |
| --- | --- |
| 🌐 The language of this chat is {name}. To change it: /language en or /language it. | 🌐 La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en. |
| 🔒 Only the group admins can change the language. | 🔒 Solo gli admin del gruppo possono cambiare la lingua. |
| From now on I speak English 🇬🇧 | Da ora parlo italiano 🇮🇹 |
| 📱 Leaderboards, statistics and conquest map in the Mini App. | 📱 Classifiche, statistiche e mappa delle conquiste nella Mini App. |
| Open | Apri |

## `/link_history` (`/collega_storico`)

| English | Italian |
| --- | --- |
| 🤷 There is no old history to link. | 🤷 Non ci sono dati storici da collegare. |
| Old history still to link: | Dati storici ancora da collegare: |
| → {name} (match found) | → {name} (corrispondenza trovata) |
| ({orphans} records without a username cannot be linked.) | ({orphans} registrazioni senza username non si possono collegare.) |
| The admins can use /link_history auto to link the matches, or reply to a message of the person with /link_history &lt;old username>. | Gli admin possono usare /collega_storico auto per collegare le corrispondenze, oppure rispondere a un messaggio della persona con /collega_storico &lt;username storico>. |
| 🔒 Only the group admins can link the old history. | 🔒 Solo gli admin del gruppo possono collegare i dati storici. |
| 🔗 Linked: | 🔗 Collegati: |
| • {username} → {name} ({days} days) | • {username} → {name} ({days} giorni) |
| 🤷 No match found between the old history and the users who have already written in the group. | 🤷 Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo. |
| To link by hand (reply to a message of the person with /link_history &lt;old username>): | Da collegare a mano (rispondi a un messaggio della persona con /collega_storico &lt;username storico>): |
| ⚠️ Reply to a message of the person to link. Use: {usage} | ⚠️ Rispondi a un messaggio della persona da collegare. Usa: {usage} |
| 🤷 No old history found for «{username}» (already linked or never recorded). | 🤷 Nessun dato storico trovato per «{username}» (già collegato o inesistente). |
| 🔗 Linked {days} days of old history of «{username}» to {name}. | 🔗 Collegati {days} giorni di dati storici di «{username}» a {name}. |

## Messages with 💩 or 🚽

| English | Italian |
| --- | --- |
| 💩 today: {count} | 💩 oggi: {count} |
| {name} at this hour? Night brings wisdom, and 💩 too. | {name} a quest'ora? La notte porta consiglio, e anche 💩. |
| Gut insomnia for {name}: the night shift forgives nothing. | Insonnia intestinale per {name}: il turno di notte non perdona. |
| {name} does 💩 while the world sleeps. Silent hero. | {name} fa 💩 mentre il mondo dorme. Eroe silenzioso. |
| Lights off, flush on: well done {name}. | Luci spente, scarico acceso: bravo {name}. |
| {name} starts the day with a 💩: breakfast of champions. | {name} apre la giornata con una 💩: colazione dei campioni. |
| The coffee kicked in, {name}! | Il caffè ha fatto effetto, {name}! |
| Alarm, coffee, 💩: {name}'s routine never fails. | Sveglia, caffè, 💩: la routine di {name} non tradisce. |
| Good morning {name}, and happy unloading! | Buongiorno {name}, e buon alleggerimento! |
| {name} does 💩 instead of working: the perfect excuse. | {name} fa 💩 invece di lavorare: la scusa perfetta. |
| Strategic bathroom break for {name}, phone included. | Pausa strategica in bagno per {name}, telefono incluso. |
| Productive morning for {name}: at least something got delivered. | Mattinata produttiva per {name}: almeno qualcosa è uscito. |
| {name} completes an important task. | {name} porta a termine un compito importante. |
| Lunch is barely over and {name} is already operational. | Il pranzo è appena finito e {name} è già operativo. |
| {name} clears lunch in record time. | {name} smaltisce il pranzo in tempo record. |
| Lightning digestion for {name}! | Digestione lampo per {name}! |
| After lunch duty calls, and {name} answers. | Dopo pranzo il dovere chiama, e {name} risponde. |
| Afternoon of glory for {name}. | Pomeriggio di gloria per {name}. |
| {name} takes the afternoon break: wise. | {name} approfitta della pausa pomeridiana: saggio. |
| Snack cleared? {name} certainly. | Merenda smaltita? {name} sì. |
| {name} survives the mid-afternoon slump with a 💩. | {name} sopravvive al calo di metà pomeriggio con una 💩. |
| {name} closes the day in style. | {name} chiude la giornata in bellezza. |
| After dinner comes the cleanup: {name} is on it. | Dopo cena si smaltisce: ci pensa {name}. |
| Relaxing evening for {name}, throne included. | Serata di relax per {name}, trono incluso. |
| {name} goes to bed lighter. | {name} va a letto più leggero. |
| Well done {name}! | Complimenti {name}! |
| {name} did their duty. | {name} ha fatto il suo dovere. |
| A round of applause for {name}, who never backs down. | Un applauso per {name}, che non si tira indietro. |
| Mission accomplished for {name}. | Missione compiuta per {name}. |
| {name} leaves a mark. | {name} lascia il segno. |
| What a relief, {name}! | Che soddisfazione, {name}! |
| The leaderboard thanks {name}. | La classifica ringrazia {name}. |
| {name} writes another page of history. | {name} scrive un'altra pagina di storia. |
| First 💩 of the day for {name}: a good start. | Prima 💩 della giornata per {name}: si parte bene. |
| {name} opens the day. | {name} inaugura la giornata. |
| Here is the first of today, {name}! | Ecco la prima di oggi, {name}! |
| {name} is an early bird: the first 💩 comes early. | {name} è mattiniero: la prima 💩 arriva presto. |
| First 💩 of the day after lunch? {name} took a while. | Prima 💩 della giornata dopo pranzo? {name} ci ha messo un po'. |
| {name} starts the day in the dead of night. | {name} inizia la giornata a notte fonda. |
| {name} again?! What did they eat? | Di nuovo {name}?! Che cosa ha mangiato? |
| {name} cannot be stopped. | {name} non si ferma più. |
| {name} is going big today. | {name} fa le cose in grande oggi. |
| {name} in the small hours and 💩 again: need a doctor? | {name} nelle ore piccole e ancora 💩: serve un medico? |
| Lunch did not sit well with {name}: again! | Il pranzo non è andato giù a {name}: ancora! |

## Mentions of the bot

| English | Italian |
| --- | --- |
| 💬 What do you want to tell me? | 💬 Cosa vuoi dirmi? |

## Messages with "run"

| English | Italian |
| --- | --- |
| {name} what the hell are you writing *Run* for? I only work with my own commands, not with the ones you make up. | {name} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu. |
| {name}, *Run* is not a command. I only work with real ones, not the ones you make up. | {name}, *Run* non è un comando. Funziono solo con quelli veri, non con quelli che ti inventi tu. |
| {name}, seriously? *Run*?! Check the command menu, then try again. | {name}, ma sei serio? *Run*?! Guarda il menu dei comandi, poi riprova. |

## Shared: arguments, dates and people

| English | Italian |
| --- | --- |
| ⚠️ Invalid format. Use: {usage} | ⚠️ Formato non valido. Usa: {usage} |
| ⚠️ Error: {error} | ⚠️ Errore: {error} |
| Invalid date. Examples: 05-03-2026, 5/3/26, 5.3 (current year), today, yesterday. | Data non valida. Esempi: 05-03-2026, 5/3/26, 5.3 (anno corrente), oggi, ieri. |
| The selected date is in the future. | La data selezionata è nel futuro. |
| The year must be {year} or later. | L'anno deve essere dal {year} in poi. |
| ⚠️ Invalid date format. Use MM-YYYY (also 3/2026, 03.26 or march 2026). | ⚠️ Formato data non valido. Usa MM-YYYY (anche 3/2026, 03.26 o marzo 2026). |
| ⚠️ Invalid year format. Use YYYY (also 26). | ⚠️ Formato anno non valido. Usa YYYY (anche 26). |
| 🤔 I do not know @{username}: they must write at least one message in the group (or reply to one of their messages). | 🤔 Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo (oppure rispondi a un suo messaggio). |
| /records [@username \| me] | /record [@username \| io] |
| /trophies [@username \| me] | /trofei [@username \| io] |
| /add_poop @username DD-MM-YYYY | /aggiungi_cacca @username DD-MM-YYYY |
| /remove_poop @username DD-MM-YYYY | /togli_cacca @username DD-MM-YYYY |
| /day_count @username DD-MM-YYYY | /conto_giorno @username DD-MM-YYYY |
| /last_poop @username | /ultima_cacca @username |
| /link_history &lt;old username> (as a reply to a message of the person) | /collega_storico &lt;username storico> (in risposta a un messaggio della persona) |
| 🤷 No data available. | 🤷 Nessun dato disponibile. |
| 🤷 No data available for {name}. | 🤷 Nessun dato disponibile per {name}. |
| ℹ️ There is old history still to link: use /link_history. | ℹ️ Ci sono dati storici ancora da collegare: usa /collega_storico. |

## Shared: words used inside other sentences

| English | Italian |
| --- | --- |
| time | volta |
| times | volte |
| day | giorno |
| days | giorni |
| {n} day in a row | {n} giorno consecutivo |
| {n} days in a row | {n} giorni consecutivi |
| and {extra} more | e altri {extra} |
| and | e |
| in the month | nel mese |
| in the months | nei mesi |

## Group messages: midnight announcement

| English | Italian |
| --- | --- |
| each | a testa |
| 🗺️ *Season {season} is over!* | 🗺️ *Stagione {season} finita!* |
| 🚩 Conqueror: {names} with {n} conquests | 🚩 Conquistatore: {names} con {n} conquiste |
| ⛰️ King of the hill: {names} | ⛰️ Re della collina: {names} |
| {label}: {names} with {total} 💩 | {label}: {names} con {total} 💩 |
| 🎆 *Happy new year! Welcome {year}!* 🥂 | 🎆 *Buon anno! Benvenuto {year}!* 🥂 |
| 🏅 💩 of December | 🏅 💩 di dicembre |
| 👑 💩 of the year {year} | 👑 💩 dell'anno {year} |
| Well done! May {year} be as regular as a Swiss watch 🎉 | Complimenti! Che il {year} sia regolare come un orologio svizzero 🎉 |
| 🌙 *Midnight: {month} is over!* | 🌙 *Mezzanotte: {month} è finito!* |
| 🏅 💩 of the month | 🏅 💩 del mese |
| Well done! Back to zero: happy {month} and happy 💩 🧻 | Complimenti! Si riparte da zero: buon {month} e buone 💩 🧻 |
| ✨ Your month | ✨ Il tuo mese |
| ✨ Your year | ✨ Il tuo anno |

## Mini App: image of the recap of a month or a year (#195)

| English | Italian |
| --- | --- |
| RECAP {period} | RIEPILOGO {period} |
| #{place} of {total}! | {place}° posto su {total}! |
| what a month! | che mese! |
| what a year! | che anno! |
| vs {month} | su {month} |
| vs {year} | sul {year} |
| on {month} {day} | il {day} {month} |
| day streak | giorno di fila |
| day streak | giorni di fila |

## Shared: charts

| English | Italian |
| --- | --- |
| Leaderboard of {title} | Classifica di {title} |
| Leaderboard of {title} | Classifica del {title} |
| Total | Totale |
| Day | Giorno |
| Running total | Totale progressivo |
| How it went day by day | Come è andata giorno per giorno |
| Statistics of {title} | Statistiche di {title} |
| Statistics of {title} | Statistiche del {title} |
| Times per day | Volte al giorno |
| Days | Giorni |
| Daily distribution  (◆ mean, — median) | Distribuzione giornaliera  (◆ media, — mediana) |

## Shared: leaderboards, statistics and records compared with the group (#201)

| English | Italian |
| --- | --- |
| Tied for the lead with {value}: {names}. | In testa a pari merito con {value}: {names}. |
| {name} leads with {value}, {gap} more than {other}. | {name} è in testa con {value}, {gap} più di {other}. |
| {name}: #{place} with {value}, {gap} behind {other} | {name}: {place}° con {value}, a {gap} da {other} |
| , at this pace #{place} (~{value} 💩) | , a questo ritmo {place}° (~{value} 💩) |
| {value} a day | {value} al giorno |
| {name}, how you are doing: {label}. | {name}, come vai: {label}. |
| very regular | molto regolare |
| fairly regular | abbastanza regolare |
| up and down | a sbalzi |
| (group record) | (record del gruppo) |
| (group record, tied) | (record del gruppo, a pari merito) |
| (#{place} of {total}) | ({place}° su {total}) |
