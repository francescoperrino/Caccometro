# 💩 Caccometro Bot Telegram

<p align="center">
  <img src="assets/avatar.png" alt="Caccometro avatar" height="200">
  <img src="assets/demo.gif" alt="Caccometro: a 💩 sent from the phone, the leaderboard gets +1 and a medal" height="200">
</p>

Benvenuto in Caccometro, un bot Telegram open source progettato per tracciare i movimenti intestinali (💩) e sfidare gli amici a mantenere un conteggio accurato! \

Il bot offre classifiche mensili/annuali, statistiche dettagliate e il calcolo dei giorni di "costipazione" per mantenere alta la motivazione del gruppo.

Prima di iniziare, segui attentamente questi passaggi per configurare correttamente l'ambiente di sviluppo e il bot.

---

## 🛠️ Installazione e Setup

Si raccomanda vivamente l'uso di un ambiente virtuale (`.venv`) per isolare le dipendenze.

### 1. Preparazione dell'Ambiente Virtuale

Esegui i comandi appropriati per il tuo sistema operativo.

| Sistema Operativo | Crea Ambiente           | Attiva Ambiente             |
| :---------------- | :---------------------- | :-------------------------- |
| **Linux / macOS** | `python3 -m venv .venv` | `source .venv/bin/activate` |
| **Windows**       | `python -m venv .venv`  | `.\.venv\Scripts\activate`  |

### 2. Installazione delle Dipendenze

Con l'ambiente virtuale attivo, installa tutte le librerie necessarie:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configurazione del Bot

Prima di poter avviare il bot, è necessario crearne uno nuovo su Telegram e configurarlo correttamente. Segui questi passaggi:

### 1. Creazione e Token

