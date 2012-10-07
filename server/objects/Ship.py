# Encoding: utf-8

class Ship(object):
  """
  Obiekt statku, który udostępnia potrzebne do rozegrania gry metody.

  Posiada metody, które modyfikują wewnętrzny stan obiektu oraz akcesory.
  Ich wykorzystanie zgodnie z zasadami gry nie jest zapewniane - to ma zapewnić
  klasa GameState.
  """
  def __init__(self, x, y, ship_len, ori, player):
    """
    Konstruktor klasy.

    Na podstawie argumentów oblicza przestrzeń, którą statek zajmuje, oraz
    sprawdza, oraz definiuje pomocnicze struktury. Zapisuje również statek
    do odpowiedniego gracza.
    """
    if ori == 1: # Horizontal
      self._tiles = [(x+i,y) for i in xrange(ship_len)]
    else: # Vertical
      self._tiles = [(x,y+i) for i in xrange(ship_len)]

    self._destroyed = {}
    self._player = player


  def tiles(self):
    """
    Zwraca listę kratek, które zajmuje nasz statek.
    """
    return self._tiles


  def get_player(self):
    """
    Zwraca gracza, do którego należy statek.
    """
    return self._player


  def destroyed(self):
    """
    Sprawdza, czy statek został całkowicie zniszczony.

    Całkowite zniszczenie jest wtedy, kiedy wszystkie kratki, które zajmuje
    statek, zostały strzelone przez gracza drużyny przeciwnej.
    """
    for tile in self.tiles():
      if self._destroyed.get(tile, False) == False:
        return False
    
    return True


  def shooted(self, x, y):
    """
    Sprawdza, czy dane pozycje (x,y) to pozycje, w które można 'strzelić' dany
    statek.

    W szczególności, jeżeli pole zostało już zniszczone, funkcja zwraca false.
    """
    return (x,y) in self._tiles and not self._destroyed.get((x,y), False)


  def tile_destroyed(self, x, y):
    """
    Sprawdza, czy dana kratka statku została zniszczona.
    """
    return self._destroyed.get((x,y), False)


  def destroy(self, x, y):
    """
    Ustawia daną kratkę statku jako "zniszczoną".
    """
    self._destroyed[(x,y)] = True
