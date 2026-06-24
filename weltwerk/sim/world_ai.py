# SPDX-License-Identifier: AGPL-3.0-only
"""
world_ai.py — Phase 9: the combat-AI AUTHORITY. Deterministic, engine-independent, no rendering.

The FPS prototype is a projection; this is the authority it mirrors. Everything a bot "decides" is a pure
function of grid + perception, so it is testable and reproducible. The renderer may disappear and the AI
still exists here. `observation ≠ authority`.

Four authority pieces, each pure and deterministic:

  1. Grid + line_of_sight  — bots see by RAYCAST over a grid; a wall blocks sight. No omniscience: if a
                             blocked cell lies between bot and player, the bot CANNOT see (and so cannot fire).
  2. astar                 — bots PATH AROUND obstacles (4-connected grid A*, deterministic tie-break).
                             A bot never moves through a wall.
  3. transition            — an EXPLICIT, table-driven state machine over IDLE/PATROL/INVESTIGATE/
                             CHASE/ATTACK/SEARCH. One small handler per state; no giant if-blob.
  4. squad_broadcast       — bots share information: a bot that sees the player alerts nearby allies, who
                             escalate (INVESTIGATE / CHASE).

Combat death is NOT handled here as a special case — when a bot or entity dies, the projection routes it
through Weltwerk's event system (world_sim.apply_event("destroy", id)), so consequences propagate by
CAUSALITY, not script. test_world_ai verifies that integration end-to-end.

NOT claimed: pathing optimality beyond 4-connected A*, perception beyond grid LOS, MMO/networking/UE5.
This is the smallest honest AI substrate that hosts real gameplay.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

# --- bot states (explicit; the transition table is keyed on these) ------------------------------
IDLE, PATROL, INVESTIGATE, CHASE, ATTACK, SEARCH = "IDLE", "PATROL", "INVESTIGATE", "CHASE", "ATTACK", "SEARCH"
SUPPRESS, RETREAT, RELOAD = "SUPPRESS", "RETREAT", "RELOAD"
STATES = (IDLE, PATROL, INVESTIGATE, CHASE, ATTACK, SEARCH, SUPPRESS, RETREAT, RELOAD)

DEFAULT_VIEW_RANGE = 14.0
DEFAULT_ATTACK_RANGE = 9.0
SEARCH_LIMIT = 12          # ticks a bot searches a last-known position before giving up → PATROL
ALERT_RADIUS = 10.0        # squad: allies within this distance of the spotter are alerted
LOW_HP_FRAC = 0.35         # below this fraction of max health a bot prefers to RETREAT
CONTACT_MEMORY = 8         # ticks the bot keeps acting on a recent sighting (SUPPRESS the last-known cell)
REACTION_MIN_MS, REACTION_MAX_MS = 150, 350   # simulated human reaction delay before first engagement
BURST_ROUNDS = 3           # bots fire in bursts, not laser-perfect continuous spam


class Grid:
    """A 2-D occupancy grid. blocked = set of (x,y) cells a ray/agent cannot pass. The world's solid
    geometry (entity footprints) projects DOWN into this grid; the grid is the AI's model of the world,
    a stated MODEL BOUNDARY (Arbitrary-Boundary Law) — not the continuous world itself."""
    def __init__(self, w: int, h: int, blocked=None):
        self.w, self.h = w, h
        self.blocked = set(blocked or ())

    def in_bounds(self, x, y) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def passable(self, x, y) -> bool:
        return self.in_bounds(x, y) and (x, y) not in self.blocked


def bresenham(a, b):
    """Integer line cells from a to b inclusive (deterministic)."""
    (x0, y0), (x1, y1) = a, b
    cells = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    x, y = x0, y0
    while True:
        cells.append((x, y))
        if (x, y) == (x1, y1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x += sx
        if e2 < dx:
            err += dx; y += sy
    return cells


def line_of_sight(grid: Grid, a, b) -> bool:
    """True iff no BLOCKED cell lies strictly between a and b. Endpoints excluded (the shooter and the
    target stand where they stand). This is the no-cheating rule: a wall between them ⇒ no sight."""
    cells = bresenham(a, b)
    for c in cells[1:-1] if len(cells) > 2 else []:
        if c in grid.blocked:
            return False
    return True


def visible(grid: Grid, a, b, view_range: float = DEFAULT_VIEW_RANGE) -> bool:
    """Bots see only within view_range AND with clear line of sight. No omniscience."""
    if math.dist(a, b) > view_range:
        return False
    return line_of_sight(grid, a, b)


def astar(grid: Grid, start, goal):
    """4-connected grid A* with Manhattan heuristic. Deterministic (counter tie-break, fixed neighbour
    order). Returns the path [start..goal] or None. A bot NEVER routes through a blocked cell."""
    if start == goal:
        return [start]
    if not grid.passable(*goal):
        return None
    NEIGH = ((1, 0), (-1, 0), (0, 1), (0, -1))
    def h(p):
        return abs(p[0] - goal[0]) + abs(p[1] - goal[1])
    counter = 0
    open_heap = [(h(start), 0, counter, start)]
    came, gscore = {start: None}, {start: 0}
    while open_heap:
        _f, g, _c, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = [cur]
            while came[path[-1]] is not None:
                path.append(came[path[-1]])
            return path[::-1]
        for dx, dy in NEIGH:
            nxt = (cur[0] + dx, cur[1] + dy)
            if not grid.passable(*nxt):
                continue
            ng = g + 1
            if ng < gscore.get(nxt, 1 << 30):
                gscore[nxt] = ng
                came[nxt] = cur
                counter += 1
                heapq.heappush(open_heap, (ng + h(nxt), ng, counter, nxt))
    return None


@dataclass
class Percept:
    """Everything a bot's transition is allowed to depend on — built by perceive()."""
    can_see_player: bool = False
    in_range: bool = False
    heard_alert: bool = False
    reached_target: bool = False
    search_timed_out: bool = False
    low_hp: bool = False             # health below LOW_HP_FRAC ⇒ prefer to retreat
    out_of_ammo: bool = False        # magazine empty ⇒ must reload
    recent_contact: bool = False     # saw the player within CONTACT_MEMORY ticks ⇒ may suppress
    reached_cover: bool = False      # standing on the chosen cover cell
    reloading_done: bool = True      # reload timer elapsed


