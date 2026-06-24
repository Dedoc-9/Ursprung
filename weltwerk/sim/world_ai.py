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
STATES = (IDLE, PATROL, INVESTIGATE, CHASE, ATTACK, SEARCH)

DEFAULT_VIEW_RANGE = 14.0
DEFAULT_ATTACK_RANGE = 9.0
SEARCH_LIMIT = 12          # ticks a bot searches a last-known position before giving up → PATROL
ALERT_RADIUS = 10.0        # squad: allies within this distance of the spotter are alerted


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


def _from_chase(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    return SEARCH                       # lost sight → search the last-known position


def _from_attack(p):
    if not p.can_see_player: return SEARCH
    if not p.in_range: return CHASE
    return ATTACK


def _from_search(p):
    if p.can_see_player: return ATTACK if p.in_range else CHASE
    if p.search_timed_out: return PATROL
    return SEARCH


TRANSITIONS = {
    IDLE: _from_idle, PATROL: _from_patrol, INVESTIGATE: _from_investigate,
    CHASE: _from_chase, ATTACK: _from_attack, SEARCH: _from_search,
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
    alive: bool = True


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
    )


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
    CHASE/ATTACK head for the player; INVESTIGATE/SEARCH head for the last-known (alert/target) cell."""
    if bot.state in (CHASE, ATTACK):
        goal = tuple(player_cell)
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
    p = perceive(grid, bot, player_cell, view_range, attack_range)
    prev = bot.state
    bot.state = transition(prev, p)
    # bookkeeping: entering SEARCH pins the last-known cell; SEARCH counts down; sight clears alerts
    if bot.state == SEARCH and prev != SEARCH:
        bot.target = bot.alert or tuple(player_cell)
        bot.search_ticks = 0
    elif bot.state == SEARCH:
        bot.search_ticks += 1
    else:
        bot.search_ticks = 0
    if p.can_see_player:
        bot.alert = None              # direct sight supersedes hearsay
    bot.path = plan(grid, bot, player_cell)
    return {"id": bot.id, "state": bot.state, "prev": prev, "percept": p, "path": list(bot.path),
            "can_fire": bot.state == ATTACK and p.can_see_player and p.in_range}


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
