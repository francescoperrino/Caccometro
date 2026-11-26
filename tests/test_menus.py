"""The menu of a chat follows the language chosen with /language (#152)."""
import asyncio
import logging
import re

import pytest
from telegram import BotCommandScopeChat, BotCommandScopeChatAdministrators
from telegram.error import NetworkError

from caccometro import cmd_settings, database, menus, messages
from conftest import make_context, make_update


def language(*args, member_status="administrator", chat_type="group"):
    """Send /language and return (update, context)."""
    upd, ctx = make_update(chat_type=chat_type), make_context(*args, member_status=member_status)
    asyncio.run(cmd_settings.language_command(upd, ctx))
    return upd, ctx


def menus_set(ctx):
    """{scope type: [command names]} of every set_my_commands call."""
    return {call.kwargs["scope"].type: [name for name, _ in call.args[0]] for call in ctx.bot.set_my_commands.call_args_list}


def test_in_a_group_the_users_and_the_admins_get_the_menu_in_the_new_language(chat_id):
    _, ctx = language("en")
    assert menus_set(ctx) == {"chat": [name for name, _ in menus.menu("en")],
                              "chat_administrators": [name for name, _ in menus.menu("en", admins=True)]}
    for call in ctx.bot.set_my_commands.call_args_list:
        assert call.kwargs["scope"].chat_id == chat_id
        assert "language_code" not in call.kwargs   # one menu for every app language
    assert "link_history" in menus_set(ctx)["chat_administrators"]
    assert "link_history" not in menus_set(ctx)["chat"]


def test_choosing_italian_sets_the_italian_menu():
    _, ctx = language("it")
    assert menus_set(ctx)["chat"][1] == "classifica_mese"


def test_a_private_chat_gets_the_chat_menu_only():
    _, ctx = language("en", chat_type="private")
    assert list(menus_set(ctx)) == ["chat"]


@pytest.mark.parametrize("args, member_status", [(("en",), "member"), ((), "administrator")])
def test_the_menu_does_not_change_without_a_new_language(args, member_status):
    _, ctx = language(*args, member_status=member_status)
    ctx.bot.set_my_commands.assert_not_called()


def test_a_failed_menu_keeps_the_language_and_the_reply(chat_id, caplog):
    upd, ctx = make_update(), make_context("en", member_status="administrator")
    ctx.bot.set_my_commands.side_effect = NetworkError("httpx.ProxyError: 503 Service Unavailable")
    with caplog.at_level(logging.WARNING, logger="caccometro"):
        asyncio.run(cmd_settings.language_command(upd, ctx))
    assert database.get_language(chat_id) == "en"
    upd.message.reply_text.assert_called_once_with("From now on I speak English 🇬🇧")
    assert "Could not set the menu" in caplog.text


def migrate(language=None, old=-100, new=-1001):
    if language:
        database.set_language(old, language)
    upd, ctx = make_update(chat_id=new), make_context()
    upd.message.migrate_from_chat_id = old
    asyncio.run(messages.handle_migration(upd, ctx))
    return ctx


def test_a_new_supergroup_gets_the_menu_of_its_language_again():
    ctx = migrate("en")
    scopes = [call.kwargs["scope"] for call in ctx.bot.set_my_commands.call_args_list]
    assert scopes == [BotCommandScopeChat(-1001), BotCommandScopeChatAdministrators(-1001)]


def test_a_new_supergroup_without_a_chosen_language_keeps_the_global_menus():
    migrate().bot.set_my_commands.assert_not_called()


@pytest.mark.parametrize("language", ["it", "en"])
def test_the_menus_follow_the_telegram_rules(language):
    commands_ = menus.menu(language, admins=True)
    assert len(commands_) <= 100
    for name, description in commands_:
        assert re.fullmatch(r"[a-z0-9_]{1,32}", name), name
        assert 1 <= len(description) <= 256, name
