import pygame
import sys
import random
import math
import os

pygame.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (100, 100, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
CYAN = (50, 255, 255)
MAGENTA = (255, 50, 255)

class AimTrainerGame:
    def __init__(self):
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        print(f"Текущее разрешение экрана: {self.width}x{self.height}")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.display.set_caption("МЕГА АИМ ТРЕНЕР")
        self.clock = pygame.time.Clock()
        self.font_size = int(self.height * 0.04)
        self.small_font_size = int(self.height * 0.03)
        self.font = pygame.font.SysFont("Arial", self.font_size)
        self.small_font = pygame.font.SysFont("Arial", self.small_font_size)
        self.settings = {
            "enable_lives": True,
            "lives": 5,
            "target_speed": 2,
            "target_spawn_rate": 1000,
            "target_color": RED,
            "radius_min": 20,
            "radius_max": 40,
        }
        self.gradient_val = 0
        self.gradient_dir = 1
        self.game_state = "main_menu"
        self.current_mode = None
        self.score = 0
        self.lives_left = self.settings["lives"]
        self.misses = 0
        self.targets = []
        self.last_spawn_time = pygame.time.get_ticks()
        self.show_help = False
        self.death_anim = 0
        self.help_text = [
            "Режимы:",
            "1) Классика - статичные цели",
            "2) Подвижные - движущиеся цели",
            "3) Реакция - одна цель на короткое время",
            "4) Задержка - цель появляется и исчезает",
            "5) Трекинг - цель двигается, очки за ведение курсором",
            "6) ГридШот - несколько целей в сетке",
            "7) Снайпер - цели с маленьким радиусом",
            "8) Дождь целей - много падающих сверху целей",
            "9) Комбо - сочетание статичных и движущихся целей",
        ]
        self.highscores = {
            "classic": 0,
            "moving": 0,
            "reaction": 0,
            "delay": 0,
            "tracking": 0,
            "gridshot": 0,
            "sniper": 0,
            "targets_rain": 0,
            "combo": 0
        }
        self.records_file = "records.txt"
        self.load_records()
        self.modes = {
            "classic": self.classic_mode,
            "moving": self.moving_mode,
            "reaction": self.reaction_mode,
            "delay": self.delayed_mode,
            "tracking": self.tracking_mode,
            "gridshot": self.gridshot_mode,
            "sniper": self.sniper_mode,
            "targets_rain": self.targets_rain_mode,
            "combo": self.combo_mode
        }
        self.tracking_score_time = 0
        self.settings_sliders = {
            "target_speed": {"min": 1, "max": 30, "val": self.settings["target_speed"]},
            "target_spawn_rate": {"min": 200, "max": 3000, "val": self.settings["target_spawn_rate"]},
            "radius_min": {"min": 5, "max": 50, "val": self.settings["radius_min"]},
            "radius_max": {"min": 5, "max": 100, "val": self.settings["radius_max"]},
            "lives": {"min": 1, "max": 20, "val": self.settings["lives"]},
        }

    def load_records(self):
        if not os.path.exists(self.records_file):
            return
        try:
            with open(self.records_file, "r", encoding="utf-8") as f:
                for line in f:
                    nm, v = line.strip().split(":")
                    if nm in self.highscores:
                        self.highscores[nm] = int(v)
        except:
            pass

    def save_records(self):
        try:
            with open(self.records_file, "w", encoding="utf-8") as f:
                for nm, v in self.highscores.items():
                    f.write(f"{nm}:{v}\n")
        except:
            pass

    def run(self):
        while True:
            self.clock.tick(60)
            self.handle_events()
            self.update_screen()
            pygame.display.flip()
            if self.game_state == "exit":
                break
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.game_state = "exit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.game_state == "play":
                        self.update_highscore()
                        self.game_state = "main_menu"
                    elif self.game_state == "death":
                        self.game_state = "main_menu"
                        self.death_anim = 0
                if e.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "main_menu":
                    self.handle_main_menu_click()
                elif self.game_state == "settings":
                    self.handle_settings_click()
                elif self.game_state == "play":
                    self.handle_play_click()
                elif self.game_state == "death":
                    self.game_state = "main_menu"
                    self.death_anim = 0
                self.handle_help_icon_click()
            if e.type == pygame.MOUSEMOTION:
                if self.game_state == "settings":
                    self.handle_settings_slider_drag()

    def update_screen(self):
        self.animate_bg()
        if self.game_state == "main_menu":
            self.draw_main_menu()
        elif self.game_state == "settings":
            self.draw_settings_menu()
        elif self.game_state == "play":
            if self.current_mode in self.modes:
                self.modes[self.current_mode]()
            else:
                self.game_state = "main_menu"
        elif self.game_state == "death":
            self.draw_death_screen()
        self.draw_help_icon()
        if self.show_help:
            self.draw_help_overlay()

    def draw_main_menu(self):
        t = self.font.render("МЕГА АИМ ТРЕНЕР", True, WHITE)
        self.screen.blit(t, (self.width // 2 - t.get_width() // 2, self.height * 0.07))
        items = [
            ("Классика", (self.width // 2, self.height * 0.17), "classic"),
            ("Подвижные", (self.width // 2, self.height * 0.25), "moving"),
            ("Реакция", (self.width // 2, self.height * 0.33), "reaction"),
            ("Задержка", (self.width // 2, self.height * 0.41), "delay"),
            ("Трекинг", (self.width // 2, self.height * 0.49), "tracking"),
            ("ГридШот", (self.width // 2, self.height * 0.57), "gridshot"),
            ("Снайпер", (self.width // 2, self.height * 0.65), "sniper"),
            ("Дождь целей", (self.width // 2, self.height * 0.73), "targets_rain"),
            ("Комбо", (self.width // 2, self.height * 0.81), "combo"),
            ("Настройки", (self.width // 2, self.height * 0.89), "settings"),
            ("Выход", (self.width // 2, self.height * 0.97), "exit"),
        ]
        for txt, pos, act in items:
            lbl = self.font.render(txt, True, WHITE)
            r = lbl.get_rect(center=pos)
            self.screen.blit(lbl, r)

    def handle_main_menu_click(self):
        mx, my = pygame.mouse.get_pos()
        items = [
            ("classic", (self.width // 2, self.height * 0.17)),
            ("moving", (self.width // 2, self.height * 0.25)),
            ("reaction", (self.width // 2, self.height * 0.33)),
            ("delay", (self.width // 2, self.height * 0.41)),
            ("tracking", (self.width // 2, self.height * 0.49)),
            ("gridshot", (self.width // 2, self.height * 0.57)),
            ("sniper", (self.width // 2, self.height * 0.65)),
            ("targets_rain", (self.width // 2, self.height * 0.73)),
            ("combo", (self.width // 2, self.height * 0.81)),
            ("settings", (self.width // 2, self.height * 0.89)),
            ("exit", (self.width // 2, self.height * 0.97)),
        ]
        for act, pos in items:
            dist = math.hypot(mx - pos[0], my - pos[1])
            if dist < self.height * 0.05:
                if act == "exit":
                    self.game_state = "exit"
                elif act == "settings":
                    self.game_state = "settings"
                else:
                    self.start_game_mode(act)
                break

    def draw_slider(self, x, y, w, h, key):
        col_back = (80, 80, 80)
        pygame.draw.rect(self.screen, col_back, (x, y, w, h), border_radius=4)
        v = self.settings_sliders[key]["val"]
        mn = self.settings_sliders[key]["min"]
        mx = self.settings_sliders[key]["max"]
        rel = (v - mn) / (mx - mn) if mx != mn else 0
        knob_x = x + int(rel * w)
        col_knob = (150, 150, 150)
        pygame.draw.rect(self.screen, col_knob, (knob_x - 5, y, 10, h), border_radius=4)

    def handle_settings_slider_drag(self):
        if not pygame.mouse.get_pressed()[0]:
            return
        mx, my = pygame.mouse.get_pos()
        settings_list = [
            ("lives", "ЖИЗНИ"),
            ("target_speed", "СКОРОСТЬ"),
            ("target_spawn_rate", "ИНТЕРВАЛ (МС)"),
            ("radius_min", "МИН. РАДИУС"),
            ("radius_max", "МИКС. РАДИУС"),
        ]
        x_label = self.width * 0.07
        y_start = self.height * 0.19
        y_step = self.height * 0.075
        slider_w = self.width * 0.15
        slider_h = self.height * 0.025
        for i, (key, _) in enumerate(settings_list):
            y_pos = y_start + i * y_step
            sx = x_label + self.width * 0.35
            sy = y_pos + self.height * 0.005
            rect_slider = pygame.Rect(sx, sy, slider_w, slider_h)
            if rect_slider.collidepoint(mx, my):
                mn = self.settings_sliders[key]["min"]
                mxv = self.settings_sliders[key]["max"]
                rel = (mx - sx) / slider_w
                if slider_w != 0:
                    rel = (mx - sx) / slider_w
                else:
                    rel = 0
                rel = max(0, min(rel, 1))
                val = mn + rel * (mxv - mn)
                if key == "target_spawn_rate":
                    val = int(val)
                else:
                    val = int(round(val))
                val = max(mn, min(val, mxv))
                self.settings_sliders[key]["val"] = val
                if key == "lives":
                    self.settings["lives"] = val
                elif key == "target_speed":
                    self.settings["target_speed"] = val
                elif key == "target_spawn_rate":
                    self.settings["target_spawn_rate"] = val
                elif key == "radius_min":
                    self.settings["radius_min"] = val
                    if self.settings["radius_min"] > self.settings["radius_max"]:
                        self.settings["radius_min"] = self.settings["radius_max"]
                elif key == "radius_max":
                    self.settings["radius_max"] = val
                    if self.settings["radius_max"] < self.settings["radius_min"]:
                        self.settings["radius_max"] = self.settings["radius_min"]

    def draw_settings_menu(self):
        t = self.font.render("НАСТРОЙКИ", True, WHITE)
        self.screen.blit(t, (self.width // 2 - t.get_width() // 2, self.height * 0.06))
        text_1 = "ВКЛЮЧИТЬ ЖИЗНИ: ON" if self.settings["enable_lives"] else "ВКЛЮЧИТЬ ЖИЗНИ: OFF"
        r_1 = self.font.render(text_1, True, WHITE)
        self.screen.blit(r_1, (self.width * 0.07, self.height * 0.13))
        settings_list = [
            ("lives", "ЖИЗНИ"),
            ("target_speed", "СКОРОСТЬ"),
            ("target_spawn_rate", "ИНТЕРВАЛ (МС)"),
            ("radius_min", "МИН. РАДИУС"),
            ("radius_max", "МИКС. РАДИУС"),
        ]
        x_label = self.width * 0.07
        y_start = self.height * 0.19
        y_step = self.height * 0.075
        for i, (key, txt_label) in enumerate(settings_list):
            y_pos = y_start + i * y_step
            r_txt = self.font.render(txt_label, True, WHITE)
            self.screen.blit(r_txt, (x_label, y_pos))
            v = self.settings_sliders[key]["val"]
            r_v = self.font.render(str(v), True, WHITE)
            self.screen.blit(r_v, (x_label + self.width * 0.3, y_pos))
            self.draw_slider(x_label + self.width * 0.35, y_pos + self.height * 0.005, self.width * 0.15, self.height * 0.025, key)
        col = (80, 80, 80)
        toggle_rect = pygame.Rect(self.width * 0.07 + r_1.get_width() + 20, self.height * 0.13, self.width * 0.1, self.height * 0.05)
        pygame.draw.rect(self.screen, col, toggle_rect, border_radius=5)
        onoff_text = self.font.render("СМЕНА", True, WHITE)
        self.screen.blit(onoff_text, onoff_text.get_rect(center=toggle_rect.center))
        back_text = self.font.render("СОХРАНИТЬ И ВЕРНУТЬСЯ", True, WHITE)
        back_rect = back_text.get_rect(center=(self.width // 2, self.height * 0.95))
        pygame.draw.rect(self.screen, GREY, back_rect.inflate(20, 10), border_radius=10)
        self.screen.blit(back_text, back_rect)

    def handle_settings_click(self):
        mx, my = pygame.mouse.get_pos()
        r_1 = self.font.render("ВКЛЮЧИТЬ ЖИЗНИ: OFF", True, WHITE)
        toggle_rect = pygame.Rect(self.width * 0.07 + r_1.get_width() + 20, self.height * 0.13, self.width * 0.1, self.height * 0.05)
        if toggle_rect.collidepoint(mx, my):
            self.settings["enable_lives"] = not self.settings["enable_lives"]
        back_text = self.font.render("СОХРАНИТЬ И ВЕРНУТЬСЯ", True, WHITE)
        back_rect = back_text.get_rect(center=(self.width // 2, self.height * 0.95))
        back_rect_infl = back_rect.inflate(20, 10)
        if back_rect_infl.collidepoint(mx, my):
            self.game_state = "main_menu"
            return

    def change_mode(self, new_mode):
        self.current_mode = new_mode
        self.game_state = "play"
        self.score = 0
        self.lives_left = self.settings["lives"]
        self.misses = 0
        self.targets.clear()
        self.last_spawn_time = pygame.time.get_ticks()
        self.death_anim = 0

    def start_game_mode(self, m):
        self.current_mode = m
        self.game_state = "play"
        self.score = 0
        self.lives_left = self.settings["lives"]
        self.misses = 0
        self.targets.clear()
        self.last_spawn_time = pygame.time.get_ticks()
        self.death_anim = 0
        if m == "tracking":
            self.tracking_score_time = 0

    def handle_play_click(self):
        mp = pygame.mouse.get_pos()
        hit_any = False
        for t in self.targets:
            x, y = t["pos"]
            r = t["radius"]
            dist = math.hypot(mp[0] - x, mp[1] - y)
            if dist <= r:
                self.score += 1
                t["hit"] = True
                t["flash_time"] = pygame.time.get_ticks()
                hit_any = True
        if not hit_any:
            if self.settings["enable_lives"]:
                self.lives_left -= 1
                if self.lives_left <= 0:
                    self.game_state = "death"
                    self.update_highscore()
            else:
                self.misses += 1

    def update_highscore(self):
        if self.current_mode in self.highscores:
            if self.score > self.highscores[self.current_mode]:
                self.highscores[self.current_mode] = int(self.score)
                self.save_records()

    def classic_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"]:
            self.spawn_target()
            self.last_spawn_time = now
        self.update_and_draw_targets()
        self.draw_score_and_lives_or_misses()

    def moving_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"]:
            self.spawn_target(moving=True)
            self.last_spawn_time = now
        self.update_and_draw_targets(moving=True)
        self.draw_score_and_lives_or_misses()

    def reaction_mode(self):
        if len(self.targets) == 0:
            self.spawn_target(lifetime=1500)
        self.update_and_draw_targets(lifetime_check=True)
        self.draw_score_and_lives_or_misses()

    def delayed_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"]:
            self.spawn_target(lifetime=1000)
            self.last_spawn_time = now
        self.update_and_draw_targets(lifetime_check=True)
        self.draw_score_and_lives_or_misses()

    def tracking_mode(self):
        dt = self.clock.get_time() / 1000.0
        mx, my = pygame.mouse.get_pos()
        if len(self.targets) == 0:
            self.spawn_target(moving=True)
        for t in self.targets:
            x, y = t["pos"]
            r = t["radius"]
            d = math.hypot(mx - x, my - y)
            if d <= r:
                self.tracking_score_time += dt
                self.score = int(self.tracking_score_time)
        self.update_and_draw_targets(moving=True)
        self.draw_score_and_lives_or_misses()

    def gridshot_mode(self):
        if len(self.targets) == 0:
            rows, cols = 3, 3
            cw = self.width // (cols + 1)
            ch = self.height // (rows + 1)
            for rr in range(1, rows + 1):
                for cc in range(1, cols + 1):
                    rad = random.randint(self.settings["radius_min"], self.settings["radius_max"])
                    x = cw * cc
                    y = ch * rr
                    t = {
                        "pos": [x, y],
                        "radius": rad,
                        "color": self.settings["target_color"],
                        "hit": False,
                        "speed": [0, 0],
                        "spawn_time": pygame.time.get_ticks(),
                        "lifetime": 0,
                        "flash_time": None,
                    }
                    self.targets.append(t)
        self.update_and_draw_targets()
        self.draw_score_and_lives_or_misses()

    def sniper_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"]:
            rad = random.randint(5, 10)
            x = random.randint(rad, self.width - rad)
            y = random.randint(rad, self.height - rad)
            sx, sy = 0, 0
            t = {
                "pos": [x, y],
                "radius": rad,
                "color": self.settings["target_color"],
                "hit": False,
                "speed": [sx, sy],
                "spawn_time": pygame.time.get_ticks(),
                "lifetime": 0,
                "flash_time": None
            }
            self.targets.append(t)
            self.last_spawn_time = now
        self.update_and_draw_targets()
        self.draw_score_and_lives_or_misses()

    def targets_rain_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"] // 2:
            r = random.randint(self.settings["radius_min"], self.settings["radius_max"])
            x = random.randint(r, self.width - r)
            y = -r
            sx = 0
            sy = random.randint(self.settings["target_speed"], self.settings["target_speed"] + 3)
            t = {
                "pos": [x, y],
                "radius": r,
                "color": self.settings["target_color"],
                "hit": False,
                "speed": [sx, sy],
                "spawn_time": now,
                "lifetime": 0,
                "flash_time": None
            }
            self.targets.append(t)
            self.last_spawn_time = now
        remove_list = []
        for i, t in enumerate(self.targets):
            t["pos"][1] += t["speed"][1]
            if t["pos"][1] - t["radius"] > self.height:
                if self.settings["enable_lives"]:
                    self.lives_left -= 1
                    if self.lives_left <= 0:
                        self.game_state = "death"
                        self.update_highscore()
                else:
                    self.misses += 1
                remove_list.append(i)
        for i in sorted(remove_list, reverse=True):
            self.targets.pop(i)
        self.update_and_draw_targets()
        self.draw_score_and_lives_or_misses()

    def combo_mode(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.settings["target_spawn_rate"]:
            c = random.choice(["static", "moving"])
            if c == "static":
                self.spawn_target()
            else:
                self.spawn_target(moving=True)
            self.last_spawn_time = now
        self.update_and_draw_targets(moving=True)
        self.draw_score_and_lives_or_misses()

    def update_and_draw_targets(self, moving=False, lifetime_check=False):
        now = pygame.time.get_ticks()
        to_remove = []
        for i, t in enumerate(self.targets):
            if moving:
                t["pos"][0] += t["speed"][0]
                t["pos"][1] += t["speed"][1]
                if t["pos"][0] - t["radius"] < 0 or t["pos"][0] + t["radius"] > self.width:
                    t["speed"][0] *= -1
                if t["pos"][1] - t["radius"] < 0 or t["pos"][1] + t["radius"] > self.height:
                    t["speed"][1] *= -1
            if lifetime_check and t.get("lifetime", 0) > 0:
                if now - t["spawn_time"] > t["lifetime"]:
                    if not t["hit"]:
                        if self.settings["enable_lives"]:
                            self.lives_left -= 1
                            if self.lives_left <= 0:
                                self.game_state = "death"
                                self.update_highscore()
                        else:
                            self.misses += 1
                    to_remove.append(i)
            if t["hit"]:
                if t["flash_time"] is not None:
                    if now - t["flash_time"] > 100:
                        to_remove.append(i)
            self.draw_target(t)
        for i in sorted(to_remove, reverse=True):
            self.targets.pop(i)

    def draw_target(self, t):
        if t["flash_time"]:
            elapsed = pygame.time.get_ticks() - t["flash_time"]
            ratio = 1 - min(elapsed / 100, 1)
            rr = t["radius"] + int(30 * ratio)
            col = (
                int(t["color"][0] + (255 - t["color"][0]) * ratio),
                int(t["color"][1] + (255 - t["color"][1]) * ratio),
                int(t["color"][2] + (255 - t["color"][2]) * ratio),
            )
            pygame.draw.circle(self.screen, col, (int(t["pos"][0]), int(t["pos"][1])), rr)
        else:
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 2
            pygame.draw.circle(
                self.screen,
                t["color"],
                (int(t["pos"][0]), int(t["pos"][1])),
                int(t["radius"] + pulse)
            )

    def draw_score_and_lives_or_misses(self):
        sc = self.font.render(f"Счёт: {int(self.score)}", True, WHITE)
        self.screen.blit(sc, (self.width * 0.01, self.height * 0.01))
        if self.settings["enable_lives"]:
            lf = self.font.render(f"Жизни: {self.lives_left}", True, WHITE)
            self.screen.blit(lf, (self.width * 0.01, self.height * 0.06))
        else:
            ms = self.font.render(f"Промахи: {self.misses}", True, WHITE)
            self.screen.blit(ms, (self.width * 0.01, self.height * 0.06))

    def draw_death_screen(self):
        self.death_anim += 0.01
        if self.death_anim > 1.5:
            self.death_anim = 1.5
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill(BLACK)
        alpha_val = min(int(self.death_anim * 200), 200)
        overlay.set_alpha(alpha_val)
        self.screen.blit(overlay, (0, 0))
        txt = self.font.render("КОНЕЦ ИГРЫ!", True, WHITE)
        sc = 1.0 + self.death_anim * 0.3
        tw = int(txt.get_width() * sc)
        th = int(txt.get_height() * sc)
        surf = pygame.transform.smoothscale(txt, (tw, th))
        self.screen.blit(surf, (self.width // 2 - tw // 2, self.height // 2 - th // 2))
        info = self.small_font.render("Нажмите ESC или кликните, чтобы вернуться в меню", True, WHITE)
        self.screen.blit(info, (self.width // 2 - info.get_width() // 2, self.height // 2 + th // 2 + 30))

    def animate_bg(self):
        self.gradient_val += self.gradient_dir
        if self.gradient_val >= 255 or self.gradient_val <= 0:
            self.gradient_dir *= -1
        c1 = (self.gradient_val, 50, 255 - self.gradient_val)
        c2 = (255 - self.gradient_val, 255, self.gradient_val)
        for y in range(self.height):
            r = y / self.height
            rr = int(c1[0] * (1 - r) + c2[0] * r)
            gg = int(c1[1] * (1 - r) + c2[1] * r)
            bb = int(c1[2] * (1 - r) + c2[2] * r)
            pygame.draw.line(self.screen, (rr, gg, bb), (0, y), (self.width, y))

    def draw_help_icon(self):
        icon_text = self.font.render("!", True, WHITE)
        r = icon_text.get_rect(center=(self.width - 40, self.height - 40))
        pygame.draw.circle(self.screen, (80, 80, 80), r.center, 30)
        self.screen.blit(icon_text, r)

    def handle_help_icon_click(self):
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            dx = mx - (self.width - 40)
            dy = my - (self.height - 40)
            dist = math.hypot(dx, dy)
            if dist < 30:
                self.show_help = not self.show_help

    def draw_help_overlay(self):
        rc = pygame.Rect(50, 50, self.width - 100, self.height - 100)
        help_surface = pygame.Surface((rc.width, rc.height), pygame.SRCALPHA)
        help_surface.set_alpha(220)
        help_surface.fill(BLACK)
        pygame.draw.rect(help_surface, WHITE, help_surface.get_rect(), 2)
        self.screen.blit(help_surface, rc.topleft)
        xx = rc.x + 30
        yy = rc.y + 30
        for line in self.help_text:
            ls = self.small_font.render(line, True, WHITE)
            self.screen.blit(ls, (xx, yy))
            yy += 30

    def spawn_target(self, moving=False, lifetime=0):
        r = random.randint(self.settings["radius_min"], self.settings["radius_max"])
        x = random.randint(r, self.width - r)
        y = random.randint(r, self.height - r)
        color = self.settings["target_color"]
        hit = False
        speed = [0, 0]
        if moving:
            speed = [
                random.choice([-1, 1]) * self.settings["target_speed"],
                random.choice([-1, 1]) * self.settings["target_speed"]
            ]
        t = {
            "pos": [x, y],
            "radius": r,
            "color": color,
            "hit": hit,
            "speed": speed,
            "spawn_time": pygame.time.get_ticks(),
            "lifetime": lifetime,
            "flash_time": None,
        }
        self.targets.append(t)

def main():
    g = AimTrainerGame()
    g.run()

if __name__ == "__main__":
    main()
