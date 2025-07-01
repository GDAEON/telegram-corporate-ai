from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import services.db as db
import constants.redis_models as rdb
import httpx
import services.sender_adapter as sa
import services.helper_functions as hf
import services.webhook_server as ws
from services.logging_setup import interaction_logger
from constants.prometheus_models import MESSAGE_COUNT, MESSAGE_TEXT_COUNT

router = APIRouter(tags=["Telegram"])

MESSAGES = {
    "all_set": {
        "en": "Thanks, you’re all set! 🎉",
        "ru": "Спасибо, все готово! 🎉",
    },
    "bot_has_owner": {
        "en": "Sorry, this bot already has an owner.",
        "ru": "Извините, у этого бота уже есть владелец.",
    },
    "logged_in": {"en": "You are logged in!", "ru": "Вы вошли!"},
    "share_contact": {
        "en": "Almost done! Please share your contact by tapping the button below.",
        "ru": "Почти готово! Пожалуйста, поделитесь своим контактом, нажав кнопку ниже.",
    },
    "share_phone_btn": {"en": "Share my phone", "ru": "Поделиться телефоном"},
    "bad_code": {
        "en": "Sorry, I didn’t recognize that code. Please try again.",
        "ru": "Извините, я не распознал этот код. Попробуйте ещё раз.",
    },
    "not_allowed": {
        "en": "Sorry, you are not allowed to use this bot!",
        "ru": "Извините, вы не можете использовать этого бота!",
    },
    "deactivated": {
        "en": "Sorry, seems like your account is deactivated, contact support",
        "ru": "Извините, ваша учетная запись отключена, обратитесь в поддержку",
    },
}

def tr(key: str, locale: str) -> str:
    return MESSAGES.get(key, {}).get(locale, MESSAGES[key]["en"])


async def _parse_update(update: dict, token: str):
    """Extract message data from the Telegram update."""
    message = update.get("message") or update.get("edited_message")
    callback = update.get("callback_query")
    if not message and not callback:
        raise ValueError("Unsupported update type")

    if callback:
        contact_id = callback["from"]["id"]
        text = callback.get("data", "")
        message = callback.get("message", {})
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                data={"callback_query_id": callback["id"]},
            )
    else:
        contact_id = message["from"]["id"]
        text = message.get("text", "")
    return message, contact_id, text


def _update_metrics(bot_id: int, text: str, contact_id: int):
    MESSAGE_COUNT.labels(direction="incoming", bot_id=str(bot_id)).inc()
    MESSAGE_TEXT_COUNT.labels(
        direction="incoming",
        bot_id=str(bot_id),
        text=text[:100],
    ).inc()
    interaction_logger.info(
        f"INCOMING bot_id={bot_id} user_id={contact_id} text={text}"
    )


async def _handle_contact(bot_id: int, token: str, contact_id: int, contact_info: dict, locale: str, message_id: int, participant_name: str):
    db.update_user(
        contact_id,
        contact_info.get("first_name"),
        contact_info.get("last_name"),
        contact_info.get("phone_number"),
    )
    if db.get_is_bot_owner(bot_id, contact_id):
        db.bot_set_verified(bot_id, True)
    await sa.send_message(
        token,
        contact_id,
        tr("all_set", locale),
        remove_keyboard=True,
        bot_id=bot_id,
    )

    project_restart_code = db.get_selected_project_code(bot_id, contact_id)
    if project_restart_code is None:
        db.set_main_as_selected(bot_id, contact_id)
        project_restart_code = db.get_selected_project_code(bot_id, contact_id)

    restart_request_body = sa._build_event_request(message_id, project_restart_code, contact_id, bot_id, participant_name)

    restart_response = await sa._forward_message(restart_request_body)

    if restart_response.status_code > 202:
        interaction_logger.error(f"Failed to restart sesstion: {restart_response.content}")
        return JSONResponse(content={"ok": False, "error": str(restart_response.content)}, status_code=200)
    
    projects = db.get_not_main_projects(bot_id, contact_id)
    commands = {"commands": []}
    for project in projects:
        commands["commands"].append({"command": project, "description": project})

    commands = hf.clean_commands(commands)

    set_command_response = await ws.set_bot_commands(token, commands)

    if set_command_response['status_code'] > 202:
        interaction_logger.error(f"Failed to set telegram commands: {set_command_response['body']}")
        return JSONResponse(content={"ok": False, "error": str(set_command_response['body'])}, status_code=200)

    return {"status": "ok"}


