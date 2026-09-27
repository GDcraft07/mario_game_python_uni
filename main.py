import pygame


def main():
    pygame.init()

    width, height = (800, 450)
    screen = pygame.display.set_mode((width, height))
    done = False
    clock = pygame.time.Clock()

    mario_size = (40, 60)
    mario_pos = pygame.Vector2(20, height - mario_size[1])
    mario_vel = pygame.Vector2(0, 0)
    speed = 200
    jump = 500
    gravity = 1000
    mario_hb = pygame.Rect(mario_pos.x, mario_pos.y, mario_size[0], mario_size[1])
    mario_on_ground = True

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

        mario_vel.y += gravity * dt

        mario_pos.x += mario_vel.x * dt
        mario_hb.x = mario_pos.x

        mario_pos.y += mario_vel.y * dt
        mario_hb.y = mario_pos.y

        mario_on_ground = False
        if mario_hb.bottom >= height:
            mario_hb.bottom = height
            mario_pos.y = mario_hb.y
            mario_vel.y = 0
            mario_on_ground = True

        screen.fill((255, 255, 255))
        pygame.draw.rect(screen, (0, 0, 0), mario_hb)
        pygame.display.flip()


if __name__ == "__main__":
    main()