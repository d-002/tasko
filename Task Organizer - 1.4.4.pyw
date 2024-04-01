VERSION = '1.4.4'

""" Modules to import via pip:
    - pillow
    - pystray
    - pygame
    - pywin32
"""

try:
    import os
    import sys
    import glob
    import win32api
    import win32con
    import win32gui
    import pystray
    import pygame

    from pygame.locals import *
    from urllib.request import *

    from PIL import Image
    from threading import Thread
    from math import cos, sin, pi
    from socket import gethostbyname, gethostname

except ModuleNotFoundError as error:
    from tkinter import Tk
    from tkinter.messagebox import showerror

    name = str(error).split("'")[1]
    if name == 'PIL':
        name = 'pillow'
    elif name.startswith('win32'):
        name = 'pywin32'

    tk = Tk()
    tk.title('Erreur d\'importation')
    tk.wm_attributes('-alpha', 0)
    showerror('Erreur d\'importation', 'Ce programme requiert le module %s.\nTéléchargez-le depuis PyPI' %name)
    tk.destroy()
    exit()

def quit():
    tray.stop()
    pygame.quit()
    sys.exit()

class Colors:
    def __init__(self):
        self.palettes = [{'name': 'Original', # name of the color palette
                          'blocks': [(255, 50, 0), (255, 210, 10), (50, 255, 0)],
                          'black': (0, 0, 0),
                          'dark': (23, 23, 23),
                          'grey': (49, 49, 49),
                          'light': (150, 150, 150),
                          'white': (220, 220, 220),
                          'red': (222, 80, 44)},

                         {'name': 'Light',
                          'blocks': [(255, 0, 0), (255, 185, 38), (0, 127, 39)],
                          'black': (200, 200, 200),
                          'dark': (255, 255, 255),
                          'grey': (236, 236, 236),
                          'light': (105, 105, 105),
                          'white': (35, 35, 35),
                          'red': (255, 0, 0)},

                         {'name': 'Feu',
                          'blocks': [(252, 57, 0), (255, 182, 11), (191, 255, 0)],
                          'black': (0, 0, 0),
                          'dark': (33, 14, 14),
                          'grey': (67, 46, 31),
                          'light': (177, 155, 122),
                          'white': (248, 234, 192),
                          'red': (255, 66, 11)},

                         {'name': 'Stack Overfl.',
                          'blocks': [(209, 166, 132), (180, 184, 188), (255, 204, 1)],
                          'black': (9, 8, 13),
                          'dark': (34, 36, 38),
                          'grey': (57, 57, 57),
                          'light': (188, 187, 187),
                          'white': (255, 255, 255),
                          'red': (244, 128, 36)},

                         {'name': 'Opera GX',
                          'blocks': [(250, 30, 78), (221, 60, 160), (169, 112, 255)],
                          'black': (9, 8, 13),
                          'dark': (18, 16, 25),
                          'grey': (37, 31, 31),
                          'light': (140, 125, 176),
                          'white': (255, 255, 255),
                          'red': (250, 30, 78)},

                         {'name': 'Windows',
                          'blocks': [(0, 57, 209), (0, 150, 241), (0, 214, 247)],
                          'black': (0, 0, 0),
                          'dark': (25, 25, 25),
                          'grey': (32, 32, 32),
                          'light': (150, 150, 200),
                          'white': (255, 255, 255),
                          'red': (255, 255, 255)}]

        self.set_palette(0) # default color palette

    def set_palette(self, palette):
        self.palette = palette
        for var, value in self.palettes[palette].items():
            if var != 'name':
                setattr(self, var, value) # set every color

