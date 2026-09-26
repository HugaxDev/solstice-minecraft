import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testlib import run_server, BOTS
from scenarios import ensure_room
import sc_r6 as R

def sc(t):
    ensure_room(t, 6)
    t.wait(40)
    holder = next((b for b in BOTS if t.has(b, R.LANT)), None)
    print("HOLDER", holder)
    R.hold(t, holder, R.LANT)
    R.click(t, holder, 2, "flame")
    print("ember", t.g("#ember"), t.rc(f"data get entity {holder} SelectedItem"))
    R.click(t, holder, 4, "brazier")
    print("ember", t.g("#ember"), "burn", t.g("#burn"), t.pos(holder), t.score(holder, "sol.sea"))
    print(t.rc(f"data get entity {holder} SelectedItem"))
run_server("server-dbg", [sc], "dbg.json")
