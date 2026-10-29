"""Week 6. Run unchanged in TRIK Studio Python mode and on the robot."""
import math
import time

DIGITS = '39'  # Provisional: inferred from week2/39PID.qrs.
RADIUS = 0.0375  # metres; measure and replace for your robot in BOTH projects.
TRACK = 0.194
LEFT_MOTOR, RIGHT_MOTOR = 'M3', 'M4'
LEFT_ENCODER, RIGHT_ENCODER = 'E3', 'E4'
LEFT_SIGN, RIGHT_SIGN = 1, 1
PERIOD_MS = 30
LOG_FILE = 'Husanboy_odometry_data.txt'  # Rename after each run: _sim.txt / _real.txt.
WIDTH, HEIGHT, GAP = 0.4, 0.6, 0.25

# Continuous strokes; repeated edges are intentional. Coordinates are in a
# digit-local frame, starting at its top-left, +y upward.
STROKES = {
 '0': [(0,0),(1,0),(1,-1),(0,-1),(0,0)],
 '1': [(0.5,0),(0.5,-1)],
 '2': [(0,0),(1,0),(1,-.5),(0,-.5),(0,-1),(1,-1)],
 '3': [(0,0),(1,0),(1,-.5),(0,-.5),(1,-.5),(1,-1),(0,-1)],
 '4': [(0,0),(0,-.5),(1,-.5),(1,0),(1,-1)],
 '5': [(1,0),(0,0),(0,-.5),(1,-.5),(1,-1),(0,-1)],
 '6': [(1,0),(0,0),(0,-1),(1,-1),(1,-.5),(0,-.5)],
 '7': [(0,0),(1,0),(0,-1)],
 '8': [(0,0),(1,0),(1,-1),(0,-1),(0,0),(0,-.5),(1,-.5)],
 '9': [(0,0),(1,0),(1,-.5),(0,-.5),(0,0),(1,0),(1,-1),(0,-1)]
}


def waypoints():
    if len(DIGITS) != 2 or any(d not in STROKES for d in DIGITS):
        raise ValueError('DIGITS must contain exactly two decimal digits')
    return [(i * (WIDTH + GAP) + a * WIDTH, b * HEIGHT)
            for i, digit in enumerate(DIGITS) for a, b in STROKES[digit]]


def integrate(x, y, theta, degrees_l, degrees_r):
    dl = math.radians(degrees_l) * RADIUS
    dr = math.radians(degrees_r) * RADIUS
    ds, da = (dl + dr) / 2, (dr - dl) / TRACK
    return (x + ds * math.cos(theta + da / 2),
            y + ds * math.sin(theta + da / 2), theta + da)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def main():
    targets = waypoints()
    x = y = theta = 0.0
    old_l = brick.encoder(LEFT_ENCODER).read()
    old_r = brick.encoder(RIGHT_ENCODER).read()
    clock = getattr(time, 'monotonic', time.time)
    start = clock()
    target_started = start
    index = 0
    turning = True
    # The lecture demo explicitly lowers the simulator marker.
    # Hardware may not expose this simulator-only device.
    marker = None
    try:
        marker = brick.marker()
    except AttributeError:
        pass
    if marker is not None:
        marker.up()
    digit_boundary = len(STROKES[DIGITS[0]])
    try:
        with open(LOG_FILE, 'w') as log:
            log.write('0.000000,0.000000,0\n')
            while index < len(targets):
                script.wait(PERIOD_MS)
                now = clock()
                enc_l = brick.encoder(LEFT_ENCODER).read()
                enc_r = brick.encoder(RIGHT_ENCODER).read()
                x, y, theta = integrate(x, y, theta,
                    LEFT_SIGN * (enc_l-old_l), RIGHT_SIGN * (enc_r-old_r))
                old_l, old_r = enc_l, enc_r
                log.write('%.6f,%.6f,%d\n' % (x, y, round((now-start)*1000)))
                log.flush()
                if now - target_started > 45 or now - start > 600:
                    raise RuntimeError('Motion timeout: check geometry, wiring and encoders')
                tx, ty = targets[index]
                distance = math.hypot(tx-x, ty-y)
                if distance < 0.012:
                    brick.motor(LEFT_MOTOR).setPower(0)
                    brick.motor(RIGHT_MOTOR).setPower(0)
                    # First waypoint of each digit: start drawing. After the
                    # last point of digit one: lift during connecting travel.
                    if marker is not None:
                        if index == 0 or index == digit_boundary:
                            marker.down('blue')
                        elif index == digit_boundary - 1:
                            marker.up()
                    index += 1
                    target_started = now
                    turning = True
                    continue
                error = wrap(math.atan2(ty-y, tx-x)-theta)
                if turning and abs(error) < 0.04:
                    turning = False
                if abs(error) > 0.4:
                    turning = True
                v = 0 if turning else min(35, max(10, 90*distance))
                u = max(-25, min(25, 28*error))
                if turning and abs(u) < 8:
                    u = 8 if error > 0 else -8
                brick.motor(LEFT_MOTOR).setPower(int(v-u))
                brick.motor(RIGHT_MOTOR).setPower(int(v+u))
            # Record coast-down after stopping, including the actual final reading.
            for _ in range(10):
                script.wait(PERIOD_MS)
                enc_l = brick.encoder(LEFT_ENCODER).read()
                enc_r = brick.encoder(RIGHT_ENCODER).read()
                x, y, theta = integrate(x,y,theta,LEFT_SIGN*(enc_l-old_l),RIGHT_SIGN*(enc_r-old_r))
                old_l, old_r = enc_l, enc_r
                log.write('%.6f,%.6f,%d\n' % (x,y,round((clock()-start)*1000)))
    finally:
        brick.motor(LEFT_MOTOR).setPower(0)
        brick.motor(RIGHT_MOTOR).setPower(0)
        if marker is not None:
            marker.up()


if __name__ == '__main__':
    main()
