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


def bfs_path(graph, start, goal):
    if start == goal:
        return [start]
    
    visited = {start}
    queue = deque([[start]])

    while queue:
        path = queue.popleft()

        for i in graph.get(path[-1], []):
            if i == goal:
                return path + [i]
            
            if i not in visited:
                visited.add(i)
                queue.append(path + [i])

    return None


def try_place_platforms(width, row_y, platform_widths, platform_height):
    rows = [random.randint(0, 2) for _ in range(6)]

    if 0 not in rows:
        rows[random.randint(0, 5)] = 0

    random.shuffle(rows)
    platforms = []

    for i, row in enumerate(rows):
        w = random.choice(platform_widths)
        placed = False

        for _ in range(40):
            x = random.randint(30, width - w - 30)
            cand = {"x": x, "y": row_y[row], "w": w, "h": platform_height, "row": row, "id": i + 1}
            
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

    for _ in range(300):
        candidate = try_place_platforms(width, row_y, platform_widths, platform_height)
    
        if candidate is None:
            continue
    
        nodes = [ground_node] + candidate
        graph = build_graph(nodes, max_jump_gap)
    
        if bfs_all_reachable(graph, 0, [i["id"] for i in candidate]):
            platforms = candidate
            break

    if platforms is None:
        platforms = []
        row = 0
        x = 130
    
        for i in range(6):
            row = max(0, min(2, row + random.choice([-1, 0, 1])))
            platforms.append({"x": x, "y": row_y[row], "w": 100, "h": platform_height, "row": row, "id": i + 1})
            x += 120

    nodes = [ground_node] + platforms
    graph = build_graph(nodes, max_jump_gap)

    dist = {0: 0}
    queue = deque([0])
    
    while queue:
        cur = queue.popleft()
    
        for i in graph.get(cur, []):
            if i not in dist:
                dist[i] = dist[cur] + 1
                queue.append(i)
    
    exit_plat = max(platforms, key=lambda x: dist.get(x["id"], 0))

    coins = []
    
    for platform in platforms:
        if platform["id"] != exit_plat["id"]:
            coins.append({"x": platform["x"] + platform["w"] // 2, "y": platform["y"] - 25, "collected": False})

    exit_hb = pygame.Rect(exit_plat["x"] + exit_plat["w"] // 2 - 15, exit_plat["y"] - 30, 30, 30)

    enemies = [{"pos": pygame.Vector2(width - 60, ground_y - 60), "vel": pygame.Vector2(random.choice([-120, 120]), 0), "hb": pygame.Rect(width - 60, ground_y - 60, 40, 60), "kind": "random", "on_ground": True, "node": 0}, {"pos": pygame.Vector2(width - 120, ground_y - 60), "vel": pygame.Vector2(0, 0), "hb": pygame.Rect(width - 120, ground_y - 60, 40, 60), "kind": "chase", "on_ground": True, "node": 0}]

    return {"platforms": platforms, "coins": coins, "exit_hb": exit_hb, "enemies": enemies, "nodes": nodes, "graph": graph}


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


def find_node(hb, on_ground, nodes, ground_y):
    if not on_ground:
        return None
    
    for i in nodes:
        if i["id"] == 0:
            continue

        if abs(hb.bottom - i["y"]) < 3 and hb.right > i["x"] and hb.left < i["x"] + i["w"]:
            return i["id"]
        
    if abs(hb.bottom - ground_y) < 3:
        return 0
    
    return None


def update_enemy_random(enemy, dt, gravity, jump_vel, platforms, ground_y, width, nodes):
    if random.random() < 0.02:
        enemy["vel"].x = random.choice([-160, -110, 0, 110, 160])

    if enemy["on_ground"] and random.random() < 0.01:
        enemy["vel"].y = jump_vel

    if enemy["hb"].x <= 0:
        enemy["vel"].x = abs(enemy["vel"].x) or 120

    if enemy["hb"].x >= width - enemy["hb"].w:
        enemy["vel"].x = -abs(enemy["vel"].x) or -120

    enemy["on_ground"] = apply_physics(enemy["pos"], enemy["vel"], enemy["hb"], (enemy["hb"].w, enemy["hb"].h), dt, gravity, platforms, ground_y, width)
    node = find_node(enemy["hb"], enemy["on_ground"], nodes, ground_y)

    if node is not None:
        enemy["node"] = node


def update_enemy_chase(enemy, dt, gravity, jump_vel, chase_speed, platforms, ground_y, width, nodes, graph, mario_x, mario_node):
    cur_node = next(n for n in nodes if n["id"] == enemy["node"])
    path = bfs_path(graph, enemy["node"], mario_node)
    next_id = path[1] if path and len(path) > 1 else enemy["node"]
    next_node = next(n for n in nodes if n["id"] == next_id)

    if next_id == enemy["node"] or next_id == 0:
        target_x = mario_x

    else:
        target_x = next_node["x"] + next_node["w"] / 2

    if target_x > enemy["hb"].centerx + 2:
        enemy["vel"].x = chase_speed

    elif target_x < enemy["hb"].centerx - 2:
        enemy["vel"].x = -chase_speed

    else:
        enemy["vel"].x = 0

    if enemy["on_ground"] and next_id != enemy["node"] and next_node["row"] >= cur_node["row"]:
        if cur_node["id"] == 0:
            near_edge = abs(enemy["hb"].centerx - target_x) < 40

        else:
            going_right = target_x > enemy["hb"].centerx
            edge_x = cur_node["x"] + cur_node["w"] if going_right else cur_node["x"]
            enemy_edge = enemy["hb"].right if going_right else enemy["hb"].left
            near_edge = abs(enemy_edge - edge_x) < 25

        if near_edge:
            enemy["vel"].y = jump_vel

    enemy["on_ground"] = apply_physics(enemy["pos"], enemy["vel"], enemy["hb"], (enemy["hb"].w, enemy["hb"].h), dt, gravity, platforms, ground_y, width)
    node = find_node(enemy["hb"], enemy["on_ground"], nodes, ground_y)

    if node is not None:
        enemy["node"] = node


def main():
    pygame.init()

    width, height = (800, 450)
    level_width = width * 2
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
    mario_node = 0

    lives = 3
    invuln_timer = 0.0
    invuln_time = 2.0
    chase_speed = 170
    enemy_jump_vel = -jump

    total_levels = 3
    level_index = 0
    state = 0
    camera_x = 0

    level = generate_level(level_width, row_y, platform_widths, platform_height, ground_y, max_jump_gap)

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

            mario_on_ground = apply_physics(mario_pos, mario_vel, mario_hb, mario_size, dt, gravity, level["platforms"], ground_y, level_width)
            node = find_node(mario_hb, mario_on_ground, level["nodes"], ground_y)
            
            if node is not None:
                mario_node = node

            camera_x = max(0, min(mario_pos.x - width / 2, level_width - width))

            if invuln_timer > 0:
                invuln_timer = max(0.0, invuln_timer - dt)

            for enemy in level["enemies"]:
                if enemy["kind"] == "random":
                    update_enemy_random(enemy, dt, gravity, enemy_jump_vel, level["platforms"], ground_y, level_width, level["nodes"])
                
                else:
                    update_enemy_chase(enemy, dt, gravity, enemy_jump_vel, chase_speed, level["platforms"], ground_y, level_width, level["nodes"], level["graph"], mario_pos.x, mario_node)

            for coin in level["coins"]:
                coin_hb = pygame.Rect(coin["x"] - 10, coin["y"] - 10, 20, 20)
                
                if not coin["collected"] and mario_hb.colliderect(coin_hb):
                    coin["collected"] = True

            if invuln_timer == 0:
                for enemy in level["enemies"]:
                    if mario_hb.colliderect(enemy["hb"]):
                        lives -= 1
                        invuln_timer = invuln_time
                        mario_vel.x = -speed * 2 if enemy["hb"].x > mario_hb.x else speed * 2
                        mario_vel.y = -300
                        
                        if lives <= 0:
                            state = 2
                        
                        break

            all_coins_collected = all(i["collected"] for i in level["coins"])
            if all_coins_collected and mario_hb.colliderect(level["exit_hb"]):
                level_index += 1

                if level_index >= total_levels:
                    state = 1

                else:
                    level = generate_level(level_width, row_y, platform_widths, platform_height, ground_y, max_jump_gap)
                    mario_pos = pygame.Vector2(20, ground_y - mario_size[1])
                    mario_vel = pygame.Vector2(0, 0)
                    mario_hb.x, mario_hb.y = mario_pos.x, mario_pos.y

        screen.fill((255, 255, 255))

        if state == 0:
            pygame.draw.rect(screen, (90, 60, 30), (0, ground_y, width, height - ground_y))
            
            for platform in level["platforms"]:
                pygame.draw.rect(screen, (0, 0, 0), (platform["x"] - camera_x, platform["y"], platform["w"], platform["h"]))
            
            for coin in level["coins"]:
                if not coin["collected"]:
                    pygame.draw.circle(screen, (240, 200, 40), (coin["x"] - camera_x, coin["y"]), 10)

            all_coins_collected = all(c["collected"] for c in level["coins"])
            exit_color = (40, 180, 40) if all_coins_collected else (120, 120, 120)
            exit_hb = level["exit_hb"]
            pygame.draw.rect(screen, exit_color, (exit_hb.x - camera_x, exit_hb.y, exit_hb.w, exit_hb.h))

            for enemy in level["enemies"]:
                color = (200, 40, 40) if enemy["kind"] == "random" else (150, 40, 180)
                pygame.draw.rect(screen, color, (enemy["hb"].x - camera_x, enemy["hb"].y, enemy["hb"].w, enemy["hb"].h))

            if invuln_timer == 0 or int(invuln_timer * 10) % 2 == 0:
                pygame.draw.rect(screen, (0, 0, 0), (mario_hb.x - camera_x, mario_hb.y, mario_hb.w, mario_hb.h))

            collected = sum(1 for c in level["coins"] if c["collected"])
            info = f"Уровень: {level_index + 1}/{total_levels}  Жизни: {lives}  Монеты: {collected}/{len(level['coins'])}"
            screen.blit(small_font.render(info, True, (0, 0, 0)), (10, 10))

        elif state == 1:
            text = font.render("ПОБЕДА!", True, (20, 120, 20))
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        elif state == 2:
            text = font.render("ТЫ ПРОИГРАЛ", True, (200, 40, 40))
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        pygame.display.flip()


if __name__ == "__main__":
    main()