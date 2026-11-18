# GitHub Copilot Instructions for STOSCBot

STOSCBot is an asynchronous Telegram Bot that manages parishioner affairs, member directories, church service announcements, area prayer groups, streaming links, and financial contributions/Xero tracking for the **St. Thomas Orthodox Syrian Cathedral (STOSC), Singapore**.

---

## 1. Toolchain & Runtime Environment

- **Python Version:** `>=3.13` (strictly Python 3.13 in CI/deployment).
- **Package & Environment Manager:** Use **`uv`** exclusively.
  - Install/sync dependencies: `uv sync` (or `uv sync --group test` for running tests)
  - Run bot locally: `uv run python run_stoscbot.py`
  - Run tests: `uv run pytest`
  - Manage dependencies: `uv add <package>` or `uv add --group test <package>`
  - Version bumping: `uv version --bump <patch|minor|major>`
  - *Do NOT suggest `pip install`, `pipenv`, or `poetry`.*
- **Timezone:** Default timezone is Singapore Standard Time (`Asia/Singapore`, UTC+8). Use `pendulum` or timezone-aware `datetime` objects.
- **SSL / Proxy Compatibility:** Corporate SSL proxies (e.g., Zscaler) may lack critical Basic Constraints on root certificates, which Python 3.13 strictly enforces. `run_stoscbot.py` configures `urllib3.util.ssl_.VERIFY_X509_STRICT = 0` before network imports. Keep this in mind when troubleshooting network SSL issues in scripts.

---

## 2. Frameworks & Telegram Architecture

