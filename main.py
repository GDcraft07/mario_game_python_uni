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


def generate_level(width, row_y, platform_widths, platform_height, ground_y, max_jump_gap):
    ground_node = {"id": 0, "x": 0, "w": width, "y": ground_y, "row": -1}
 
    platforms = None
    graph = None
    for _ in range(300):
        candidate = try_place_platforms(width, row_y, platform_widths, platform_height)
        if candidate is None:
            continue
        nodes = [ground_node] + candidate
        g = build_graph(nodes, max_jump_gap)
        if bfs_all_reachable(g, 0, [p["id"] for p in candidate]):
            platforms = candidate
            graph = g
            break
 
    if platforms is None:
        platforms = []
        row = 0
        x = 130
        for i in range(6):
            row = max(0, min(2, row + random.choice([-1, 0, 1])))
            platforms.append({"x": x, "y": row_y[row], "w": 100, "h": platform_height, "row": row, "id": i + 1})
            x += 120
        graph = build_graph([ground_node] + platforms, max_jump_gap)
 
    # выход ставим на платформу, до которой дальше всего идти - так интереснее, чем просто "последняя по счёту"
    dist = {0: 0}
    queue = deque([0])
    while queue:
        cur = queue.popleft()
        for nxt in graph.get(cur, []):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                queue.append(nxt)
    exit_plat = max(platforms, key=lambda p: dist.get(p["id"], 0))
 
    coins = []
    for p in platforms:
        if p["id"] != exit_plat["id"]:
            coins.append({"x": p["x"] + p["w"] // 2, "y": p["y"] - 25, "collected": False})
 
    exit_hb = pygame.Rect(exit_plat["x"] + exit_plat["w"] // 2 - 15, exit_plat["y"] - 30, 30, 30)
 
    return {"platforms": platforms, "coins": coins, "exit_hb": exit_hb}


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

    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 26)

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

    total_levels = 3
    level_index = 0
    state = 0

    level = generate_level(width, row_y, platform_widths, platform_height, ground_y, max_jump_gap)

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

        if state == 0:
            if mario_on_ground:
                mario_vel.x = 0
                if keys[pygame.K_d]:
                    mario_vel.x = speed
                if keys[pygame.K_a]:
                    mario_vel.x = -speed

            mario_on_ground = apply_physics(mario_pos, mario_vel, mario_hb, mario_size, dt, gravity, level["platforms"], ground_y, width)

            for coin in level["coins"]:
                coin_hb = pygame.Rect(coin["x"] - 10, coin["y"] - 10, 20, 20)
                if not coin["collected"] and mario_hb.colliderect(coin_hb):
                    coin["collected"] = True

            all_coins_collected = all(c["collected"] for c in level["coins"])
            if all_coins_collected and mario_hb.colliderect(level["exit_hb"]):
                level_index += 1
                if level_index >= total_levels:
                    state = 1
                else:
                    level = generate_level(width, row_y, platform_widths, platform_height, ground_y, max_jump_gap)
                    mario_pos = pygame.Vector2(20, ground_y - mario_size[1])
                    mario_vel = pygame.Vector2(0, 0)
                    mario_hb.x, mario_hb.y = mario_pos.x, mario_pos.y

        screen.fill((255, 255, 255))

        if state == 0:
            pygame.draw.rect(screen, (90, 60, 30), (0, ground_y, width, height - ground_y))
            for platform in level["platforms"]:
                pygame.draw.rect(screen, (0, 0, 0), (platform["x"], platform["y"], platform["w"], platform["h"]))
            for coin in level["coins"]:
                if not coin["collected"]:
                    pygame.draw.circle(screen, (240, 200, 40), (coin["x"], coin["y"]), 10)

            all_coins_collected = all(c["collected"] for c in level["coins"])
            exit_color = (40, 180, 40) if all_coins_collected else (120, 120, 120)
            pygame.draw.rect(screen, exit_color, level["exit_hb"])

            pygame.draw.rect(screen, (0, 0, 0), mario_hb)

            collected = sum(1 for c in level["coins"] if c["collected"])
            info = f"Уровень: {level_index + 1}/{total_levels}  Монеты: {collected}/{len(level['coins'])}"
            screen.blit(small_font.render(info, True, (0, 0, 0)), (10, 10))

        elif state == 1:
            text = font.render("ПОБЕДА!", True, (20, 120, 20))
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        pygame.display.flip()


if __name__ == "__main__":
    main()