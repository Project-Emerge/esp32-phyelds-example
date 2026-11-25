import board
from phyelds.calculus import aggregate, neighbors, remember
from phyelds.libraries.device import local_id
from phyelds.vm.device import Device

SILENT_ROUNDS = 3  # rounds a neighbor is kept after its last message


@aggregate
def program():
    """The rounds run so far, and the ids of the boards in range."""
    count, set_count = remember(0)
    return set_count(count + 1), sorted(neighbors(local_id()).exclude_self())


def describe(result):
    """The lines that show the result of a round."""
    count, ids = result
    return [f"round {count} nbr {len(ids)}"]


if __name__ == "__main__":
    # Compact paths and the binary codec: about 10 bytes a message, an ESP-NOW packet holds 250.
    device = Device(board.device_id(), program, paths="compact", binary=True, lifetime=SILENT_ROUNDS)
    board.Host("Phyelds", device, describe).run()
