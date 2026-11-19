"""Build and send the rich family profile used by member-code lookups."""

import asyncio
import logging
import re
from datetime import UTC, date, datetime, time
from io import BytesIO
from typing import cast

from pyrogram import Client, enums, errors, types
from requests import RequestException

from stoscbots.util import utils

logger = logging.getLogger("Handler.Main")

# Keep the display value separate from its optional rich rendering for the text fallback.
type Field = tuple[str, str | None, types.RichText | None]
RELATED_FAMILY_PREFIX = "related_family:"
PHOTO_ERRORS = (
    errors.MediaEmpty,
    errors.PhotoInvalid,
    errors.PhotoInvalidDimensions,
    errors.PhotoExtInvalid,
    errors.PhotoSaveFileInvalid,
    errors.ChatSendPhotosForbidden,
)


def _rich_text(value: str | list[str | types.RichText]) -> types.RichText:
    """Bridge Kurigram's RichText annotation and its accepted string/list inputs."""
    return cast(types.RichText, value)


def _paragraphs(fields: list[Field]) -> list[types.InputRichBlock]:
    """Render populated fields, so empty rows don't create blank space."""
    return [
        _paragraph(label, value, link) for label, value, link in fields if value
    ]


def _paragraph(label: str, value: str, link: types.RichText | None) -> types.InputRichBlockParagraph:
    """Render the label separately so only the value becomes a link."""
    return types.InputRichBlockParagraph(
        text=_rich_text([types.RichTextBold(text=_rich_text(f"{label}: ")), link or value])
    )


def _household_block(fields: list[Field]) -> types.InputRichBlockParagraph:
    """Use line breaks within one block to avoid Telegram's inter-block spacing."""
    lines: list[str | types.RichText] = [types.RichTextBold(text=_rich_text("Household"))]
    for label, value, _ in fields:
        if value:
            lines.extend(["\n", types.RichTextBold(text=_rich_text(f"{label}: ")), value])
    return types.InputRichBlockParagraph(text=_rich_text(lines))


def _family_photo(family_id: int) -> BytesIO | None:
    """Fetch an uploadable family photo, if the CRM has one."""
    try:
        response = utils.fetch_crm_profile_photo(f"family/{family_id}")
        if response.status_code in (204, 404):
            return None
        response.raise_for_status()
    except RequestException as exc:
        logger.warning("Could not fetch family profile photo: %s", type(exc).__name__)
        return None

    # Check the bytes instead of assuming a successful response contains an image.
    content = response.content
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = "png"
    elif content.startswith(b"\xff\xd8\xff"):
        extension = "jpg"
    else:
        if content:
            logger.warning("CRM returned an unsupported family profile photo")
        return None

    photo = BytesIO(content)
    photo.name = f"family.{extension}"
    return photo


def _family_map(postcode: str) -> types.InputRichBlockMap | None:
    """Turn a postcode lookup into a map block only if the coordinates are valid."""
    coordinates = utils.get_address_details(postcode)
    if not coordinates:
        return None
    try:
        latitude, longitude = map(float, coordinates)
    except (TypeError, ValueError):
        logger.warning("Invalid coordinates for family profile map")
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        logger.warning("Out-of-range coordinates for family profile map")
        return None
    return types.InputRichBlockMap(
        location=types.Location(latitude=latitude, longitude=longitude),
        zoom=16,
        width=320,
        height=160,
    )


def _date_field(label: str, value: object) -> Field:
    """Make a rich date while retaining its display text for the fallback reply."""
    if not value:
        return label, "", None
    stored = str(value)
    try:
        day = date.fromisoformat(stored)
    except ValueError:
        logger.debug("Leaving non-ISO profile date as text: %s", label)
        return label, stored, None

    text = utils.format_iso_date_readable(stored)
    instant = datetime.combine(day, time.min, tzinfo=UTC)
    if not -(2**31) <= instant.timestamp() < 2**31:
        logger.debug("Leaving profile date outside Telegram's timestamp range as text: %s", label)
        return label, text, None

    # Keep the displayed calendar date fixed rather than formatting it in the reader's time zone.
    return label, text, types.RichTextDateTime(text=_rich_text(text), date=instant)


def family_code_link(code: str) -> str | types.RichTextButton:
    """Open the family card from a rich message, or keep an invalid code as text."""
    if not re.fullmatch(r"[A-Za-z][0-9]{3}", code):
        return code
    return types.RichTextButton(button=types.RichMessageButton(
        text=_rich_text(code),
        style=enums.ButtonStyle.LINK,
        callback_data=f"{RELATED_FAMILY_PREFIX}{code.upper()}",
    ))


def _related_families_field(value: str | None) -> Field:
    """Make each family code tappable without changing separators or notes."""
    parts: list[str | types.RichText] = []
    for index, part in enumerate(re.split(r"\b([A-Za-z][0-9]{3})\b", value or "")):
        if index % 2:
            parts.append(family_code_link(part))
        elif part:
            parts.append(part)
    return "Related families", value, _rich_text(parts) if parts else None


