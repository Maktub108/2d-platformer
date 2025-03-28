import pygame
import random
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Type
from custom_logging.logger import Logger

# Типы для аннотаций
Color = Tuple[int, int, int]
Position = Tuple[int, int]
Size = Tuple[int, int]


class GameObject(ABC):
    """Базовый класс для всех игровых объектов"""

    def __init__(self, position: Position, size: Size, logger: Logger = None):
        self.rect = pygame.Rect(position[0], position[1], size[0], size[1])
        self.is_active = True
        self.logger = logger.getChild(self.__class__.__name__) if logger else Logger(self.__class__.__name__)
        self.logger.debug(f"Created at {position}")

    @abstractmethod
    def update(self):
        """Обновление состояния объекта"""
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        """Отрисовка объекта"""
        pass

    def check_collision(self, other_rect: pygame.Rect) -> bool:
        """Проверка коллизии с другим объектом"""
        collision = self.rect.colliderect(other_rect)
        if collision:
            self.logger.debug(f"Collision detected at {other_rect.topleft}")
        return collision


class Obstacle(GameObject):
    """Базовый класс препятствий"""
    pass


class Spike(Obstacle):
    """Статичные шипы"""

    def __init__(self, position: Position, logger: Logger = None):
        super().__init__(position, (32, 32), logger)
        self.color = (139, 0, 0)  # Темно-красный
        self.logger.info(f"Spike created at {position}")

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        pygame.draw.polygon(surface, self.color, [
            (self.rect.left, self.rect.bottom),
            (self.rect.centerx, self.rect.top),
            (self.rect.right, self.rect.bottom)
        ])


class Pit(Obstacle):
    """Ямы различной ширины"""

    def __init__(self, position: Position, width: int, logger: Logger = None):
        super().__init__(position, (width, 50), logger)
        self.color = (0, 0, 0)  # Черный
        self.logger.info(f"Pit created (width={width}) at {position}")

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect)


class MovingObstacle(Obstacle):
    """Движущиеся препятствия"""

    def __init__(self, position: Position, size: Size, move_range: int, logger: Logger = None):
        super().__init__(position, size, logger)
        self.original_x = position[0]
        self.move_range = move_range
        self.speed = 2
        self.direction = 1
        self.color = (255, 165, 0)  # Оранжевый
        self.logger.info(f"Moving obstacle created (range={move_range}) at {position}")

    def update(self):
        self.rect.x += self.speed * self.direction

        if self.rect.x > self.original_x + self.move_range:
            self.direction = -1
            self.logger.debug("Changed direction to left")
        elif self.rect.x < self.original_x - self.move_range:
            self.direction = 1
            self.logger.debug("Changed direction to right")

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect)


class Bonus(GameObject):
    """Базовый класс бонусов"""

    def __init__(self, position: Position, size: Size, points: int, logger: Logger = None):
        super().__init__(position, size, logger)
        self.points = points

    def collect(self) -> int:
        """Сбор бонуса"""
        self.is_active = False
        self.logger.info(f"Collected! +{self.points} points")
        return self.points


class Coin(Bonus):
    """Обычные монеты (100 очков)"""

    def __init__(self, position: Position, logger: Logger = None):
        super().__init__(position, (16, 16), 100, logger)
        self.color = (255, 215, 0)  # Золотой
        self.logger.debug(f"Coin created at {position}")

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, self.rect.center, self.rect.width // 2)


class SpecialBonus(Bonus):
    """Специальные бонусы (500 очков)"""

    def __init__(self, position: Position, logger: Logger = None):
        super().__init__(position, (24, 24), 500, logger)
        self.color = (0, 255, 255)  # Голубой
        self.animation_counter = 0
        self.logger.debug(f"Special bonus created at {position}")

    def update(self):
        self.animation_counter = (self.animation_counter + 0.1) % 360
        size_factor = 1 + 0.1 * abs(pygame.math.Vector2(1, 0).rotate(self.animation_counter).x)
        self.rect.width = int(24 * size_factor)
        self.rect.height = int(24 * size_factor)

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, self.rect.center, self.rect.width // 2)


