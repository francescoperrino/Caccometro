<p align="center">
  <img src="assets/demo.gif" alt="Caccometro: il robot si sforza sul water, manda una 💩 dal telefono, arriva un podio con la medaglia d'oro e fa pollice in su" width="400">
</p>

<h1 align="center">Caccometro</h1>

<p align="center"><b>Chi ne fa di più? Il bot Telegram che conta le 💩 del tuo gruppo.</b></p>

<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

<p align="center">
  <a href="https://github.com/francescoperrino/Caccometro/actions/workflows/tests.yml"><img src="https://github.com/francescoperrino/Caccometro/actions/workflows/tests.yml/badge.svg" alt="Test"></a>
  <a href="https://github.com/francescoperrino/Caccometro/releases/latest"><img src="https://img.shields.io/github/v/release/francescoperrino/Caccometro" alt="Ultima versione"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/francescoperrino/Caccometro" alt="Licenza MIT"></a>
</p>

<p align="center">
  <a href="https://t.me/caccometro_bot?startgroup=true"><img src="https://img.shields.io/badge/Aggiungilo_al_gruppo-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Aggiungi Caccometro al tuo gruppo Telegram"></a>
</p>

Hai fatto il tuo dovere? Manda 💩 nel gruppo. Caccometro tiene il conto di tutti e lo trasforma in una gara tra amici:

- 🏆 **Classifiche** del mese e dell'anno, con la previsione a fine mese
- 📊 **Statistiche e grafici**: medie, la giornata tipo, chi è più regolare
- 🏅 **Record e trofei**: serie di giorni, il 💩 del mese e dell'anno
- 🚩 **Gioco di conquista**: dopo la 💩 manda la posizione e l'esagono sulla mappa è tuo, stagione dopo stagione
- 📱 **Mini App**: mappa, classifiche, statistiche e trofei in un posto solo, aperta dalla chat; nella prima settimana del mese, il riepilogo del tuo mese (a gennaio, del tuo anno) da condividere
- 🌍 Italiano e inglese, open source

## 📱 Mini App

| Mappa | Classifica | Statistiche | Trofei |
| :---: | :---: | :---: | :---: |
| <img src="assets/screenshots/miniapp_map_it.jpg" alt="Mappa della Mini App: gli esagoni conquistati intorno a Milano nei colori di chi li tiene" width="190"> | <img src="assets/screenshots/miniapp_leaderboard_it.jpg" alt="Classifica del mese nella Mini App: chi è in testa, il podio con medaglie e previsioni, la lista degli altri" width="190"> | <img src="assets/screenshots/miniapp_stats_it.jpg" alt="Statistiche della Mini App: i tuoi numeri del mese e quanto sei regolare" width="190"> | <img src="assets/screenshots/miniapp_trophies_it.jpg" alt="Trofei della Mini App: i trofei in corso e la bacheca del gruppo" width="190"> |

---

