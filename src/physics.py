import pymunk

from .settings import GRAVITY, SPACE_DAMPING, SPACE_ITERATIONS, PHYSICS_SUBSTEPS


def configure_space(space: pymunk.Space) -> None:
    space.gravity = GRAVITY
    space.damping = SPACE_DAMPING
    space.iterations = SPACE_ITERATIONS


def step_space(space: pymunk.Space, dt: float) -> None:
    sub_dt = dt / PHYSICS_SUBSTEPS
    for _ in range(PHYSICS_SUBSTEPS):
        space.step(sub_dt)
