import pygame
import random
from collections import deque


def platform_gap(platform_1, platform_2):
    platform_1_left, platform_1_right = (platform_1["x"], platform_1["x"] + platform_1["w"])
    platform_2_left, platform_2_right = (platform_2["x"], platform_2["x"] + platform_2["w"])
    if platform_1_right < platform_2_left:
        return platform_2_left - platform_1_right
    if platform_2_right < platform_1_left:
        return platform_1_left - platform_2_right
    return 0


def can_reach(platform_1, platform_2, max_jump_gap):
    return platform_gap(platform_1, platform_2) <= max_jump_gap and (platform_2["row"] - platform_1["row"]) <= 1


def build_graph(nodes, max_jump_gap):
    graph = {n["id"]: [] for n in nodes}
    for i in nodes:
        for j in nodes:
            if i["id"] != j["id"] and can_reach(i, j, max_jump_gap):
                graph[i["id"]].append(j["id"])
    return graph


def bfs_all_reachable(graph, start, all_ids):
    visited = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for i in graph.get(cur, []):
            if i not in visited:
                visited.add(i)
                queue.append(i)
    return all([i in visited for i in all_ids])


def try_place_platforms(width, row_y, plat_widths, plat_h):
    rows = [random.randint(0, 2) for _ in range(6)]
    if 0 not in rows:
        rows[random.randint(0, 5)] = 0
    random.shuffle(rows)

    platforms = []
    for i, row in enumerate(rows):
        w = random.choice(plat_widths)
        placed = False
        for _ in range(40):
            x = random.randint(30, width - w - 30)
            cand = {"x": x, "y": row_y[row], "w": w, "h": plat_h, "row": row, "id": i + 1}
            if all(not (p["row"] == row and platform_gap(p, cand) < 15) for p in platforms):
                placed = True
                break
        if not placed:
            return None
        platforms.append(cand)
    return platforms


def generate_level(level_width, row_y, platform_widths, platform_height, ground_y, max_jump_gap):
    ground_node = {"id": 0, "x": 0, "w": level_width, "y": ground_y, "row": -1}

    for _ in range(300):
        candidate = try_place_platforms(level_width, row_y, platform_widths, platform_height)
        if candidate is None:
            continue
        nodes = [ground_node] + candidate
        graph = build_graph(nodes, max_jump_gap)
        if bfs_all_reachable(graph, 0, [i["id"] for i in candidate]):
            return candidate

    platforms = []
    row = 0
    x = 130
    for i in range(6):
        row = max(0, min(2, row + random.choice([-1, 0, 1])))
        platforms.append({"x": x, "y": row_y[row], "w": 100, "h": platform_height, "row": row, "id": i + 1})
        x += 120
    return platforms


def apply_physics(pos, vel, hb, size, dt, gravity, platforms, ground_y, width):
    old_bottom = hb.bottom
    vel.y += gravity * dt

    pos.x += vel.x * dt
    pos.x = max(0, min(pos.x, width - size[0]))
    hb.x = pos.x

    pos.y += vel.y * dt
    hb.y = pos.y

    on_ground = False
    for platform in platforms:
        platform_rect = pygame.Rect(platform["x"], platform["y"], platform["w"], platform["h"])
        overlap_x = hb.right > platform_rect.left and hb.left < platform_rect.right
        if overlap_x and vel.y >= 0 and old_bottom <= platform_rect.top + 1 and hb.bottom >= platform_rect.top:
            hb.bottom = platform_rect.top
            pos.y = hb.y
            vel.y = 0
            on_ground = True

    if hb.bottom >= ground_y:
        hb.bottom = ground_y
        pos.y = hb.y
        vel.y = 0
        on_ground = True

    return on_ground


def main():
    pygame.init()

    width, height = (800, 450)
    screen = pygame.display.set_mode((width, height))
    done = False
    clock = pygame.time.Clock()

    ground_y = height - 40
    row_y = [ground_y - 110, ground_y - 220, ground_y - 330]
    platform_widths = [70, 100, 140]
    platform_height = 20
    max_jump_gap = 150

    mario_size = (40, 60)
    mario_pos = pygame.Vector2(20, ground_y - mario_size[1])
    mario_vel = pygame.Vector2(0, 0)
    speed = 200
    jump = 500
    gravity = 1000
    mario_hb = pygame.Rect(mario_pos.x, mario_pos.y, mario_size[0], mario_size[1])
    mario_on_ground = True

    platforms = generate_level(width, row_y, platform_widths, platform_height, ground_y, max_jump_gap)

    while not done:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and mario_on_ground:
                    mario_vel.y = -jump
                    mario_on_ground = False

        keys = pygame.key.get_pressed()

        if mario_on_ground:
            mario_vel.x = 0
            if keys[pygame.K_d]:
                mario_vel.x = speed
            if keys[pygame.K_a]:
                mario_vel.x = -speed

        mario_on_ground = apply_physics(mario_pos, mario_vel, mario_hb, mario_size, dt, gravity, platforms, ground_y, width)

        screen.fill((255, 255, 255))
        pygame.draw.rect(screen, (90, 60, 30), (0, ground_y, width, height - ground_y))
        for platform in platforms:
            pygame.draw.rect(screen, (0, 0, 0), (platform["x"], platform["y"], platform["w"], platform["h"]))
        pygame.draw.rect(screen, (0, 0, 0), mario_hb)
        pygame.display.flip()


if __name__ == "__main__":
    main()