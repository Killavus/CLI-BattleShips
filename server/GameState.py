# Encoding: utf-8
from objects.Ship import Ship

import random

class GameState(object):
  """
    Klasa GameState przechowuje stan gry oraz dostarcza metody do modyfikacji
    tego stanu. W szczególności wewnątrz tej klasy implementowane są zasady
    gry.
  """

  def __init__(self, cfg):
    """
      Konstruktor klasy. Inicjalizuje mapę oraz stan.
    """
    self._map = []
    self._state = 'wait'
    self._cfg = cfg

    self._turn = None


  def waiting_for_players(self):
    """
      Sprawdza, czy gra jest w stanie oczekiwania na graczy.
    """
    return self._state == 'wait'


  def start(self):
    """
      Startuje grę. Metoda ta inicjalizuje także start gry.
    """
    self._state = 'game'
    self._turn = 0

    self.__populate_map()


  def reset(self):
    """
      Ta funkcja resetuje nam stan gry.

      Przydatne, gdy gra się skończy, a my nie chcemy za bardzo restartować
      serwera.
    """
    self._state = 'wait'
    self._turn = None
    self._map = []


  def playing_game(self):
    """
      Sprawdza, czy jesteśmy podczas gry.
    """
    return self._state == 'game'


  def turn(self):
    """
      Sprawdza, w turze którego gracza jesteśmy.
    """
    return self._turn


  def toggle_turn(self):
    """
      Zmienia turę na turę kolejnego gracza i zwraca ją.

      UWAGA: Gdy gra nie jest rozpoczęta, funkcja ta nic nie robi.
    """
    if not self.playing_game():
      return None

    self._turn += 1
    self._turn %= 2

    return self._turn


  def completed(self):
    """
      Sprawdza, czy gra nie jest przypadkiem zakończona.

      Zwraca ID przegranego, lub None gdy gra trwa.
    """
    if not self.playing_game():
      return None

    for player in [0,1]:
      ships = self.get_ships(player)
      if filter(lambda ship: not ship.destroyed(), ships) == []:
        return player
    return None


  def shoot(self, player, x, y):
    """
      Przeprowadza strzał.

      UWAGA: Strzały gracza we własne statki nie są pożądane - metoda zwraca
      0 - pudło
      1 - trafiony statek gracza przeciwnego (NISZCZY go)
      2 - trafiony własny statek (NIE niszczy go)
      3 - trafiony statek gracza przeciwnego, w dodatku ZATOPIONY.
    """
    for player_ in [0,1]:
      for ship in self.get_ships(player_):
        if ship.shooted(x,y):
          if player == player_:
            return 2
          else:
            pre = ship.destroyed()
            ship.destroy(x,y)
            post = ship.destroyed()

            if pre == False and post == True:
              return 3 # TRAFIONY ZATOPIONY

            return 1
    return 0


  def get_ships(self, player):
    """
      Zwraca statki, które gracz powinien "widzieć".
    """
    return filter(lambda ship: ship.get_player() == player, self._map)


  def __populate_map(self):
    """
      Ta prywatna metoda generuje nam plansze.
    """

    tiles_used = set()
    for player in [0,1]:
      ships = self._cfg["player_%d" % player]
      for ship_type in ships:
        count = ships[ship_type]
        length = int(ship_type[4:])

        on_map = 0
        while on_map < count:
          ori = random.randint(0,1)
          lx, ly = random.randint(0,8), random.randint(0,8)
          if ori == 0:
            ly = random.randint(0,9-length)
          else:
            lx = random.randint(0,9-length)

          ship = Ship(lx, ly, length, ori, player)
          if len(set(ship.tiles()) & tiles_used) > 0:
            continue

          tiles_used = tiles_used | set(ship.tiles())
          self._map.append(ship)
          on_map += 1

