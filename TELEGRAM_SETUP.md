# Telegram Bot Setup

This section explains how to obtain your **Telegram bot token** and **chat ID** for use with the Telegram uploader.

---

## 1. Create a Telegram Bot

1. Open **Telegram** app and search for the user **[@BotFather](https://t.me/BotFather)**.

2. Start a chat and send the command:

   ```
   /newbot
   ```

3. Follow the prompts:

   * **Bot name**: Choose a display name (e.g., `QuoteUploaderBot`).
   * **Username**: Choose a unique username ending with `bot` (e.g., `quote_uploader_bot`).

4. After creation, BotFather will provide a **token**:

   ```
   123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
   ```

5. This token is your **`TELEGRAM_BOT_TOKEN`**.

---

## 2. Get Chat ID

### For a Telegram Channel:

1. Create a **new channel** (public or private).
2. Add your bot as an **admin** with at least **post permissions**.
3. Get the channel **username** (e.g., `@myquoteschannel`).
4. Use this username as your **`TELEGRAM_CHAT_ID`**:

   ```
   TELEGRAM_CHAT_ID=@myquoteschannel
   ```

### For a Telegram Group or Personal Chat:

1. Add your bot to the group or start a chat with the bot.

2. Open Telegram and search for **[@userinfobot](https://t.me/userinfobot)**.

3. Start a chat with **@userinfobot** and send the command `/start`.

4. The bot will reply with your **user ID** or **group ID**. Example:

   ```
   Your Telegram ID: 123456789
   ```

5. Use this ID as your **`TELEGRAM_CHAT_ID`**:

   ```
   TELEGRAM_CHAT_ID=123456789
   ```

> **Note:** Group IDs may appear as negative numbers, which is normal.

---

## 3. Add Environment Variables

Create a `.env` file in your project root:

```bash
# .env
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=@myquoteschannel
```

> Make sure **`.env`** is included in `.gitignore` to avoid leaking your token.

---

## 4. Usage in the Project

The Telegram uploader will automatically read these variables if they exist:

```bash
python telegram_uploader.py --action test
```

This will send a **test message** to verify your bot and chat ID are correctly configured.

