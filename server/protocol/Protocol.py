# Encoding: utf-8
from protocol.PacketWriter import PacketWriter
from protocol.PacketReader import PacketReader
from Logger import Logger

import struct

class Protocol(object):
  """
  Klasa ta tworzy protokół i obsługuje pakiety.
  """

  def __init__(self, gamestate, client_socks, client_queues):
    """
    Inicjalizuje obiekt protokołu.
    """
    self._clients = client_socks
    self._queues = client_queues
    self._gamestate = gamestate


  def handle(self, fno):
    """
    Obsługuje dane wysłane DO serwera.

    Dane rozpoznawane są za pomocą headerów pakietów. Po więcej informacji
    na temat budowy pakietu należy przeczytać plik PACKETS dołączony do
    kodu źródłowego.
    """
    pack = self.__get_pack(self._clients[fno])
    read = PacketReader(pack)

    if read.header == 0xC2: # Get Status
      if not self._gamestate.playing_game():
        self.push_error(fno, 0xE1) # Błąd o niemożności wykonania akcji.
        return

      player = read.get_uint()
      ships = self._gamestate.get_ships(player)

      wri = PacketWriter(0xA2)
      ret = []
      for ship in ships:
        tiles = ship.tiles()
        for tx,ty in tiles:
          ret.append(tx)
          ret.append(ty)
          if ship.tile_destroyed(tx,ty):
            ret.append(1)
          else:
            ret.append(0)

      wri.push_uint(len(ret)//3)
      for r in ret:
        wri.push_uint(r)

      self.push(fno, wri.serialize())

    elif read.header == 0xC1: # Shoot
      if not self._gamestate.playing_game():
        self.push_error(fno, 0xE1) # Błąd o niemożności wykonania akcji.
        return

      player = read.get_uint()
      if player != self._gamestate.turn():
        self.push_error(fno, 0xE1)
        return
      else:
        x, y = read.get_uint(), read.get_uint()
        if not ((0 <= x <= 8) and (0 <= y <= 8)):
          self.push_error(fno, 0xE2) # Nieprawidłowa pozycja
          return
 
        match = '%s%d' % (chr(ord('A')+x), (y+1))
        Logger.log("Gracz #%d strzela w %s" % (player, match))
        ret = self._gamestate.shoot(player, x, y)
        wri = PacketWriter(0xA1)
        wri.push_uint(player)
        wri.push_uint(ret)

        self.push_all(wri.serialize())
        if ret != 2:
          self._gamestate.toggle_turn()


  def push_error(self, fno, head):
    """
    Klasa wysyłająca elementarne pakiety na temat błędów.

    Konwencja jest następująca: Są to pakiety nie zawierające danych i
    posiadające header 0xE[numer]. Nie jest to jednak żadna reguła.
    """
    wri = PacketWriter(head)
    self.push(fno, wri.serialize())


  def __get_pack(self, sock):
    """
    Pobiera pojedyńczy pakiet od klienta, zakładając że ten istnieje.

    Zwraca ciąg danych binarnych, który jest pakietem i może zostać przeczytany.
    """
    packet_id, packet_size = sock.recv(2), sock.recv(4)
    data_size = struct.unpack('!I', packet_size)[0]
    packet_data = ''
    # FIX: Recv(0) czeka w nieskończoność, musimy to wyifować.
    if data_size > 0:
      packet_data = sock.recv(data_size)

    return packet_id + packet_size + packet_data


  def push(self, fno, packet):
    """
    Wrzuca na odpowiednią kolejkę pakietów do wysłania odpowiednie dane.
    """
    Logger.log('Puszczamy pakiet...')
    self._queues[fno].append(packet)


  def push_all(self, packet):
    """
    Wrzuca na wszystkie kolejki pakietów odpowiedni pakiet do wysłania.
    """
    Logger.log('Puszczamy pakiet WSZYSTKIM...')
    for client in self._clients:
      self._queues[client].append(packet)


  def push_player(self, fno, player):
    """
    Wysyła informacje na temat numeru gracza do odpowiedniego socketu.
    """
    wri = PacketWriter(0xA3)
    wri.push_uint(player)

    self.push(fno, wri.serialize())


  def push_complete(self, loser):
    """
    Wysyła pakiet na temat zakończenia gry, wraz z informacją kto przegrał.
    """
    wri = PacketWriter(0xA4)
    wri.push_uint(loser)
    
    self.push_all(wri.serialize())


  def push_start(self):
    """
    Wysyła pakiet z informacją, że gra się rozpoczęła.
    """
    wri = PacketWriter(0xA5)

    self.push_all(wri.serialize())
