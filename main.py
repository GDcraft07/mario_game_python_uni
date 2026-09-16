import pygame

def main():
    pygame.init()
    width, height = (600, 400)
    screen = pygame.display.set_mode((width, height))
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        screen.fill((255, 255, 255))
        pygame.display.flip()


if __name__ == "__main__":
    main()