class Level(ABC):
    """Абстрактный базовый класс уровня"""

    def __init__(self, level_num: int, screen_size: Tuple[int, int], logger: Logger):
        self.logger = logger.getChild(f'level_{level_num}')
        self.logger.info(f"Initializing level {level_num}")

        self.level_num = level_num
        self.screen_width, self.screen_height = screen_size
        self.difficulty = level_num
        self.completed = False
        self.score = 0

        self.obstacles: List[Obstacle] = []
        self.bonuses: List[Bonus] = []

        self.player_start_pos = (100, screen_size[1] - 100)
        self.finish_rect = pygame.Rect(screen_size[0] - 100, screen_size[1] - 150, 50, 100)

        self.generate_level()
        self.logger.info(f"Level generated with {len(self.obstacles)} obstacles and {len(self.bonuses)} bonuses")

    @abstractmethod
    def generate_level(self):
        """Генерация элементов уровня"""
        self.logger.debug("Starting level generation")

    def update(self):
        """Обновление уровня"""
        active_count = 0
        for obj in self.obstacles + self.bonuses:
            if obj.is_active:
                obj.update()
                active_count += 1
        self.logger.debug(f"Updated {active_count} active objects")

    def draw(self, surface: pygame.Surface):
        """Отрисовка уровня"""
        try:
            surface.fill((50, 50, 70))  # Фон

            for obj in self.obstacles + self.bonuses:
                if obj.is_active:
                    obj.draw(surface)

            pygame.draw.rect(surface, (0, 255, 0), self.finish_rect)  # Финиш
            self.logger.debug("Level rendered")
        except Exception as e:
            self.logger.error(f"Rendering error: {str(e)}", exc_info=True)
            raise

    def check_finish(self, player_rect: pygame.Rect) -> bool:
        """Проверка достижения финиша"""
        finished = player_rect.colliderect(self.finish_rect)
        if finished:
            self.completed = True
            self.logger.info("Player reached finish")
        return finished

    def collect_bonuses(self, player_rect: pygame.Rect) -> int:
        """Сбор бонусов игроком"""
        collected = 0
        for bonus in self.bonuses:
            if bonus.is_active and bonus.check_collision(player_rect):
                collected += bonus.collect()
                self.score += bonus.points

        if collected > 0:
            self.logger.info(f"Collected bonuses: +{collected} points")

        return collected

    def get_active_bonuses(self) -> int:
        """Количество оставшихся бонусов"""
        count = sum(1 for b in self.bonuses if b.is_active)
        self.logger.debug(f"{count} bonuses remaining")
        return count


class Level1(Level):
    """Первый уровень (базовый)"""

    def generate_level(self):
        super().generate_level()

        # Препятствия (10 штук)
        for i in range(10):
            try:
                obstacle_type = random.choice([Spike, Pit, MovingObstacle])

                if obstacle_type == Spike:
                    x = random.randint(200, self.screen_width - 100)
                    y = self.screen_height - 50
                    self.obstacles.append(Spike((x, y), self.logger))

                elif obstacle_type == Pit:
                    width = random.randint(50, 150)
                    x = random.randint(200, self.screen_width - width - 100)
                    y = self.screen_height - 50
                    self.obstacles.append(Pit((x, y), width, self.logger))

                elif obstacle_type == MovingObstacle:
                    x = random.randint(200, self.screen_width - 200)
                    y = random.randint(100, self.screen_height - 150)
                    size = (random.randint(30, 60), random.randint(30, 60))
                    move_range = random.randint(50, 150)
                    self.obstacles.append(MovingObstacle((x, y), size, move_range, self.logger))

                self.logger.debug(f"Created obstacle {i + 1}/{10}")
            except Exception as e:
                self.logger.error(f"Failed to create obstacle: {str(e)}")

        # Бонусы (20 монет)
        for i in range(20):
            try:
                x = random.randint(150, self.screen_width - 150)
                y = random.randint(50, self.screen_height - 100)
                self.bonuses.append(Coin((x, y), self.logger))
                self.logger.debug(f"Created coin {i + 1}/{20}")
            except Exception as e:
                self.logger.error(f"Failed to create coin: {str(e)}")


class Level2(Level1):
    """Второй уровень (увеличенная сложность)"""

    def generate_level(self):
        super().generate_level()

        # Дополнительные препятствия (10 штук)
        for i in range(10):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(100, self.screen_height - 150)
                size = (random.randint(30, 60), random.randint(30, 60))
                move_range = random.randint(50, 200)
                self.obstacles.append(MovingObstacle((x, y), size, move_range, self.logger))
                self.logger.debug(f"Added moving obstacle {i + 1}/{10}")
            except Exception as e:
                self.logger.error(f"Failed to add moving obstacle: {str(e)}")

        # Дополнительные бонусы (20 монет + 2 спецбонуса)
        for i in range(20):
            try:
                x = random.randint(150, self.screen_width - 150)
                y = random.randint(50, self.screen_height - 100)
                self.bonuses.append(Coin((x, y), self.logger))
                self.logger.debug(f"Added coin {i + 1}/{20}")
            except Exception as e:
                self.logger.error(f"Failed to add coin: {str(e)}")

        for i in range(2):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(100, self.screen_height - 150)
                self.bonuses.append(SpecialBonus((x, y), self.logger))
                self.logger.debug(f"Added special bonus {i + 1}/{2}")
            except Exception as e:
                self.logger.error(f"Failed to add special bonus: {str(e)}")


