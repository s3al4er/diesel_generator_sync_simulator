import pygame
import sys
import math

# Инициализация Pygame
pygame.init()

# Настройки экрана
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Симулятор Синхронизации Дизель-Генераторов")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
DARK_RED = (150, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BUTTON_DARK = (51, 51, 51)
HOVER_BUTTON_DARK = (80, 80, 80)

# Шрифты
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 30)
FONT_LARGE = pygame.font.Font(None, 40)
FONT_SYNC = pygame.font.Font(None, 60)
FONT_7SEG = pygame.font.Font(None, 50)
FONT_PLUS_MINUS = pygame.font.Font(None, 40)

# --- Класс Кнопки ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None, shape='rect', border_radius=0, text_color=WHITE, font=FONT_SMALL):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False
        self.is_enabled = True
        self.text_color = text_color
        self.font = font
        self.shape = shape
        self.border_radius = border_radius

        if self.shape == 'circle':
            self.radius = width // 2
            self.center = (x + self.radius, y + self.radius)
            self.rect = pygame.Rect(x, y, self.radius * 2, self.radius * 2)

    def draw(self, screen):
        current_color = self.color
        if self.is_enabled:
            if self.is_hovered:
                current_color = self.hover_color
        else:
            current_color = DARK_GRAY

        if self.shape == 'rect':
            if self.border_radius > 0:
                pygame.draw.rect(screen, current_color, self.rect, border_radius=self.border_radius)
            else:
                pygame.draw.rect(screen, current_color, self.rect)
        elif self.shape == 'circle':
            pygame.draw.circle(screen, current_color, self.center, self.radius)
            
        text_surf = self.font.render(self.text, True, self.text_color)
        if self.shape == 'rect':
            text_rect = text_surf.get_rect(center=self.rect.center)
        elif self.shape == 'circle':
            text_rect = text_surf.get_rect(center=self.center)
        
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if self.is_enabled:
            if event.type == pygame.MOUSEMOTION:
                if self.shape == 'circle':
                    distance = math.hypot(event.pos[0] - self.center[0], event.pos[1] - self.center[1])
                    self.is_hovered = distance <= self.radius
                else: 
                    self.is_hovered = self.rect.collidepoint(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (self.shape == 'circle' and self.is_hovered) or \
                   (self.shape == 'rect' and self.rect.collidepoint(event.pos)):
                    if self.action:
                        self.action()
                        return True
        return False

    def set_enabled(self, enabled):
        self.is_enabled = enabled

# --- Класс Генератора ---
class Generator:
    PANEL_WIDTH = 200
    PANEL_HEIGHT = 550
    PANEL_Y_OFFSET = 50

    def __init__(self, gen_id, x_offset):
        self.id = gen_id
        self.is_on = False
        self.rpm_adjustment_steps = 3
        self.power_output = 0
        self.synchronoscope_angle = 0
        self.synchronization_successful = False
        self.x_offset = x_offset

        self.header_y = self.PANEL_Y_OFFSET + 20 

        btn_onoff_size = 50
        self.on_off_button = Button(
            self.x_offset + (self.PANEL_WIDTH - btn_onoff_size) // 2,
            self.PANEL_Y_OFFSET + 70,
            btn_onoff_size, btn_onoff_size,
            "ВКЛ", RED, DARK_RED, self.toggle_power, shape='circle', text_color=WHITE, font=FONT_SMALL
        )

        power_display_width = 100
        power_display_height = 30
        self.power_display_rect = pygame.Rect(
            self.x_offset + (self.PANEL_WIDTH - power_display_width) // 2,
            self.PANEL_Y_OFFSET + 155,
            power_display_width, power_display_height
        )
        
        self.power_label_y = self.power_display_rect.top - 10

        btn_pm_size = 40
        gap_between_pm_buttons = 15
        total_pm_buttons_width = btn_pm_size * 2 + gap_between_pm_buttons
        start_x_for_minus = self.x_offset + (self.PANEL_WIDTH - total_pm_buttons_width) // 2

        self.decrease_rpm_button = Button(
            start_x_for_minus,
            self.PANEL_Y_OFFSET + 215,
            btn_pm_size, btn_pm_size,
            "-", BUTTON_DARK, HOVER_BUTTON_DARK, self.decrease_rpm, shape='circle', font=FONT_PLUS_MINUS
        )
        self.increase_rpm_button = Button(
            start_x_for_minus + btn_pm_size + gap_between_pm_buttons,
            self.PANEL_Y_OFFSET + 215,
            btn_pm_size, btn_pm_size,
            "+", BUTTON_DARK, HOVER_BUTTON_DARK, self.increase_rpm, shape='circle', font=FONT_PLUS_MINUS
        )

        self.synchronoscope_center = (self.x_offset + self.PANEL_WIDTH // 2, self.PANEL_Y_OFFSET + 350)
        self.synchronoscope_radius = 80

        sync_btn_width = 150 
        sync_btn_height = 40
        self.sync_button = Button(
            self.x_offset + (self.PANEL_WIDTH - sync_btn_width) // 2,
            self.PANEL_Y_OFFSET + 470,
            sync_btn_width, sync_btn_height,
            "Синхронизировать", GREEN, DARK_GREEN, self.attempt_synchronization, border_radius=5
        )

        self.update_button_states()

    def draw(self, screen):
        pygame.draw.rect(screen, DARK_GRAY, (self.x_offset, self.PANEL_Y_OFFSET, self.PANEL_WIDTH, self.PANEL_HEIGHT), 2, border_radius=10)
        
        text_surf = FONT_LARGE.render(f"Генератор {self.id}", True, BLACK)
        text_rect = text_surf.get_rect(center=(self.x_offset + self.PANEL_WIDTH // 2, self.header_y))
        screen.blit(text_surf, text_rect)

        self.on_off_button.draw(screen)
        self.decrease_rpm_button.draw(screen)
        self.increase_rpm_button.draw(screen)
        self.sync_button.draw(screen)

        pygame.draw.rect(screen, BLACK, self.power_display_rect)
        power_text_color = GREEN if self.is_on else DARK_RED
        power_surf = FONT_7SEG.render(f"{self.power_output:03}", True, power_text_color)
        power_rect = power_surf.get_rect(center=self.power_display_rect.center)
        screen.blit(power_surf, power_rect)
        
        power_label_surf = FONT_SMALL.render("Мощность (кВ)", True, BLACK)
        power_label_rect = power_label_surf.get_rect(center=(self.x_offset + self.PANEL_WIDTH // 2, self.power_label_y))
        screen.blit(power_label_surf, power_label_rect)

        self.draw_synchronoscope(screen)

    def draw_synchronoscope(self, screen):
        center_x, center_y = self.synchronoscope_center
        radius = self.synchronoscope_radius

        pygame.draw.circle(screen, BLACK, (center_x, center_y), radius + 2, 2)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), radius)

        sync_zone_start_angle = 345
        sync_zone_end_angle = 15

        num_dots = 36
        dot_radius = 3
        for i in range(num_dots):
            angle_deg = (i * (360 / num_dots))
            angle_rad = math.radians(angle_deg - 90)

            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)

            dot_color = RED
            if (sync_zone_start_angle <= angle_deg < 360) or (0 <= angle_deg <= sync_zone_end_angle):
                dot_color = GREEN
            
            pygame.draw.circle(screen, dot_color, (int(x), int(y)), dot_radius)
        
        text_plus = FONT_SMALL.render("+", True, BLACK)
        text_minus = FONT_SMALL.render("-", True, BLACK)
        text_sync = FONT_SMALL.render("SYNC", True, GREEN)
        text_s = FONT_SYNC.render("S", True, BLACK)

        screen.blit(text_plus, text_plus.get_rect(center=(center_x - radius - 15, center_y))) 
        screen.blit(text_minus, text_minus.get_rect(center=(center_x + radius + 15, center_y))) 

        screen.blit(text_sync, text_sync.get_rect(center=(center_x, center_y - radius // 2 - 10))) 
        screen.blit(text_s, text_s.get_rect(center=(center_x, center_y))) 

        pygame.draw.line(screen, BLACK, (center_x - 30, center_y + 10), (center_x - 10, center_y + 30), 2)
        pygame.draw.line(screen, BLACK, (center_x + 30, center_y + 10), (center_x + 10, center_y + 30), 2)

        # Стрелка синхроноскопа
        if self.is_on and not self.synchronization_successful:
            hand_length = radius - 10
            angle_rad = math.radians(self.synchronoscope_angle - 90)
            end_x = center_x + hand_length * math.cos(angle_rad)
            end_y = center_y + hand_length * math.sin(angle_rad)
            pygame.draw.line(screen, BLACK, (center_x, center_y), (int(end_x), int(end_y)), 3)
            pygame.draw.circle(screen, BLACK, (center_x, center_y), 5)
        elif self.synchronization_successful:
            # Если синхронизация успешна, стрелка замирает на 0 градусов (вертикально вверх)
            hand_length = radius - 10
            angle_rad = math.radians(0 - 90) # 0 градусов = вертикально вверх
            end_x = center_x + hand_length * math.cos(angle_rad)
            end_y = center_y + hand_length * math.sin(angle_rad)
            pygame.draw.line(screen, BLACK, (center_x, center_y), (int(end_x), int(end_y)), 3)
            pygame.draw.circle(screen, BLACK, (center_x, center_y), 5)
        elif not self.is_on:
            pass

    def update(self):
        if self.is_on and not self.synchronization_successful:
            rotation_speed = self.rpm_adjustment_steps * 0.5
            self.synchronoscope_angle = (self.synchronoscope_angle + rotation_speed) % 360

    def handle_event(self, event):
        self.on_off_button.handle_event(event)
        self.decrease_rpm_button.handle_event(event)
        self.increase_rpm_button.handle_event(event)
        self.sync_button.handle_event(event)

    def toggle_power(self):
        if self.is_on:
            self.is_on = False
            self.power_output = 0
            self.rpm_adjustment_steps = 3
            self.synchronization_successful = False
            self.on_off_button.text = "ВКЛ"
            self.on_off_button.color = RED
        else:
            self.is_on = True
            self.on_off_button.text = "ВЫКЛ"
            self.on_off_button.color = GREEN
        self.update_button_states()

    def decrease_rpm(self):
        if self.is_on and not self.synchronization_successful:
            if self.rpm_adjustment_steps > -5: 
                self.rpm_adjustment_steps -= 1
                if self.rpm_adjustment_steps == -5:
                    self.is_on = False
                    self.power_output = 0
                    self.synchronization_successful = False
                    self.on_off_button.text = "ВКЛ"
                    self.on_off_button.color = RED
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, message="Генератор Остановлен", gen_id=self.id))
            else:
                pass
        self.update_button_states()

    def increase_rpm(self):
        if self.is_on and not self.synchronization_successful:
            if self.rpm_adjustment_steps < 5: 
                self.rpm_adjustment_steps += 1
            else:
                pass
        self.update_button_states()

    def is_in_sync_zone(self):
        current_angle = self.synchronoscope_angle
        if (345 <= current_angle < 360) or (0 <= current_angle <= 15):
            return True
        return False

    def attempt_synchronization(self):
        if not self.is_on:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, message="Ошибка Синхронизации", gen_id=self.id, detail="Генератор выключен."))
            return

        if self.is_in_sync_zone():
            self.power_output = 75
            self.synchronization_successful = True
            self.rpm_adjustment_steps = 0
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, message="Синхронизация Успешна", gen_id=self.id))
        else:
            self.is_on = False
            self.power_output = 0
            self.synchronization_successful = False
            self.rpm_adjustment_steps = 3
            self.on_off_button.text = "ВКЛ"
            self.on_off_button.color = RED
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, message="Ошибка Синхронизации", gen_id=self.id, detail="Не в зоне синхронизации. Генератор выключен."))
        self.update_button_states()

    def update_button_states(self):
        if self.is_on and not self.synchronization_successful:
            self.decrease_rpm_button.set_enabled(True)
            self.increase_rpm_button.set_enabled(True)
            self.sync_button.set_enabled(True)
        else:
            self.decrease_rpm_button.set_enabled(False)
            self.increase_rpm_button.set_enabled(False)
            self.sync_button.set_enabled(False)

        if self.synchronization_successful:
             self.on_off_button.set_enabled(False)
        else:
            self.on_off_button.set_enabled(True)

# --- Главный класс симулятора ---
class Simulator:
    def __init__(self):
        self.generators = []
        for i in range(1, 4):
            total_panels_width = Generator.PANEL_WIDTH * 3 + 2 * 30
            
            start_x_for_first_gen = (SCREEN_WIDTH - total_panels_width) // 2
            
            x_offset = start_x_for_first_gen + (i - 1) * (Generator.PANEL_WIDTH + 30) 
            self.generators.append(Generator(i, x_offset))

        self.running = True
        self.clock = pygame.time.Clock()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.USEREVENT:
                    pass

                for gen in self.generators:
                    gen.handle_event(event)

            SCREEN.fill(LIGHT_GRAY)

            for gen in self.generators:
                gen.update()
                gen.draw(SCREEN)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    sim = Simulator()
    sim.run()