async def send_family_profile(client: Client, chat_id: int, row: tuple) -> None:
    """Send a household-first profile, degrading to a photo-free or plain-text reply."""
    # Match the SELECT column order in get_member_details for a code lookup.
    (
        family_id, code, name, email, _, head_email, spouse, spouse_email,
        children, others, address1, address2, postcode, mobile, home_phone,
        parish, joined, related, electoral_roll, prayer_group, head_dob,
        spouse_dob, _, _, anniversary,
    ) = row
    spouse = spouse if spouse != name else None
    title = f"{name} & {spouse}" if spouse else name
    subtitle = f"Family profile ({code})"
    household: list[Field] = [
        ("Head", name, None),
        ("Spouse", spouse, None),
        ("Children", children, None),
        ("Other family members", others, None),
    ]
    address = ", ".join(str(part) for part in (address1, address2, postcode) if part)

    # WhatsApp needs international digits; keep the stored number as the display text.
    digits = re.sub(r"[\s()+-]", "", mobile or "")
    if re.fullmatch(r"[689][0-9]{7}", digits):
        digits = "65" + digits
    mobile_link = (
        types.RichTextUrl(text=_rich_text(mobile), url=f"https://wa.me/{digits}")
        if mobile and re.fullmatch(r"[1-9][0-9]{7,14}", digits) else None
    )
    home_link = (
        types.RichTextPhoneNumber(text=_rich_text(home_phone), phone_number=home_phone)
        if home_phone else None
    )
    contact: list[Field] = [
        ("Address", address, None),
        ("Mobile", mobile, mobile_link),
        ("Home phone", home_phone, home_link),
    ]
    # Don't label a shared family or head email as a separate spouse email.
    spouse_email = spouse_email if spouse_email not in (email, head_email) else None
    for label, value in (("Email", email), ("Spouse email", spouse_email)):
        if value:
            contact.append((label, value, types.RichTextEmailAddress(
                text=_rich_text(value), email_address=value,
            )))

    sections: list[tuple[str, list[Field]]] = [
        ("Contact & address", contact),
        ("Birthdays & anniversary", [
            _date_field("Head DOB", head_dob),
            _date_field("Spouse DOB", spouse_dob),
            _date_field("Anniversary", anniversary),
        ]),
        ("Membership & prayer group", [
            ("Prayer group", prayer_group, None),
            ("Electoral roll", "On the roll" if str(electoral_roll).lower() in ("true", "1") else "Not on the roll", None),
            ("Home parish", parish, None),
            _date_field("Membership date", joined),
            _related_families_field(related),
        ]),
    ]

    # Both lookups use blocking HTTP. Run them off the event loop and in parallel when possible.
    profile_map = None
    if postcode:
        photo, profile_map = await asyncio.gather(
            asyncio.to_thread(_family_photo, family_id),
            asyncio.to_thread(_family_map, str(postcode)),
        )
    else:
        photo = await asyncio.to_thread(_family_photo, family_id)

    # Keep the name and code together to avoid a separate block's vertical margin.
    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockParagraph(text=_rich_text([
            types.RichTextBold(text=_rich_text(title)),
            f"\n{subtitle}",
        ])),
    ]
    photo_block = types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo)) if photo else None
    if photo_block:
        blocks.append(photo_block)
    if any(value for _, value, _ in household):
        blocks.append(_household_block(household))
    for label, fields in sections:
        details = _paragraphs(fields)
        if fields is contact and profile_map:
            details.append(profile_map)
        if details:
            blocks.append(types.InputRichBlockDetails(summary=_rich_text(label), blocks=details, is_open=False))

    async def send_rich() -> None:
        # Rebuild from the current blocks so the retry can omit the rejected photo.
        await client.send_rich_message(chat_id, types.InputRichMessage(blocks=blocks))

    try:
        try:
            await send_rich()
        except PHOTO_ERRORS:
            if photo_block is None:
                raise
            logger.warning("Telegram rejected the family profile photo; retrying without it")
            blocks.remove(photo_block)
            await send_rich()
    except errors.RichMessageUnsupported:
        logger.warning("Telegram rejected rich formatting; sending family profile as text")
        # Reuse the same fields, but send database values without markup parsing.
        lines = [title, subtitle]
        for label, fields in [("Household", household), *sections]:
            values = [f"{key}: {value}" for key, value, _ in fields if value]
            if values:
                lines.extend(["", label, *values])
        await client.send_message(
            chat_id, "\n".join(lines), parse_mode=enums.ParseMode.DISABLED,
            link_preview_options=types.LinkPreviewOptions(is_disabled=True),
        )
    finally:
        if photo:
            photo.close()
