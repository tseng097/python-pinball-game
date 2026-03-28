import sys
import pygame
import pymunk

from .settings import (
    BG_COLOR,
    FPS,
    GRAVITY,
    HEIGHT,
    INITIAL_BALLS,
    LAUNCHER_CHARGE_RATE,
    LAUNCHER_MAX_FORCE,
    TEXT_COLOR,
    WIDTH,
)
from .entities import (
    Flipper,
    create_ball,
    create_boundaries,
    create_bumpers,
    draw_ball,
    draw_bumpers,
    draw_flipper,
    draw_segments,
)


class PinballGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Python Pinball")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 46, bold=True)

        self.left_pressed = False
        self.right_pressed = False
        self.space_held = False
        self.launch_power = 0.0

        self.reset_game()

    def reset_game(self):
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY

        self.score = 0
        self.balls_left = INITIAL_BALLS
        self.game_over = False

        self.walls = create_boundaries(self.space)
        self.bumpers = create_bumpers(self.space)

        self.left_flipper = Flipper(
            self.space,
            pos=(240, 145),
            length=90,
            rest_angle=-0.45,
            max_angle=0.55,
            is_left=True,
        )
        self.right_flipper = Flipper(
            self.space,
            pos=(360, 145),
            length=-90,
            rest_angle=3.59,
            max_angle=4.58,
            is_left=False,
        )

        self.ball = None
        self.spawn_ball()

        handler = self.space.add_collision_handler(1, 2)
        handler.begin = self._on_ball_hits_bumper

    def _on_ball_hits_bumper(self, arbiter, space, data):
        shapes = arbiter.shapes
        for s in shapes:
            if hasattr(s, "score_value"):
                self.score += int(s.score_value)
                break
        return True

    def spawn_ball(self):
        if self.balls_left <= 0:
            self.game_over = True
            self.ball = None
            return
        self.balls_left -= 1
        self.ball = create_ball(self.space)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.left_pressed = True
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.right_pressed = True
                if event.key == pygame.K_SPACE and self.ball and not self.game_over:
                    self.space_held = True
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.left_pressed = False
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.right_pressed = False
                if event.key == pygame.K_SPACE and self.space_held:
                    self.space_held = False
                    self.launch_ball()

        self.left_flipper.set_active(self.left_pressed)
        self.right_flipper.set_active(self.right_pressed)

    def launch_ball(self):
        if not self.ball:
            return
        force = min(self.launch_power, LAUNCHER_MAX_FORCE)
        self.ball.body.apply_impulse_at_local_point((0, force), (0, 0))
        self.launch_power = 0.0

    def update(self, dt):
        if self.game_over:
            return

        if self.space_held and self.ball:
            self.launch_power = min(
                LAUNCHER_MAX_FORCE,
                self.launch_power + LAUNCHER_CHARGE_RATE * dt,
            )

        self.space.step(dt)

        if self.ball:
            bx, by = self.ball.body.position
            if by < 30 or bx < -50 or bx > WIDTH + 50:
                self.space.remove(self.ball, self.ball.body)
                self.ball = None
                self.spawn_ball()

    def draw_ui(self):
        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        balls_text = self.font.render(f"Balls: {self.balls_left + (1 if self.ball else 0)}", True, TEXT_COLOR)
        self.screen.blit(score_text, (20, 16))
        self.screen.blit(balls_text, (460, 16))

        if self.space_held and self.ball:
            pct = int((self.launch_power / LAUNCHER_MAX_FORCE) * 100)
            ptxt = self.font.render(f"Launch: {pct}%", True, TEXT_COLOR)
            self.screen.blit(ptxt, (240, 16))

        if self.game_over:
            over = self.big_font.render("GAME OVER", True, (255, 120, 120))
            hint = self.font.render("Press R to restart", True, TEXT_COLOR)
            self.screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 50))
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 10))

    def draw(self):
        self.screen.fill(BG_COLOR)
        draw_segments(self.screen, self.walls, pygame)
        draw_bumpers(self.screen, self.bumpers, pygame)
        draw_flipper(self.screen, self.left_flipper, pygame)
        draw_flipper(self.screen, self.right_flipper, pygame)
        if self.ball:
            draw_ball(self.screen, self.ball, pygame)
        self.draw_ui()
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_input()
            self.update(dt)
            self.draw()
