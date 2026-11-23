"""Conquest maps (#157): tile coordinates, grouping, the three views, the crop, the tile cache, the text fallback."""
import asyncio
import os
import time
from datetime import timedelta

import h3
import httpx
import pytest
from PIL import Image

from caccometro import commands, maps
from caccometro.conquest import cell_of
from caccometro.database import User
from conftest import REAL_CACHED_TILE, make_context, make_update, uid
from test_conquest import MILAN, ROME, T0, poop_and_conquer

PARIS, NEW_YORK, FIJI = (48.8566, 2.3522), (40.7128, -74.006), (-17.7, 179.9)


@pytest.fixture
def tiles(monkeypatch):
    """Map tiles are blank images: the maps get drawn without network."""
    monkeypatch.setattr(maps, "cached_tile", lambda *args: Image.new("RGB", (maps.TILE_SIZE, maps.TILE_SIZE), "white"))


@pytest.fixture
def drawn(monkeypatch):
    """Record what draw() is asked to draw instead of drawing it."""
    calls = []
    monkeypatch.setattr(maps, "draw", lambda *args, **kwargs: calls.append((args, kwargs)) or b"png")
    return calls


USERS = {1: User(1, "giulia", "Giulia"), 2: User(2, None, "Marco")}


def test_tile_coordinates_follow_web_mercator():
    assert maps.tile_xy(0, 0, 1) == pytest.approx((1, 1))
    assert maps.tile_xy(0, -180, 3)[0] == 0
    assert maps.tile_xy(maps.MAX_LAT, 0, 2)[1] == pytest.approx(0, abs=1e-3)
    assert maps.tile_xy(90, 0, 2) == maps.tile_xy(maps.MAX_LAT, 0, 2)  # the poles do not break the formula
    x, y = maps.tile_xy(*MILAN, 11)
    assert (int(x), int(y)) == (1076, 732)  # the OpenStreetMap tile of Milan centre


def test_a_hexagon_across_180_degrees_stays_in_one_piece():
    xs = [x for x, _ in maps.outline(h3.latlng_to_cell(*FIJI, 1), 2)]
    assert max(xs) - min(xs) < 1  # a hexagon 840 km wide, not stretched across the whole map


def test_a_large_hexagon_goes_to_the_member_with_most_tiles_inside_and_on_a_tie_to_the_latest():
    milan, near, rome = cell_of(*MILAN), cell_of(45.50, 9.25), cell_of(*ROME)
    assert maps.grouped(maps.owners([(1, milan), (1, near), (2, rome)]), 1) == {
        h3.cell_to_parent(milan, 1): 1, h3.cell_to_parent(rome, 1): 2}
    parent = h3.cell_to_parent(milan, 4)
    assert maps.grouped(maps.owners([(1, milan), (2, near)]), 4) == {parent: 2}
    assert maps.grouped(maps.owners([(2, near), (1, milan)]), 4) == {parent: 1}
    assert maps.grouped(maps.owners([(1, milan), (2, near), (1, near)]), 4) == {parent: 1}  # 1 took near back


def test_each_view_draws_its_own_resolution_and_outlines_the_latest_conquest(drawn):
    history = [(1, cell_of(*MILAN)), (2, cell_of(*ROME))]
    for view in (maps.zoom_map, maps.region_map, maps.country_map, maps.world_map):
        view(history, USERS)
    assert len(drawn) == 4
    for (args, kwargs), res, z in zip(drawn, (6, 5, 4, 1), (11, 8, 6, 2)):
        title, level, box, hexagons, colors, legend, latest = args
        assert level == z and {h3.get_resolution(cell) for cell in hexagons} == {res}
        assert latest == h3.cell_to_parent(cell_of(*ROME), res)
        assert legend == [(1, "@giulia: 1"), (2, "Marco: 1")]
    assert drawn[0][1]["grid"] and cell_of(*MILAN) not in drawn[0][0][3]  # the zoom shows only the tiles around Rome


