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
Members results use compact striped tables. Check that today's date is
highlighted in the weekly birthday and anniversary tables, and that the family
codes inside name cells are tappable.
Birthday tables show **NA** in the Age column when the birth year
is missing; anniversary tables use a linked missing-year note.
Telegram controls the colors.
The `/bday` and `/anniv` commands keep their existing text output.

For a Telegram smoke test of the **Household first** layout, use an authorized
account and run `/u <member code>`. A compact header and the family photo appear
first, followed by the head, spouse, children, and other household members when listed.
Contact (including the map when available), dates, and membership start
collapsed. Birth dates, the anniversary, and the membership date use Telegram
date entities where supported, while keeping their calendar-date labels.
Under **Membership & prayer group**, tap a related family code to open its card.
Check the same command with a record that has no photo. Telegram
replies that reject rich formatting fall back to text.

For a smoke test of the **My Details** suite, tap **My details** from the main menu.
The card shows quick actions for **My profile**, **Contributions**, and **Dues**, with
**Church giving & services** collapsed.
Tap **My profile** to check that your personal family card opens with an update disclaimer
and a **Back to My Details** navigation button.
Tap **Contributions** to check that your current year Xero receipts display as a compact
striped table with right-aligned amounts, a total footer, and the Xero timestamp.
Tap **Dues** to check that outstanding subscription invoices display with invoice numbers,
line item descriptions, due balances, and a direct **PayNow** shortcut.
Tap **List of accounts** to check that eligible contribution heads are listed in a compact
table with bold formatting for contributed heads.

For a smoke test of **Area Prayer Groups**, open **Community ▸ Prayer groups** from the home screen.
Check that the 7 area buttons appear on the rich card. Tap an area (e.g. **East Coast**) to check
that its registered families render in a compact striped table with a family count subtitle, tappable
family codes, and a **Back to Prayer Groups** button. Tap a family code to open its family card.

For a smoke test of **PayNow**, tap **PayNow** from the home screen or from **My Dues**.
Check that the card presents the payment options with tap-to-copy code blocks for the UEN
(`S79SS0001L`) and DBS account number (`0480155596`), cash/cheque instructions, a reference and receipt
guide drawer with clickable email, and navigation to **Return to Main menu**.

For a smoke test of **My Harvest Festival**, open **Community ▸ My Harvest Festival** from the home screen.
Check that the card presents the cathedral header, member code, live auction web portal link button (if configured),
a compact striped table for **Auction Wins** with total spend (or friendly notice if no bids),
and an expandable drawer for **Donated Items** with sold prices, alongside the **Main menu** return button.

For a smoke test of **Church Finance & Accounts** (MC only), open **Committee tools ▸ Finance** from the home screen.
Check that the card presents the committee header and two closed help drawers for member contributions (`/x <CODE> [year]`)
and invoices & dues (`/xs <CODE> [year]`), paired with the full 9-button finance keyboard (`Executive Summary`, `Bank Summary`, `Trial Bal Revenue`, `Trial Bal Expense`, `Latest Transactions`, `Payments WTD`, `Outstanding`, `Projects`, and `Return to Main menu`).
Tap **Bank Summary** to verify the compact account table with In, Out, Closing balances, and Fixed Deposits total.
Tap **Executive Summary** to verify the expandable section accordions with comparison tables and variance indicators.
Tap **Latest Transactions** to verify the striped table of past 7 days bank and cash movements with inflow/outflow totals.
Tap **Payments WTD** to verify invoice settlements and bill payments with directional indicators (⇨/⇦) and receipt totals.
Name and phone search keep their existing layouts.

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

