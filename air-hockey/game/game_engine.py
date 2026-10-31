"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

Starter version: the puck bounces around and paddles can hit it, but
there is no scoring, no match timer, and the reset that happens after
a goal is incomplete. That's what Tasks 2-4 fix/add.
"""

import random

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5


class GameEngine:
    def __init__(self):
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS, max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.ai = ComputerAI()

        # Task 2: match score, plus a latch so one goal is only counted once
        self.player_score = 0
        self.computer_score = 0
        self._goal_latched = False

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)
        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        import pygame
        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED
        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED
        self.player.move_by(dx, dy)

    def update(self):
        self.ai.update(self.computer, self.puck)

        self.puck.move()
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        handle_paddle_collision(self.puck, self.player)
        handle_paddle_collision(self.puck, self.computer)

        self._handle_goals()

    def _handle_goals(self):
        puck = self.puck
        left_edge = puck.x - puck.radius
        right_edge = puck.x + puck.radius

        # The whole puck must fit between the goal posts to count as "in the gap".
        in_gap = GOAL_TOP + puck.radius <= puck.y <= GOAL_BOTTOM - puck.radius

        # After a goal, ignore the goal zones until the puck is back in play.
        if self._goal_latched:
            if left_edge >= MARGIN and right_edge <= WIDTH - MARGIN:
                self._goal_latched = False
            else:
                return

        if left_edge < MARGIN:                       # touching the left end wall
            if in_gap:
                if right_edge < MARGIN:              # fully past the left end line
                    self._score_goal("computer")
            else:                                    # wall (not goal): bounce back
                puck.x = MARGIN + puck.radius
                puck.vx = abs(puck.vx)
        elif right_edge > WIDTH - MARGIN:            # touching the right end wall
            if in_gap:
                if left_edge > WIDTH - MARGIN:       # fully past the right end line
                    self._score_goal("player")
            else:
                puck.x = WIDTH - MARGIN - puck.radius
                puck.vx = -abs(puck.vx)

    def _score_goal(self, scorer):
        """Award one point and reset. The latch stops a second count."""
        if self._goal_latched:
            return
        if scorer == "player":
            self.player_score += 1
        else:
            self.computer_score += 1
        self._goal_latched = True
        self._reset_puck()

    def get_winner(self):
        """Result based on the current score: 'Player', 'Computer' or 'Draw'."""
        if self.player_score > self.computer_score:
            return "Player"
        if self.computer_score > self.player_score:
            return "Computer"
        return "Draw"

    def _reset_puck(self):
        self.puck.x, self.puck.y = WIDTH / 2, HEIGHT / 2
        self.puck.vx = 0
        self.puck.vy = 0

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_table(surface)
        renderer.draw_scores(surface, font, self.player_score, self.computer_score)
        renderer.draw_paddle(surface, self.player, renderer.COLOR_PLAYER)
        renderer.draw_paddle(surface, self.computer, renderer.COLOR_COMPUTER)
        renderer.draw_puck(surface, self.puck)