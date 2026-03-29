import math
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import pymunk

from src.entities import create_ball, create_boundaries, create_bumpers
from src.settings import GRAVITY, MAX_BALL_SPEED, SPACE_DAMPING, WIDTH


class PhysicsStabilityTests(unittest.TestCase):
    def test_ball_remains_finite_over_time(self):
        space = pymunk.Space()
        space.gravity = GRAVITY
        space.damping = SPACE_DAMPING

        create_boundaries(space)
        create_bumpers(space)
        ball = create_ball(space)

        dt = 1 / 60.0
        for _ in range(600):
            space.step(dt)
            x, y = ball.body.position
            vx, vy = ball.body.velocity
            self.assertTrue(math.isfinite(x) and math.isfinite(y))
            self.assertTrue(math.isfinite(vx) and math.isfinite(vy))
            self.assertLess(abs(x), WIDTH * 3)
            self.assertLess(abs(y), WIDTH * 3)
            self.assertLess(ball.body.velocity.length, 4000)

    def test_ball_velocity_cap_applies(self):
        space = pymunk.Space()
        space.gravity = GRAVITY
        space.damping = SPACE_DAMPING

        create_boundaries(space)
        ball = create_ball(space)
        ball.body.apply_impulse_at_local_point((0, MAX_BALL_SPEED * 10), (0, 0))

        space.step(1 / 60.0)
        self.assertLessEqual(ball.body.velocity.length, MAX_BALL_SPEED + 1e-3)


if __name__ == "__main__":
    unittest.main()