class Block:
    def __init__(self, text, zone):
        self.start_drag = None
        self.hover_index = 0 # where the block will be inserted
        self.text = text
        self.zone = zone # red, orange or green
        if len(blocks):
            self.zoneindex = len(blocks[self.zone])
        else:
            self.zoneindex = 0

        # generate surfaces now to optimise
        text = separate(self.text)
        size = (200, 12 + 18*len(text))
        self.rect = Rect((0, 0), size)
        if type(self) == Todo:
            self.images = [0]*7
            # red, yellow, green, red hover, yellow hover, green hover, dragged
            for x in range(3):
                surf = pygame.Surface(size, SRCALPHA)
                round_rect(surf, colors.dark, size)
                self.images[x] = surf.copy()

                round_rect(surf, lighten(colors.dark), size)
                self.images[x+3] = surf
                    
            surf = pygame.Surface((size[0]+5, size[1]+5), SRCALPHA)
            shadow = pygame.Surface(size, SRCALPHA)
            shadow.set_alpha(100)
            round_rect(shadow, colors.black, size)
            surf.blit(shadow, (5, 5))
            round_rect(surf, colors.dark, size)
            self.images[6] = surf
        else:
            self.images = []
            # normal, hover
            surf = pygame.Surface(size, SRCALPHA)
            round_rect(surf, colors.light, size)
            self.images.append(surf.copy())
            round_rect(surf, lighten(colors.light), size)
            self.images.append(surf)

        # draw text on top
        if type(self) == Todo:
            for image in range(7):
                if image == 6:
                    color = colors.light
                else:
                    color = colors.blocks[image%3]
                for y in range(len(text)):
                    self.images[image].blit(font.render(text[y], 1, color), (7, 7 + 18*y))
        else:
            for image in self.images:
                image.blit(font.render(text[0], 1, colors.dark), (7, 7))

    def height(self, index):
        # all blocks do not have the same height
        return 80-scroll.scroll[self.zone] + sum([block.rect.height+10 for block in blocks[self.zone][:index]])

    def draw(self, x, size):
        global obj_hover
        if self.rect.collidepoint(pygame.mouse.get_pos()) or self in blocks[-1]:
            obj_hover = 1 # show hand cursor

        y = self.height(self.zoneindex)

        # make some space for a potential hovering block
        for block in blocks[-1]:
            if self.zone == opened and block.hover_index <= self.zoneindex:
                y += block.rect.height+10

        self.rect = Rect((x, y), size)
        if type(self) == Todo:
            image = self.images[self.zone + 3*hover(self.rect)]
        else:
            image = self.images[hover(self.rect)]

        if size[0] == 200:
            screen.blit(image, (self.rect.x, self.rect.y))
        else:
            right_side = pygame.Surface((8, size[1]), SRCALPHA)
            right_side.blit(image, (8-image.get_width(), 0))
            surf = pygame.Surface(size, SRCALPHA)
            surf.blit(image, (0, 0)) # cut the Surface if too large
            pygame.draw.rect(surf, (0, 0, 0, 0), Rect((size[0]-8, 0), (8, size[1])))
            surf.blit(right_side, (size[0]-8, 0))
            screen.blit(surf, (self.rect.x, self.rect.y))

    def update(self):
        y = self.height(self.zoneindex)
        h = 12 + 18*len(separate(self.text))
        if -h <= y <= 300: # only update if visible
            if opened == self.zone:
                x, size = 10 + 90*self.zone, (200, h)
            elif self.zone > opened:
                x, size = 130 + 90*self.zone, (80, h)
            else:
                x, size = 10 + 90*self.zone, (80, h)

            self.draw(x, size)

            # cross to delete the block
            if type(self) == Todo:
                if self.rect.collidepoint(pygame.mouse.get_pos()):
                    screen.blit(cross, (x+175, y+5))

class Todo(Block):
    def __init__(self, text, zone):
        Block.__init__(self, text, zone)
        self.text = text

    def update(self):
        if self.start_drag:
            mousex, mousey = pygame.mouse.get_pos()
            x = self.rect.x+mousex-self.start_drag[0]
            y = self.rect.y+mousey-self.start_drag[1]

            # define the height where the block will be dropped
            y_ = 80-scroll.scroll[opened]
            self.hover_index = 0
            for index in range(len(blocks[opened])+1):
                if index == len(blocks[opened]):
                    self.hover_index = index-1
                    break # at the end, but no block collided
                if y + self.rect.height/2 < y_ + blocks[opened][index].rect.height/2:
                    self.hover_index = index
                    break
                y_ += blocks[opened][index].rect.height+10
            if y > sum([block.rect.height+10 for block in blocks[opened]]):
                self.hover_index = len(blocks[opened])-1 # even more to the bottom

            screen.blit(self.images[6], (x, y))
        else:
            Block.update(self)

