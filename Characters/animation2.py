import pygame

from Characters.action import Action
from Characters.character import Character


class AnimatedObject:
   def __init__(self, character: Character):
      self.character = character
      self.animation_speed = 100  # ms per frame
      self.frames = {}  # Хранит кадры для каждого действия
      self.current_action = Action.IDLE
      self.frame = 0
      self.last_update = pygame.time.get_ticks()
      self.direction = 1
      self.draw_hitbox = True  # Флаг для отключения хитбокса

   def load_action_frames(self, action: Action, file_path: str, frame_count: int):
      """
      Загружает кадры для конкретного действия из файла-строки
      :param action: Название действия ('idle', 'jump' и т.д.)
      :param file_path: Путь к файлу с кадрами
      :param frame_count: Количество кадров в файле
      """
      sprite_sheet = pygame.image.load(file_path).convert_alpha()
      frame_width = sprite_sheet.get_width() // frame_count
      frame_height = sprite_sheet.get_height()

      frames = []
      for i in range(frame_count):
         frame = sprite_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
         frame = pygame.transform.scale(frame, (self.character.width, self.character.height))
         frames.append(frame)

      self.frames[action] = frames

   def update_animation(self):
      """Обновляет кадр анимации"""
      now = pygame.time.get_ticks()
      if now - self.last_update > self.animation_speed:
         self.last_update = now

         # Для прыжка: не зацикливать анимацию
         if self.current_action == Action.JUMP:
            if self.frame < len(self.frames) - 1:
               self.frame += 1
         else:
            self.frame = (self.frame + 1) % len(self.frames)

   def change_action(self, new_action: Action):
      """Меняет текущее действие"""
      if new_action != self.current_action and new_action in self.frames:
         self.current_action = new_action
         self.frame = 0

   def update(self):
      """Обновляет состояние анимации"""
      self.change_action(self.character.current_action)
      self.update_animation()

   def draw(self, surface: pygame.Surface):
      """Отрисовывает текущий кадр"""
      if self.current_action in self.frames:
         frames = self.frames[self.current_action]
         frame = frames[self.frame]

         # Отражение при смене направления
         if self.character.direction != self.direction:
            frame = pygame.transform.flip(frame, True, False)
            self.direction = self.character.direction

         # Отрисовываем спрайт персонажа
         surface.blit(frame, self.character.rect)

      # Отрисовываем хитбокс (только в режиме отладки)
      if self.draw_hitbox:  # Глобальная переменная для отладки
         # Создаем поверхность для хитбокса с прозрачностью
         hitbox_surf = pygame.Surface((self.character.rect.w, self.character.rect.h), pygame.SRCALPHA)

         # Рисуем полупрозрачную заливку
         pygame.draw.rect(hitbox_surf, (255, 0, 0, 50), hitbox_surf.get_rect())

         # Рисуем контур
         pygame.draw.rect(hitbox_surf, (255, 0, 0, 255), hitbox_surf.get_rect(), 1)

         # Наложение на экран
         surface.blit(hitbox_surf, self.character.rect)