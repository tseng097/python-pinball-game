import math
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import pymunk

from src.entities import (
    Flipper,
    apply_launcher_impulse,
    create_ball,
    create_boundaries,
    create_bumpers,
    is_ball_in_launcher_lane,
)
from src.physics import configure_space, step_space
from src.settings import (
    BALL_ANGULAR_VELOCITY_LIMIT,
    FLIPPER_ANGULAR_VELOCITY_LIMIT,
    FLIPPER_LIMIT_BUFFER,
    FLIPPER_SPRING_DAMPING,
    FLIPPER_SPRING_STIFFNESS,
    MAX_BALL_SPEED,
    HEIGHT,
    LAUNCHER_LANE_X_MIN,
    LAUNCHER_LANE_Y_MAX,
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

    def test_ball_angular_velocity_cap_applies(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        ball = create_ball(space)
        ball.body.angular_velocity = BALL_ANGULAR_VELOCITY_LIMIT * 10

        step_space(space, 1 / 60.0)
        self.assertLessEqual(
            abs(ball.body.angular_velocity),
            BALL_ANGULAR_VELOCITY_LIMIT + 1e-3,
        )

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

    def test_flippers_start_at_rest_angle(self):
        space = pymunk.Space()
        configure_space(space)
        space.gravity = (0, 0)

        left = Flipper(
            space,
            pos=(240, 145),
            length=90,
            rest_angle=-0.45,
            max_angle=0.55,
            is_left=True,
        )
        right = Flipper(
            space,
            pos=(360, 145),
            length=-90,
            rest_angle=3.59,
            max_angle=4.58,
            is_left=False,
        )

        self.assertAlmostEqual(left.body.angle, left.rest_angle, delta=1e-4)
        self.assertAlmostEqual(right.body.angle, right.rest_angle, delta=1e-4)

        step_space(space, 1 / 120.0)

        self.assertGreaterEqual(left.body.angle, left.rest_angle - 0.05)
        self.assertLessEqual(left.body.angle, left.max_angle + 0.05)
        self.assertGreaterEqual(right.body.angle, right.rest_angle - 0.05)
        self.assertLessEqual(right.body.angle, right.max_angle + 0.05)

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

    def test_fast_ball_large_dt_stays_in_bounds(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        ball = create_ball(space, x=60, y=200)
        ball.body.velocity = (-6000, 0)

        dt = PHYSICS_MAX_DT
        for _ in range(120):
            step_space(space, dt)
            x, y = ball.body.position
            self.assertGreaterEqual(x, -10)
            self.assertLessEqual(x, WIDTH + 10)
            self.assertGreaterEqual(y, -10)

    def test_wall_bounces_do_not_add_energy(self):
        space = pymunk.Space()
        configure_space(space)
        space.gravity = (0, 0)

        create_boundaries(space)
        ball = create_ball(space, x=WIDTH / 2, y=HEIGHT / 2)
        ball.body.velocity = (1500, 700)

        initial_speed = ball.body.velocity.length
        max_speed = initial_speed

        dt = 1 / 120.0
        for _ in range(600):
            step_space(space, dt)
            max_speed = max(max_speed, ball.body.velocity.length)

        self.assertLessEqual(max_speed, initial_speed * 1.05)

    def test_flipper_returns_to_rest_when_released(self):
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
        for step in range(120):
            flipper.set_active(True)
            step_space(space, dt)

        angle_at_release = flipper.body.angle
        for _ in range(60):
            flipper.set_active(False)
            step_space(space, dt)

        self.assertLess(abs(flipper.body.angle - flipper.rest_angle), abs(angle_at_release - flipper.rest_angle))

        for _ in range(180):
            flipper.set_active(False)
            step_space(space, dt)

        self.assertAlmostEqual(flipper.body.angle, flipper.rest_angle, delta=0.08)
        self.assertLess(abs(flipper.body.angular_velocity), 1.0)
        self.assertGreater(FLIPPER_SPRING_STIFFNESS, 0)
        self.assertGreater(FLIPPER_SPRING_DAMPING, 0)

    def test_flipper_motor_idles_near_limits(self):
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
        for _ in range(240):
            flipper.set_active(True)
            step_space(space, dt)

        flipper.set_active(True)
        self.assertLessEqual(flipper.body.angle, flipper.max_angle + 0.05)
        self.assertEqual(flipper.motor.rate, 0.0)
        self.assertEqual(flipper.motor.max_force, 0.0)
        self.assertLessEqual(flipper.body.angle, flipper.max_angle + FLIPPER_LIMIT_BUFFER + 0.1)

        for _ in range(240):
            flipper.set_active(False)
            step_space(space, dt)

        flipper.set_active(False)
        self.assertGreaterEqual(flipper.body.angle, flipper.rest_angle - 0.05)
        self.assertEqual(flipper.motor.rate, 0.0)
        self.assertEqual(flipper.motor.max_force, 0.0)
        self.assertGreaterEqual(flipper.body.angle, flipper.rest_angle - FLIPPER_LIMIT_BUFFER - 0.1)

    def test_launcher_impulse_only_applies_in_lane(self):
        space = pymunk.Space()
        configure_space(space)
        space.gravity = (0, 0)

        create_boundaries(space)
        ball = create_ball(space)

        self.assertGreaterEqual(ball.body.position.x, LAUNCHER_LANE_X_MIN)
        self.assertLessEqual(ball.body.position.y, LAUNCHER_LANE_Y_MAX)
        self.assertTrue(is_ball_in_launcher_lane(ball.body))

        ball.body.velocity = (0, 0)
        applied = apply_launcher_impulse(ball.body, 2000)
        self.assertTrue(applied)
        step_space(space, 1 / 120.0)
        self.assertGreater(ball.body.velocity.y, 0)

        ball.body.position = (WIDTH / 2, HEIGHT / 2)
        ball.body.velocity = (0, 0)
        self.assertFalse(is_ball_in_launcher_lane(ball.body))
        applied = apply_launcher_impulse(ball.body, 2000)
        self.assertFalse(applied)
        step_space(space, 1 / 120.0)
        self.assertLess(abs(ball.body.velocity.y), 1e-3)

    def test_bumper_bounces_keep_speed_capped(self):
        space = pymunk.Space()
        configure_space(space)

        create_boundaries(space)
        create_bumpers(space)
        ball = create_ball(space, x=300, y=620)
        ball.body.velocity = (0, 1800)

        dt = 1 / 120.0
        for _ in range(720):
            step_space(space, dt)
            self.assertLessEqual(ball.body.velocity.length, MAX_BALL_SPEED + 1e-3)


if __name__ == "__main__":
    unittest.main()