async def _handle_start(bot_id: int, token: str, contact_id: int, text: str, message: dict, locale: str):
    if not text.startswith("/start"):
        return None
    _, _, input_uuid = text.partition(" ")
    if not input_uuid:
        _, _, input_uuid = text.partition("=")
    input_uuid = input_uuid.strip()

    if input_uuid and db.compare_bot_auth_owner(bot_id, input_uuid):
        existing_owner = db.get_bot_owner_id(bot_id)
        if existing_owner and existing_owner != contact_id:
            await sa.send_message(
                token,
                contact_id,
                tr("bot_has_owner", locale),
                bot_id=bot_id,
            )
            return {"status": "ok"}

        if db.get_is_bot_owner(bot_id, contact_id) and db.owner_has_contact(bot_id, contact_id):
            db.bot_set_verified(bot_id, True)
            await sa.send_message(
                token,
                contact_id,
                tr("logged_in", locale),
                bot_id=bot_id,
            )
            return {"status": "ok"}

        contact_button = [[{"text": tr("share_phone_btn", locale), "request_contact": True}]]
        if not db.get_is_bot_owner(bot_id, contact_id):
            db.add_owner_user(bot_id, contact_id)
        await sa.send_message(
            token,
            contact_id,
            tr("share_contact", locale),
            reply_keyboard=contact_button,
            bot_id=bot_id,
        )
        return {"status": "ok"}

    if input_uuid and db.compare_bot_auth_pass(bot_id, input_uuid):
        if db.bot_has_user(bot_id, contact_id):
            await sa.send_message(
                token,
                contact_id,
                tr("logged_in", locale),
            )
            return {"status": "ok"}

        contact_button = [[{"text": tr("share_phone_btn", locale), "request_contact": True}]]
        db.add_user_to_a_bot(
            bot_id,
            contact_id,
            message["from"].get("first_name"),
            message["from"].get("last_name"),
            None,
        )

        db.add_user_to_all_projects(bot_id, contact_id)
        
        db.mark_pass_token_used(bot_id, input_uuid)
        await sa.send_message(
            token,
            contact_id,
            tr("share_contact", locale),
            reply_keyboard=contact_button,
            bot_id=bot_id,
        )

        projects = db.get_not_main_projects(bot_id, contact_id)
        commands = {"commands": []}
        for project in projects:
            commands["commands"].append({"command": project, "description": project})

        commands = hf.clean_commands(commands)

        await ws.set_bot_commands(token, commands)

        return {"status": "ok"}

    await sa.send_message(
        token,
        contact_id,
        tr("bad_code", locale),
        bot_id=bot_id,
    )
    return {"status": "ok"}


async def _check_user_status(bot_id: int, token: str, contact_id: int, user_status, locale: str):
    if user_status is None:
        await sa.send_message(
            token,
            contact_id,
            tr("not_allowed", locale),
            bot_id=bot_id,
        )
        return {"status": "ok"}
    if user_status is False:
        await sa.send_message(
            token,
            contact_id,
            tr("deactivated", locale),
            bot_id=bot_id,
        )
        return {"status": "ok"}
    return None


