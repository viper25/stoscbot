[![STOSCBot Build](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml/badge.svg)](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml)  [![codecov](https://codecov.io/gh/viper25/stoscbot/branch/main/graph/badge.svg?token=QQ3WXQ2TSQ)](https://codecov.io/gh/viper25/stoscbot)

[![Better Stack Badge](https://uptime.betterstack.com/status-badges/v2/monitor/2oncc.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

# STOSC Bot

A Telegram bot (based on [Pyrogram](https://docs.pyrogram.org/)) to manage affairs of the St. Thomas Orthodox Syrian
Cathedral (STOSC), Singapore.

> Since [Pyrogram](https://github.com/pyrogram/pyrogram) is no longer in active development, I've switched to a fork of
> Pyrogram called [KurimuzonAkuma](https://github.com/KurimuzonAkuma/pyrogram). Docs are
> at [pyrodocs.kurimuzon.ru](https://pyrodocs.kurimuzon.ru/)

![image](https://user-images.githubusercontent.com/327990/142089101-04f782d3-0982-4ac0-83d0-899d714bc1cb.png) ![02](https://user-images.githubusercontent.com/327990/142300513-b2cbde04-f695-40f3-92f3-5e56649550f9.png) ![markup_41332 (1)](https://user-images.githubusercontent.com/327990/145735665-da9a6c31-29cc-4a5e-8824-8cd8653b84f8.png)

## Setup Dev Environment

Create a `.env` file by modifying the [.env.sample](.env.sample)

```bash
uv sync
uv run python run_stoscbot.py
```

## Run Tests

For a home screen smoke test, open `/start` in a private bot chat. **My details**,
**Members**, and **PayNow** are visible immediately. The home card also shows
a family-search example and links to the church website, events calendar, and
livestream. **Community** starts
collapsed. **Committee tools** is visible only to committee members and super
admins; **Admin** is visible only to super admins. Open a submenu, then use
**Return to Main menu** to get the same grouped home. If Telegram rejects the
rich message, the bot sends the original inline keyboard.

Open **Members** to check that today's birthday and anniversary buttons are
visible immediately, while **This week** and **Church & membership** start collapsed.
Open a result and use **Back to Members** to return to the menu.
In the birthday, anniversary, new member, and committee cards, tap a member
code to open its family card. **General Body & quorum** shows aggregate counts only.

For a Telegram smoke test of the **Household first** layout, use an authorized
account and run `/u <member code>`. A compact header and the family photo appear
first, followed by the head, spouse, children, and other household members when listed.
Contact (including the map when available), dates, and membership start
collapsed. Birth dates, the anniversary, and the membership date use Telegram
date entities where supported, while keeping their calendar-date labels.
Under **Membership & prayer group**, tap a related family code to open its card.
Check the same command with a record that has no photo. Telegram
replies that reject rich formatting fall back to text. Name search, phone
search, and My Details keep their existing layouts.

```bash
uv sync --group test
uv run -m pytest
```

Using [pytest-cov](https://github.com/pytest-dev/pytest-cov)

```bash
pytest --cov=./ --cov-report=xml
coverage report
```
## Bump Version

Bump version explicitly `uv version 0.1.0` or [semantically](https://docs.astral.sh/uv/reference/cli/#uv-version--bump) `uv version --bump minor`

## Deployment

We use [GitHub Actions](https://github.com/viper25/stoscbot/actions) to deploy, but the basic deploy steps are lsited
below
<details>
<summary>Deploy on a VM</summary>

1. Update server timezone to local timezone
2. [Do not re-use](https://docs.pyrogram.org/faq/using-multiple-clients-at-once-on-the-same-account) a session file when
   deploying to a new instance. On a new instance, delete any existing `.session` file
   and [generate a new session file](https://docs.pyrogram.org/start/auth#bot-authorization).
3. Keep the `.env` and `.session` files in a `..\credentials\` directory.
   The [deployment scripts](.github\workflows\python-app.yml) will copy these files to the correct location.
4. Subsequently, run headless as ` nohup python3 run_stoscbot.py &`

</details>

## Activity

![Alt](https://repobeats.axiom.co/api/embed/8f7c105c760f4c1728a380d4940249878f8775b4.svg "Repobeats analytics image")