# --- the state machine: one small handler per state (explicit, not a blob) -----------------------
def _from_idle(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    if p.heard_alert: return INVESTIGATE
    return PATROL


def _from_patrol(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    if p.heard_alert: return INVESTIGATE
    return PATROL


def _from_investigate(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    if p.reached_target: return SEARCH
    return INVESTIGATE


def _engage(p):
    """Shared combat priority: reload if empty, retreat if hurt, else attack/chase by range."""
    if p.out_of_ammo: return RELOAD
    if p.low_hp: return RETREAT
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    return None


def _from_chase(p):
    e = _engage(p)
    if e: return e
    return SUPPRESS if p.recent_contact else SEARCH   # lost sight: pin last-known, else search


def _from_attack(p):
    e = _engage(p)
    if e: return e
    return SUPPRESS if p.recent_contact else SEARCH    # _engage returns None only when sight lost


def _from_suppress(p):
    e = _engage(p)
    if e: return e
    return SUPPRESS if p.recent_contact else SEARCH    # suppress fire until contact memory expires


def _from_retreat(p):
    if p.low_hp:                                       # still hurt → keep falling back to cover
        if p.out_of_ammo and p.reached_cover: return RELOAD
        return RETREAT
    if p.can_see_player: return ATTACK if p.in_range else CHASE   # recovered → re-engage
    return SEARCH if p.recent_contact else PATROL


def _from_reload(p):
    if not p.reloading_done: return RELOAD             # still reloading
    if p.low_hp: return RETREAT
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    return SUPPRESS if p.recent_contact else SEARCH


def _from_search(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    if p.search_timed_out: return PATROL
    return SEARCH


TRANSITIONS = {
    IDLE: _from_idle, PATROL: _from_patrol, INVESTIGATE: _from_investigate,
    CHASE: _from_chase, ATTACK: _from_attack, SEARCH: _from_search,
    SUPPRESS: _from_suppress, RETREAT: _from_retreat, RELOAD: _from_reload,
}


def transition(state: str, p: Percept) -> str:
    """Pure state transition. state × percept → next state. Deterministic and total over STATES."""
    return TRANSITIONS[state](p)


@dataclass
class Bot:
    id: str
    pos: tuple                      # grid cell (x, y)
    team: str = "red"
    state: str = PATROL
    target: tuple = None            # current goal cell (patrol point / last-known player / search cell)
    path: list = field(default_factory=list)
    alert: tuple = None             # last-known player cell heard from a squadmate (None = no alert)
    search_ticks: int = 0
    health: int = 100
    max_health: int = 100
    alive: bool = True
    # combat memory + state
    ammo: int = 30
    mag: int = 30
    reloading: int = 0              # ticks remaining on a reload
    last_seen: tuple = None         # last cell the player was directly seen at (bot memory)
    last_damage_from: str = ""      # id/direction of the last damage source (bot memory)
    time_since_contact: int = 999   # ticks since the player was last seen (bot memory)
    cover: tuple = None             # chosen cover cell


def perceive(grid: Grid, bot: Bot, player_cell, view_range=DEFAULT_VIEW_RANGE,
             attack_range=DEFAULT_ATTACK_RANGE) -> Percept:
    """Build a bot's percept from the world. The ONLY way a bot learns about the player is sight (range +
    LOS) or a squad alert — never direct access to player state."""
    see = visible(grid, bot.pos, player_cell, view_range)
    rng = see and math.dist(bot.pos, player_cell) <= attack_range
    return Percept(
        can_see_player=see,
        in_range=rng,
        heard_alert=bot.alert is not None,
        reached_target=bot.target is not None and bot.pos == bot.target,
        search_timed_out=bot.search_ticks >= SEARCH_LIMIT,
        low_hp=bot.health <= LOW_HP_FRAC * max(1, bot.max_health),
        out_of_ammo=bot.ammo <= 0,
        recent_contact=bot.time_since_contact <= CONTACT_MEMORY,
        reached_cover=bot.cover is not None and bot.pos == bot.cover,
        reloading_done=bot.reloading <= 0,
    )


def hit_chance(dist, moving=False, suppressed=False, low_hp=False) -> float:
    """Deterministic accuracy MODEL (the authority defines it; the projection rolls against it). Accuracy
    falls with distance, while moving, while suppressed, and at low health. Pure; clamped to [0.05, 0.95]."""
    acc = 0.9
    acc -= 0.02 * max(0.0, dist - 4.0)        # distance falloff beyond a comfort radius
    if moving:     acc -= 0.25
    if suppressed: acc -= 0.35
    if low_hp:     acc -= 0.15
    return max(0.05, min(0.95, round(acc, 4)))


def reaction_delay(seed: int) -> int:
    """Simulated human reaction delay in ms, deterministic per seed, in [REACTION_MIN_MS, REACTION_MAX_MS].
    A bot does not engage the instant the player appears — it reacts after this delay."""
    span = REACTION_MAX_MS - REACTION_MIN_MS
    return REACTION_MIN_MS + (abs(hash(("react", seed))) % (span + 1))


def burst_pattern(rounds: int = BURST_ROUNDS, gap: float = 0.08, cooldown: float = 0.55) -> dict:
    """Bots fire in bursts, not continuous laser spam. Returns the burst shape (rounds > 1)."""
    return {"rounds": max(2, rounds), "gap": gap, "cooldown": cooldown}


def find_cover(grid: Grid, bot_cell, player_cell, search: int = 3):
    """Lightweight cover reasoning (not a navmesh): the nearest passable cell that BREAKS line of sight to
    the player. Returns that cell, or bot_cell if none is found nearby. Pure + deterministic."""
    best = None
    for r in range(1, search + 1):
        cands = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                c = (bot_cell[0] + dx, bot_cell[1] + dy)
                if grid.passable(*c) and not line_of_sight(grid, c, player_cell):
                    cands.append((abs(dx) + abs(dy), c))
        if cands:
            best = min(cands)[1]
            break
    return best if best is not None else bot_cell


def squad_broadcast(bots, spotter: Bot, player_cell, radius: float = ALERT_RADIUS):
    """The spotter shares the player's position with nearby allies (same team). Alerted allies record the
    last-known cell so their next perceive() reports heard_alert. Returns the ids alerted (deterministic)."""
    alerted = []
    for b in bots:
        if b is spotter or not b.alive or b.team != spotter.team:
            continue
        if math.dist(b.pos, spotter.pos) <= radius:
            b.alert = tuple(player_cell)
            alerted.append(b.id)
    return sorted(alerted)


def plan(grid: Grid, bot: Bot, player_cell) -> list:
    """Choose the bot's goal cell from its state and path to it (A* around walls). Pure given inputs.
    CHASE heads for the player; ATTACK closes only if not already in range; RETREAT/RELOAD head for cover;
    SUPPRESS holds position; INVESTIGATE/SEARCH head for the last-known (alert/target) cell."""
    if bot.state == CHASE:
        goal = tuple(player_cell)
    elif bot.state == ATTACK:
        goal = bot.pos if bot.pos == tuple(bot.pos) and math.dist(bot.pos, player_cell) <= DEFAULT_ATTACK_RANGE else tuple(player_cell)
    elif bot.state in (RETREAT, RELOAD):
        goal = bot.cover or bot.pos
    elif bot.state == SUPPRESS:
        goal = bot.pos                          # hold and fire at the last-known cell
    elif bot.state == INVESTIGATE and bot.alert is not None:
        goal = bot.alert
    elif bot.state == SEARCH and bot.target is not None:
        goal = bot.target
    else:
        goal = bot.target or bot.pos
    path = astar(grid, bot.pos, goal)
    return path or [bot.pos]


def step_bot(grid: Grid, bot: Bot, player_cell, view_range=DEFAULT_VIEW_RANGE,
             attack_range=DEFAULT_ATTACK_RANGE) -> dict:
    """Advance one bot by one tick: perceive → transition → (re)plan → record. Returns a debug record
    (state, percept, path) the projection can display in the AI overlay. Does NOT move continuous geometry
    — the projection interpolates toward path[1]; the AUTHORITY is the cell-level decision here."""
    RELOAD_TICKS = 6
    # --- update bot MEMORY before deciding (perception happened this tick) ---
    if visible(grid, bot.pos, player_cell, view_range):
        bot.last_seen = tuple(player_cell)
        bot.time_since_contact = 0
    else:
        bot.time_since_contact += 1
    p = perceive(grid, bot, player_cell, view_range, attack_range)
    prev = bot.state
    bot.state = transition(prev, p)
    # entering SEARCH pins the last-known cell; SEARCH counts down; sight clears alerts
    if bot.state == SEARCH and prev != SEARCH:
        bot.target = bot.alert or bot.last_seen or tuple(player_cell)
        bot.search_ticks = 0
    elif bot.state == SEARCH:
        bot.search_ticks += 1
    else:
        bot.search_ticks = 0
    # entering RETREAT/RELOAD picks cover once; RELOAD runs a timer then refills the magazine
    if bot.state in (RETREAT, RELOAD) and prev not in (RETREAT, RELOAD):
        bot.cover = find_cover(grid, bot.pos, player_cell)
    if bot.state == RELOAD:
        if prev != RELOAD:
            bot.reloading = RELOAD_TICKS
        bot.reloading = max(0, bot.reloading - 1)
        if bot.reloading == 0:
            bot.ammo = bot.mag
    else:
        bot.reloading = 0
    if p.can_see_player:
        bot.alert = None              # direct sight supersedes hearsay
    # firing: ATTACK needs current LOS+range; SUPPRESS fires at the remembered cell. A round is spent per tick.
    can_fire = (bot.state == ATTACK and p.can_see_player and p.in_range) or \
               (bot.state == SUPPRESS and bot.ammo > 0 and bot.last_seen is not None)
    if can_fire and bot.ammo > 0:
        bot.ammo -= 1
    bot.path = plan(grid, bot, player_cell)
    return {"id": bot.id, "state": bot.state, "prev": prev, "percept": p, "path": list(bot.path),
            "ammo": bot.ammo, "cover": bot.cover, "last_seen": bot.last_seen,
            "time_since_contact": bot.time_since_contact, "can_fire": bool(can_fire)}


# --- demo -----------------------------------------------------------------------------------------
def _demo_grid():
    # a 12×8 arena with a wall the bot must path around and that can break line of sight
    blocked = {(6, y) for y in range(0, 5)}        # a vertical wall, gap at the bottom
    return Grid(12, 8, blocked)


def main():
    print("world_ai.py — Phase 9: the combat-AI authority (deterministic, engine-independent)\n")
    g = _demo_grid()
    bot = Bot(id="bot_1", pos=(1, 6), team="red", state=PATROL, target=(1, 1))
    ally = Bot(id="bot_2", pos=(3, 6), team="red", state=PATROL, target=(3, 1))
    player = (10, 6)

    print(f"  grid {g.w}×{g.h}, wall at x=6 (y 0..4), gap at y≥5")
    print(f"  LOS bot_1{bot.pos} → player{player}: {line_of_sight(g, bot.pos, player)}  (clear along y=6)")
    blocked_player = (10, 1)
    print(f"  LOS bot_1{bot.pos} → player{blocked_player}: {line_of_sight(g, bot.pos, blocked_player)}  (wall between)\n")

    path = astar(g, bot.pos, player)
    print(f"  A* bot_1 → player: {len(path)} cells, routes around wall: {(6,0) not in path}")
    rec = step_bot(g, bot, player)
    print(f"  bot_1 PATROL + sees player in range → {rec['state']}  (can_fire={rec['can_fire']})")

    alerted = squad_broadcast([bot, ally], bot, player)
    arec = step_bot(g, ally, (10, 1))                 # ally cannot see player (wall), but was alerted
    print(f"  squad: bot_1 alerts {alerted}; bot_2 (no LOS) → {arec['state']}  (heard alert ⇒ investigates)")
    print("\n  every decision above is a pure function of grid + perception — reproducible, no omniscience.")
    print("  death routes through world_sim.apply_event('destroy', id); consequences propagate by causality.")


if __name__ == "__main__":
    main()
