"""The command replies carry what the Mini App shows (#201): who leads, the place of the sender, records in the group."""
import asyncio

from caccometro import cmd_leaderboards, cmd_records
from conftest import make_context, make_update, uid


def ask(command, sender, *args):
    upd = make_update(username=sender, user_id=uid(sender))
    asyncio.run(command(upd, make_context(*args)))
    return upd.message


def test_leaderboard_says_who_leads_and_where_the_sender_is(seed):
    seed({"anna": {"2024-03-01": 5}, "luca": {"2024-03-01": 3}, "chiara": {"2024-03-01": 1}})  # made-up names
    caption = ask(cmd_leaderboards.leaderboard_month_command, "chiara", "03-2024").reply_photo.call_args.kwargs["caption"]
    assert "@anna è in testa con 5 💩, 2 più di @luca." in caption
    assert "@chiara: 3° con 1 💩, a 2 da @luca." in caption


def test_statistics_say_who_leads_and_leave_out_the_regularity_without_data(seed):
    seed({"anna": {"2024-03-01": 5}, "luca": {"2024-03-01": 3}})
    caption = ask(cmd_leaderboards.stats_month_command, "luca", "03-2024").reply_photo.call_args.kwargs["caption"]
    assert "@anna è in testa con 0.16 al giorno" in caption
    assert "come vai" not in caption   # too few days for the label


def test_a_personal_record_shows_its_place_in_the_group(seed):
    seed({"anna": {"2024-03-01": 5}, "luca": {"2024-03-01": 3}, "chiara": {"2024-03-01": 1}})
    text = ask(cmd_records.records_command, "luca", "io").reply_text.call_args[0][0]
    assert "(2° su 3)" in text