1.  Avvia una chat con **[@BotFather](https://t.me/botfather)** su Telegram.
2.  Utilizza il comando `/newbot` per ottenere il tuo `BOT_USERNAME` e il **`BOT_TOKEN`**.

### 2. Variabili d'Ambiente (`.env`)

Copia `.env.example` in un file `.env` nella directory principale del progetto e inserisci i tuoi valori. `.env` è escluso da Git: non va mai committato.

```env
BOT_USERNAME = '@username_bot'
BOT_TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
WEBHOOK_SECRET = 'una_stringa_casuale_lunga' # lettere, numeri, _ e -: Telegram la rimanda a ogni chiamata del webhook

HOSTING_USERNAME = 'il_tuo_username_di_pythonanywhere' # usato solo da set_webhook.py

RUN_MODE = 'WEBHOOK' # 'WEBHOOK' or 'POLLING'
```

### 3. Impostazione dei Comandi

Utilizza il comando `/setcommands` su **[@BotFather](https://t.me/botfather)** per registrare i comandi:

```
start - Avvia il bot e spiega come contare le 💩.
classifica_mese - Classifica del mese, corrente o [MM-YYYY].
classifica_anno - Classifica dell'anno, corrente o [YYYY].
statistiche_mese - Media, mediana e varianza del mese, corrente o [MM-YYYY].
statistiche_anno - Media, mediana e varianza dell'anno, corrente o [YYYY].
record - Record del gruppo; con io o @username quelli di una persona.
conto_giorno - 💩 di un giorno: [@username] [DD-MM-YYYY].
costipazione - Giorni senza 💩: [@username].
aggiungi - Aggiunge 1 💩 in un giorno: [@username] DD-MM-YYYY (altri: solo admin).
togli - Toglie 1 💩 in un giorno: [@username] DD-MM-YYYY (altri: solo admin).
collega - Collega lo storico dei vecchi username agli utenti (admin).
```

Con `/setdescription` e `/setabouttext` imposta anche le descrizioni del bot:

- **Descrizione:** Manda 💩 o 🚽 quando hai fatto il tuo dovere: il bot tiene il conto per ogni persona del gruppo, con classifiche, statistiche, grafici e record personali e di gruppo.
- **Descrizione breve:** Conta le 💩 del gruppo: classifiche, statistiche, grafici e record.

---

## ▶️ Avvio del Bot

Il bot supporta due modalità operative, selezionate tramite la variabile `RUN_MODE` nel file `.env`.

### Modalità 1: POLLING (Sviluppo Locale)

In questa modalità, il bot interroga direttamente i server di Telegram per ricevere gli aggiornamenti. È l'opzione consigliata per il testing e il debug in locale.

```bash
# Assicurati che RUN_MODE = 'POLLING' in .env
python caccometro.py
```

> 💡 **Suggerimento:** Per terminare l'esecuzione in modo pulito in console, usa `CTRL+C`.

### Modalità 2: WEBHOOK (Produzione / PythonAnywhere)

Questa modalità è ottimizzata per l'hosting su servizi esterni (PAAS) come PythonAnywhere, dove il server Flask riceve direttamente gli aggiornamenti. Assicurati che `RUN_MODE = 'WEBHOOK'` nel tuo `.env`.

#### 1. Configurazione WSGI su PythonAnywhere

Quando crei una nuova Web App su PythonAnywhere, essa genera automaticamente un file WSGI (solitamente `/var/www/USERNAME_com_wsgi.py`).

Devi integrare l'applicazione Flask del bot (`caccometro.py`) in questo file WSGI di PythonAnywhere.

```python
# WSGI configuration for the hosting: copy this file over the WSGI file the hosting created
# for the web app and set `path` to the folder that holds caccometro.py.

import sys

# Folder of the project, written out: the environment and .env are not loaded yet at this point
path = '/home/<your-username>'
if path not in sys.path:
    sys.path.insert(0, path)

# The hosting looks for a variable named "application"
from caccometro import app as application
```

#### 2. Configurazione del Webhook (Passaggio Unico)

Dopo che l'applicazione è stata avviata correttamente tramite la configurazione WSGI, devi comunicare a Telegram l'URL del tuo server. Esegui il tuo script `set_webhook.py` **una sola volta** dalla console Bash del tuo host:

```bash
python set_webhook.py
```

> 💡 Dopo l'esecuzione, puoi chiudere lo script. Telegram invierà i Webhook all'URL specificato..

---

## 📚 Comandi Dettagliati

| Comando                                | Descrizione                                                                                                           |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `/start`                               | Inizializza il database per la chat corrente.                                                                         |
| `/classifica_mese [MM-YYYY]`           | Mostra la classifica mensile. Se la data è omessa, usa il mese corrente.                                              |
| `/classifica_anno [YYYY]`              | Mostra la classifica annuale. Se la data è omessa, usa l'anno corrente.                                               |
| `/statistiche_mese [MM-YYYY]`          | Mostra statistiche avanzate (Media, Mediana, Varianza) per il mese. Se la data è omessa, usa il mese corrente.        |
| `/statistiche_anno [YYYY]`             | Mostra statistiche avanzate (Media, Mediana, Varianza) per l'anno. Se la data è omessa, usa l'anno corrente.          |
| `/record [@username \| io]`            | Senza argomenti mostra i **record del gruppo** (chi detiene ciascun record e chi è in testa adesso). Con `io` i tuoi record, con `@username` (o rispondendo a un messaggio) quelli di un altro utente: massimi giornalieri/mensili, serie più lunghe, pause, ciascuno con lo **stato attuale** (oggi, questo mese, serie e pausa in corso). |
| `/aggiungi [@username] DD-MM-YYYY`     | Aggiunge manualmente +1 al conteggio per un giorno passato o corrente.                                                |
| `/togli [@username] DD-MM-YYYY`        | Sottrae manualmente -1 al conteggio (fino a 0) per un giorno passato o corrente.                                      |
| `/conto_giorno [@username] DD-MM-YYYY` | Restituisce il conteggio totale per un utente in un giorno specifico.                                                 |
| `/costipazione [@username]`            | Restituisce i giorni consecutivi trascorsi dall'ultima evacuazione registrata.                                        |
| `/collega [auto \| username storico]`  | Collega lo storico dei dati registrati per username agli utenti (vedi sotto). Senza argomenti mostra cosa resta da collegare. |

Nei comandi con `[@username]` il destinatario può essere indicato anche **rispondendo a un messaggio** della persona (utile per chi non ha uno username).

---

## 🏅 Come si calcolano i record

- **Giorno / serie / pause:** sul giorno con più 💩, sulla serie più lunga di giorni consecutivi con almeno un 💩, sulla serie con più 💩 complessivi e sulla pausa più lunga tra due giorni con 💩. A parità vengono elencati tutti i periodi.
- **Mese migliore:** solo mesi completi (il mese in corso non vale ancora).
- **Mese peggiore:** solo mesi completi, escluso il primo mese con dati (potresti aver iniziato a metà) e quelli dopo l'ultimo mese con dati (potresti essere uscito dal gruppo); i mesi in mezzo senza nessun 💩 contano come 0. Serve quindi almeno un secondo mese di dati.
- **Record del gruppo:** per ogni metrica il valore migliore tra tutti gli utenti (anche chi è uscito dal gruppo) e chi lo detiene; a parità sono elencati tutti. Il blocco "Adesso" considera solo chi ha fatto 💩 negli ultimi 90 giorni.
- **Stato attuale:** una serie è "in corso" se l'ultimo 💩 è di oggi o di ieri; la pausa in corso sono i giorni dall'ultimo 💩. Il 🔥 compare quando raggiungi un record (da 2 in su) o superi la pausa record.

---

## 🔄 Identità degli utenti e migrazione dei dati storici

I conteggi sono associati allo **UserID di Telegram**, non più allo username: chi cambia username non perde i dati e chi non ha uno username viene contato con il proprio nome.

- Il bot impara username e nome di chi scrive: un `@username` nei comandi funziona solo per utenti che hanno già scritto almeno un messaggio nel gruppo. In alternativa si può rispondere a un messaggio della persona.
- Al primo avvio i database esistenti vengono **migrati automaticamente**. Prima della migrazione viene creata una copia (`db/<chat_id>_bot_data.db.v1.bak`); i dati vecchi restano in una tabella di archivio finché non vengono collegati.
- Gli **admin** del gruppo collegano lo storico alle persone con `/collega`:
  1. `/collega` mostra lo storico ancora da collegare;
  2. quando tutti hanno scritto almeno un messaggio, `/collega auto` collega gli username identici;
  3. per gli altri, si risponde a un messaggio della persona con `/collega <username storico>`.
- Le registrazioni vecchie senza username non possono essere collegate.

---

Ora sei pronto per iniziare a sperimentare con il codice di Caccometro! Buon divertimento!

## Licenza

Caccometro è distribuito con licenza [MIT](LICENSE).
