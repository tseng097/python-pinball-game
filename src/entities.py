import math
import pymunk

from .settings import (
    BALL_COLOR,
    BALL_ELASTICITY,
    BALL_FRICTION,
    BALL_MASS,
    BALL_RADIUS,
    BALL_ANGULAR_VELOCITY_LIMIT,
    BUMPER_COLOR,
    BUMPER_ELASTICITY,
    DRAIN_ELASTICITY,
    WALL_ELASTICITY,
    FLIPPER_COLOR,
    FLIPPER_ANGULAR_VELOCITY_LIMIT,
    FLIPPER_MAX_FORCE,
    FLIPPER_LIMIT_BUFFER,
    FLIPPER_SPRING_DAMPING,
    FLIPPER_SPRING_STIFFNESS,
    HEIGHT,
    LAUNCHER_LANE_X_MIN,
    LAUNCHER_LANE_Y_MAX,
    MAX_BALL_SPEED,
    WALL_COLOR,
    WIDTH,
)


def _to_pygame(p):
    return int(p.x), int(HEIGHT - p.y)


def create_boundaries(space):
    static = space.static_body
    segs = []

    wall_specs = [
        ((30, 80), (30, HEIGHT - 30), 4),
        ((WIDTH - 30, 80), (WIDTH - 30, HEIGHT - 30), 4),
        ((30, HEIGHT - 30), (WIDTH - 30, HEIGHT - 30), 4),
        ((30, 80), (230, 30), 4),
        ((WIDTH - 30, 80), (WIDTH - 230, 30), 4),
        ((230, 30), (WIDTH - 230, 30), 4),
    ]

    for a, b, r in wall_specs:
        s = pymunk.Segment(static, a, b, r)
        s.elasticity = WALL_ELASTICITY
        s.friction = 0.6
        segs.append(s)

    drain_left = pymunk.Segment(static, (220, 95), (280, 70), 3)
    drain_right = pymunk.Segment(static, (WIDTH - 220, 95), (WIDTH - 280, 70), 3)
    for s in (drain_left, drain_right):
        s.elasticity = DRAIN_ELASTICITY
        s.friction = 0.8
        segs.append(s)

    space.add(*segs)
    return segs


def create_bumpers(space):
    bumpers = []
    points = [(200, 600), (300, 680), (400, 600), (300, 520)]
    for p in points:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = p
        shape = pymunk.Circle(body, 26)
        shape.elasticity = BUMPER_ELASTICITY
        shape.friction = 0.2
        shape.collision_type = 2
        shape.score_value = 100
        bumpers.append(shape)

    space.add(*[b.body for b in bumpers], *bumpers)
    return bumpers


def create_ball(space, x=545, y=150):
    moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
    body = pymunk.Body(BALL_MASS, moment)
    body.position = (x, y)
    body.velocity_limit = MAX_BALL_SPEED
    body.angular_velocity_limit = BALL_ANGULAR_VELOCITY_LIMIT
    shape = pymunk.Circle(body, BALL_RADIUS)
    shape.elasticity = BALL_ELASTICITY
    shape.friction = BALL_FRICTION
    shape.collision_type = 1
    space.add(body, shape)
    return shape


def is_ball_in_launcher_lane(body: pymunk.Body) -> bool:
    x, y = body.position
    return x >= LAUNCHER_LANE_X_MIN and y <= LAUNCHER_LANE_Y_MAX


def apply_launcher_impulse(body: pymunk.Body, impulse: float) -> bool:
    if not is_ball_in_launcher_lane(body):
        return False
    body.apply_impulse_at_local_point((0, impulse), (0, 0))
    return True


class Flipper:
    def __init__(self, space, pos, length, rest_angle, max_angle, is_left=True):
        self.is_left = is_left
        mass = 100
        moment = pymunk.moment_for_segment(mass, (0, 0), (length, 0), 8)
        self.body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
        self.body.position = pos
        self.body.angle = rest_angle
        self.body.angular_velocity = 0.0
        self.shape = pymunk.Segment(self.body, (0, 0), (length, 0), 8)
        self.shape.elasticity = 0.4
        self.shape.friction = 1.0

        anchor = pymunk.Body(body_type=pymunk.Body.STATIC)
        anchor.position = pos

        self.pin = pymunk.PinJoint(self.body, anchor, (0, 0), (0, 0))
        self.limit = pymunk.RotaryLimitJoint(self.body, anchor, rest_angle, max_angle)
        self.motor = pymunk.SimpleMotor(self.body, anchor, 0.0)
        self.motor.max_force = FLIPPER_MAX_FORCE
        self.spring = pymunk.DampedRotarySpring(
            self.body,
            anchor,
            rest_angle,
            FLIPPER_SPRING_STIFFNESS,
            FLIPPER_SPRING_DAMPING,
        )
        self.body.angular_velocity_limit = FLIPPER_ANGULAR_VELOCITY_LIMIT

        self.rest_angle = rest_angle
        self.max_angle = max_angle
        self.up_speed = 18 if is_left else -18
        self.down_speed = -14 if is_left else 14

        space.add(
            self.body,
            self.shape,
            self.pin,
            self.limit,
            self.motor,
            self.spring,
            anchor,
        )

    def set_active(self, active: bool):
        if active:
            if self.body.angle >= self.max_angle - FLIPPER_LIMIT_BUFFER:
                self.motor.rate = 0.0
                self.motor.max_force = 0.0
            else:
                self.motor.rate = self.up_speed
                self.motor.max_force = FLIPPER_MAX_FORCE
        else:
            if self.body.angle <= self.rest_angle + FLIPPER_LIMIT_BUFFER:
                self.motor.rate = 0.0
            else:
                self.motor.rate = self.down_speed
            # Let the spring handle return torque to avoid the motor fighting it.
            self.motor.max_force = 0.0


def draw_segments(screen, segs, pygame):
    for s in segs:
        a = _to_pygame(s.a + s.body.position)
        b = _to_pygame(s.b + s.body.position)
        pygame.draw.line(screen, WALL_COLOR, a, b, max(2, int(s.radius * 2)))


def draw_bumpers(screen, bumpers, pygame):
    for b in bumpers:
        pos = _to_pygame(b.body.position)
        pygame.draw.circle(screen, BUMPER_COLOR, pos, int(b.radius))
        pygame.draw.circle(screen, (255, 220, 220), pos, int(b.radius * 0.55))


def draw_ball(screen, ball_shape, pygame):
    pos = _to_pygame(ball_shape.body.position)
    pygame.draw.circle(screen, BALL_COLOR, pos, int(ball_shape.radius))


def draw_flipper(screen, flipper, pygame):
    a_world = flipper.body.local_to_world(flipper.shape.a)
    b_world = flipper.body.local_to_world(flipper.shape.b)
    a = _to_pygame(a_world)
    b = _to_pygame(b_world)
    pygame.draw.line(screen, FLIPPER_COLOR, a, b, int(flipper.shape.radius * 2))
    pygame.draw.circle(screen, FLIPPER_COLOR, a, int(flipper.shape.radius * 1.2))
