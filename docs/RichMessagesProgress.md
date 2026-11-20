# Telegram Rich Messages Redesign Progress

Tracking document for converting STOSCBot screens to Telegram's [Rich Message Formatting Options](https://core.telegram.org/bots/api#rich-message-formatting-options) via [Kurigram `InputRichMessage`](https://docs.kurigram.icu/api/types/InputRichMessage/).

---

## 1. Design Conventions & Standards

All redesigned screens adhere to the following patterns established in the initial rollout:

* **Container:** `pyrogram.types.InputRichMessage(blocks=[...])`.
* **Drawers & Collapsible Sections:** `types.InputRichBlockDetails(summary=..., blocks=[...], is_open=False)` for submenus, secondary details, or role-restricted actions.
* **Tables:** `types.InputRichBlockTable(cells=[...], is_striped=True, is_compact=True)` for tabular lists, financial summaries, and rosters.
* **Tappable Member Codes:** Embed codes into table cells or text blocks using `types.RichTextButton(text="CODE", callback_data="related_family:CODE")` so users can jump straight to a family profile.
* **Action Buttons:** Native in-message buttons using `types.InputRichBlockButtons` with `types.RichMessageButton` and styles (`PRIMARY`, `DEFAULT`, `LINK`).
* **Entities:** Use `types.RichTextDateTime`, `types.RichTextPhoneNumber`, `types.RichTextEmailAddress`, `types.RichTextUrl`, and `types.RichTextMarked`.
* **Footnotes & Anchors:** Use `types.InputRichBlockAnchor`, `types.RichTextReferenceLink`, and `types.InputRichBlockFooter` for table notes and missing-data indicators.
* **Error & Compatibility Fallback:**
  * Wrap all calls in `try...except RichMessageUnsupported:` with a plain text or inline keyboard fallback.
  * Handle media failures (`PHOTO_ERRORS`) by retrying without the media block before falling back to text.
  * In `utils.edit_and_send_msg()`, reply rather than edit when `query.message.rich_message` is present to preserve the active rich card.

---

## 2. Completed Screens

