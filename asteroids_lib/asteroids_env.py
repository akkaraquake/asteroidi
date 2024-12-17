# -*- encoding: utf-8 -*-

"""Игра Астероиды"""
import sys

import pygame
import random
import math
import time

from asteroids_lib.vector import Vector
from asteroids_lib.constants import GlobalConstants, Constants, Color
from asteroids_lib.collision import *
from asteroids_lib.drawing import *
from asteroids_lib.objects import *



class Scene(object):
    """Сцена

    Хранит рисуемые и обрабатываемые объекты."""

    def __init__(self, screen_size):
        super(Scene, self).__init__()

        # Списки для астероидов и пуль.
        self.asteroids = []
        self.bullets = []

        # Создаём корабль.
        self.ship = Ship(screen_size / 2.0, Vector(0, 0), Constants.ship_radius)
        self.ship.orientation = math.pi

        self.create_asteroids(screen_size, Constants.asteroids_num)

    def create_asteroids(self, screen_size, num):
        # Создаём астероиды.
        for i in range(num):
            pos = Vector(random.randint(0, screen_size.x - 1),
                         random.randint(0, screen_size.y - 1))
            max_speed = Constants.asteroid_max_start_speed
            vel = Vector(random.uniform(-max_speed, max_speed),
                         random.uniform(-max_speed, max_speed))
            size = random.random()
            radius = Constants.asteroid_min_start_size + \
                     size * (Constants.asteroid_max_start_size -
                             Constants.asteroid_min_start_size)
            mass = math.pi * radius ** 2
            self.asteroids.append(Asteroid(pos, vel, radius, mass))


class State(object):
    """Перечисление состояний игры"""

    WAITING_START = 0  # Ожидаем, пока пользователь нажмёт пробел и корабль
    # войдёт в игру.
    IN_GAME = 1  # Корабль в игре.


