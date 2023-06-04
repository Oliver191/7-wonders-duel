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

    def display_row(self, image_dict, selectable_dict, max_row):
        index = max_row
        num_rows = 1
        while len(image_dict[-1]) > num_rows * len(image_dict[index]) or len(image_dict[-2]) > num_rows * len(image_dict[index]):
            num_rows += 1
        self.screen = pygame.display.set_mode((self.width*len(image_dict[index]), self.height*num_rows))
        pygame.display.set_caption("7wonders")
        win = gw.getWindowsWithTitle("7wonders")[0]
        win.minimize()
        win.restore()
        win.move(-600,-250)
        combined_image = pygame.Surface((self.width*len(image_dict[index]), self.height*num_rows))
        for i in range(len(image_dict[index])):
            offset = (self.width / 2) * abs(len(image_dict[max_row]) - len(image_dict[index]))
            name = image_dict[index][i]
            if name != 'black':
                img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                combined_image.blit(img, ((self.width*i)+offset, 0))
                name = 'check' if selectable_dict[index][i] == 1 else 'cross'
                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                img = pygame.transform.scale(img, (44, 44))
                combined_image.blit(img, ((self.width*i)+offset, 0))
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
                    index = max(-2, min(index, len(image_dict) - 1 -2))
                    combined_image.fill((0, 0, 0))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
                    combined_image = pygame.Surface((self.width * len(image_dict[max_row]), self.height*num_rows))
                    for i in range(len(image_dict[index])):
                        name = image_dict[index][i]
                        if name != 'black' and index >= 0:
                            offset = (self.width / 2) * abs(len(image_dict[max_row]) - len(image_dict[index]))
                            img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                            combined_image.blit(img, ((self.width*i)+offset, 0))
                            name = 'check' if selectable_dict[index][i] == 1 else 'cross'
                            img = pygame.image.load(f"images\{name}.png").convert_alpha()
                            img = pygame.transform.scale(img, (44, 44))
                            combined_image.blit(img, ((self.width*i)+offset, 0))
                        elif index < 0:
                            j = self.get_multiple(len(image_dict[max_row]), i+1)
                            img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                            combined_image.blit(img, ((self.width * i) - (len(image_dict[max_row])*j*self.width), j*self.height))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
        pygame.quit()

    def get_multiple(self, max_value, value):
        multiple = 0
        while value > max_value:
            value -= max_value
            multiple += 1
        return multiple

    # def display_board(self, image_dict, selectable_dict, max_row):
    #     max_width = self.width * len(image_dict[max_row])
    #     max_height = (self.height/2) * len(image_dict) + (self.height/2)
    #     scale = 0.9 if len(image_dict) < 7 else 0.7
    #     self.screen = pygame.display.set_mode((max_width*scale, max_height*scale))
    #     pygame.display.set_caption("7wonders")
    #     win = gw.getWindowsWithTitle("7wonders")[0]
    #     win.minimize()
    #     win.restore()
    #     win.move(-400,-330)
    #     combined_image = pygame.Surface((max_width, max_height))
    #     for row in reversed(sorted(image_dict)):
    #         for i in range(len(image_dict[row])):
    #             offset = (self.width/2) * abs(len(image_dict[max_row])-len(image_dict[row]))
    #             name = image_dict[row][i]
    #             if name != 'black':
    #                 img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
    #                 combined_image.blit(img, ((self.width * i)+offset, (self.height/2) * (len(image_dict) - row - 1)))
    #                 name = 'check' if selectable_dict[row][i] == 1 else 'cross'
    #                 img = pygame.image.load(f"images\{name}.png").convert_alpha()
    #                 img = pygame.transform.scale(img, (44, 44))
    #                 combined_image.blit(img, ((self.width * i)+offset, (self.height/2) * (len(image_dict) - row - 1)))
    #     combined_image = pygame.transform.scale(combined_image, (max_width*scale, max_height*scale))
    #     self.screen.blit(combined_image, (0, 0))
    #     pygame.display.update()
    #     while self.running:
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
    #                 self.running = False
    #     pygame.quit()

    def display_board(self, image_dict, selectable_dict, max_row, age):
        image_dict2 = image_dict.copy()
        del image_dict2[-1]
        del image_dict2[-2]

        max_width = self.width * len(image_dict2[max_row])
        max_height = (self.height/2) * len(image_dict2) + (self.height/2)
        scale = 0.9
        self.screen = pygame.display.set_mode((max_width*scale, max_height*scale))
        pygame.display.set_caption("7wonders")
        win = gw.getWindowsWithTitle("7wonders")[0]
        win.minimize()
        win.restore()
        win.move(-620,-450)
        combined_image = self.board(max_width, max_height, image_dict2, selectable_dict, max_row, scale, age)
        self.screen.blit(combined_image, (0, 0))
        pygame.display.update()
        index = 0
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
                    index = max(-2, min(index, 0))
                    combined_image.fill((0, 0, 0))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
                    if index >= 0:
                        self.screen = pygame.display.set_mode((max_width * scale, max_height * scale))
                        combined_image = self.board(max_width, max_height, image_dict2, selectable_dict, max_row, scale, age)
                    elif index < 0:
                        multiple = self.get_multiple(7, len(image_dict[index]))
                        pygame.display.set_caption("Player " + str(abs(index)))
                        self.screen = pygame.display.set_mode((self.width * min(len(image_dict[index]), 7), self.height * (multiple+1)))
                        combined_image = pygame.Surface((self.width * min(len(image_dict[index]), 7), self.height * (multiple+1)))
                        for i in range(len(image_dict[index])):
                            name = image_dict[index][i]
                            j = self.get_multiple(7, i + 1)
                            img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                            combined_image.blit(img, (
                                (self.width * i) - (7 * j * self.width), j * self.height))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
        pygame.quit()

    def board(self, max_width, max_height, image_dict2, selectable_dict, max_row, scale, age):
        pygame.display.set_caption("Age " + str(age+1) + " Board")
        combined_image = pygame.Surface((max_width, max_height))
        for row in reversed(sorted(image_dict2)):
            for i in range(len(image_dict2[row])):
                offset = (self.width/2) * abs(len(image_dict2[max_row])-len(image_dict2[row]))
                name = image_dict2[row][i]
                if name != 'black':
                    img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                    combined_image.blit(img, ((self.width * i)+offset, (self.height/2) * (len(image_dict2) - row - 1)))
                    name = 'check' if selectable_dict[row][i] == 1 else 'cross'
                    img = pygame.image.load(f"images\{name}.png").convert_alpha()
                    img = pygame.transform.scale(img, (44, 44))
                    combined_image.blit(img, ((self.width * i)+offset, (self.height/2) * (len(image_dict2) - row - 1)))
        combined_image = pygame.transform.scale(combined_image, (max_width*scale, max_height*scale))
        return combined_image