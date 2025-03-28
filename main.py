import pygame
import sys
from custom_logging.logger import Logger
from levels import LevelManager, Spike, Pit


class DemoPlayer:
    """Демонстрационный игрок для автоматической прокрутки"""

    def __init__(self, logger: Logger):
        self.rect = pygame.Rect(100, 500, 30, 50)
        self.speed = 3
        self.is_moving = True
        self.color = (255, 0, 0)
        self.logger = logger.getChild('player')
        self.logger.info("Player initialized")

    def update(self, level):
        if not self.is_moving:
            return

        self.rect.x += self.speed

        # Проверка столкновений (упрощенная)
        for obstacle in level.obstacles:
            if obstacle.is_active and obstacle.check_collision(self.rect):
                if isinstance(obstacle, Spike):
                    self.logger.warning("Player hit a spike!")
                elif isinstance(obstacle, Pit):
                    self.logger.warning("Player fell into a pit!")

        # Сбор бонусов
        collected = level.collect_bonuses(self.rect)
        if collected > 0:
            self.logger.info(f"Collected {collected} points")

        # Проверка финиша
        if level.check_finish(self.rect):
            self.is_moving = False
            self.logger.info("Player reached finish")

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


def initialize_logger():
    """Инициализация логгера с обработкой разных случаев"""
    try:
        # Пробуем разные варианты инициализации
        try:
            logger = Logger('main')  # Если логгер принимает имя
        except TypeError:
            logger = Logger()  # Если логгер без параметров
        logger.info("Logger initialized successfully")
        return logger
    except Exception as e:
        print(f"CRITICAL: Failed to initialize logger: {str(e)}")

        # Фолбэк-логгер
        class FallbackLogger:
            def __init__(self): self.name = "fallback"

            def info(self, msg): print(f"[INFO] {msg}")

            def debug(self, msg): print(f"[DEBUG] {msg}")

            def warning(self, msg): print(f"[WARN] {msg}")

            def error(self, msg): print(f"[ERROR] {msg}")

            def getChild(self, name): return self

        return FallbackLogger()


def main():
    """Основная функция игры"""
    # Инициализация логгера
    logger = initialize_logger()

    try:
        logger.info("Starting game initialization")

        # Инициализация Pygame
        pygame.init()
        SCREEN_WIDTH = 800
        SCREEN_HEIGHT = 600
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D Platformer - Level Demo")
        logger.info("Pygame initialized")

        # Инициализация игровых систем
        clock = pygame.time.Clock()
        font = pygame.font.SysFont('Arial', 24)
        level_manager = LevelManager((SCREEN_WIDTH, SCREEN_HEIGHT), logger)
        player = DemoPlayer(logger)
        logger.info("Game systems initialized")

        # Автоматическое переключение уровней
        auto_switch_timer = 0
        switching_level = False

        # Основной игровой цикл
        logger.info("Entering main game loop")
        running = True
        while running:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Received quit event")
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        logger.info("ESC pressed, exiting")
                        running = False

            # Обновление игры
            if not level_manager.current_level.completed:
                player.update(level_manager.current_level)
                level_manager.update()
            else:
                if not switching_level:
                    switching_level = True
                    auto_switch_timer = pygame.time.get_ticks()
                    logger.info("Level completed, waiting 3 seconds")

                if pygame.time.get_ticks() - auto_switch_timer > 3000:
                    if not level_manager.next_level():
                        logger.info("All levels completed!")
                        running = False
                    else:
                        player = DemoPlayer(logger)
                        switching_level = False

            # Отрисовка
            level_manager.draw(screen)
            player.draw(screen)

            # Отображение информации
            info_texts = [
                f"Level: {level_manager.current_level_num}",
                f"Score: {level_manager.current_level.score}",
                f"Total: {level_manager.total_score}"
            ]
            for i, text in enumerate(info_texts):
                screen.blit(font.render(text, True, (255, 255, 255)), (10, 10 + i * 30))

            if level_manager.current_level.completed:
                completion_text = font.render(
                    level_manager.get_level_completion_message(),
                    True,
                    (255, 255, 255)
                )
                text_rect = completion_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(completion_text, text_rect)

            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        logger.error(f"Game crashed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down game")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()