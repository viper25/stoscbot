import asyncio
import logging
import re
from io import BytesIO
from typing import cast

from pyrogram import Client, enums, errors, types
from requests import RequestException

from stoscbots.util import utils

logger = logging.getLogger("Handler.Main")

type Field = tuple[str, str | None, types.RichText | None]
PHOTO_ERRORS = (
    errors.MediaEmpty,
    errors.PhotoInvalid,
    errors.PhotoInvalidDimensions,
    errors.PhotoExtInvalid,
    errors.PhotoSaveFileInvalid,
    errors.ChatSendPhotosForbidden,
)


def _rich_text(value: str | list[str | types.RichText]) -> types.RichText:
    # Kurigram documents and serializes strings and lists as RichText.
    return cast(types.RichText, value)


def _paragraphs(fields: list[Field]) -> list[types.InputRichBlock]:
    return [
        _paragraph(label, value, link) for label, value, link in fields if value
    ]


def _paragraph(label: str, value: str, link: types.RichText | None) -> types.InputRichBlockParagraph:
    return types.InputRichBlockParagraph(
        text=_rich_text([types.RichTextBold(text=_rich_text(f"{label}: ")), link or value])
    )


def _family_photo(family_id: int) -> BytesIO | None:
    try:
        response = utils.fetch_crm_profile_photo(f"family/{family_id}")
        if response.status_code in (204, 404):
            return None
        response.raise_for_status()
    except RequestException as exc:
        logger.warning("Could not fetch family profile photo: %s", type(exc).__name__)
        return None

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


def _date(value: object) -> str:
    return utils.format_iso_date_readable(str(value)) if value else ""


async def send_family_profile(client: Client, chat_id: int, row: tuple) -> None:
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
    spouse_email = spouse_email if spouse_email not in (email, head_email) else None
    for label, value in (("Email", email), ("Spouse email", spouse_email)):
        if value:
            contact.append((label, value, types.RichTextEmailAddress(
                text=_rich_text(value), email_address=value,
            )))

    sections: list[tuple[str, list[Field]]] = [
        ("Contact & address", contact),
        ("Birthdays & anniversary", [
            ("Head DOB", _date(head_dob), None),
            ("Spouse DOB", _date(spouse_dob), None),
            ("Anniversary", _date(anniversary), None),
        ]),
        ("Membership & prayer group", [
            ("Prayer group", prayer_group, None),
            ("Electoral roll", "On the roll" if str(electoral_roll).lower() in ("true", "1") else "Not on the roll", None),
            ("Home parish", parish, None),
            ("Membership date", _date(joined), None),
            ("Related families", related, None),
        ]),
    ]

    profile_map = None
    if postcode:
        photo, profile_map = await asyncio.gather(
            asyncio.to_thread(_family_photo, family_id),
            asyncio.to_thread(_family_map, str(postcode)),
        )
    else:
        photo = await asyncio.to_thread(_family_photo, family_id)

    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=_rich_text(title), size=2),
        types.InputRichBlockParagraph(text=_rich_text(subtitle)),
    ]
    photo_block = types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo)) if photo else None
    if photo_block:
        blocks.append(photo_block)
    household_blocks = _paragraphs(household)
    if household_blocks:
        blocks.append(types.InputRichBlockSectionHeading(text=_rich_text("Household"), size=3))
        blocks.extend(household_blocks)
    blocks.append(types.InputRichBlockDivider())
    for label, fields in sections:
        details = _paragraphs(fields)
        if fields is contact and profile_map:
            details.append(profile_map)
        if details:
            blocks.append(types.InputRichBlockDetails(summary=_rich_text(label), blocks=details, is_open=False))

    async def send_rich() -> None:
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
