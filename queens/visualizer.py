import pygame


def visualize(grid, solution, colors, solve_time):
    n = len(grid)
    cell_size = 50
    width = n * cell_size
    height = n * cell_size

    pygame.init()
    try:
        pygame.display.set_caption(f"Colored Queens (Optimized - {solve_time:.5f}s)")

        screen = pygame.display.set_mode((width, height))
        font = pygame.font.SysFont(None, int(cell_size * 0.75))
        queen_surface = font.render("Q", True, colors["black"])

        for r in range(n):
            for c in range(n):
                color_name = grid[r][c]
                rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, colors[color_name], rect)
                pygame.draw.rect(screen, colors["black"], rect, 2)

                if solution[r][c]:
                    queen_rect = queen_surface.get_rect(center=rect.center)
                    screen.blit(queen_surface, queen_rect)

        pygame.display.flip()

        running = True
        while running:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEOEXPOSE:
                pygame.display.flip()
    finally:
        pygame.quit()
