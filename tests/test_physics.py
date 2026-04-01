import math
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import pymunk

from src.entities import Flipper, create_ball, create_boundaries, create_bumpers
from src.physics import configure_space, step_space
from src.settings import (
    FLIPPER_ANGULAR_VELOCITY_LIMIT,
    MAX_BALL_SPEED,
    HEIGHT,
    PHYSICS_MAX_DT,
    WIDTH,
)


class PhysicsStabilityTests(unittest.TestCase):
    def test_ball_remains_finite_over_time(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        create_bumpers(space)
        ball = create_ball(space)

        dt = 1 / 60.0
        for _ in range(600):
            step_space(space, dt)
            x, y = ball.body.position
            vx, vy = ball.body.velocity
            self.assertTrue(math.isfinite(x) and math.isfinite(y))
            self.assertTrue(math.isfinite(vx) and math.isfinite(vy))
            self.assertLess(abs(x), WIDTH * 3)
            self.assertLess(abs(y), WIDTH * 3)
            self.assertLess(ball.body.velocity.length, 4000)

    def test_ball_velocity_cap_applies(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        ball = create_ball(space)
        ball.body.apply_impulse_at_local_point((0, MAX_BALL_SPEED * 10), (0, 0))

        step_space(space, 1 / 60.0)
        self.assertLessEqual(ball.body.velocity.length, MAX_BALL_SPEED + 1e-3)

    def test_step_space_clamps_large_dt(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        ball = create_ball(space, x=WIDTH / 2, y=HEIGHT / 2)
        ball.body.velocity = (1000, 0)

        x0, _ = ball.body.position
        step_space(space, PHYSICS_MAX_DT * 10)
        x1, _ = ball.body.position

        self.assertLessEqual(x1 - x0, 1000 * PHYSICS_MAX_DT * 1.1)

    def test_flipper_limits_and_angular_velocity(self):
        space = pymunk.Space()
        configure_space(space)
        space.gravity = (0, 0)

        flipper = Flipper(
            space,
            pos=(240, 145),
            length=90,
            rest_angle=-0.45,
            max_angle=0.55,
            is_left=True,
        )

        dt = 1 / 120.0
        for step in range(240):
            flipper.set_active(step < 120)
            step_space(space, dt)

        self.assertGreaterEqual(flipper.body.angle, flipper.rest_angle - 0.05)
        self.assertLessEqual(flipper.body.angle, flipper.max_angle + 0.05)
        self.assertLessEqual(
            abs(flipper.body.angular_velocity),
            FLIPPER_ANGULAR_VELOCITY_LIMIT + 0.5,
        )

    def test_fast_ball_does_not_escape_walls(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        ball = create_ball(space, x=60, y=200)
        ball.body.velocity = (-3000, 0)

        dt = 1 / 120.0
        for _ in range(240):
            step_space(space, dt)
            x, y = ball.body.position
            self.assertGreaterEqual(x, -10)
            self.assertLessEqual(x, WIDTH + 10)
            self.assertGreaterEqual(y, -10)


if __name__ == "__main__":
    unittest.main()