@router.post(
    '/webhook/{bot_id}',
    description='Handle incoming Telegram updates for the bot',
    tags=["Telegram"],
)
async def handle_webhook(bot_id: int, request: Request):
    """Process Telegram webhook updates and forward messages."""
    try:
        interaction_logger.info(f"Webhook call for bot_id={bot_id}")
        update = await request.json()

        token = db.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")

        locale = db.get_bot_locale(bot_id) or "en"

        try:
            message, contact_id, text = await _parse_update(update, token)
        except ValueError as e:
            return JSONResponse(content={"ok": False, "error": str(e)}, status_code=200)

        _update_metrics(bot_id, text, contact_id)

        user_info = message.get("from", {})
        participant_name = (
            user_info.get("username")
            or " ".join(
                part for part in [user_info.get("first_name"), user_info.get("last_name")] if part
            )
        )
        message_id = message.get("message_id")

        contact_info = message.get("contact")
        user_status = db.get_botuser_status(bot_id, contact_id)

        if contact_info and db.bot_has_user(bot_id, contact_id):
            return await _handle_contact(bot_id, token, contact_id, contact_info, locale, message_id, participant_name)

        start_resp = await _handle_start(bot_id, token, contact_id, text, message, locale)
        if start_resp:
            return start_resp

        status_resp = await _check_user_status(bot_id, token, contact_id, user_status, locale)
        if status_resp:
            return status_resp

        attachments, message_type = hf.extract_telegram_attachments(message, token)

        if db.no_project_selected(bot_id, contact_id):
            db.set_main_as_selected(bot_id, contact_id)
            project_restart_code = db.get_selected_project_code(bot_id, contact_id)
            project_restart_code += f"_{message_id}"
            restart_request_body = sa._build_event_request(
                message_id,
                project_restart_code,
                contact_id,
                bot_id,
                participant_name,
            )
            rdb.Message.set(
                bot_id,
                contact_id,
                message_id,
                text,
                participant_name,
                attachments,
                message_type,
            )
            restart_response = await sa._forward_message(restart_request_body)

            return {"status": "ok", "raw_response": restart_response.text}

        
        projects = db.get_not_main_projects(bot_id, contact_id)
        commands = {"commands": []}
        for project in projects:
            commands["commands"].append({"command": project, "description": project})

        commands = hf.clean_commands(commands)

        set_command_response = await ws.set_bot_commands(token, commands)

        if set_command_response["status_code"] > 202:
            interaction_logger.error(f"Failed to set telegram commands: {set_command_response['body']}")
            return JSONResponse(content={"ok": False, "error": str(set_command_response["body"])}, status_code=200)

        if text.startswith("/"):
            command_text = text[1:].split()[0]
            command_text = command_text.split("@")[0]
            project_match = db.find_project_by_command(bot_id, contact_id, command_text)
            if project_match:
                project_id, project_code = project_match
                db.set_project_selected(bot_id, project_id, contact_id)

                stop_request_body = sa._build_event_request(
                    message_id,
                    "stop",
                    contact_id,
                    bot_id,
                    participant_name,
                )
                stop_response = await sa._forward_message(stop_request_body)
                if stop_response.status_code > 202:
                    interaction_logger.error(
                        f"Failed to stop session: {stop_response.content}"
                    )
                    return JSONResponse(
                        content={"ok": False, "error": str(stop_response.content)},
                        status_code=200,
                    )

                restart_request_body = sa._build_event_request(
                    message_id,
                    project_code,
                    contact_id,
                    bot_id,
                    participant_name,
                )
                restart_response = await sa._forward_message(restart_request_body)
                if restart_response.status_code > 202:
                    interaction_logger.error(
                        f"Failed to restart sesstion: {restart_response.content}"
                    )
                    return JSONResponse(
                        content={"ok": False, "error": str(restart_response.content)},
                        status_code=200,
                    )
                return {"status": "ok"}


        request_body = sa._build_event_request(
            message_id,
            text,
            contact_id,
            bot_id,
            participant_name,
            attachments,
            message_type,
        )

        response = await sa._forward_message(request_body)

        if response.status_code >= 400:
            return JSONResponse(content={"ok": False, "error": response.text}, status_code=200)

        if response.content:
            try:
                return response.json()
            except Exception:
                return {"status": "ok", "raw_response": response.text}
        else:
            return {"status": "ok", "message": "No content"}

    except Exception as e:
        interaction_logger.error(f"Webhook handling failed for bot_id={bot_id}: {e}")
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=200)