def test_the_overviews_show_lombardy_italy_and_the_world(drawn):
    maps.region_map([(1, cell_of(*MILAN))], USERS)
    maps.country_map([(1, cell_of(*MILAN))], USERS)
    maps.world_map([(1, cell_of(*MILAN))], USERS)
    (lombardy, z_l), (italy, z_i), (world, z_w) = [(args[2], args[1]) for args, _ in drawn]

    def inside(box, z, point):
        x, y = maps.tile_xy(*point, z)
        return box[0] < x < box[2] and box[1] < y < box[3]

    assert inside(lombardy, z_l, MILAN) and not inside(lombardy, z_l, (45.07, 7.69))  # Milan, not Turin
    assert all(inside(italy, z_i, p) for p in (MILAN, (37.08, 15.29), (39.22, 9.12), (40.35, 18.17), (46.5, 11.35)))
    assert world[0] == 0 and world[2] == 2 ** z_w and inside(world, z_w, (-33.87, 151.21))
    grids = [kwargs["grid"] for _, kwargs in drawn]
    assert len(grids[2]) == 842  # every resolution 1 cell of the world
    assert cell_of(*MILAN) and h3.cell_to_parent(cell_of(*MILAN), 5) in grids[0] and h3.cell_to_parent(cell_of(*MILAN), 4) in grids[1]


def test_the_maps_are_drawn(tiles):
    history = [(1, cell_of(*MILAN)), (2, cell_of(*FIJI)), (1, cell_of(*NEW_YORK))]
    for view in (maps.zoom_map, maps.region_map, maps.country_map, maps.world_map):
        assert view(history, USERS).startswith(b"\xff\xd8")  # JPEG


# the tile cache

def client_answering(*statuses):
    """httpx client whose answers have the given statuses in turn; it counts its requests."""
    answers = iter(statuses)
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(next(answers), content=png())))
    client.requests = lambda: len(statuses) - len(list(answers))
    return client


def png():
    out = __import__("io").BytesIO()
    Image.new("RGB", (maps.TILE_SIZE, maps.TILE_SIZE), "red").save(out, "PNG")
    return out.getvalue()


def test_a_tile_is_fetched_once_then_read_from_the_cache():
    calls = []
    client = httpx.Client(transport=httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200, content=png())))
    for _ in range(2):
        assert REAL_CACHED_TILE(5, 1, 2, client, time.time() + 10).size == (256, 256)
    assert len(calls) == 1 and calls[0].url.path == "/5/1/2.png"


def test_a_503_is_tried_again(monkeypatch):
    monkeypatch.setattr(maps.time, "sleep", lambda seconds: None)
    calls = []
    answers = iter((503, 200))
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: calls.append(request) or httpx.Response(next(answers), content=png())))
    REAL_CACHED_TILE(5, 1, 2, client, time.time() + 10)
    assert len(calls) == 2


def test_a_stale_tile_is_used_when_the_server_fails_and_a_missing_one_raises(monkeypatch):
    monkeypatch.setattr(maps.time, "sleep", lambda seconds: None)
    failing = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    with pytest.raises(httpx.HTTPError):
        REAL_CACHED_TILE(5, 1, 2, failing, time.time() + 10)
    maps.CACHE_DIR.mkdir()
    stale = maps.CACHE_DIR / "5_1_2.png"
    stale.write_bytes(png())
    os.utime(stale, (0, 0))
    assert REAL_CACHED_TILE(5, 1, 2, failing, time.time() + 10).size == (256, 256)


def test_the_cache_keeps_the_newest_tiles(monkeypatch):
    monkeypatch.setattr(maps, "CACHE_MAX_FILES", 2)
    maps.CACHE_DIR.mkdir()
    for i in range(4):
        (maps.CACHE_DIR / f"1_{i}_0.png").write_bytes(b"x")
        os.utime(maps.CACHE_DIR / f"1_{i}_0.png", (i, i))
    maps.trim_cache()
    assert sorted(f.name for f in maps.CACHE_DIR.iterdir()) == ["1_2_0.png", "1_3_0.png"]


# the replies

def test_without_tiles_the_conquest_reply_goes_out_as_text(chat_id):
    assert poop_and_conquer("mario", MILAN).startswith("🚩")  # conftest: no network, text only


