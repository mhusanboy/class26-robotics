# TRIK Studio Python, matching line_follow_sim.qrs graphical controller.
# Simulator wiring: A4 left sensor, A3 right sensor; M4 left, M3 right.
BASE = 18
TURN = 22
THRESHOLD = 0.5
PERIOD_MS = 20


def command(left, right, last_turn, lost):
    # Sensors are close enough that a centred line covers both.
    if left > THRESHOLD and right > THRESHOLD:
        return BASE, BASE, last_turn, 0
    if left > THRESHOLD:
        return 8 - TURN, 8 + TURN, 1, 0
    if right > THRESHOLD:
        return 8 + TURN, 8 - TURN, -1, 0
    lost += 1
    if lost < 3:
        return BASE, BASE, last_turn, lost
    return -TURN * last_turn, TURN * last_turn, last_turn, lost


def main():
    last_turn = 1
    lost = 0
    try:
        while True:
            left = brick.sensor("A4").read()
            right = brick.sensor("A3").read()
            lpower, rpower, last_turn, lost = command(left, right, last_turn, lost)
            brick.motor("M4").setPower(lpower)
            brick.motor("M3").setPower(rpower)
            script.wait(PERIOD_MS)
    finally:
        brick.motor("M4").setPower(0)
        brick.motor("M3").setPower(0)


main()