- **Telegram Bot Framework:** **`kurigram`** (the maintained fork of Pyrogram, imported as `pyrogram`).
  - **Important:** Do NOT import or generate code for `python-telegram-bot`, `telebot`, `aiogram`, or unmaintained `pyrogram`.
  - Documentation reference: [pyrodocs.kurimuzon.ru](https://pyrodocs.kurimuzon.ru/).
  - Handlers use decorators: `@Client.on_message(...)` and `@Client.on_callback_query(...)`.
- **Conversation State Engine:** **`convopyro`** (`from convopyro import Conversation`).
  - Active conversation listener pattern:
    ```python
    try:
        response = await client.listen.Message(
            filters.text, id=filters.user(message.from_user.id), timeout=30
        )
    except asyncio.TimeoutError:
        await message.reply("Timed out, please try again.")
        return
    ```
  - **Crucial:** Always cancel listener on timeouts, cancellation commands (e.g., `/start` or `/cancel`), or validation failures:
    ```python
    await client.listen.Cancel(filters.user(message.from_user.id))
    ```

---

## 3. Project Structure & Organization

```
stoscbot/
├── run_stoscbot.py             # Application entry point
├── plugins/                    # Pyrogram auto-loaded plugin handlers (root="plugins")
│   ├── handlers_main.py        # /start, /help, main navigation
│   ├── handlers_my_details.py  # Member profile, family details, address
│   ├── handlers_members.py     # Member search, birthdays, anniversaries
│   ├── handlers_finance.py     # Financial reports, outstandings, dues, Xero receipts
│   ├── handlers_services.py    # Holy Qurbana schedules and registrations
│   ├── handlers_streaming.py   # Live broadcast URLs and announcements
│   ├── handlers_area_prayer_groups.py # Prayer group meetings and lists
│   └── handlers_dev.py         # Bot health, versioning, admin tools
├── stoscbots/                  # Core library packages
│   ├── bot/
│   │   ├── bot.py              # Pyrogram Client and Convopyro initialization
│   │   └── keyboards.py        # Inline keyboards, callback buttons, WebAppInfo
│   ├── db/
│   │   └── db.py               # MariaDB/MySQL (ChurchCRM) queries
│   ├── xero/
│   │   └── xero_utils.py       # Xero OAuth refresh tokens (DynamoDB) and API calls
│   └── util/
│       ├── bot_auth.py         # Role-based access control and authorization decorators
│       ├── loggers.py          # Rotating file logger and audit tracking decorator
│       └── utils.py            # Formatting helpers, message builders, validators
└── tests/                      # Pytest suite
    ├── conftest.py             # Event loop setup for Pyrogram imports
    ├── mocks.py                # Mocked Pyrogram Client, Messages, Users, and queries
    └── plugins/                # Handler unit and integration tests
```

---

## 4. Coding Standards & Conventions

1. **Strict Asynchronous Execution:**
   - All handlers and helper functions performing I/O must be `async def` and awaited.
   - Do NOT use blocking synchronous sleep (`time.sleep`); use `await asyncio.sleep(...)`.

2. **Access Control & Permissions:**
   - Always protect member-only or management-only routes using decorators from `stoscbots.util.bot_auth`:
     - `@bot_auth.async_member_only` (general registered church members)
     - `@bot_auth.async_management_only` (Management Committee / MC members)
     - `@bot_auth.async_area_prayer_coordinator_only` (APC or MC members)
     - `@bot_auth.super_admin_only` (Super admins defined in `SUPER_ADMIN_TELEGRAM_IDS`)
   - For inline button callback checks, query `bot_auth.is_member(...)` or `bot_auth.is_mgmt_member(...)` and call `await bot_auth.send_access_denied_msg(client, query)` upon failure.

3. **Logging & Metrics:**
   - Initialize loggers with:
     ```python
     logger = logging.getLogger("Handler.<Name>")
     logger.setLevel(LOGLEVEL)
     ```
   - Decorate command/button handlers with `@loggers.async_log_access` to audit access and increment user metrics in AWS DynamoDB.

4. **Safe Dictionary & Object Lookups:**
   - Prefer `.get('key', default)` instead of direct `dict['key']` indexing to prevent `KeyError`.

5. **Telegram Formatting & UI:**
   - Use Telegram Markdown syntax for formatting (`**bold**`, `__italic__`, `` `code` ``).
   - When sending URLs where link expansion is noisy, disable previews with:
     ```python
     link_preview_options=LinkPreviewOptions(is_disabled=True)
     ```
   - Define reusable buttons and keyboards in `stoscbots.bot.keyboards` rather than embedding inline keyboard structures inside handler logic.

6. **Database & External Services:**
   - Database operations in `stoscbots.db.db` run against ChurchCRM via MariaDB/MySQL using prepared statements (`cursor.execute(sql, args)`).
   - Queries must respect server-side query timeout limits (`SET SESSION max_statement_time`).
   - Xero token lifecycle in `stoscbots.xero.xero_utils` stores refresh tokens in AWS DynamoDB table `stosc_xero_tokens`. Refresh tokens rotate on use.

---

## 5. Testing & Mocking Guidelines

- **Runner:** `uv run pytest` (coverage: `uv run pytest --cov=./ --cov-report=xml`).
- **Async Tests:** Mark with `@pytest.mark.asyncio`.
- **Event Loops:** `tests/conftest.py` configures a default event loop in `pytest_configure` to prevent Python 3.10+ `asyncio.get_event_loop()` deprecation warnings during module import.
- **Mocking Telegram & External Calls:**
  - Import pre-built fixtures and dummies from `tests.mocks` (`telegram_client`, `msg`, `telegram_member_mc`, `telegram_member_non`, etc.).
  - Use pytest's `monkeypatch` to neuter Telegram API methods (`Client.send_message`, `Message.reply_text`, `CallbackQuery.answer`, `listen.Message`, `listen.Cancel`).
  - Never trigger actual Telegram messages, DynamoDB updates, or live database modifications during unit tests.

---

## 6. Security & Credentials

- Never commit secrets, session files, or API credentials to git:
  - Keep Telegram bot tokens, AWS keys, database credentials, and admin IDs in `.env` (refer to `.env.sample`).
  - Do not commit `*.session` or `*.session-journal` SQLite files generated by Kurigram/Pyrogram.
  - Access configuration via `os.environ.get(...)` or `stoscbots.util.loggers.get_config(...)`.

---

## 7. Git & Commit Guidelines

- **Commit Message Style:**
  - Do **NOT** use conventional commit prefixes such as `feat:`, `docs:`, `fix:`, `chore:`, or `refactor:`.
  - Write clear, direct commit messages in the imperative mood starting with a capital letter (e.g., `Add mock for requests.get in test_get_address_details`, `Fix VIBIN_TELEGRAM_ID assignment`, `Refactor member authentication checks`).
  - For semantic version bumping via CI, include `(MAJOR)` or `(MINOR)` in the commit message or body where appropriate.