def test_with_tiles_the_conquest_reply_is_a_photo_with_the_text_as_caption(chat_id, tiles):
    from caccometro import messages
    from test_conquest import send
    send("mario", "💩")
    upd = make_update(username="mario", user_id=uid("mario"), location=MILAN, date=T0 + timedelta(minutes=1))
    asyncio.run(messages.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()
    assert upd.message.reply_photo.call_args.kwargs["caption"].startswith("🚩")


def test_conquests_sends_the_region_country_and_world_maps_as_an_album(chat_id, monkeypatch):
    poop_and_conquer("mario", MILAN)
    monkeypatch.setattr(maps, "cached_tile", lambda *args: Image.new("RGB", (maps.TILE_SIZE, maps.TILE_SIZE)))
    upd = make_update(text="/conquests", username="mario")
    asyncio.run(commands.conquests_command(upd, make_context()))
    album = upd.message.reply_media_group.call_args.args[0]
    assert len(album) == 3 and album[0].caption.startswith("🗺️")


def test_a_poop_reminds_to_send_a_location():
    from test_conquest import send
    assert send("mario", "💩").endswith("📍 Manda la posizione entro 15 minuti per conquistare la zona!")


def test_with_a_person_each_hexagon_is_lighter_the_more_tiles_were_lost_inside(drawn):
    near = (45.50, 9.25)  # same Italy hexagon as Milan, another tile
    history = [(1, cell_of(*MILAN)), (1, cell_of(*near)), (1, cell_of(*ROME)), (2, cell_of(*ROME)), (2, cell_of(*near))]
    maps.country_map(history, USERS, 1)
    (title, z, box, hexagons, colors, legend, latest), kwargs = drawn[0]
    milan4, rome4 = h3.cell_to_parent(cell_of(*MILAN), 4), h3.cell_to_parent(cell_of(*ROME), 4)
    assert hexagons == {}  # nobody else on the map
    assert kwargs["shares"] == (1, {milan4: 0.5, rome4: 0.0}, 2)  # Milan: 1 of 2 still held; Rome: taken by Marco
    assert legend == [(1, "@giulia: 1")] and latest is None


def test_a_person_who_lost_every_tile_still_gets_a_legend(drawn):
    history = [(1, cell_of(*ROME)), (2, cell_of(*ROME))]
    maps.world_map(history, USERS, 1)
    (args, kwargs), = drawn
    assert args[5] == [(1, "@giulia: 0")] and list(kwargs["shares"][1].values()) == [0.0] and kwargs["shares"][2] == 1


def test_conquests_of_a_person_draw_only_that_person_and_none_for_someone_without_tiles(chat_id, monkeypatch):
    poop_and_conquer("giulia", MILAN)
    poop_and_conquer("marco", ROME, at=T0 + timedelta(minutes=1))
    drawn = []
    monkeypatch.setattr(maps, "draw", lambda *args, **kwargs: drawn.append((args, kwargs)) or b"png")
    upd = make_update(text="/conquiste io", username="giulia", user_id=uid("giulia"))
    asyncio.run(commands.conquests_command(upd, make_context("io")))
    assert len(drawn) == 4 and all(kwargs["shares"][0] == uid("giulia") for _, kwargs in drawn)  # + her tiles map
    drawn.clear()
    upd = make_update(text="/conquiste io", username="anna", user_id=uid("anna"))
    asyncio.run(commands.conquests_command(upd, make_context("io")))
    assert drawn == []


def test_the_person_maps_are_drawn(tiles):
    history = [(1, cell_of(*MILAN)), (2, cell_of(*ROME)), (1, cell_of(*ROME))]
    assert maps.region_map(history, USERS, 2)[:2] == b"\xff\xd8"  # a JPEG


def test_the_tiles_map_of_a_person_shows_held_tiles_full_and_lost_ones_empty_around_the_latest(drawn):
    near = (45.50, 9.25)
    history = [(1, cell_of(*MILAN)), (1, cell_of(*near)), (2, cell_of(*near)), (2, cell_of(*ROME)), (1, cell_of(*PARIS))]
    maps.person_zoom_map(history, USERS, 1)
    (title, z, box, hexagons, colors, legend, latest), kwargs = drawn[0]
    assert title == "Zona di @giulia" and legend == [(1, "@giulia: 2")]
    assert kwargs["shares"] == (1, {cell_of(*MILAN): 1.0, cell_of(*near): 0.0, cell_of(*PARIS): 1.0}, 1)
    x, y = maps.tile_xy(*PARIS, z)
    assert box[0] < x < box[2] and box[1] < y < box[3]  # around the latest conquest of the person
    assert cell_of(*PARIS) not in kwargs["grid"]