- [x] **Home Screen (`/start`, `Main Menu`)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Grouped Dashboard (Proposal 2): Cathedral identity header (`⛪ St. Thomas Orthodox Syrian Cathedral`), clean horizontal divider rules (`InputRichBlockDivider`) delineating each logical section (`👤 Personal & Giving`: My Details, PayNow; `👥 Parish Community`: Directory, Prayer Groups, Harvest Festival; `🏛️ Committee & Ministry` for authorized committee members: Finance, Streaming; `🌐 Cathedral Links`: Website, Calendar, Livestream, Prayer Requests), and a collapsible `📖 Commands & Documentation` drawer at the bottom (collapsing Admin Console for super admins, quick search syntax `/u`, `/t`, `/year`, general bot commands, committee commands, and admin tools). Eliminates visual clutter while providing clear section separation and on-demand reference.
- [x] **Members Menu (`Members Menu` callback)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* "Today first" layout with search hint, today's celebration buttons, collapsed `This week` drawer, and collapsed `Church & membership` drawer.
- [x] **Family Profile (`/u <code\>`, `related_family:<code\>`)**
  - *Location:* [family_profile.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/family_profile.py), [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Design:* "Household first" profile with CRM photo (`InputRichBlockPhoto`), household members block, and 3 collapsed sections (*Contact & address* with OneMap interactive map block, *Birthdays & anniversary* with rich dates, and *Membership & prayer group* with tappable related family codes).
- [x] **Birthdays Today (`Member Birthday Today Button`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table with member name, tappable family code, and calculated age (or `NA`).
- [x] **Anniversaries Today (`Member Anniversary Today Button`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table with couple names, tappable family code, years married, and footnote anchor for missing wedding years.
- [x] **Birthdays This Week (`Member Birthday Week Button`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table with date range subtitle, highlighted today's date (`RichTextMarked`), member names, tappable codes, and age.
- [x] **Anniversaries This Week (`Member Anniversary Week Button`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table with date range subtitle, highlighted today's date (`RichTextMarked`), couple names, tappable codes, years, and missing-year footnote link.
- [x] **Management Committee Roster (`MC`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table with role titles, committee member names, and tappable family codes.
- [x] **General Body & Quorum (`GB`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact table with eligible voter count and 25% quorum calculation.
- [x] **New Members (`New Members Button`)**
  - *Location:* [handlers_members.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_members.py)
  - *Design:* Compact striped table showing families joined in the last 12 months with parsed tappable family codes.
- [x] **`My Details Menu` (Submenu Hub)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Grouped card with profile button, contributions and dues buttons, collapsed `Church giving & services` drawer (`List of accounts` and `Submit prayer request` Web App), and return to main menu link button.
- [x] **`My Profile` (`My Profile` callback)**
  - *Location:* [handlers_my_details.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_my_details.py), [family_profile.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/family_profile.py)
  - *Design:* Reuses `family_profile.send_family_profile()` with CRM photo, household members, collapsible contact/dates/membership drawers, return to My Details keyboard, and office update note footer.
- [x] **`My Contributions` (`My Contributions` callback)**
  - *Location:* [handlers_my_details.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_my_details.py)
  - *Design:* Compact striped table with account heads, right-aligned contribution amounts, total footer with Xero timestamp, and return to My Details navigation.
- [x] **`My Dues` (`My Dues` callback)**
  - *Location:* [handlers_my_details.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_my_details.py)
  - *Design:* Displays green status message if dues are cleared; otherwise presents a compact striped table of invoices, descriptions, and due amounts, with a total due footer and direct `PayNow` action button.
- [x] **`List of Accounts` (`List of Accounts` callback)**
  - *Location:* [handlers_my_details.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_my_details.py)
  - *Design:* Compact striped table showing all eligible church contribution heads, with contributed accounts and amounts highlighted in bold.
- [x] **`Area Prayer Groups Menu` & Member List (`Prayer Groups Menu`, `Area Prayer Group`)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [handlers_area_prayer_groups.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_area_prayer_groups.py), [keyboards.py](file:///home/viper25/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:*
    - *Menu:* Clean rich card header with a balanced, full-width 2-column grid keyboard for all 7 areas and main menu return.
    - *Roster:* Compact striped table of registered families with parsed tappable family codes (`related_family:<CODE>`), family count subtitle, footer tip, and `← Back to Prayer Groups` navigation button.
- [x] **`PayNow Menu` (`PayNow Menu` callback)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Rich payment card with optional QR photo (`InputRichBlockPhoto`), tap-to-copy monospace code blocks for UEN (`S79SS0001L`) and DBS Account (`0480155596`), cash/cheque instructions, collapsible reference and receipt guide with email link, and clean `[ 🔙 Return to Main menu ]` navigation.
- [x] **`My Harvest Festival Menu` (`My Harvest Festival Menu` callback)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py), [utils.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/util/utils.py)
  - *Design:* Option 1 clean tabular breakdown:
    - *Header:* Cathedral title, member code tag (`RichTextCode`), and optional direct link button to live web auction portal (`🌐 Open Auction Portal`).
    - *Auction Wins:* Open by default with a compact striped table (`InputRichBlockTable`) of Lot, Item name, and Winning bid with total spend footer (or friendly `~ No bids or purchases yet ~` note).
    - *Donated Items:* Expandable drawer (`InputRichBlockDetails`) titled `🎁 Donated Items (N items · $Y)` with a striped table of Lot, Item, Buyer, and Sold amount.
    - *Navigation:* Native reply markup keyboard with `[ 🔙 Return to Main menu ]`.
- [x] **`Finance Menu` Hub (`Finance Menu` callback)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Protected with `@bot_auth.async_management_only`. Presents a rich card with cathedral committee badge and member ledger search hints (`/x <CODE>` for payments, `/xs <CODE>` for invoices). Retains all 8 finance action buttons in a balanced 2-column inline keyboard plus return to main menu.
- [x] **`Finance Bank Summary` (`Finance Bank Summary Button` callback)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/viper25/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Compact striped table (`InputRichBlockTable`) listing active operating bank accounts with Inflows, Outflows, and Closing balances, plus a footer block consolidating Fixed Deposits (`DBS FD`) and operating totals. Kept all finance buttons in `reply_markup` for seamless switching.
- [x] **`Finance Executive Summary` (`Finance Executive Summary Button` callback)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Subtitle contrasting current vs previous month. Section accordions (`InputRichBlockDetails`) for each financial section (Cash, Balance Sheet, Customers) containing compact comparison tables with formatted variance arrows (▲/▼). All finance buttons kept visible in `reply_markup`.
- [x] **`Finance Latest Transactions` (`Finance Latest Transactions Button` callback)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Compact striped table (`InputRichBlockTable`) of past 7 days cash movements across Cash, DBS, and NETS with transaction dates, diamond markers (`🔹` inflow, `🔸` outflow), contact names, and total Inflow/Outflow footer. All finance buttons kept visible in `reply_markup`.
- [x] **`Finance Payments WTD` (`Finance Payments WTD Button` callback)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Compact striped table (`InputRichBlockTable`) of invoice settlements (`ACCREC` / `🔹`) and bill payments (`ACCPAY` / `🔸`) with dates, contacts, direction tags (`Receipt ⇦`, `Bill ⇨`), and total Received/Paid footer. All finance buttons kept visible in `reply_markup`.
- [x] **`Finance Trial Balance` (Revenue & Expense) (`Finance Trial Balance Revenue Button`, `Finance Trial Balance Expense Button` callbacks)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Compact striped table (`InputRichBlockTable`) of active chart of accounts with YTD balances, year and basis subtitle (Cash basis for revenue, YTD ledger for expenses), Option 3 total footer (`🔹 Total Revenue: $...` / `🔸 Total Expense: $...`), and persistent `finance_menu_keyboard` for instant switching.
- [x] **Member Financial Search Commands (`/x`, `/xs`) & Callbacks (`search_xero_payments`, `search_xero_dues`)**
  - *Location:* [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:*
    - **`/x <CODE> [YEAR]` (Contributions):** Compact striped table (`InputRichBlockTable`) of member accounts and amounts, total contributions footer (`🔹 Total Contributions: $...`) with Xero timestamp, and action buttons (`[ 📜 View Dues (/xs) ]`, `[ 👤 Family Profile ]`).
    - **`/xs <CODE> [YEAR]` (Invoices & Dues):** Upfront striped table of outstanding invoices (`🔸 Due: $...`), collapsible drawer for settled receipts (`📁 Settled Invoices (N paid · $...)`), total due/settled footer, and action buttons (`[ 💳 View Contributions (/x) ]`, `[ 👤 Family Profile ]`).
    - **Interactive Callbacks:** Seamless 1-tap switching between payments, dues, and family profile without retyping commands.

- [x] **`Streaming Menu` & Announcement Slides (`Streaming Menu`, `Generate Announcement Slides` callbacks)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [handlers_streaming.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_streaming.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:*
    - **Menu Card (`get_rich_streaming_menu`):** Cathedral Media & Streaming title, collapsible guide drawer explaining slide generation and flyer image URL generation (via photo uploads), in-card link buttons to Google Drive slides and live broadcast, plus updated inline keyboard (`[ 📺 Generate Announcement Slides ]`, `[ 📂 Google Drive Slides ]`, `[ 🔙 Return to Main menu ]`).
    - **Trigger Feedback (`get_rich_slide_generation_result`):** Rich card indicating generation status (`✅` success on Linux, `⚠️` non-zero code or OS restriction) with direct link button to view synced output on Google Drive.

- [x] **`Services Menu` (Retired & Streamlined)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:* Retired dedicated services card per user request; `Prayer Requests` (`https://stosc.com/pr`) moved directly to the Cathedral Links bar on the main home screen next to `Livestream`. All leftover service schedules and COVID-era service code completely purged.

---

- [x] **Free Text / Name Search Results (`/u <name>`)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:*
    - **Header & Match Count:** Search banner showing query and total matching parishioner count.
    - **Interactive 2-Column Table:** Clean 2-column table (`Parishioner` and `Code`) eliminating awkward name wrapping and redundant family names.
    - **Direct Tap Links:** Tapping any parishioner's name directly opens their individual profile (`Member_<fam>_<person_id>`); tapping the family code opens the household profile (`related_family:<fam_code>`).
    - **Strict Left Name Alignment with Right-Side Indicators:** All names are perfectly left-aligned at column 0. Head of Family is marked with `⭐` on the right (e.g. `Anish Mathew Samuel ⭐`), and dependent children are marked with `🎒` on the right (e.g. `Annika Mathew 🎒`), completely avoiding prefix indentation jitter and ugly line wrapping.
    - **Clean Navigation:** Streamlined bottom keyboard with only `[ 🔙 Return to Main menu ]`, removing duplicate button bloat.

- [x] **Individual Member Card (`Member_<fam>_<id>` button callback)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [family_profile.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/family_profile.py)
  - *Design:*
    - **Header:** Member name with nickname in parenthesis and family name with tappable family code link.
    - **Individual Photo:** CRM person photo (`InputRichBlockPhoto`) fetched dynamically with automated fallback if unsupported.
    - **Personal & Contact Info:** Profession, WhatsApp mobile link (`https://wa.me/65...`), tap-to-email link (`mailto:`), and date of birth.
    - **Collapsible Address & Location:** Collapsible drawer with OneMap interactive static map block and formatted address.
    - **Action Keyboard:** Direct button to view household family profile (`[ 👨‍👩‍👧‍👦 View Family Profile ]`) and return to main menu.

- [x] **Mobile Search (`/t <phone>`)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [family_profile.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/family_profile.py)
  - *Design:* Direct lookup by Singapore telephone number rendering the rich family profile card (`send_family_profile`) with household roster, photo, and interactive location drawer.

---

- [x] **Members Born in Year (`/year <YYYY>`)**
  - *Location:* [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py)
  - *Design:*
    - **Header & Age Context:** Title showing birth year (`🎂`) with calculated current age (`Turning X yrs in YYYY`) and matching parishioner count.
    - **Compact 3-Column Table:** Striped table detailing Parishioner name, Birthday (`DD Mon`), and centered interactive family code button (`related_family:<fam_code>`).
    - **Access Control & Fallback:** Protected with `@bot_auth.async_member_only`, with clean plain text fallback for older clients and `[ 🔙 Return to Main menu ]`.

---

- [x] **Developer & Super Admin Tools (`/version`, `/ver`, and Admin Callbacks)**
  - *Location:* [handlers_dev.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_dev.py), [keyboards.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/bot/keyboards.py), [bot_auth.py](file:///home/vibinjk/code/viper25/stoscbot/stoscbots/util/bot_auth.py)
  - *Design:*
    - **Bot Version Card (`/version`, `/ver`):**
      - Header with Cathedral Developer & System Info badge (`ℹ️`).
      - Compact 2-column key-value attribute table (`Release Version`, `Release Date`, `Build SHA`, `Git Branch`, `Kurigram Engine`, `Python Runtime`, `Session Name`).
      - Confidentiality footer with return to main menu navigation.
    - **Admin Menu Hub (`Admin Menu` callback):**
      - Header with Developer & Admin Hub badge (`🛠`).
      - Collapsible drawer (`InputRichBlockDetails`) with CLI command quick reference (`/cmd logs`, `/id`, `/add`, `/send`, `/version`).
      - Confidentiality footer and inline keyboard for Stats, Logs, and Error Logs.
    - **Admin Stats Card (`Show Stats` callback):**
      - Header with Top Active Parishioners title (`📊`) and audit month indicator.
      - Compact striped table (`InputRichBlockTable`) listing Rank (`#1`, `#2`, ...), Parishioner Name (resolved from Telegram ID via DynamoDB), and Message count.
      - Total messages footer from top users and graceful note on non-Linux hosts.
    - **System Activity & Error Logs (`Show Logs`, `Show Error Logs` callbacks):**
      - Header with Recent System Activity (`📜`) or System Error Diagnostics (`⚠️`).
      - Formatted monospace code block (`RichTextCode`) with safe length truncation (capped to 3,000 chars) to prevent Telegram payload overflow.
      - Timestamped footer and full plain text fallback.
    - **Member Telegram ID Lookup Card (`/id <member_code>`):**
      - Header with `Registered Telegram Accounts 🆔`, member code badge (`RichTextCode`), and registered account count subtitle.
      - Compact striped table (`InputRichBlockTable`) listing Parishioner name with role badges (`👑 Super Admin`, `🏛️ MC`) and tap-to-copy Telegram ID (`RichTextCode`).
      - Not-found rich card if member code has no registered accounts yet.
      - Direct action navigation button `[ 👨‍👩‍👧‍👦 View Family Profile (<CODE>) ]` linking to CRM profile/photos/household and `[ 🔙 Return to Main menu ]`.
    - **Security & Route Protection:**
      - Hardened `@bot_auth.super_admin_only` decorator to support both `Message` and `CallbackQuery` objects, ensuring super-admin restricted button callbacks reject unauthorized callers safely.

---

## 3. Remaining Screens Identified for Redesign

All planned screens across Groups A, B, C, D, and Developer/Admin tools are now fully converted to Telegram's Rich Message format!