# Аналогично реализуем Level3-Level5 с прогрессирующей сложностью
class Level3(Level2):
    """Третий уровень"""

    def generate_level(self):
        super().generate_level()
        # Добавляем больше движущихся препятствий
        for i in range(10):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(50, self.screen_height - 200)
                size = (random.randint(20, 40), random.randint(20, 40))
                move_range = random.randint(100, 250)
                self.obstacles.append(MovingObstacle((x, y), size, move_range, self.logger))
                self.logger.debug(f"Added fast obstacle {i + 1}/{10}")
            except Exception as e:
                self.logger.error(f"Failed to add fast obstacle: {str(e)}")

        # Добавляем больше бонусов
        for i in range(20):
            try:
                x = random.randint(150, self.screen_width - 150)
                y = random.randint(50, self.screen_height - 100)
                self.bonuses.append(Coin((x, y), self.logger))
                self.logger.debug(f"Added coin {i + 1}/{20}")
            except Exception as e:
                self.logger.error(f"Failed to add coin: {str(e)}")

        for i in range(3):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(100, self.screen_height - 150)
                self.bonuses.append(SpecialBonus((x, y), self.logger))
                self.logger.debug(f"Added special bonus {i + 1}/{3}")
            except Exception as e:
                self.logger.error(f"Failed to add special bonus: {str(e)}")


class Level4(Level3):
    """Четвертый уровень"""

    def generate_level(self):
        super().generate_level()
        # Добавляем шипы на платформы
        for i in range(10):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(50, self.screen_height - 200)
                self.obstacles.append(Spike((x, y), self.logger))
                self.logger.debug(f"Added spike {i + 1}/{10}")
            except Exception as e:
                self.logger.error(f"Failed to add spike: {str(e)}")

        # Добавляем бонусы
        for i in range(20):
            try:
                x = random.randint(150, self.screen_width - 150)
                y = random.randint(50, self.screen_height - 100)
                self.bonuses.append(Coin((x, y), self.logger))
                self.logger.debug(f"Added coin {i + 1}/{20}")
            except Exception as e:
                self.logger.error(f"Failed to add coin: {str(e)}")

        for i in range(4):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(100, self.screen_height - 150)
                self.bonuses.append(SpecialBonus((x, y), self.logger))
                self.logger.debug(f"Added special bonus {i + 1}/{4}")
            except Exception as e:
                self.logger.error(f"Failed to add special bonus: {str(e)}")


class Level5(Level4):
    """Пятый уровень (максимальная сложность)"""

    def generate_level(self):
        super().generate_level()
        # Добавляем широкие ямы
        for i in range(10):
            try:
                width = random.randint(80, 200)
                x = random.randint(200, self.screen_width - width - 100)
                y = self.screen_height - 50
                self.obstacles.append(Pit((x, y), width, self.logger))
                self.logger.debug(f"Added wide pit {i + 1}/{10}")
            except Exception as e:
                self.logger.error(f"Failed to add wide pit: {str(e)}")

        # Добавляем бонусы
        for i in range(20):
            try:
                x = random.randint(150, self.screen_width - 150)
                y = random.randint(50, self.screen_height - 100)
                self.bonuses.append(Coin((x, y), self.logger))
                self.logger.debug(f"Added coin {i + 1}/{20}")
            except Exception as e:
                self.logger.error(f"Failed to add coin: {str(e)}")

        for i in range(5):
            try:
                x = random.randint(200, self.screen_width - 200)
                y = random.randint(100, self.screen_height - 150)
                self.bonuses.append(SpecialBonus((x, y), self.logger))
                self.logger.debug(f"Added special bonus {i + 1}/{5}")
            except Exception as e:
                self.logger.error(f"Failed to add special bonus: {str(e)}")


class LevelManager:
    """Менеджер уровней"""

    def __init__(self, screen_size: Tuple[int, int], logger: Logger):
        self.logger = logger.getChild('level_manager')
        self.screen_size = screen_size
        self.current_level_num = 1
        self.total_score = 0
        self.current_level = self._create_level()
        self.logger.info("Level manager initialized")

    def _create_level(self) -> Level:
        """Создание уровня по номеру"""
        level_classes = {
            1: Level1,
            2: Level2,
            3: Level3,
            4: Level4,
            5: Level5
        }
        self.logger.info(f"Creating level {self.current_level_num}")
        return level_classes[self.current_level_num](
            self.current_level_num,
            self.screen_size,
            self.logger
        )

    def next_level(self) -> bool:
        """Переход на следующий уровень"""
        self.total_score += self.current_level.score
        self.logger.info(f"Completed level {self.current_level_num} (Score: {self.current_level.score})")

        if self.current_level_num < 5:
            self.current_level_num += 1
            self.current_level = self._create_level()
            return True

        self.logger.info("All levels completed!")
        return False

    def update(self):
        """Обновление текущего уровня"""
        self.current_level.update()

    def draw(self, surface: pygame.Surface):
        """Отрисовка текущего уровня"""
        self.current_level.draw(surface)

    def is_game_complete(self) -> bool:
        """Проверка завершения игры"""
        return self.current_level_num == 5 and self.current_level.completed

    def get_level_completion_message(self) -> str:
        """Сообщение о завершении уровня"""
        if self.current_level.completed:
            if self.current_level_num < 5:
                msg = f"Level {self.current_level_num} completed! Score: {self.total_score}"
            else:
                msg = f"Game completed! Final score: {self.total_score}"
            self.logger.info(msg)
            return msg
        return ""