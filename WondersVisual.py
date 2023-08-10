import pygame
import pygetwindow as gw

class ImageDisplay:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.running = True

    def get_multiple(self, max_value, value):
        multiple = 0
        while value > max_value:
            value -= max_value
            multiple += 1
        return multiple

    def display_board(self, image_dict, selectable_dict, max_row, age, military_conflict, m_tokens, coins, p_tokens, p_tokens_in_play, wonders):
        pygame.font.init()

        image_dict2 = image_dict.copy()
        del image_dict2[-1]
        del image_dict2[-2]

        max_width = self.width * len(image_dict2[max_row])
        max_height = (self.height/2) * len(image_dict2) + (self.height/2)
        scale = 0.9
        self.screen = pygame.display.set_mode((max_width*scale* 0.7, max_height*scale* 0.7))
        pygame.display.set_caption("7wonders")
        win = gw.getWindowsWithTitle("7wonders")[0]
        win.minimize()
        win.restore()
        win.move(-620,-300)
        combined_image = self.board(max_width, max_height, image_dict2, selectable_dict, max_row, scale, age)
        current_width, current_height = combined_image.get_size()
        combined_image = pygame.transform.smoothscale(combined_image, (int(current_width * 0.7), int(current_height * 0.7)))
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
                    index = max(-2, min(index, 1))
                    combined_image.fill((0, 0, 0))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
                    if index == 0:
                        self.screen = pygame.display.set_mode((max_width * scale * 0.7, max_height * scale * 0.7))
                        combined_image = self.board(max_width, max_height, image_dict2, selectable_dict, max_row, scale, age)
                    elif index > 0:
                        pygame.display.set_caption("Military & Science Board")
                        names = ["board", "military5", "military2", "conflict"]
                        self.screen = pygame.display.set_mode((1639 * 0.7, 490 * 0.7))
                        combined_image = pygame.image.load(f"images\{names[0]}.png").convert_alpha()
                        img = pygame.image.load(f"images\{names[1]}.png").convert_alpha()
                        img = pygame.transform.smoothscale(img, (200, 90))
                        if m_tokens[0] == 0: combined_image.blit(img, (170, 350))
                        if m_tokens[3] == 0: combined_image.blit(img, (1265, 350))
                        img = pygame.image.load(f"images\{names[2]}.png").convert_alpha()
                        img = pygame.transform.smoothscale(img, (180, 80))
                        if m_tokens[1] == 0: combined_image.blit(img, (420, 355))
                        if m_tokens[2] == 0: combined_image.blit(img, (1044, 355))
                        img = pygame.image.load(f"images\{names[3]}.png").convert_alpha()
                        img = pygame.transform.smoothscale(img, (75, 200))
                        combined_image.blit(img, (780+(military_conflict*78), 185))

                        for i in range(len(p_tokens)):
                            if p_tokens[i].token_in_slot:
                                name = p_tokens[i].token_name
                                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                                img = pygame.transform.smoothscale(img, (160, 160))
                                combined_image.blit(img, (405 + 165 * i, 24))

                        img = pygame.font.Font(None, 60)
                        text_surface = img.render("City Player 1", True, (255, 255, 255))
                        combined_image.blit(text_surface, (100, 100))
                        text_surface = img.render("City Player 2", True, (255, 255, 255))
                        combined_image.blit(text_surface, (1280, 100))
                    elif index < 0:
                        # multiple = self.get_multiple(7, len(image_dict[index]))
                        types = ['Brown', 'Grey', 'Blue', 'Red', 'Green', 'Yellow', 'Purple']
                        type_count = [0,0,0,0,0,0,0]
                        multiple = self.get_type_count(image_dict, selectable_dict, index)
                        pygame.display.set_caption("Player " + str(abs(index)))
                        self.screen = pygame.display.set_mode(((7*self.width + self.height + 50) * 0.7, max(4*self.width, 150 + self.height + max(0,multiple -1) * 85) * 0.7))
                        combined_image = pygame.Surface((7*self.width + self.height + 50, max(4*self.width, 150 + self.height + max(0,multiple-1) * 85)))
                        img = pygame.font.Font(None, 60)
                        text_surface = img.render("Player " + str(abs(index)) + " -> Coins: " + str(coins[index]) + ', Tokens: ', True, (255, 255, 255))
                        combined_image.blit(text_surface, (0, 50))

                        for i in range(len(p_tokens_in_play[index])):
                            name = p_tokens_in_play[index][i].token_name
                            img = pygame.image.load(f"images\{name}.png").convert_alpha()
                            img = pygame.transform.smoothscale(img, (140, 140))
                            combined_image.blit(img, (600 + 145 * i, 0))

                        for i in range(len(types)):
                            img = pygame.image.load(f"images\{types[i]}.jpg").convert_alpha()
                            combined_image.blit(img, (
                                self.width * i, 150))

                        for i in range(len(image_dict[index])):
                            name = image_dict[index][i]
                            type_index = types.index(selectable_dict[index][i])
                            # j = self.get_multiple(7, i + 1)
                            img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                            # combined_image.blit(img, (
                            #     (self.width * i) - (7 * j * self.width), 150 + j * self.height))
                            combined_image.blit(img, (
                                self.width * type_index, 150 + type_count[type_index] * 85))
                            type_count[type_index] += 1

                        for i in range(len(wonders[index][0])):
                            if wonders[index][0][i] in wonders[index][1]:
                                name = 'age1back'
                                img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
                                img = pygame.transform.rotate(img, 90)
                                img = pygame.transform.smoothscale(img, (self.height*0.75, self.width*0.75))
                                combined_image.blit(img, (7 * self.width  + 125, self.width * i + 29))
                            if wonders[index][0][i] in wonders[index][1] or not wonders[index][0][i].wonder_in_play:
                                name = wonders[index][0][i].wonder_name
                                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                                img = pygame.transform.smoothscale(img, (self.height, self.width))
                                combined_image.blit(img, (7*self.width, self.width*i))

                    current_width, current_height = combined_image.get_size()
                    combined_image = pygame.transform.smoothscale(combined_image, (int(current_width * 0.7), int(current_height * 0.7)))
                    self.screen.blit(combined_image, (0, 0))
                    pygame.display.update()
        pygame.quit()

    def get_type_count(self, image_dict, selectable_dict, index):
        types = ['Brown', 'Grey', 'Blue', 'Red', 'Green', 'Yellow', 'Purple']
        type_count = [0, 0, 0, 0, 0, 0, 0]
        for i in range(len(image_dict[index])):
            type_index = types.index(selectable_dict[index][i])
            type_count[type_index] += 1
        multiple = max(type_count)
        return multiple

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
                    img = pygame.transform.smoothscale(img, (44, 44))
                    combined_image.blit(img, ((self.width * i)+offset, (self.height/2) * (len(image_dict2) - row - 1)))
        combined_image = pygame.transform.smoothscale(combined_image, (max_width*scale, max_height*scale))
        return combined_image

    def display_wonder(self, remaining_wonders, selectable, shift, p1_wonders, p2_wonders):
        pygame.display.set_caption("Draft Wonders")
        win = gw.getWindowsWithTitle("Draft Wonders")[0]
        win.minimize()
        win.restore()
        win.move(-620, -300)
        self.screen = pygame.display.set_mode((4 * self.height, 4 * self.width))
        combined_image = pygame.Surface((4 * self.height, 4 * self.width))

        for i in range(len(remaining_wonders)):
            if selectable[i+shift]:
                name = remaining_wonders[i].wonder_name
                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                img = pygame.transform.smoothscale(img, (self.height, self.width))
                combined_image.blit(img, (self.height*i, 0))

        for wonders, j in zip([p1_wonders, p2_wonders], [2,3]):
            for i in range(len(wonders)):
                name = wonders[i].wonder_name
                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                img = pygame.transform.smoothscale(img, (self.height, self.width))
                combined_image.blit(img, (self.height * i, j * self.width))

        self.screen.blit(combined_image, (0, 0))
        pygame.display.update()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    self.running = False
        pygame.quit()

    def display_cards(self, cards, print_object):
        pygame.display.set_caption("Pick a " + print_object)
        win = gw.getWindowsWithTitle("Pick a " + print_object)[0]
        win.minimize()
        win.restore()
        win.move(-620, -300)
        multiple = self.get_multiple(7, len(cards))
        self.screen = pygame.display.set_mode(((min(7, len(cards)) * self.width)*0.7, (1+multiple) * self.height*0.7))
        combined_image = pygame.Surface((min(7, len(cards)) * self.width, (1+multiple) * self.height))

        for i in range(len(cards)):
            j = self.get_multiple(7, i + 1)
            if print_object == 'Card':
                name = cards[i].card_name.replace(" ", "").lower()
                img = pygame.image.load(f"images\{name}.jpg").convert_alpha()
            elif print_object == 'Token':
                name = cards[i].token_name
                img = pygame.image.load(f"images\{name}.png").convert_alpha()
                img = pygame.transform.smoothscale(img, (140, 140))
            combined_image.blit(img, (self.width * (i - 7*j), j * self.height))

        current_width, current_height = combined_image.get_size()
        combined_image = pygame.transform.smoothscale(combined_image,(int(current_width * 0.7), int(current_height * 0.7)))
        self.screen.blit(combined_image, (0, 0))
        pygame.display.update()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    self.running = False
        pygame.quit()