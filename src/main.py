import abc as _abc
import math as _math
import pygame as _pg
import enum as _enum

_pg.init()
_pg.display.set_caption("Rays")
CLOCK = _pg.time.Clock()
FONT = _pg.font.SysFont("Rays", 24)
CANVAS_WIDTH, CANVAS_HEIGHT = 1600, 900
SCREEN = _pg.display.set_mode(size=(CANVAS_WIDTH, CANVAS_HEIGHT), vsync=_pg.DOUBLEBUF)

_SPEED = 100
FPS_TARGET = 60
SPEED_MOV = _SPEED
SPEED_ROT = _SPEED
DELTA_TIME = float()
GRAVITY = float(9.81)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
TOTAL_PIXELS = CANVAS_WIDTH * CANVAS_HEIGHT


class Directions(_enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Drawable(_abc.ABC):
    @_abc.abstractmethod
    def draw() -> None:
        raise NotImplementedError()


# Define the Point class
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y

    def intersects_line(self, line: "Wall") -> float:
        dist_from_end = _math.hypot(self.x - line.end.x, self.y - line.end.y)
        dist_from_start = _math.hypot(self.x - line.start.x, self.y - line.start.y)
        line_length = _math.hypot(line.start.x - line.end.x, line.start.y - line.end.y)

        return abs(dist_from_end + dist_from_start - line_length) < 0.01


# Define the BoundaryWall class
class BoundaryWall(Drawable):
    def __init__(self, start_point: Point, end_point: Point) -> None:
        self.start = start_point
        self.end = end_point

    @property
    def center(self) -> Point:
        return Point(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2,
        )

    def draw(self) -> None:
        _pg.draw.aaline(
            surface=SCREEN,
            color=COLOR_WHITE,
            start_pos=(self.start.x, self.start.y),
            end_pos=(self.end.x, self.end.y),
        )

    def get_angle(self, direction: Directions) -> float:
        if direction == Directions.LEFT:
            dx_line = self.start.x - self.end.x
            dy_line = self.start.y - self.end.y
        elif direction == Directions.RIGHT:
            dx_line = self.end.x - self.start.x
            dy_line = self.end.y - self.start.y
        else:
            raise NotImplementedError(f"Direction {direction} not implemented")

        return _math.atan2(dy_line, dx_line)

    def intersects_line(self, line: "BoundaryWall") -> bool:
        def ccw(A, B, C):
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

        A = self.start
        B = self.end
        C = line.start
        D = line.end

        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


# Define the Wall class
class Wall(BoundaryWall):
    def draw(self) -> None:
        # Only rorate one-way at a time
        keys = _pg.key.get_pressed()
        if keys[_pg.K_RSHIFT]:
            self.rotate(SPEED_ROT * DELTA_TIME)
        elif keys[_pg.K_LSHIFT]:
            self.rotate(-SPEED_ROT * DELTA_TIME)

        super().draw()

    def rotate(self, angle_degrees) -> None:
        center = self.center
        angle_radians = _math.radians(angle_degrees)

        # Translate the line to origin
        translated_end_x = self.end.x - center.x
        translated_end_y = self.end.y - center.y
        translated_start_x = self.start.x - center.x
        translated_start_y = self.start.y - center.y

        # Rotate the line
        rotated_start_x = translated_start_x * _math.cos(
            angle_radians
        ) - translated_start_y * _math.sin(angle_radians)
        rotated_start_y = translated_start_x * _math.sin(
            angle_radians
        ) + translated_start_y * _math.cos(angle_radians)
        rotated_end_x = translated_end_x * _math.cos(
            angle_radians
        ) - translated_end_y * _math.sin(angle_radians)
        rotated_end_y = translated_end_x * _math.sin(
            angle_radians
        ) + translated_end_y * _math.cos(angle_radians)

        # Translate line back or original coordinates
        self.end.x = rotated_end_x + center.x
        self.end.y = rotated_end_y + center.y
        self.start.x = rotated_start_x + center.x
        self.start.y = rotated_start_y + center.y


# Define the Ray class
class Ray(Drawable):
    def __init__(self, source: Point, angle: float, length: int, color: tuple) -> None:
        self.color = color
        self.source = source
        self.length = length
        self.end_point: Point | None = None
        self.direction: _pg.Vector2 = (
            _pg.math.Vector2(_math.cos(angle), _math.sin(angle)) * length
        )

    def _set_end_point(self) -> None:
        nearest_wall_distance = self.length
        nearest_wall_intersection_point = None

        for wall in WALLS:
            if intersects_at := self.intersects_line(wall):
                distance_to_wall = _math.hypot(
                    self.source.x - intersects_at.x, self.source.y - intersects_at.y
                )
                if distance_to_wall < nearest_wall_distance:
                    nearest_wall_distance = distance_to_wall
                    nearest_wall_intersection_point = intersects_at

        if nearest_wall_intersection_point:
            end_point = nearest_wall_intersection_point
        else:
            end_point = Point(
                self.source.x + self.direction.x, self.source.y + self.direction.y
            )

        self.end_point = end_point

    def draw(self) -> None:
        self._set_end_point()

        assert (
            self.end_point is not None
        ), "No end_point set for this Ray. Either set an end_point or call _set_end_point() before the draw occurs."

        _pg.draw.aaline(
            SCREEN,
            self.color,
            (self.source.x, self.source.y),
            (self.end_point.x, self.end_point.y),
        )

    def intersects_line(self, line: BoundaryWall) -> Point | None:
        x1, y1 = self.source.x, self.source.y
        x2, y2 = self.source.x + self.direction.x, self.source.y + self.direction.y

        x3, y3 = line.start.x, line.start.y
        x4, y4 = line.end.x, line.end.y

        # Check for zero-length lines
        if (x1 == x2 and y1 == y2) or (x3 == x4 and y3 == y4):
            return None

        denominator = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

        # Check for parallel lines
        if denominator == 0:
            return None

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denominator
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denominator

        # Check if intersection is within the line segments
        if ua < 0 or ua > 1 or ub < 0 or ub > 1:
            return None

        x = x1 + ua * (x2 - x1)
        y = y1 + ua * (y2 - y1)

        return Point(x, y)


# Define the LightSource class
class LightSource(Drawable):
    def __init__(self, color: tuple, ray_density: int = 1) -> None:
        self.radius = 5
        self.color = color
        self.ray_density = ray_density
        self.pos = Point(0, 0)
        self._mouse_x_old = 0
        self._mouse_y_old = 0

    def draw(self) -> None:
        keys = _pg.key.get_pressed()
        mouse_x, mouse_y = _pg.mouse.get_pos()

        if (self._mouse_x_old, self._mouse_y_old) != (mouse_x, mouse_y):
            # If mouse has moved, follow it.
            self.pos.x, self.pos.y = mouse_x, mouse_y
            self._mouse_x_old, self._mouse_y_old = mouse_x, mouse_y
        else:
            # Follow WASD keys.
            if keys[_pg.K_w]:
                y = self.pos.y - SPEED_MOV * DELTA_TIME
                self.pos.y = max(float(0), y)
            if keys[_pg.K_s]:
                y = self.pos.y + SPEED_MOV * DELTA_TIME
                self.pos.y = min(CANVAS_HEIGHT, y)
            if keys[_pg.K_a]:
                new_x_lat = max(0, self.pos.x - SPEED_MOV * DELTA_TIME)
                self.pos = self.intersects_any_line(
                    Point(new_x_lat, self.pos.y), Directions.LEFT
                )
            if keys[_pg.K_d]:
                new_x_lat = min(CANVAS_WIDTH, self.pos.x + SPEED_MOV * DELTA_TIME)
                self.pos = self.intersects_any_line(
                    Point(new_x_lat, self.pos.y), Directions.RIGHT
                )

        _pg.draw.circle(SCREEN, self.color, (self.pos.x, self.pos.y), self.radius)

        if _pg.mouse.get_pressed()[0] or keys[_pg.K_SPACE]:
            self.draw_rays()

    def draw_rays(self) -> None:
        for i in range(1, self.ray_density + 1):
            angle = i * 2 * _math.pi / self.ray_density
            Ray(self.pos, angle, TOTAL_PIXELS, self.color).draw()

    def intersects_any_line(self, new_pos: Point, direction: Directions) -> Point:
        temp_line = Wall(self.pos, new_pos)
        for wall in WALLS:
            if temp_line.intersects_line(wall):
                wall_angle = wall.get_angle(direction)

                if wall_angle in [_math.pi, -_math.pi, _math.pi / 2, -_math.pi / 2]:
                    # Block movement on vertical or horizontal lines
                    return self.pos

                move_length = _math.hypot(
                    new_pos.x - self.pos.x, new_pos.y - self.pos.y
                )
                direction_vector: _pg.Vector2 = (
                    _pg.math.Vector2(_math.cos(wall_angle), _math.sin(wall_angle))
                    * move_length
                )
                return Point(
                    self.pos.x + direction_vector.x, self.pos.y + direction_vector.y
                )

        return new_pos


def show_stats() -> None:
    fps = CLOCK.get_fps()
    stats = f"FPS: {int(fps)}, SPEED_MOV: {SPEED_MOV}, SPEED_ROT: {SPEED_ROT}"

    surface = FONT.render(stats, True, COLOR_WHITE)

    SCREEN.blit(surface, (10, 10))


# Walls setup
WALLS: list[BoundaryWall] = [
    # Obstacles
    Wall(Point(300, 100), Point(500, 300)),
    Wall(Point(200, 600), Point(500, 800)),
    Wall(Point(600, 300), Point(600, 500)),
    Wall(Point(800, 600), Point(1000, 600)),
    Wall(Point(1200, 100), Point(1200, 700)),
    # Scene boundaries
    BoundaryWall(Point(0, 0), Point(CANVAS_WIDTH, 0)),
    BoundaryWall(Point(0, 0), Point(0, CANVAS_HEIGHT)),
    BoundaryWall(Point(CANVAS_WIDTH, 0), Point(CANVAS_WIDTH, CANVAS_HEIGHT)),
    BoundaryWall(Point(0, CANVAS_HEIGHT), Point(CANVAS_WIDTH, CANVAS_HEIGHT)),
]

# Initialize scene objects
DRAWABLES: list[Drawable] = [
    *WALLS,
    LightSource(color=(253, 184, 19), ray_density=1440),
]

# Main loop
running = True
while running:
    # Quit check
    for event in _pg.event.get():
        if event.type == _pg.QUIT:
            running = False

    # Speed adjustments
    if keys := _pg.key.get_pressed():
        if keys[_pg.K_EQUALS]:
            SPEED_MOV += 1

        if keys[_pg.K_MINUS]:
            SPEED_MOV = abs(SPEED_MOV - 1)

        if keys[_pg.K_LEFT]:
            SPEED_ROT = abs(SPEED_ROT - 1)

        if keys[_pg.K_RIGHT]:
            SPEED_ROT += 1

        # Reset speeds
        if keys[_pg.K_ESCAPE]:
            SPEED_MOV = SPEED_ROT = _SPEED

    # Clear the SCREEN
    SCREEN.fill(COLOR_BLACK)

    # Draw all objects
    [obj.draw() for obj in DRAWABLES]

    # Update the stats & display
    show_stats()
    _pg.display.flip()

    # Time elapsed since previous render
    DELTA_TIME = CLOCK.tick(FPS_TARGET) / 1000

_pg.quit()