- [Come si usa](#-come-si-usa)
- [Comandi](#-comandi)
- [Grafici e mappe](#-grafici-e-mappe)
- [Regole](#-regole)
- [Privacy](#-privacy)
- [Documentazione](#-documentazione)

## 💬 Come si usa

<p align="center"><img src="docs/images/come_funziona_il_bot.svg" alt="Come funziona il Caccometro: mandi 💩, il bot la conta, conquisti un esagono con la posizione, confronti classifiche e statistiche, a mezzanotte del primo del mese si annuncia il 💩 del mese" width="600"></p>

1. Aggiungi il bot al gruppo e manda `/start`.
2. Quando hai fatto il tuo dovere manda un messaggio con 💩 o 🚽 (anche come sticker): il bot risponde con una frase divertente (cambia con l'ora e con il numero della 💩 del giorno), il conto di oggi e ricorda di mandare la posizione.
3. Entro 15 minuti dalla 💩 manda una posizione (📎 → Posizione) per conquistare la sua zona: vedi le [regole della conquista](#-regole).
4. Usa i comandi qui sotto per classifiche, statistiche e record, oppure `/app` per la Mini App.
5. Il bot parla italiano; per l'inglese un admin manda `/lingua en` (in privato chiunque).

---

## 📚 Comandi

| Comando                                        | Cosa fa |
| :--------------------------------------------- | :------ |
| `/start`                                       | Versione del bot e comandi principali. |
| `/classifica_mese [MM-YYYY]`                   | Classifica del mese, con grafico e previsione. |
| `/classifica_anno [YYYY]`                      | Classifica dell'anno, con grafico e previsione. |
| `/statistiche_mese [MM-YYYY]`                  | Media, mediana e varianza delle 💩 al giorno nel mese. |
| `/statistiche_anno [YYYY]`                     | Le stesse statistiche sull'anno. |
| `/record [io \| @username]`                    | Record del gruppo o di una persona. |
| `/trofei [io \| @username]`                    | Trofei del gruppo o di una persona. |
| `/conquiste [io \| @username]`                 | Zone tenute, re della collina e mappe. |
| `/app`                                         | Apre la Mini App su questa chat. |
| `/conto_giorno [@username] [DD-MM-YYYY]`       | 💩 di una persona in un giorno. |
| `/ultima_cacca [@username]`                    | Giorni passati dall'ultima 💩. |
| `/aggiungi_cacca [@username] DD-MM-YYYY`       | Aggiunge 1 💩 in un giorno. |
| `/togli_cacca [@username] DD-MM-YYYY`          | Toglie 1 💩 in un giorno. |
| `/collega_storico [auto \| username storico]`  | Solo admin: collega il vecchio storico alle persone. |
| `/lingua [it \| en]`                           | Lingua della chat. |

Ogni comando ha anche un nome inglese (`/leaderboard_month`, `/add_poop`, ...), valido in ogni chat qualunque sia la sua lingua: vedi la [tabella dei menu](docs/deployment.md#command-menus). Tutto quello che il bot può rispondere, in italiano e in inglese, è in [docs/replies.md](docs/replies.md).

<details>
<summary><b>I comandi nel dettaglio</b></summary>

- **`/start`** prepara il database della chat, mostra la versione del bot e i comandi principali.
- **`/classifica_mese [MM-YYYY]`**: il mese corrente se la data manca (anche `marzo 2026`), con un grafico dell'andamento giorno per giorno. Per il mese in corso, accanto a ogni conto, la previsione a fine mese. Sotto la lista: chi è in testa, dove sei tu e, con 🔥 accanto ai nomi, le serie in corso.
- **`/classifica_anno [YYYY]`**: l'anno corrente se manca (anche `26`), con un grafico e, per l'anno in corso, la previsione a fine anno.
- **`/statistiche_mese [MM-YYYY]`**: media, mediana e varianza delle 💩 al giorno di ogni persona nel mese, con un grafico delle distribuzioni. Sotto la lista: chi è in testa e quanto sei regolare.
- **`/record [io | @username]`**: senza argomenti i **record del gruppo** (chi detiene ciascun record e chi è in testa adesso). Con `io` i tuoi record, con `@username` (o rispondendo a un messaggio) quelli di un'altra persona, ciascuno con il suo **stato attuale** e il posto nel gruppo ("2° su 5").
- **`/trofei [io | @username]`**: senza argomenti la **bacheca dei trofei** del gruppo; con `io`, `@username` o una risposta, i trofei di una persona, con quanti giorni mancano al prossimo trofeo di serie.
- **`/conquiste [io | @username]`**: senza argomenti le **zone tenute** da ogni persona, prima il re della collina 👑; con `io`, `@username` o una risposta, le zone tenute e visitate da una persona, e mappe solo sue: Lombardia, Italia e mondo, più chiare dove ha perso zone, e una quarta mappa con le zone vere intorno all'ultima conquista (quelle perse tratteggiate).
- **`/app`** manda un pulsante che apre la **Mini App** su questa chat. Nella chat privata con il bot, il pulsante del menu la apre sulla chat privata; i dati di un gruppo li vedono solo i suoi membri. Dal 1° al 7 del mese la classifica apre **Il tuo mese**: il mese appena finito in poche schermate (totale, giorno migliore, serie più lunga, posto, confronto col mese prima), e Condividi ti manda l'immagine in privato da inoltrare o salvare. Dal 1° al 14 gennaio c'è anche **Il tuo anno**, con l'anno appena finito. L'annuncio di mezzanotte di un nuovo mese ha un pulsante che lo apre.
- **`/conto_giorno [@username] [DD-MM-YYYY]`**: oggi se la data manca (anche `ieri`).
- **`/aggiungi_cacca` e `/togli_cacca [@username] DD-MM-YYYY`** aggiungono o tolgono 1 💩 (fino a 0) in un giorno passato o di oggi (anche `oggi`, `ieri`). Sul conto di un altro: solo admin.
- **`/collega_storico`** senza argomenti mostra cosa resta da collegare: vedi [Vecchio storico e supergruppi](#-regole).
- **`/lingua [it | en]`** senza argomenti mostra la lingua della chat; con `it` o `en` la cambia (nei gruppi solo admin). Vale per le risposte, i grafici, l'annuncio di mezzanotte e il menu dei comandi della chat.

Nei comandi con `[@username]` la persona si può indicare anche **rispondendo a un suo messaggio** (utile per chi non ha uno username). Un `@username` funziona solo per chi ha già scritto almeno un messaggio nel gruppo. Nei gruppi con i topic, rispondere al messaggio che ha creato il topic non conta come rispondere a una persona.

</details>

<details>
<summary><b>Date e mesi</b></summary>

Le date si possono scrivere in vari modi: `-`, `/` e `.` sono equivalenti, gli zeri iniziali sono facoltativi e l'anno può avere due cifre (`26` = 2026, anche per `/classifica_anno` e `/statistiche_anno`). Quindi `5/3/26`, `05.03.2026` e `5-3-2026` indicano lo stesso giorno (prima il giorno, poi il mese), e `3/26`, `03.2026` e `03-2026` lo stesso mese. Si possono usare anche `oggi` e `ieri` (o `today` e `yesterday`), un giorno senza anno (`5/3`, vale l'anno corrente) e il nome del mese in italiano o in inglese (`marzo 2026`, `march 26`, `marzo` per l'anno corrente), in qualunque lingua sia la chat. Le risposte mostrano sempre `DD-MM-YYYY` e `MM-YYYY`. Sono valide solo date reali tra il 1970 e oggi (mesi e anni fino al 2100).

Le date seguono l'ora italiana (`Europe/Rome`). Una 💩 vale nel giorno in cui il messaggio è stato **inviato**, anche se il bot lo elabora più tardi.

</details>

---

## 📈 Grafici e mappe

Le classifiche e le statistiche arrivano con un grafico, e ogni conquista con una mappa. Sono disegnati dal codice del bot con dati di esempio e vengono ridisegnati a ogni modifica del codice (`tools/sample_charts.py`, `tools/sample_maps.py`).

| Classifica del mese, con la previsione | Statistiche del mese |
| :---: | :---: |
| <img src="assets/screenshots/leaderboard_month_it.png" alt="Grafico della classifica: tabella dei conteggi giornalieri con le medaglie e totale progressivo di ogni persona con la previsione tratteggiata fino a fine mese" width="400"> | <img src="assets/screenshots/stats_month_it.png" alt="Grafico delle statistiche: una curva a campana per persona e un box plot delle 💩 al giorno" width="400"> |

Gli stessi grafici in una chat inglese: [classifica](assets/screenshots/leaderboard_month_en.png), [statistiche](assets/screenshots/stats_month_en.png).

| Conquista | `/conquiste`: Lombardia |
| :---: | :---: |
| <img src="assets/screenshots/conquest_zoom_it.jpg" alt="Mappa di Milano con le zone esagonali nei colori di chi le tiene e la zona appena conquistata contornata" width="400"> | <img src="assets/screenshots/conquest_region_it.jpg" alt="Mappa della Lombardia con gli esagoni delle aree conquistate" width="400"> |
| **`/conquiste`: Italia** | **`/conquiste`: mondo** |
| <img src="assets/screenshots/conquest_country_it.jpg" alt="Mappa dell'Italia con gli esagoni più grandi delle aree conquistate" width="400"> | <img src="assets/screenshots/conquest_world_it.jpg" alt="Mappa del mondo con gli esagoni delle conquiste su più continenti" width="400"> |

---

## 📏 Regole

<details>
<summary><b>🏅 Record e trofei</b></summary>

- **Giorno / serie / pause:** il giorno con più 💩, la serie più lunga di giorni consecutivi con almeno una 💩, la serie con più 💩 in totale e la pausa più lunga tra due giorni con 💩. A parità, sono elencati tutti i periodi.
- **Mese migliore:** solo mesi completi (il mese in corso non conta ancora).
- **Mese peggiore:** solo mesi completi, escludendo il primo mese con dati (potresti aver iniziato a metà) e quelli dopo l'ultimo mese con dati (potresti aver lasciato il gruppo); i mesi in mezzo senza nessuna 💩 valgono 0. Servono quindi almeno due mesi di dati.
- **Record del gruppo:** per ogni metrica il valore migliore tra tutte le persone (anche quelle che hanno lasciato il gruppo) e chi lo detiene; a parità, tutti. Il blocco "Adesso" considera solo chi ha fatto una 💩 negli ultimi 90 giorni.
- **Stato attuale:** una serie è "in corso" se l'ultima 💩 è di oggi o di ieri; la pausa attuale sono i giorni dall'ultima 💩. Il 🔥 compare quando si raggiunge un record (dal 2 in su) o si supera il record di pausa.
- **Previsione:** per il mese o l'anno in corso, il totale finora più, per ogni giorno che manca, la media di 💩 al giorno degli ultimi 30 giorni.
- **Trofei:** 🔥 uno ogni 15 giorni consecutivi con almeno una 💩 (15, 30, 45, ...; una serie di 47 giorni vale 3 trofei), annunciato nella risposta alla prima 💩 del giorno che li completa; 🏅 **💩 del mese** e 👑 **💩 dell'anno** a chi ne ha fatte di più in un mese o in un anno completo (a parità, a tutti). I trofei sono calcolati dai conteggi, quindi `/aggiungi_cacca` e `/togli_cacca` li aggiornano. 🚩 **Conquistatore della stagione** (più conquiste in un trimestre, anche quelle rubate) e ⛰️ **re della stagione** (più zone tenute a fine trimestre) vengono dallo storico delle conquiste, con i pareggi come sopra; l'annuncio di mezzanotte del primo giorno del trimestre li nomina e `/conquiste` mostra la stagione in corso.
- **Annuncio di mezzanotte:** il primo giorno di ogni mese, a mezzanotte, il bot scrive in ogni chat la 💩 del mese appena finito; il 1° gennaio anche la 💩 dell'anno, con gli auguri di buon anno.

</details>

<details>
<summary><b>🚩 Gioco di conquista</b></summary>

- Il mondo è diviso in zone esagonali di circa 5 km² (celle [H3](https://h3geo.org/) a risoluzione 7, larghe circa 2,6 km).
- Ogni 💩 mandata come messaggio o sticker (non `/aggiungi_cacca`) apre una **finestra di 15 minuti**: la prima posizione mandata dentro conquista la zona in cui cade. Una conquista per ogni 💩. Una posizione senza finestra aperta non conquista niente.
- 🚩 zona nuova, ⚔️ zona rubata a un'altra persona, 🏠 zona propria difesa. Una zona è di chi l'ha conquistata per ultimo.
- 👑 Il **re della collina** tiene più zone di tutti; a parità il re attuale tiene la corona.
- Ogni chat ha la sua mappa, mai azzerata; togliere una 💩 con `/togli_cacca` non toglie una conquista.
- Ogni conquista arriva con una **mappa** delle zone intorno; `/conquiste` manda le zone del gruppo intorno alla sua ultima conquista, poi la Lombardia, l'Italia e il mondo intero. In queste ultime tre un esagono grande vale per le zone che contiene e prende il colore di chi ne tiene di più (a parità, di chi ha conquistato per ultimo). Se la mappa non si riesce a disegnare, la risposta arriva solo come testo.

</details>

<details>
<summary><b>🔄 Vecchio storico e supergruppi</b></summary>

I conteggi sono legati all'**ID utente di Telegram**, non allo username: chi cambia username mantiene i suoi dati, e chi non ha uno username è contato col suo nome.

- I database delle prime versioni (conteggi per username) vengono **migrati automaticamente** al primo avvio. Prima si fa una copia; i vecchi dati restano in una tabella d'archivio finché non vengono collegati.
- Gli **admin** del gruppo collegano il vecchio storico alle persone con `/collega_storico`:
  1. `/collega_storico` mostra lo storico ancora da collegare;
  2. quando tutti hanno scritto almeno un messaggio, `/collega_storico auto` collega gli username identici;
  3. per gli altri, rispondi a un messaggio della persona con `/collega_storico <username storico>`.
- I vecchi record senza username non si possono collegare.
- Quando un gruppo diventa **supergruppo**, Telegram gli dà un nuovo ID di chat: il bot sposta da solo lo storico nella nuova chat, e lo unisce se il supergruppo ha già dei conteggi.

</details>

---

## 🔒 Privacy

Il bot legge i messaggi del gruppo per trovare le 💩: per questo la sua **Group Privacy** è disattivata. Il testo dei messaggi non viene mai salvato né scritto nel log. Il bot salva, per ogni chat, ID utente Telegram, username e nome di chi scrive, e le 💩 per giorno. Per il gioco di conquista salva l'ora dell'ultima 💩 (finché la sua finestra non è usata) e, per ogni conquista, l'ora, la zona e latitudine e longitudine della posizione; il log non registra mai le coordinate. Per ogni update il log scrive solo il comando, il tipo di chat (privata o gruppo), il tempo impiegato e l'esito, senza nomi né testo. Il log registra le modifiche fatte a mano: per ogni `/aggiungi_cacca` e `/togli_cacca` chi l'ha mandato, la persona, il giorno e il conteggio prima e dopo; per `/collega_storico` il vecchio username, la persona e i giorni spostati.

---

## 📖 Documentazione

La documentazione tecnica è solo in inglese:

| Documento | Per |
| :-------- | :-- |
| [docs/replies.md](docs/replies.md) | Tutte le risposte del bot, in inglese e in italiano |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Far partire il bot in locale, test, convenzioni e flusso di una modifica |
| [docs/architecture.md](docs/architecture.md) | Moduli, percorso di un messaggio, database, traduzioni |
| [docs/deployment.md](docs/deployment.md) | Configurazione di Telegram (menu, descrizioni), produzione su un hosting WSGI, webhook, annuncio di mezzanotte |
| [docs/operations.md](docs/operations.md) | Deploy, backup e ripristino, log, release |
| [docs/research/](docs/research/README.md) | Gli studi dietro le scelte: design della Mini App, indice di regolarità, hosting, README |
| [SECURITY.md](SECURITY.md) | Segnalare una vulnerabilità |

## Licenza

Caccometro è rilasciato con licenza [MIT](LICENSE).

Le mappe usano tile e dati di [OpenStreetMap](https://www.openstreetmap.org/copyright), © OpenStreetMap contributors, disponibili con licenza Open Database License.
