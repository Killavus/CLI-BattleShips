#!/usr/bin/python
# Encoding: utf-8

import socket
import select

from collections import deque

from GameState import GameState
from Logger import Logger

from config.JSONConfig import JSONConfig
from protocol.Protocol import Protocol

# Hack na obsługę zdarzenia EPOLLRDHUP - z jakiegoś powodu Pythonowa 
# implementacja nie definiuje tego przydatnego symbolu.
if not "EPOLLRDHUP" in dir(select):
  select.EPOLLRDHUP = 0x2000

class Server(object):
  def __init__(self):
    """
    Konstruktor klasy.

    Ładuje on konfigurację, ustawia socket nasłuchujący na połączenia oraz
    definiuje struktury wymagane do działania serwera.
    """
    Logger.log('Witam!')

    self._cfg = JSONConfig(open('config.json', 'r'))
    self._gamestate = GameState(self._cfg)
    
    # Inicjalizujemy kolejkę epoll.
    self._poller = select.epoll(3)
    self._init_listen_socket()

    # Odpowiednie hashmapy do odpytywania socketów i pakietów do wysłania.
    self._client_sockets = {}
    self._packet_queues = {}
    self._player_bindings = {}

    # Tworzymy obiekt protokołu:
    self._proto = Protocol(self._gamestate, self._client_sockets,
      self._packet_queues)
    

  def _init_listen_socket(self):
    """
    Inicjalizuje gniazdko nasłuchujące na połączenia.

    Do ustalenia hosta i portu stosujemy wartości z pliku konfiguracyjnego.
    """
    host, port = self._cfg['connection.host'], self._cfg['connection.port']

    self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._sock.bind((host, port))
    self._sock.listen(2)

    Logger.log("Rejestrujemy SID serwera #%d do epoll..." % self._sock.fileno())
    self._poller.register(self._sock.fileno(), select.EPOLLIN | 
      select.EPOLLERR | select.EPOLLRDHUP | select.EPOLLHUP | select.EPOLLPRI)


  def _register_in_poll(self, sock):
    """
    Rejestruje gniazdko sieciowe klienta do kolejki EPOLL.

    Dodatkowo, tworzymy odpowiednie dowiązania do kolejek pakietów i hashmapy
    socketów, z kluczem ustawionym na deskryptor gniazda.
    """
    Logger.log("Rejestrujemy SID klienta #%d do epoll..." % sock.fileno())
    self._poller.register(sock.fileno(), select.EPOLLIN | select.EPOLLHUP |
        select.EPOLLERR | select.EPOLLRDHUP | select.EPOLLPRI | select.EPOLLOUT)
    self._client_sockets[sock.fileno()] = sock
    self._packet_queues[sock.fileno()] = deque()


  def _add_player(self): 
    """
    Dodaje połączenie gracza do serwera.

    Wchodzi w to sprawdzanie, czy może się połączyć (serwer nie jest pełen),
    oraz odpowiednie zapisanie i rejestrację danych po stronie serwera.
    """
    client_sock, _ = self._sock.accept()
    if len(self._client_sockets) == 2:
      client_sock.close()
      return
  
    client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    self._register_in_poll(client_sock)
    pl = 0
    for key in self._player_bindings:
      if self._player_bindings[key] == 0:
        pl = 1
        break
    self._player_bindings[client_sock.fileno()] = pl
    self._proto.push_player(client_sock.fileno(), pl+1)

    if len(self._client_sockets) == 2:
      Logger.log('Mamy dwóch graczy, startujemy grę!')
      self._gamestate.start()
      self._proto.push_start()


  def loop(self):
    """
    Główna pętla serwera.

    Służy głównie do czytania zdarzeń z epolla i sprawdzaniu, czy gra nie
    została ukończona.
    """
    while True:
      if self._gamestate.completed():
        Logger.log('Gra skończona! Reset...')

        loser = self._gamestate.completed()
        self._proto.push_complete(loser) # Gra skończona. Wysyłamy do klientów.
        self._gamestate.reset()

      for fno, event in self._poller.poll(0):
        if self._sock.fileno() == fno:
          Logger.log("Połączenie z serwerem...")
          self._add_player()
        else:
          sock = self._client_sockets[fno]
          if event & select.EPOLLHUP or event & select.EPOLLRDHUP:
            Logger.log('Klient o SID #%d wyszedł z gry. Resetuję...' % fno)
            self._gamestate.reset()
            self._poller.unregister(fno)
            self._client_sockets[fno].close()
            del self._client_sockets[fno]
            del self._packet_queues[fno]
            del self._player_bindings[fno]
          elif event & select.EPOLLIN:
            Logger.log('Klient do nas napisał...')
            self._proto.handle(fno)
          elif event & select.EPOLLERR:
            Logger.log('Błąd epolla (EPOLLERR)')
          elif event & select.EPOLLPRI:
            Logger.log('Ważny event doszedł do serwera.')
          elif event & select.EPOLLOUT:
            if len(self._packet_queues[fno]) > 0:
              data = self._packet_queues[fno].popleft()
              self._client_sockets[fno].sendall(data)

s = Server()
s.loop()
