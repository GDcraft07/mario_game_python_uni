import pygame


def main():
    pygame.init()

    width, height = (800, 450)
    screen = pygame.display.set_mode((width, height))
    done = False
    clock = pygame.time.Clock()

    mario_size = (40, 60)
    mario_pos = pygame.Vector2(0, height - mario_size[1])
    mario_victor = pygame.Vector2(0, 0)
    speed = 200
    jump = 500
    gravity = 1000
    matio_hb = pygame.Rect(mario_pos.x, mario_pos.y, mario_size[0], mario_size[1])

    platforms = [pygame.Rect(300, height - 100, 200, 30), pygame.Rect(100, height - 200, 200, 30), pygame.Rect(0, height - 300, 150, 30)]

    while not done:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mario_victor.y = -jump

        keys = pygame.key.get_pressed()

        mario_victor.x = 0

        if keys[pygame.K_d]:
            mario_victor.x = speed

        if keys[pygame.K_a]:
            mario_victor.x = -speed

        mario_victor.y += gravity * dt

        mario_pos.x += mario_victor.x * dt
        matio_hb.x = mario_pos.x

        mario_pos.y += mario_victor.y * dt
        matio_hb.y = mario_pos.y

        if matio_hb.y + mario_size[1] >= height:
            matio_hb.y = height - mario_size[1]
            mario_pos.y = matio_hb.y
            mario_victor.y = 0

        screen.fill((255, 255, 255))

        for platform in platforms:
            pygame.draw.rect(screen, (0, 0, 0), platform)

        pygame.draw.rect(screen, (0, 0, 0), matio_hb)

        pygame.display.flip()


if __name__ == "__main__":
    main()