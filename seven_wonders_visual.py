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

    def display_row(self, image_dict, max_row):
        index = max_row
        self.screen = pygame.display.set_mode((self.width*len(image_dict[index]), self.height))
        pygame.display.set_caption("7wonders")
        win = gw.getWindowsWithTitle("7wonders")[0]
        win.minimize()
        win.restore()
        win.move(-600,0)
        combined_image = pygame.Surface((self.width*len(image_dict[index]), self.height))
        for i in range(len(image_dict[index])):
            name = image_dict[index][i]
            img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
            combined_image.blit(img, (self.width*i, 0))
        self.screen.blit(combined_image, (0, 0))
        pygame.display.update()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        index += 1
                    elif event.key == pygame.K_s:
                        index -= 1
                    else:
                        self.running = False
            index = max(0, min(index, len(image_dict) - 1))
            combined_image.fill((0, 0, 0))
            self.screen.blit(combined_image, (0, 0))
            combined_image = pygame.Surface((self.width * len(image_dict[index]), self.height))
            for i in range(len(image_dict[index])):
                name = image_dict[index][i]
                img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                combined_image.blit(img, (self.width * i, 0))
            self.screen.blit(combined_image, (0, 0))
            pygame.display.update()
        pygame.quit()
