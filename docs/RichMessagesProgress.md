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
  - *Design:* Grouped home with search hint (`/u A001`), primary shortcut row (`My details`, `Members`, `PayNow`), collapsed `Community` drawer, role-restricted collapsed `Committee tools` drawer, and external links footer (`Church website`, `Events`, `Livestream`).
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
    - *Menu:* Clean rich card displaying all 7 area buttons and a link back to the main menu.
    - *Roster:* Compact striped table of registered families with parsed tappable family codes (`related_family:<CODE>`), family count subtitle, footer tip, and `← Back to Prayer Groups` navigation button.

---

## 3. Remaining Screens Identified for Redesign

---

### Group B: Community & Church Life

- [ ] **`PayNow Menu`**
  - *Handler:* `show_paynow_menu` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Current State:* Sends standalone QR image with payment instructions in the photo caption.
  - *Proposed Redesign:* Rich card embedding the QR photo (`InputRichBlockPhoto`), preformatted code blocks for UEN (`S79SS0001L`) and DBS Account (`0480155596`), copyable payment reference guide, and `accounts@stosc.com` email entity.

- [ ] **`My Harvest Festival Menu`**
  - *Handler:* `show_my_harvest_festival_menu` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Current State:* Text printout of auction purchases and contributions.
  - *Proposed Redesign:* Rich card with summary blocks or tables for Auction Purchases (item, lot, bid amount) and Contributions, with auction links.

---

### Group C: Committee & Management Tools (MC / Super Admin)

- [ ] **`Finance Menu` & Executive Reports**
  - *Handler:* `show_finance_menu`, `get_finance_executive_summary` in [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py)
  - *Current State:* Long text output with plain text dividers and ASCII arrows (`▲`, `▼`).
  - *Proposed Redesign:* Collapsible `InputRichBlockDetails` per financial section (e.g. Cash Position, Performance, Profitability) with compact tables comparing Current Month vs Previous Month and variance indicators.

- [ ] **`Finance Bank Summary` & `Trial Balance`**
  - *Handler:* `get_finance_bank_summary`, `get_finance_trial_balance` in [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py)
  - *Current State:* Monospaced code blocks and text messages.
  - *Proposed Redesign:* Compact striped tables with right-aligned balances and total row.

- [ ] **`Finance Latest Transactions` & `Payments WTD`**
  - *Handler:* `get_finance_latest_transactions`, `get_finance_payments_wtd` in [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py)
  - *Current State:* Plain text lines of transactions.
  - *Proposed Redesign:* Compact striped table with transaction date, contact/member, account, and amount.

- [ ] **Member Financial Search Commands (`/x`, `/xs`)**
  - *Handler:* `finance_search_member` in [handlers_finance.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_finance.py)
  - *Current State:* Text reply of member payments (`/x`) or invoices (`/xs`).
  - *Proposed Redesign:* Formatted financial statement table for the searched family.

- [ ] **`Streaming Menu` & Announcement Slides**
  - *Handler:* `show_streaming_menu` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py), `handlers_streaming.py`
  - *Current State:* Text menu with slide generation trigger.
  - *Proposed Redesign:* Rich card with slide generation action button, Google Drive folder link, and recent status.

- [ ] **`Services Menu`**
  - *Handler:* `show_services_menu` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Current State:* Text menu with liturgical calendar link.
  - *Proposed Redesign:* Clean rich card with schedule details, PDF calendar link button, and service booking links.

---

### Group D: Member Directory & Search

- [ ] **Free Text / Name Search Results (`/u <name>`)**
  - *Handler:* `member_search_cmd_handler` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Current State:* Generates individual inline keyboard buttons for each matching person.
  - *Proposed Redesign:* When multiple matches are found, display a compact table or rich list of matching names, family codes, and prayer groups, with direct tap actions to open their profile.

- [ ] **Individual Member Card (`Member_<id>` button callback)**
  - *Handler:* `member_search_button_handler` in [handlers_main.py](file:///home/vibinjk/code/viper25/stoscbot/plugins/handlers_main.py)
  - *Current State:* Calls `utils.generate_profile_msg_for_member()` and `utils.send_profile_address_and_pic()`.
  - *Proposed Redesign:* Structured individual card showing person details, individual photo if available, contact info, and link to their household family card.
