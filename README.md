# 💩 Caccometro Bot Telegram

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

Crea un file denominato `.env` nella directory principale del progetto (non committarlo su Git).

```env
BOT_USERNAME = '@username_bot'
BOT_TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'

USERNAME = 'il_tuo_username_di_pythonanywhere'
PATH = '/home/il_tuo_username_di_pythonanywhere/home_repo'

RUN_MODE = 'WEBHOOK' # 'WEBHOOK' or 'POLLING'
```

### 3. Impostazione dei Comandi

Utilizza il comando `/setcommands` su **[@BotFather](https://t.me/botfather)** per registrare i comandi:

```
start - Avvia il bot.
classifica_mese - Classifica mese (corrente o specifico [MM-YYYY]).
classifica_anno - Classifica dell'anno (corrente o specifico [YYYY]).
statistiche_mese - Statistiche del mese (corrente o specifico [MM-YYYY]).
statistiche_anno - Statistiche dell'anno (corrente o specifico [YYYY]).
record - Record dell'utente (@username).
aggiungi - Aggiunge 1 all'utente nel giorno specificato (@username [DD-MM-YYYY]).
togli - Sottrae 1 all'utente nel giorno specificato (@username [DD-MM-YYYY]).
conto_giorno - Conteggio per il giorno (@username [DD-MM-YYYY]).
costipazione - Conteggio giorni di costipazione (@username).
```

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
# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys
import os
from dotenv import load_dotenv

load_dotenv()
# add your project directory to the sys.path
PATH = os.environ.get('PATH')
if PATH not in sys.path:
    sys.path.insert(0, PATH)

# import flask app but need to call it "application" for WSGI to work
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
| `/record [@username]`                  | Visualizza i record personali (massimi giornalieri/mensili, serie più lunghe) di un utente. Omesso per il tuo record. |
| `/aggiungi [@username] DD-MM-YYYY`     | Aggiunge manualmente +1 al conteggio per un giorno passato o corrente.                                                |
| `/togli [@username] DD-MM-YYYY`        | Sottrae manualmente -1 al conteggio (fino a 0) per un giorno passato o corrente.                                      |
| `/conto_giorno [@username] DD-MM-YYYY` | Restituisce il conteggio totale per un utente in un giorno specifico.                                                 |
| `/costipazione [@username]`            | Restituisce i giorni consecutivi trascorsi dall'ultima evacuazione registrata.                                        |

---

Ora sei pronto per iniziare a sperimentare con il codice di Caccometro! Buon divertimento!
