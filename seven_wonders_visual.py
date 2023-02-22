import pygame
import pygetwindow as gw

class ImageDisplay:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.running = True

    def display_image(self, image_path):
        pygame.display.set_caption("7wonders")
        win = gw.getWindowsWithTitle("7wonders")[0]
        win.minimize()
        win.restore()
        img = pygame.image.load(image_path)
        self.screen.blit(img, (0, 0))
        pygame.display.update()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    self.running = False
        pygame.quit()