class Game(object):
    """Игра"""

    def __init__(self, screen_size):
        super(Game, self).__init__()
        self._screen_size = Vector(screen_size[0], screen_size[1])
        self._scene = Scene(self._screen_size)
        self._state = State.WAITING_START
        self.state_space = 5
        self.reward_given = False

        # Словарь { кнопка: нажата ли }.
        self._keys_state = {}

        pygame.init()

        # Устанавливаем заголовок окна.
        pygame.display.set_caption('Астероиды')

        # Создаём таймер.
        self.clock = pygame.time.Clock()

        # Создаём окно для рисования.
        self.screen = pygame.display.set_mode(GlobalConstants.screen_size)

        # Инициализируем шаг обновления.
        self.dt = 1.0 / GlobalConstants.max_fps

    def draw(self, screen):
        """Отрисовка сцены"""

        # Отрисуем фон.
        self._draw_background(screen)
        # Отрисуем астероиды.
        self._draw_asteroids(screen)
        # Отрисуем пули.
        self._draw_bullets(screen)

        draw_with_duplicates(screen, self._screen_size,
                             self._scene.ship, draw_ship_in_game)

        # if self._state == State.WAITING_START:
        #     # Рисуем корабль не активным, т.к. игра ещё не начата.
        #     draw_with_duplicates(screen, self._screen_size,
        #                          self._scene.ship, draw_ship_waiting_start)
        # else:
        #     # Рисуем корабль.
        #     assert self._state == State.IN_GAME
        #     draw_with_duplicates(screen, self._screen_size,
        #                          self._scene.ship, draw_ship_in_game)

    def update(self, dt):
        """Обновляем состояние игры на время dt.

        Возвращает:
          True, если игра продолжается,
          False, если игру необходимо завершить.
        """

        # Список произошедших внешних событий.
        # events = list(pygame.event.get())

        # Обработка общих событий для всех состояний игры.
        # for event in events:
        #     if (event.type == pygame.QUIT or
        #             (event.type == pygame.KEYDOWN and
        #              event.key == pygame.K_ESCAPE)):
        #         # Нажат крест на окне или Escape.
        #         # Прерываем обновление и возвращаем флаг, что необходимо
        #         # завершить программу
        #         return False
        #
        #     # Обрабатываем события нажатия/отжатия кнопок, чтобы всегда иметь
        #     # общее состояние клавиатуры.
        #     if event.type == pygame.KEYDOWN:
        #         self._keys_state[event.key] = True
        #     if event.type == pygame.KEYUP:
        #         self._keys_state[event.key] = False

        # Общая для всех состояний логика: обновить положения астероидов,
        # обновить положения пуль.
        self._move_asteroids(dt)
        self._collide_asteroids()
        self._move_bullets(dt)
        self._update_bullets()
        self._collide_bullets_with_asteroids()
        self._update_ship_orientation(dt)

        # Вызываем функцию обновления, соответствующую состоянию игры.
        # if self._state == State.WAITING_START:
        #     self._update_waiting_start(dt, events)
        # else:
        #     assert self._state == State.IN_GAME
        #     self._update_in_game(dt, events)

        # Возвращаем флаг, что игру необходимо продолжать
        return True


    def run_game(self):
        self.reward_given = False
        # Игра отрисовывает себя.
        self.draw(self.screen)
        # Результат рисования копируется на физический дисплей.
        pygame.display.flip()

        # Подготовка состояния игры для времени через dt.
        if not self.update(self.dt):
            # Выходим из игры.
            return

        # Устанавливаем шаг обновления в количество секунд,
        # прошедших с предыдущего вызова clock.tick().
        self.dt = self.clock.tick(GlobalConstants.max_fps) / 1000.0

        # self.update(self.dt)
        self._move_ship(self.dt)
        if self._collide_asteroids_with_ship():
            self.reward = -100
            self.reward_given = True
            self.done = True
        # else
        #     self.reward += 1
        # if self.is_asteroid_nearby():
        #     self.reward = -1
        #     reward_given = True
        if self._collide_bullets_with_asteroids():
            self.reward = 10
            self.reward_given = True
            print("ПОПАЛ!!!")
        if not self.reward_given:
            self.reward = 0

        # if len(self._scene.asteroids) == 0:
        #     self.done = True
        if len(self._scene.asteroids) < 7:
            self._scene.create_asteroids(self._screen_size, 8)
        # time.sleep(0.1)
        # if self.human:
        #     time.sleep(SLEEP)
        #     state = self.get_state()

    # AI agent
    def step(self, action):
        if action == 0:
            self._scene.ship.rotate_left(self.dt)
        if action == 1:
            self._scene.ship.rotate_right(self.dt)
        if action == 2:
            self._scene.ship.accelerate(self.dt)
        if action == 3:
            self._scene.bullets.append(self._scene.ship.create_bullet())
        self.run_game()
        state = self.get_state()
        return state, self.reward, self.done, {}

    def get_state(self):
        # state: ship
        state = [self._scene.ship.position.x / GlobalConstants.screen_size[0], self._scene.ship.position.y / GlobalConstants.screen_size[1],
                 (self._scene.ship.orientation % (2*math.pi)) / (2*math.pi), (self._scene.ship.velocity.x + 50) / 100, (self._scene.ship.velocity.y + 50) / 100]
        # for asteroid in self._scene.asteroids:
        #     state.append(int(self.is_current_asteroid_nearby(asteroid)))
        print(state)
        return state

    def reset(self):
        self.reward = 0
        self.total = 0
        self.done = False

        state = self.get_state()

        return state




    def _is_key_down(self, key):
        """Возвращаем состояние кнопки"""
        return self._keys_state.setdefault(key, False)

    def _change_state_to_in_game(self):
        """Функция перехода из состояния AWAITING_START в IN_GAME"""
        self._state = State.IN_GAME

    def _change_state_to_waiting_start(self):
        """Функция перехода из состояния IN_GAME в AWAITING_START"""
        self._state = State.WAITING_START
        self._scene.ship.position = self._screen_size / 2.0
        self._scene.ship.orientation = math.pi
        self._scene.ship.velocity = Vector(0, 0)

    def _update_waiting_start(self, dt, events):
        """Обновление сцены и обработка событий на следующие dt секунд для
        состояния, когда игра ещё не началась
        """
        for event in events:
            if (event.type == pygame.KEYDOWN and
                    event.key == pygame.K_SPACE):
                # Нажат пробел --- переходим в состояние игры.
                self._change_state_to_in_game()
                return

    def _update_in_game(self, dt, events):
        """Обновление сцены и обработка событий на следующие dt секунд для
        состояния, когда игра идёт
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Был нажат пробел --- стреляем.
                    self._scene.bullets.append(
                        self._scene.ship.create_bullet())

        self._update_ship_acceleration(dt)
        self._move_ship(dt)
        self._collide_asteroids_with_ship()

    def _move_ship(self, dt):
        """Обновляем положение корабля"""
        self._scene.ship.update_position(self._screen_size, dt)

    def _update_ship_orientation(self, dt):
        """Обработка нажатия кнопок для поворота корабля"""
        if self._is_key_down(pygame.K_LEFT):
            # Поворачиваем корабль влево.
            self._scene.ship.rotate_left(dt)
        elif self._is_key_down(pygame.K_RIGHT):
            # Поворачиваем корабль вправо.
            self._scene.ship.rotate_right(dt)

    def _update_ship_acceleration(self, dt):
        """Обработка нажатия кнопок для ускорения корабля"""
        if self._is_key_down(pygame.K_UP):
            # Ускориться.
            self._scene.ship.accelerate(dt)

    def _move_asteroids(self, dt):
        """Обновляем положения астероидов"""
        for asteroid in self._scene.asteroids:
            asteroid.update_position(self._screen_size, dt)

    def _collide_asteroids(self):
        """Сталкиваем астероиды друг с другом"""
        for i, asteroid1 in enumerate(self._scene.asteroids):
            for asteroid2 in self._scene.asteroids[i + 1:]:
                collide_asteroids(self._screen_size, asteroid1, asteroid2)

    def _move_bullets(self, dt):
        """Обновляем положение пуль"""
        for bullet in self._scene.bullets:
            bullet.update_position(self._screen_size, dt)

    def _update_bullets(self):
        """Удаляем пули, чье время жизни истекло"""

        # Функция filter(func, iter) проходит по всем элементам iter и
        # записывает в результирующий список лишь те элементы, для которых
        # func вернёт True.
        self._scene.bullets = list(filter(
            lambda bullet: not bullet.is_time_exceeded(), self._scene.bullets))

    def _collide_bullets_with_asteroids(self):
        """Сталкиваем пули и астероиды"""
        will_return = False
        new_asteroids = []
        for asteroid in self._scene.asteroids:
            for i, bullet in enumerate(self._scene.bullets):
                if is_collides(self._screen_size, asteroid, bullet):
                    new_asteroids.extend(
                        explode_asteroid(self._screen_size,
                                         asteroid, bullet))
                    del self._scene.bullets[i]
                    will_return = True
                    self.reward = 50
                    self.reward_given = True
                    print("ПОПАЛ!!!")
                    break
            else:
                new_asteroids.append(asteroid)

        self._scene.asteroids = new_asteroids
        # self.state_space = len(new_asteroids) # обновляем размер состояния, т.к кол-во астероидов могло измениться
        return will_return

    def _collide_asteroids_with_ship(self):
        """Проверяем, не столкнулися ли корабль с астероидом"""
        for asteroid in self._scene.asteroids:
            if is_collides(self._screen_size, asteroid, self._scene.ship):
                self._change_state_to_waiting_start()
                return True
        return False

    def is_asteroid_not_nearby(self):
        """Проверяем рядом ли находятся по отношению к друг другу корабль и астероид"""
        for asteroid in self._scene.asteroids:
            if not distance(self._screen_size, self._scene.ship.position, asteroid.position) < 50:
                return True
        return False

    def is_current_asteroid_nearby(self, asteroid): # рядом ли переданный в качестве аргумента астероид
        return distance(self._screen_size, self._scene.ship.position, asteroid.position) < 20

    def distance_for_nearest_asteroid(self):
        min_distance = sys.maxsize
        for asteroid in self._scene.asteroids:
            if distance(self._screen_size,self._scene.ship.position, asteroid.position) < min_distance:
                min_distance = distance(self._screen_size,self._scene.ship.position, asteroid.position)
        return min_distance

    def _draw_background(self, screen):
        """Рисует задний фон"""
        # Заполним фон белым цветом.
        screen.fill(Color.background)

    def _draw_asteroids(self, screen):
        """Рисует все астероиды на сцене"""
        for asteroid in self._scene.asteroids:
            draw_with_duplicates(screen, self._screen_size,
                                 asteroid, draw_asteroid)

    def _draw_bullets(self, screen):
        """Рисует все пули на сцене"""

        for bullet in self._scene.bullets:
            draw_with_duplicates(screen, self._screen_size, bullet, draw_bullet)



def main_impl():
    # Устанавливаем заголовок окна.
    pygame.display.set_caption('Астероиды')

    # Создаём таймер.
    clock = pygame.time.Clock()

    # Создаём окно для рисования.
    screen = pygame.display.set_mode(GlobalConstants.screen_size)

    # Создаёт объект-игру.
    game = Game(GlobalConstants.screen_size)

    # Инициализируем шаг обновления.
    dt = 1.0 / GlobalConstants.max_fps

    while True:
        # Игра отрисовывает себя.
        game.draw(screen)
        # Результат рисования копируется на физический дисплей.
        pygame.display.flip()

        # Подготовка состояния игры для времени через dt.
        if not game.update(dt):
            # Выходим из игры.
            break

        # Устанавливаем шаг обновления в количество секунд,
        # прошедших с предыдущего вызова clock.tick().
        dt = clock.tick(GlobalConstants.max_fps) / 1000.0


def main():
    # Инициализируем библиотеку PyGame.
    pygame.init()

    try:
        main_impl()
    finally:
        # Всегда деинициализируем библиотеку PyGame, даже в случае падения.
        pygame.quit()