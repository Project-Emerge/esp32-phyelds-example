import board
from phyelds.calculus import aggregate
from phyelds.libraries.collect import count_nodes
from phyelds.libraries.device import local_id
from phyelds.libraries.distances import hops_distance
from phyelds.libraries.leader_election import candidacy, elect_leader
from phyelds.libraries.spreading import broadcast, distance_to
from phyelds.vm.device import Device

SILENT_ROUNDS = 3  # rounds a neighbor is kept after its last message
AREA = 10  # hops: a leader leads the boards up to AREA hops away


@aggregate
def program():
    """Elect a leader, count the boards towards it, and tell every board the count (SCR pattern)."""
    metric = hops_distance()  # one exchange for all the blocks: each would send its own
    # candidacy(): the default election (random uuids) fails on MicroPython (phyelds#68)
    leader = elect_leader(AREA, metric, strategy=candidacy())
    is_leader = leader == local_id()
    hops = distance_to(is_leader, metric)
    boards = broadcast(is_leader, count_nodes(hops), metric)
    return leader, hops, boards


def describe(result):
    """The lines that show the result of a round."""
    leader, hops, boards = result
    return [
        f"leader {leader:06x}" if leader is not None else "leader ?",
        f"hops {hops:g} boards {boards}",
    ]


if __name__ == "__main__":
    device = Device(board.device_id(), program, paths="compact", binary=True, lifetime=SILENT_ROUNDS)
    board.Host("SCR", device, describe).run()
