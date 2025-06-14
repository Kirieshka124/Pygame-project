import pygame
import random
import math
import os
from pygame import gfxdraw

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotline Podolsk")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)


# Загрузка спрайтов
def load_image(name, scale=0.3, angle=0):
    try:
        image = pygame.image.load(f"assets/{name}.png").convert_alpha()
        if scale != 1.0:
            size = image.get_size()
            image = pygame.transform.scale(image, (int(size[0] * scale), int(size[1] * scale)))
            if angle != 0:
                image = pygame.transform.rotate(image, angle)
        return image
    except:
        # Если изображение не найдено, создаем заглушку
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(surf, BLUE if "player" in name else RED, (15, 15), 15)
        return surf


# Создаем папку assets, если её нет
if not os.path.exists("assets"):
    os.makedirs("assets")


# Игрок
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 15
        self.speed = 5
        self.color = BLUE
        self.health = 100
        self.max_health = 100
        self.bullets = []
        self.shoot_cooldown = 0
        self.special_attacks = 0
        self.angle = 0
        self.image = load_image("player")
        self.original_image = self.image
        self.last_dx, self.last_dy = 0, 0

    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_a] and self.x - self.radius > 0:
            dx -= self.speed
        if keys[pygame.K_d] and self.x + self.radius < WIDTH:
            dx += self.speed
        if keys[pygame.K_w] and self.y - self.radius > 0:
            dy -= self.speed
        if keys[pygame.K_s] and self.y + self.radius < HEIGHT:
            dy += self.speed

        if dx != 0 or dy != 0:
            self.last_dx, self.last_dy = dx, dy
            self.angle = math.degrees(math.atan2(dy, dx)) - 90
            self.image = pygame.transform.rotate(self.original_image, -self.angle)

        self.x += dx
        self.y += dy

    def shoot(self, target_x, target_y):
        if self.shoot_cooldown == 0:
            dx = target_x - self.x
            dy = target_y - self.y
            distance = max(1, math.sqrt(dx * dx + dy * dy))
            dx, dy = dx / distance * 10, dy / distance * 10  # Нормализация

            self.bullets.append({
                'x': self.x,
                'y': self.y,
                'dx': dx,
                'dy': dy,
                'radius': 5,
                'type': 'normal'
            })
            self.shoot_cooldown = 10

    def use_special_attack(self, target_x, target_y):
        if self.special_attacks > 0:
            self.bullets.append({
                'x': self.x,
                'y': self.y,
                'target_x': target_x,
                'target_y': target_y,
                'radius': 10,
                'type': 'explosive',
                'timer': 30,
                'exploded': False,
                'explosion_radius': 100,
                'contact_explode': True
            })
            self.special_attacks -= 1

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Обновление пуль
        for bullet in self.bullets[:]:
            if bullet['type'] == 'normal':
                bullet['x'] += bullet['dx']
                bullet['y'] += bullet['dy']

                # Удаление пуль за пределами экрана
                if (bullet['x'] < 0 or bullet['x'] > WIDTH or
                        bullet['y'] < 0 or bullet['y'] > HEIGHT):
                    self.bullets.remove(bullet)

            elif bullet['type'] == 'explosive':
                if not bullet['exploded']:
                    # Летит к цели
                    dx = bullet['target_x'] - bullet['x']
                    dy = bullet['target_y'] - bullet['y']
                    dist = max(1, math.sqrt(dx * dx + dy * dy))

                    if dist < 10:  # Достиг цели
                        bullet['exploded'] = True
                    else:
                        bullet['x'] += dx / dist * 8
                        bullet['y'] += dy / dist * 8
                else:
                    # Анимация взрыва
                    bullet['timer'] -= 1
                    if bullet['timer'] <= 0:
                        self.bullets.remove(bullet)

    def draw(self, screen):
        # Рисуем спрайт игрока
        img_rect = self.image.get_rect(center=(self.x, self.y))
        screen.blit(self.image, img_rect)

        # Отрисовка здоровья
        pygame.draw.rect(screen, RED, (self.x - 20, self.y - 30, 40, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 20, self.y - 30, 40 * (self.health / self.max_health), 5))

        # Отрисовка пуль
        for bullet in self.bullets:
            if bullet['type'] == 'normal':
                pygame.draw.circle(screen, BLACK, (int(bullet['x']), int(bullet['y'])), bullet['radius'])
            elif bullet['type'] == 'explosive':
                if not bullet['exploded']:
                    pygame.draw.circle(screen, ORANGE, (int(bullet['x']), int(bullet['y'])), bullet['radius'])
                else:
                    # Анимация взрыва
                    alpha = int(255 * bullet['timer'] / 30)
                    for r in range(bullet['explosion_radius'], 0, -10):
                        color = (255, min(165, 165 + r), 0, alpha)
                        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(surf, color, (r, r), r)
                        screen.blit(surf, (bullet['x'] - r, bullet['y'] - r))



