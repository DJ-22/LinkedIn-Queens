import pygame

def visualize(grid, solution, colors, solve_time):
    n = len(grid)
    cell_size = 50
    width = n * cell_size
    height = n * cell_size

    pygame.init()
    pygame.display.set_caption(f"Colored Queens (Optimized - {solve_time:.5f}s)")
    
    screen = pygame.display.set_mode((width, height))
    font = pygame.font.SysFont(None, int(cell_size * 0.75))
    clock = pygame.time.Clock()
    queen_surface = font.render("Q", True, colors["black"])

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(colors["white"])

        for r in range(n):
            for c in range(n):
                color_name = grid[r][c]
                rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, colors.get(color_name, colors["white"]), rect)
                pygame.draw.rect(screen, colors["black"], rect, 2)

                if solution and solution[r][c]:
                    queen_Rect = queen_surface.get_rect(center=rect.center)
                    screen.blit(queen_surface, queen_Rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
