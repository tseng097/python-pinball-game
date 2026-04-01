import pymunk

from .settings import (
    GRAVITY,
    PHYSICS_MAX_DT,
    PHYSICS_SUBSTEPS,
    SPACE_DAMPING,
    SPACE_ITERATIONS,
)


def configure_space(space: pymunk.Space) -> None:
    space.gravity = GRAVITY
    space.damping = SPACE_DAMPING
    space.iterations = SPACE_ITERATIONS


def step_space(space: pymunk.Space, dt: float) -> None:
    safe_dt = min(dt, PHYSICS_MAX_DT)
    sub_dt = safe_dt / PHYSICS_SUBSTEPS
    for _ in range(PHYSICS_SUBSTEPS):
        space.step(sub_dt)