class Enemy:
    def __init__(self):
        side = random.randint(0, 3)
        if side == 0:  # Сверху
            self.x = random.randint(0, WIDTH)
            self.y = -20
        elif side == 1:  # Справа
            self.x = WIDTH + 20
            self.y = random.randint(0, HEIGHT)
        elif side == 2:  # Снизу
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + 20
        else:  # Слева
            self.x = -20
            self.y = random.randint(0, HEIGHT)

        self.radius = 15
        self.speed = random.uniform(1.0, 3.0)
        self.color = RED
        self.health = 30
        self.max_health = 30
        self.angle = 0
        self.image = load_image("enemy")
        self.original_image = self.image

    def move(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        distance = max(1, math.sqrt(dx * dx + dy * dy))
        dx, dy = dx / distance * self.speed, dy / distance * self.speed

        # Обновления угла поворота
        if dx != 0 or dy != 0:
            self.angle = math.degrees(math.atan2(dy, dx)) - 90
            self.image = pygame.transform.rotate(self.original_image, -self.angle)

        self.x += dx
        self.y += dy

    def draw(self, screen):
        # Отрисовка спрайта врага
        img_rect = self.image.get_rect(center=(self.x, self.y))
        screen.blit(self.image, img_rect)

        # Рисование здоровья
        pygame.draw.rect(screen, RED, (self.x - 15, self.y - 25, 30, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 15, self.y - 25, 30 * (self.health / self.max_health), 5))


# Пьяный мастер (уворачивается от первых двух пуль)
class DrunkenMaster(Enemy):
    def __init__(self):
        super().__init__()
        self.color = CYAN
        self.speed = random.uniform(2.0, 4.0)
        self.health = 40
        self.max_health = 40
        self.dodge_count = 2  # Количество уворотов от пуль
        self.type = "drunken"
        self.direction_change_timer = 0
        self.random_angle = random.uniform(0, 2 * math.pi)
        self.dodge_vector = [0, 0]
        self.dodge_timer = 0
        self.image = load_image("drunken_master")
        self.original_image = self.image

    def move(self, player_x, player_y):
        # Если есть активный уворот
        if self.dodge_timer > 0:
            self.x += self.dodge_vector[0]
            self.y += self.dodge_vector[1]
            self.dodge_timer -= 1

            # Обновление угла поворота при увороте
            if self.dodge_vector[0] != 0 or self.dodge_vector[1] != 0:
                self.angle = math.degrees(math.atan2(self.dodge_vector[1], self.dodge_vector[0])) - 90
                self.image = pygame.transform.rotate(self.original_image, -self.angle)
        else:
            # Хаотичное движение
            if self.direction_change_timer <= 0:
                self.random_angle = random.uniform(0, 2 * math.pi)
                self.direction_change_timer = random.randint(10, 30)
            else:
                self.direction_change_timer -= 1

            # Движение к игроку с случайными отклонениями
            dx = player_x - self.x + math.cos(self.random_angle) * 50
            dy = player_y - self.y + math.sin(self.random_angle) * 50
            distance = max(1, math.sqrt(dx * dx + dy * dy))
            dx, dy = dx / distance * self.speed, dy / distance * self.speed

            # Обновление угла поворота
            if dx != 0 or dy != 0:
                self.angle = math.degrees(math.atan2(dy, dx)) - 90
                self.image = pygame.transform.rotate(self.original_image, -self.angle)

            self.x += dx
            self.y += dy

    def check_bullet_dodge(self, bullet_x, bullet_y, bullet_dx, bullet_dy):
        if self.dodge_count <= 0 or self.dodge_timer > 0:
            return False

        # Проверка пули игрока
        future_bullet_x = bullet_x + bullet_dx * 10
        future_bullet_y = bullet_y + bullet_dy * 10
        future_dist = math.sqrt((future_bullet_x - self.x) ** 2 + (future_bullet_y - self.y) ** 2)

        if future_dist < 50:  # Пуля близко и летит в нашу сторону
            # Вычисление направления для уворота
            bullet_angle = math.atan2(bullet_dy, bullet_dx)
            dodge_angle = bullet_angle + (math.pi / 2 if random.random() > 0.5 else -math.pi / 2)

            self.dodge_vector = [
                math.cos(dodge_angle) * self.speed * 2,
                math.sin(dodge_angle) * self.speed * 2
            ]
            self.dodge_timer = 15  # Длительность уворота
            self.dodge_count -= 1
            return True
        return False


# Снайпер (атакует издалека)
class Sniper(Enemy):
    def __init__(self):
        super().__init__()
        self.color = YELLOW
        self.speed = 1.0
        self.shoot_cooldown = 0
        self.bullets = []
        self.image = load_image("sniper")
        self.original_image = self.image

    def move(self, player_x, player_y):
        # Держит дистанцию от игрока
        dx = player_x - self.x
        dy = player_y - self.y
        distance = max(1, math.sqrt(dx * dx + dy * dy))

        if distance < 300:  # Слишком близко - отходит
            self.x -= dx / distance * self.speed
            self.y -= dy / distance * self.speed
        elif distance > 400:  # Слишком далеко - подходит
            self.x += dx / distance * self.speed
            self.y += dy / distance * self.speed

        # Обновление угла поворота
        if dx != 0 or dy != 0:
            self.angle = math.degrees(math.atan2(dy, dx)) - 90
            self.image = pygame.transform.rotate(self.original_image, -self.angle)

        # Стрельба
        if self.shoot_cooldown <= 0 and distance < 500:
            self.bullets.append({
                'x': self.x,
                'y': self.y,
                'dx': dx / distance * 7,
                'dy': dy / distance * 7,
                'radius': 5
            })
            self.shoot_cooldown = 60  # 1 выстрел в секунду
        else:
            self.shoot_cooldown -= 1

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']

            if (bullet['x'] < 0 or bullet['x'] > WIDTH or
                    bullet['y'] < 0 or bullet['y'] > HEIGHT):
                self.bullets.remove(bullet)

    def draw(self, screen):
        # Рисуем спрайт снайпера
        img_rect = self.image.get_rect(center=(self.x, self.y))
        screen.blit(self.image, img_rect)

        # Отрисовка здоровья
        pygame.draw.rect(screen, RED, (self.x - 15, self.y - 25, 30, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 15, self.y - 25, 30 * (self.health / self.max_health), 5))

        for bullet in self.bullets:
            pygame.draw.circle(screen, YELLOW, (int(bullet['x']), int(bullet['y'])), bullet['radius'])


# Аптечка
class Medkit:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.radius = 10
        self.heal_amount = 25
        self.active = True
        self.lifetime = 360  # 6 секунд (60 кадров/сек * 6 сек)
        self.blink_timer = 0  # Таймер для мигания
        self.visible = True  # Видимость при мигании
        self.image = load_image("medkit", scale=0.5)

    def update(self):
        if self.active:
            self.lifetime -= 1
            self.blink_timer += 1

            # Мигание в последние 2 секунды (120 кадров)
            if self.lifetime <= 120:
                # Мигаем с частотой 10 кадров (5 раз в секунду)
                self.visible = self.blink_timer % 10 < 5

            if self.lifetime <= 0:
                self.active = False

    def draw(self, screen):
        if self.active and self.visible:
            img_rect = self.image.get_rect(center=(self.x, self.y))
            screen.blit(self.image, img_rect)


# Граната (специальная атака)
class SpecialAttackItem:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.radius = 12
        self.active = True
        self.animation_timer = 0
        self.lifetime = 360  # 6 секунд
        self.blink_timer = 0  # Таймер для мигания
        self.visible = True  # Видимость при мигании
        self.image = load_image("special", scale=0.6)

    def update(self):
        if self.active:
            self.animation_timer = (self.animation_timer + 1) % 60
            self.lifetime -= 1
            self.blink_timer += 1

            # Мигание в последние 2 секунды (120 кадров)
            if self.lifetime <= 120:
                # Мигание с частотой 10 кадров (5 раз в секунду)
                self.visible = self.blink_timer % 10 < 5

            if self.lifetime <= 0:
                self.active = False

    def draw(self, screen):
        if self.active and self.visible:
            pulse = 1 + 0.2 * math.sin(self.animation_timer * 0.1)
            scaled_img = pygame.transform.scale(
                self.image,
                (int(self.image.get_width() * pulse),
                 int(self.image.get_height() * pulse))
            )
            img_rect = scaled_img.get_rect(center=(self.x, self.y))
            screen.blit(scaled_img, img_rect)


# Игровой цикл
def game_loop():
    player = Player()
    enemies = []
    medkits = []
    special_items = []
    score = 0
    game_time = 0
    enemy_spawn_timer = 0
    item_spawn_timer = 0
    font = pygame.font.SysFont(None, 36)
    clock = pygame.time.Clock()
    running = True

    # Загрузка фона
    try:
        background = pygame.image.load("assets/background.jpg").convert()
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    except:
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((50, 50, 50))  # Серый фон, если изображение не найдено

    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    player.shoot(mouse_x, mouse_y)
                elif event.button == 3 and player.special_attacks > 0:  # Правая кнопка мыши
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    player.use_special_attack(mouse_x, mouse_y)

        # Управление игроком
        keys = pygame.key.get_pressed()
        player.move(keys)
        player.update()

        # Обновление времени игры
        game_time += 1

        # Спавн врагов
        enemy_spawn_timer += 1
        if enemy_spawn_timer >= 60:  # Каждую секунду
            # После 30 секунд появляется пьяный мастер
            if game_time >= 1800 and random.random() < 0.3:  # 30% шанс
                enemies.append(DrunkenMaster())
            # После 45 секунд появляется снайпер
            elif game_time >= 2700 and random.random() < 0.2:  # 20% шанс
                enemies.append(Sniper())
            else:
                enemies.append(Enemy())
            enemy_spawn_timer = 0

        # Спавн предметов
        item_spawn_timer += 1
        if item_spawn_timer >= 600:  # Каждые 10 секунд
            if random.random() < 0.7:  # 70% шанс на аптечку
                medkits.append(Medkit())
            else:  # 30% шанс на спец атаку
                special_items.append(SpecialAttackItem())
            item_spawn_timer = 0

        # Обновление предметов
        for medkit in medkits[:]:
            medkit.update()
            if not medkit.active:
                medkits.remove(medkit)

            # Проверка подбора аптечки
            if medkit.active and medkit.visible:
                dx = player.x - medkit.x
                dy = player.y - medkit.y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < player.radius + medkit.radius:
                    player.health = min(player.max_health, player.health + medkit.heal_amount)
                    medkit.active = False
                    medkits.remove(medkit)

        for special in special_items[:]:
            special.update()
            if not special.active:
                special_items.remove(special)

            # Проверка подбора гранаты
            if special.active and special.visible:
                dx = player.x - special.x
                dy = player.y - special.y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < player.radius + special.radius:
                    player.special_attacks += 1
                    special.active = False
                    special_items.remove(special)

        # Обновление врагов
        for enemy in enemies[:]:
            if isinstance(enemy, DrunkenMaster):
                enemy.move(player.x, player.y)

                # Проверка попадания пуль игрока
                for bullet in player.bullets[:]:
                    if bullet['type'] == 'normal':
                        # Пьяный мастер пытается увернуться от первых двух пуль
                        if enemy.dodge_count > 0:
                            if enemy.check_bullet_dodge(bullet['x'], bullet['y'], bullet['dx'], bullet['dy']):
                                continue  # Пропускаем проверку попадания, если уворот успешен

                        dx = bullet['x'] - enemy.x
                        dy = bullet['y'] - enemy.y
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance < bullet['radius'] + enemy.radius:
                            enemy.health -= 10
                            if bullet in player.bullets:
                                player.bullets.remove(bullet)
                            if enemy.health <= 0:
                                enemies.remove(enemy)
                                score += 15
                            break
            elif isinstance(enemy, Sniper):
                enemy.move(player.x, player.y)
                enemy.update_bullets()

                # Проверка попадания пуль снайпера в игрока
                for bullet in enemy.bullets[:]:
                    dx = player.x - bullet['x']
                    dy = player.y - bullet['y']
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance < player.radius + bullet['radius']:
                        player.health -= 15
                        enemy.bullets.remove(bullet)
            else:
                enemy.move(player.x, player.y)

            # Проверка столкновения с игроком
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < player.radius + enemy.radius:
                player.health -= 10
                enemies.remove(enemy)
                if player.health <= 0:
                    running = False

            # Проверка попадания пуль игрока (для обычных врагов)
            if not isinstance(enemy, DrunkenMaster):
                for bullet in player.bullets[:]:
                    if bullet['type'] == 'normal':
                        dx = bullet['x'] - enemy.x
                        dy = bullet['y'] - enemy.y
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance < bullet['radius'] + enemy.radius:
                            enemy.health -= 10
                            if bullet in player.bullets:
                                player.bullets.remove(bullet)
                            if enemy.health <= 0:
                                enemies.remove(enemy)
                                score += 10
                            break
                    elif bullet['type'] == 'explosive':
                        if bullet['contact_explode'] and not bullet['exploded']:
                            # Проверка контакта с врагом для взрыва
                            dx = bullet['x'] - enemy.x
                            dy = bullet['y'] - enemy.y
                            distance = math.sqrt(dx * dx + dy * dy)
                            if distance < bullet['radius'] + enemy.radius:
                                bullet['exploded'] = True

                        if bullet['exploded']:
                            # Проверка попадания в зоне взрыва
                            dx = bullet['x'] - enemy.x
                            dy = bullet['y'] - enemy.y
                            distance = math.sqrt(dx * dx + dy * dy)
                            if distance < bullet['explosion_radius']:
                                enemy.health -= 20
                                if enemy.health <= 0:
                                    enemies.remove(enemy)
                                    score += 15 if isinstance(enemy, (DrunkenMaster, Sniper)) else 10

        # Отрисовка
        screen.blit(background, (0, 0))

        # Отрисовка предметов перед игроком и врагами
        for medkit in medkits:
            medkit.draw(screen)

        for special in special_items:
            special.draw(screen)

        # Игрок
        player.draw(screen)

        # Враги
        for enemy in enemies:
            enemy.draw(screen)
            if isinstance(enemy, Sniper):
                for bullet in enemy.bullets:
                    pygame.draw.circle(screen, YELLOW, (int(bullet['x']), int(bullet['y'])), bullet['radius'])

        # Отрисовка интерфейса
        # Полупрозрачная панель для интерфейса
        s = pygame.Surface((200, 140))  # Размер панели
        s.set_alpha(128)  # Прозрачность
        s.fill((50, 50, 50))  # Цвет
        screen.blit(s, (5, 5))  # Позиция

        # Отрисовка счета
        score_text = font.render(f"Счет: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Отрисовка здоровья
        health_text = font.render(f"Здоровье: {player.health}", True, WHITE)
        screen.blit(health_text, (10, 50))

        # Отрисовка гранат
        special_text = font.render(f"Гранаты: {player.special_attacks}", True, WHITE)
        screen.blit(special_text, (10, 90))

        # Отрисовка времени
        minutes = game_time // 3600
        seconds = (game_time % 3600) // 60
        time_text = font.render(f"Время: {minutes:02d}:{seconds:02d}", True, WHITE)
        screen.blit(time_text, (10, 130))

        pygame.display.flip()
        clock.tick(60)

    # Конец игры
    screen.fill(BLACK)
    game_over_text = font.render(f"Игра окончена! Ваш счет: {score}", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(3000)


# Запуск игры
game_loop()
pygame.quit()