class Add(Block):
    def __init__(self, zone):
        Block.__init__(self, 'Ajouter', zone)

    def click(self):
        add_button = Button('Ajouter', (125, 230))
        cancel_button = Button('Annuler', (275, 230))
        entry = Entry((75, 100))
        while True:
            events = pygame_events()
            pressed = pygame.key.get_pressed()
            action = None
            for event in events:
                if event.type == MOUSEBUTTONDOWN:
                    if add_button.click(events):
                        action = 1
                    if cancel_button.click(events):
                        action = 2

            if action == 1 or pressed[K_RETURN] or pressed[K_KP_ENTER]:
                blocks[self.zone].insert(0, Todo(entry.text, self.zone))
                blocks[self.zone][0].zoneindex = 0
                for block in blocks[self.zone][1:]:
                    block.zoneindex += 1
                scroll.goal[opened] = 0
                scroll.start_time[opened] = ticks() # initiate movement to the top
                return
            if action == 2 or pressed[K_ESCAPE]:
                return

            screen.blit(background2, (0, 0))
            screen.blit(font.render('Ajouter un objet', 1, colors.light), (75, 50))
            entry.update(events)
            entry.draw()
            add_button.draw()
            cancel_button.draw()
            close_button(events)

            flip()

class Button:
    def __init__(self, text, pos, align=1):
        self.images = [] # generate them now to optimise
        self.text = text # str (used by init_surfs)
        text = font.render(text, 1, colors.grey) # surface
        textw, h = text.get_size()
        w = max(textw, 100) # minimum width
        self.rect = Rect(*pos, w+10, h+10)
        self.align = align
        self.rect.x -= align * (w//2 + 5)
        self.rect.y -= align * (h//2 + 5)

        surf = pygame.Surface((w+10, h+10), SRCALPHA)
        round_rect(surf, colors.light, (w+10, h+10))
        self.images.append(surf.copy())
        round_rect(surf, lighten(colors.light), (w+10, h+10))
        self.images.append(surf)

        for image in self.images:
            image.blit(text, (5 + w//2 - textw//2, 5))

        # only used when changing text
        self.pos = pos

    def change_text(self, text):
        self.__init__(text, self.pos, self.align)

    def draw(self):
        global obj_hover
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            obj_hover = 1

        screen.blit(self.images[hover(self.rect, True)], (self.rect.x, self.rect.y))

    def click(self, events):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            for event in events:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    return True
        return False

class Entry:
    def __init__(self, pos, catch=None): # syntax of catch: [(KEY, function), ...]
        self.rect = Rect(*pos, 200, 30)
        self.text = ''
        self.selected = True

        if catch is None:
            catch = [] # avoid using a mutable default argument
        catch.extend([(K_RETURN, lambda: 1), (K_KP_ENTER, lambda: 1), (K_BACKSPACE, self.backspace)])
        self.keys_caught = [key for key, f in catch]
        self.functions = [f for key, f in catch]

    def backspace(self):
        self.text = self.text[:-1]

    def update(self, events):
        global obj_hover
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            obj_hover = 2 # show ibeam cursor

        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # select entry and reset blink
                    self.selected = self.rect.collidepoint(event.pos)*(ticks()+500)
            elif event.type == KEYDOWN:
                if self.selected:
                    self.selected = ticks()+500 # reset blink

                    if event.key in self.keys_caught:
                        self.functions[self.keys_caught.index(event.key)]()
                    else:
                        if len(separate(self.text)) <= 3 and event.unicode != '^' and \
                           font.render(self.text.split(' ')[-1]+' ', 1, colors.light).get_width() < 186:
                            self.text += event.unicode
                        if len(separate(self.text)) > 3: # check after adding a character
                            self.text = self.text[:-1]

    def draw(self):
        text = separate(self.text)
        self.rect.height = 12 + len(text)*18
        round_rect(screen, colors.grey, self.rect)
        # display a blinking cursor if focused
        if ((ticks()-self.selected)//333%3 and self.selected):
            text[-1] += '_'
        for y in range(len(text)):
            screen.blit(font.render(text[y], 1, colors.light), (self.rect.x+7, self.rect.y + 7 + y*18))

class Scroll: # smooth scroll
    def __init__(self, speed):
        self.start = [0, 0, 0]
        self.goal = [0, 0, 0]
        self.start_time = [0, 0, 0]
        self.movement = [0, 0, 0]
        self.speed = speed

        self.scroll = [0, 0, 0]

    def update(self, events):
        for zone in range(3):
            height = sum([block.rect.height+10 for block in blocks[zone]])
            if height < 220:
                self.scroll[zone] = 0
                continue

            if zone == opened:
                for event in events:
                    if event.type == MOUSEWHEEL:
                        self.start_time[zone] = ticks()
                        self.start[zone] = self.scroll[zone]

                        self.goal[zone] -= event.y*50

            self.goal[zone] = min(max(self.goal[zone], 0), height - 220)

            progress = (ticks()-self.start_time[zone]) * self.speed / 1000 # from 0 to 1
            if progress < 1:
                f = 0.4 + 0.6 * sin(pi * (progress - 2/7) / 1.4)
                self.scroll[zone] = self.start[zone] + (self.goal[zone]-self.start[zone]) * f
            else: # movement done
                self.scroll[zone] = self.start[zone] = self.goal[zone]

def separate(text):
    text = text.split(' ')
    lines = ['']
    while text:
        if font.render(lines[-1]+text[0], 1, colors.light).get_width() > 186:
            lines.append(text[0] + ' ')
        else:
            lines[-1] += text[0] + ' '
        text.pop(0)
    lines[-1] = lines[-1][:-1]
    return lines

def hover(rect, force=False):
    x, y = pygame.mouse.get_pos()
    return rect.collidepoint((x, y)) and (y >= 40 or force) and not pygame.mouse.get_pressed()[0]

def lighten(color):
    return (min(color[0]+20, 255), min(color[1]+20, 255), min(color[2]+20, 255))

def round_rect(surf, color, size):
    if type(size) == Rect:
        x, y, w, h = size.x, size.y, size.width, size.height
    else:
        x = y = 0
        w, h = size
    pygame.draw.rect(surf, color, Rect((x+10, y), (w-20, h)))
    pygame.draw.rect(surf, color, Rect((x, y+10), (w, h-20)))
    for x_, y_ in [(10, 10), (w-10, 10), (10, h-10), (w-10, h-10)]:
        pygame.draw.circle(surf, color, (x+x_, y+y_), 10)

def save():
    data = ''
    for group in blocks[:-1]: # do not count the moving block
        for block in group:
            if type(block) == Todo: # do not save the Add button
                data += block.text + '\n'
        if not len(group)-1:
            data += '\n'
        data += '\n' # separate columns with blank lines
    with open('files\\%s.txt' %save_file, 'wb') as f:
        f.write(data[:-2].encode()) # save in binary in case of special characters
    with open('files\\last', 'wb') as f:
        f.write(save_file.encode())
    save_settings()

def save_settings():
    with open('files\\settings', 'w') as f:
        f.write('%d\n%d\n%d' %(window_position, colors.palette, start_as))

def load_settings():
    global window_position, start_as

    if os.path.exists('files\\settings'):
        with open('files\\settings') as f:
            content = f.read().split('\n')
        try:
            window_position = int(content[0])
            colors.set_palette(int(content[1]))
            start_as = int(content[2])
        except: # stopped if the settings aren't long enough
            pass # leave the next settings as default

def readfile():
    global blocks
    blocks = [[], [], [], []] # last cell is for the moving block
    with open('files\\%s.txt' %save_file, 'rb') as f:
        groups = f.read().decode().split('\n\n')
    for x in range(3):
        for block in groups[x].split('\n'):
            if len(groups[x]) > 1 or block: # non-empty zone
                blocks[x].append(Todo(block, x))
        blocks[x].append(Add(x))

def update_title():
    global top_background
    top_background = pygame.Surface((400, 80))
    top_background.blit(top_background_empty, (0, 0))

    text = font.render(save_file, True, colors.white)
    top_background.blit(text, (130, 15))

def choose_file(start=False):
    global save_file, blocks, obj_hover

    def auto_complete():
        for path in sorted(glob.glob('files\\*.txt')):
            file = os.path.splitext(os.path.basename(path))[0]
            if file.startswith(filename.text):
                filename.text = file
                return

    filename = Entry((30, 70), [(K_TAB, auto_complete)])
    filename_btn = Button('Ouvrir', (250, 70), 0)
    settings_btn = Button('Réglages', (250, 10), 0)

    if start: # when launching, automatically open the last file if it exists
        if os.path.exists('files\\last'):
            with open('files\\last', 'rb') as f: # prefill with the last opened file
                save_file = f.read().decode()

        readfile()
        update_title()
        return

    while True:
        events = pygame_events()
        filename.update(events)

        exists = os.path.exists('files\\%s.txt' %filename.text)
        if exists:
            text = 'Ouvrir un fichier existant :'
            filename_btn.change_text('Ouvrir')
        else:
            text = 'Créer un nouveau fichier :'
            filename_btn.change_text('Créer')

        screen.blit(background2, (0, 0))
        screen.blit(font.render(text, 1, colors.light), (30, 40))
        filename.draw()
        filename_btn.draw()
        settings_btn.draw()
        close_button(events)

        if (True in [char in filename.text for char in '\/:*?"<>|']
            or not len(filename.text.strip()) or filename.text.strip() != filename.text):
            screen.blit(font.render('Le nom de fichier est invalide.', 1, colors.red), (30, 105))
            invalid = True
        else:
            invalid = False

        screen.blit(font.render('Fichiers pertinents :', 1, colors.light), (30, 130))
        y = 160
        files = [os.path.splitext(os.path.basename(path))[0] for path in sorted(glob.glob('files\\*.txt'))]
        files = [path for path in files if path.startswith(filename.text)]
        if len(files) > 6: # max 6 lines
            files = files[:5] + ['...'] # too much files to show

        select_suggestion = False
        for path in files:
            text = font.render(path, 1, colors.light)
            screen.blit(text, (35, y))
            if Rect((35, y), text.get_size()).collidepoint(pygame.mouse.get_pos()):
                obj_hover = 1
                if pygame.mouse.get_pressed()[0]:
                    if path == '...': continue
                    filename.text = path # click on a suggestion
                    filename.selected = True
                    pygame.mouse.set_cursor(arrow)
                    select_suggestion = True
                    exists = True
            y += 20

        pressed = pygame.key.get_pressed()
        if filename_btn.click(events) or pressed[K_RETURN] or pressed[K_KP_ENTER] or select_suggestion:
            if exists:
                save_file = filename.text
                readfile()
                update_title()
                return
            elif not invalid: # only checking here because should only be invalid in this case
                save_file = filename.text
                blocks = [[], [], [], []]
                for x in range(3):
                    blocks[x].append(Add(x))
                save()
                update_title()
                return

        if settings_btn.click(events):
            settings()
            settings_btn.change_text(settings_btn.text)

        flip()

def settings():
    global window_position, start_as

    back = positions_btns = color_btns = start_as_btn = None
    def make_btns():
        nonlocal back, positions_btns, color_btns, start_as_btn
        back = Button('Retour', (10, 10), 0)
        positions_btns = [Button(text, pos, 0) for text, pos in [('Haut gauche', (30, 80)), ('Haut droit', (150, 80)),
                                                                 ('Bas gauche', (30, 130)), ('Bas droit', (150, 130))]]
        color_btns = [Button(colors.palettes[x]['name'], (30 + 120*(x%3), 200 + 50*(x//3)), 0) for x in range(len(colors.palettes))]
        if start_as:
            text = 'Normal'
        else:
            text = 'Réduit'
        start_as_btn = Button(text, (270, 110), 0)
    make_btns()

    while True:
        events = pygame_events()

        screen.blit(background2, (0, 0))
        back.draw()
        close_button(events)

        # window position
        screen.blit(font.render('Position de la fenêtre', 1, colors.white), (30, 50))
        for btn in positions_btns:
            btn.draw()
            if btn.click(events):
                window_position = positions_btns.index(btn)
                pygame.display.quit()
                init_screen() # refresh the screen position

        # start as normal or minimized
        screen.blit(font.render('Ouvrir en', 1, colors.white), (270, 80))
        start_as_btn.draw()
        if start_as_btn.click(events):
            start_as = not start_as
            make_btns()

        # color palette
        screen.blit(font.render('Palettes de couleurs', 1, colors.white), (30, 170))
        for btn in color_btns:
            btn.draw()
            if btn.click(events):
                colors.set_palette(color_btns.index(btn))
                init_surfs()
                # update the icon (and the tray)
                set_icon()
                # commented because cause the window to close
                #tray.stop()
                #Thread(target=setup_tray).start()
                make_btns()

        if back.click(events):
            save_settings()
            return

        flip()

def propose_delete():
    yes = Button('Oui', (125, 230))
    no = Button('Non', (275, 230))

    while True:
        events = pygame_events()

        screen.blit(background2, (0, 0))
        yes.draw()
        no.draw()
        close_button(events)
        text = font.render('Vous avez tout marqué comme terminé.', 1, colors.light)
        screen.blit(text, (200-text.get_width()//2, 50))
        text = font.render('Supprimer le fichier ?', 1, colors.light)
        screen.blit(text, (200-text.get_width()//2, 80))

        text = font.render('Fichier : "%s"' %save_file, 1, colors.light)
        screen.blit(text, (200-text.get_width()//2, 150))

        if yes.click(events):
            os.remove('files\\%s.txt' %save_file)
            with open('files\\last', 'wb') as f: # empty the entry for the next reboot
                f.write(b'')
            return choose_file() # back to start menu
        if no.click(events):
            return

        flip()

def minus_button(events):
    global WINDOW_VISIBLE, obj_hover
    screen.blit(minus, (minus_rect.x, minus_rect.y+7))
    if minus_rect.collidepoint(pygame.mouse.get_pos()):
        obj_hover = 1
        for event in events:
            if event.type == MOUSEBUTTONUP:
                WINDOW_VISIBLE = False
                pygame.display.quit()
                return True

def close_button(events):
    global obj_hover
    screen.blit(cross, (cross_rect.x, cross_rect.y))
    if cross_rect.collidepoint(pygame.mouse.get_pos()):
        obj_hover = 1
        for event in events:
            if event.type == MOUSEBUTTONUP:
                pygame.event.post(pygame.event.Event(QUIT))

def update():
    message, changelog, new_version = 'Vous êtes à jour.', '', VERSION
    if gethostbyname(gethostname()) == '127.0.0.1': # offline
        return 'Vous êtes hors ligne.', changelog, new_version
    filename = os.path.abspath(__file__)
    try:
        with urlopen('http://leo.daloz.eu/python/tasko/version.txt') as f:
            new_version = f.read().decode()
            if newer_version(VERSION, new_version) != VERSION: # new version
                message = "Téléchargement d'une nouvelle version..."
                with urlopen('http://leo.daloz.eu/python/tasko/code.pyw') as f:
                    with open(filename, 'wb') as f_:
                        f_.write(f.read())
                with urlopen('http://leo.daloz.eu/python/tasko/changelog.txt') as f:
                    changelog = f.read().decode('utf-8')
    except:
        message = 'Erreur de connection.'
    return message, changelog, new_version

def newer_version(v1_, v2_): # this functions classes versions so that 1.0 > 2.0, 1.1 > 1.0, 1.0.1 > 1.0 etc
    v1 = v1_.split('.')
    v2 = v2_.split('.')
    if v1 == v2:
        return v1_
    for x in range(min(len(v1), len(v2))):
        if int(v1[x]) > int(v2[x]):
            return v1_
        elif int(v1[x]) < int(v2[x]):
            return v2_

    if len(v1) > len(v2):
        return v1_
    return v2_

def intro():
    # effects will be seen in the next launch of the program
    message, changelog, new_version = update()
    version_msg = font.render('Version : %s' %VERSION, True, colors.light)
    message = font.render(message, True, colors.white)
    w1 = version_msg.get_width()
    w2 = message.get_width()

    # transparent text
    text = pygame.font.SysFont('calibri', 50, True).render('TaskO', True, (255, 255, 255))
    w, h = text.get_size()
    w, h = w+20, h+10
    text_surf = pygame.Surface((w, h), SRCALPHA)
    text_surf.fill(colors.grey)
    round_rect(text_surf, colors.dark, (w, h))
    for x in range(w-20):
        for y in range(h-10):
            _, _, _, a = text.get_at((x, y))
            r, g, b, _ = text_surf.get_at((x+10, y+7)) # original color
            text_surf.set_at((x+10, y+7), (r, g, b, 255-a))

    text = pygame.Surface((400, h), SRCALPHA)
    text.blit(text_surf, (200 - w//2, 0))
    pygame.draw.rect(text, colors.grey, Rect((0, 0), (200 - w//2, h)))
    pygame.draw.rect(text, colors.grey, Rect((200 + w//2, 0), (200 - w//2, h)))

    # colors under the transparent text
    colors_surf = pygame.Surface((3*w, h))
    for x in range(3):
        pygame.draw.rect(colors_surf, colors.blocks[x], Rect((w*x, 0), (w, h)))
        pygame.draw.line(colors_surf, colors.grey, (w*x, 0), (w*x, h), 3)

    smooth = lambda x: (1-cos(pi*x)) / 2
    start = ticks()
    while ticks()-start < 5000:
        pygame_events()
        screen.blit(background, (0, 0))
        screen.blit(colors_surf, (200 - w//2 - min(smooth(min((ticks()-start)/2000, 1)), 1)*2*w, 80))
        screen.blit(text, (0, 80))

        a = min(max((ticks()-start-2000) * 255 // 1000, 0), 255)
        version_msg.set_alpha(a)
        message.set_alpha(a)
        screen.blit(version_msg, (200 - w1//2, 170))
        screen.blit(message, (200 - w2//2, 200))

        flip()

    if changelog:
        screen.blit(background, (0, 0))
        title = font.render('La version %s a été téléchargée.' %new_version, True, colors.light)
        screen.blit(title, (200 - title.get_width()//2, 20))
        title = font.render('Modifications apportées :', True, colors.light)
        screen.blit(title, (200 - title.get_width()//2, 50))

        y = 90
        for line in changelog.split('\n'):
            screen.blit(font.render(line, True, colors.white), (20, y))
            y += 30

        pygame.display.flip()

        while not True in pygame.key.get_pressed() and not True in pygame.mouse.get_pressed():
            pygame_events()
            close_button(events)
            clock.tick(10)

def setup_tray():
    global tray

    # set up the tray icon
    raw_str = pygame.image.tostring(icon, 'RGBA', False)
    image = Image.frombytes('RGBA', icon.get_size(), raw_str)
    menu = (pystray.MenuItem('Ouvrir', click_tray, default=True),)
    tray = pystray.Icon('Ouvrir', image, 'Task Organiser', menu)

    tray.run() # needs to be in a thread to avoid stopping the program

def click_tray():
    global WINDOW_VISIBLE

    if not WINDOW_VISIBLE:
        pygame.display.init()
        pygame.key.set_repeat(400, 30)
        init_screen()
        WINDOW_VISIBLE = True

def init_screen():
    global screen
    set_window_position()

    screen = pygame.display.set_mode((400, 300), NOFRAME)

    # green is the transparent color
    hwnd = pygame.display.get_wm_info()['window']
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                           win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 255, 0), 0, win32con.LWA_COLORKEY)

    try:
        win32gui.SetForegroundWindow(hwnd) # set foreground window, useful when clicking on the tray icon
    except: # could have Win+Tab for example
        pass

def set_icon():
    global icon

    icon = pygame.image.load('files\\icon.png')
    w, h = icon.get_size()
    R, G, B = colors.blocks[2] # make the icon be of this color

    for x in range(w):
        for y in range(h):
            r, g, b, a = icon.get_at((x, y))
            light = (r+g+b) / 765
            icon.set_at((x, y), (R*light, G*light, B*light, a))

    pygame.display.set_icon(icon)

def set_window_position():
    # place the window to a set point in the screen
    w, h = info.current_w, info.current_h
    os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' %[(10, 10), (w-410, 10), (10, h-350), (w-410, h-350)][window_position]

def init_surfs():
    global background, top_background_empty, background2, minus, cross, back, minus_rect, cross_rect
    # initialise surfaces according to the current color palette

    background = pygame.Surface((400, 300))
    background.fill((0, 255, 0)) # transparent
    round_rect(background, colors.grey, (400, 300))
    top_background_empty = pygame.Surface((400, 80))
    top_background_empty.blit(background, (0, 0))
    # actual top_background will be created in update_title
    background2 = background.copy()
    round_rect(background2, colors.dark, (400, 300))

    minus = pygame.Surface((15, 5), SRCALPHA)
    minus.fill(colors.light)
    cross = pygame.Surface((20, 20), SRCALPHA)
    pygame.draw.line(cross, colors.red, (4, 16), (16, 4), 4)
    pygame.draw.line(cross, colors.red, (4, 4), (16, 16), 4)

    back = Button('Retour', (10, 10), 0)
    minus_rect = Rect((345, 10), (15, 20))
    cross_rect = Rect((370, 10), (20, 20))

def pygame_events():
    global obj_hover
    obj_hover = 0 # no objects hovered

    events = pygame.event.get()
    pressed = pygame.key.get_pressed()
    alt = pressed[K_LALT] or pressed[K_RALT]
    for event in events:
        if event.type == QUIT:
            pygame.display.set_caption('Task Organiser - Sauvegarde et arrêt...')
            screen.blit(background, (0, 0))
            text = font.render('Sauvegarde et arrêt...', True, colors.light)
            w, h = text.get_size()
            screen.blit(text, (200 - w//2, 150 - h//2))
            pygame.display.flip()

            if blocks is not None:
                save()
            quit()
        if event.type == KEYDOWN:
            if event.key == K_F4:
                pygame.event.post(pygame.event.Event(QUIT))
    return events

def flip():
    if obj_hover == 2:
        pygame.mouse.set_cursor(ibeam)
    elif obj_hover:
        pygame.mouse.set_cursor(hand)
    else:
        pygame.mouse.set_cursor(arrow)

    pygame.display.flip()
    clock.tick(60)

# need to be initialised very early (most likely used a lot)
colors = Colors()
colors.set_palette(0) # default
window_position = 3 # default
start_as = 1 # default
load_settings()
set_icon() # create colored icon
blocks = None # to know if save needed when exiting

WINDOW_VISIBLE = start_as
Thread(target=setup_tray).start()

pygame.init()
pygame.key.set_repeat(400, 30) # all keys will now be able to repeat

info = pygame.display.Info()

font = pygame.font.SysFont('calibri', 18, True) # fixed-width font
pygame.display.set_caption('Task Organiser')
clock = pygame.time.Clock()
ticks = pygame.time.get_ticks
arrow = pygame.cursors.Cursor(SYSTEM_CURSOR_ARROW)
hand = pygame.cursors.Cursor(SYSTEM_CURSOR_HAND)
ibeam = pygame.cursors.Cursor(SYSTEM_CURSOR_IBEAM)

init_screen()
init_surfs()

opened = 0
scroll = Scroll(2)
last_action_time = ticks()
saved = False

intro()

choose_file(True)
prev_state = [group[:] for group in blocks]

if not start_as:
    pygame.display.quit()

while True:
    if not WINDOW_VISIBLE:
        clock.tick(1)
        continue

    no_dragged_todo = True
    for group in blocks[:-1]:
        for block in group:
            if block.start_drag:
                no_dragged_todo = False
                break # can't drag another one

    events = pygame_events()
    for event in events:
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                for group in blocks[:-1]:
                    for block in group:
                        if block.rect.collidepoint(event.pos) and event.pos[1] >= 40 and no_dragged_todo:
                            if type(block) == Todo: # drag if not a button
                                if block.rect.right-event.pos[0] >= 20: # drag the block
                                    block.start_drag = event.pos
                                    no_dragged_todo = False
                                    block.zone = None
                                    blocks[-1].append(block)
                                # move the blocks below upwards 1 block
                                group.remove(block)
                                for b in group:
                                    if b.zoneindex > block.zoneindex:
                                        b.zoneindex -= 1
                            else: # click on an Add block (adblock lol)
                                block.click()
                                break
                        else:
                            block.start_drag = None
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                for block in blocks[-1]: # only check the moving block
                    # insert the block at the right index
                    block.zoneindex = block.hover_index
                    for b in blocks[opened]:
                        if b.zoneindex >= block.zoneindex:
                            b.zoneindex += 1
                    block.zone = opened
                    blocks[-1].remove(block)
                    blocks[opened].insert(block.zoneindex, block)
                    block.start_drag = None

    if ticks() - last_action_time > 5000 and not saved: # save every 5 seconds
        save()
        saved = True

    # if everything marked as completed then propose to delete the file
    if blocks != prev_state: # do not spam the delete? message, wait for something to change
        last_action_time = ticks()
        saved = False # the content has changed
        if [bool(len(blocks[x])-1) for x in range(4)] in [[0, 0, 0, 1], [0, 0, 1, 1]]:
            propose_delete()
    prev_state = [group[:] for group in blocks]

    if pygame.mouse.get_focused():
        x, y = pygame.mouse.get_pos()
        zone = Rect(90*opened, 0, 220, 300)
        if not zone.collidepoint((x, y)):
            if x < zone.left:
                opened = x//90
            else:
                opened = (x-220+90) // 90
    else: # show middle zone when mouse outside of screen
        opened = 1
    # prevent IndexError and out-of-bounds placing
    opened = min(max(opened, 0), 2)

    scroll.update(events)

    screen.blit(background, (0, 0))

    for group in blocks:
        for block in group:
            if not block.start_drag:
                block.update()

    screen.blit(top_background, (0, 0))
    for zone in range(3):
        # text on top
        if zone > opened:
            x = 130 + 90*zone
        else:
            x = 10 + 90*zone
        text = ['A faire', 'En cours', 'Terminé'][zone]
        screen.blit(font.render(text, 1, colors.blocks[zone]), (x, 50))

        # scroll bars if needed
        if zone == opened:
            height = sum([block.rect.height+10 for block in blocks[zone]])
            if height > 220:
                y = scroll.scroll[zone] * 220/height
                pygame.draw.rect(screen, colors.white, Rect(200 + 90*zone, y+85, 5, 220**2/height - 10))

    back.draw()
    if back.click(events):
        save()
        choose_file()
        prev_state = [group[:] for group in blocks] # update to not ask to delete the file immediately

    if minus_button(events):
        continue
    close_button(events)

    for group in blocks:
        for block in group:
            if block.start_drag:
                block.update()

    flip()
