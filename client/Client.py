#!/usr/bin/python
# Encoding: utf-8

import socket
import select
import struct
from collections import deque

import sys

from protocol.PacketReader import PacketReader
from protocol.PacketWriter import PacketWriter

if not "EPOLLRDHUP" in dir(select):
  select.EPOLLRDHUP = 0x2000

class Client(object):
  """
  Klasa klienta realizująca wszystkie funkcje wymagane od takiego programu.

  Nie jest podzielona na większe klasy, ponieważ jej funkcje da się zapisać
  prosto w dość małej liczbie linii kodu.
  """
  def __init__(self):
    """
    Konstruktor klasy klienta.

    Inicjalizuje on odpowiednie gniazdko sieciowe na podstawie danych od 
    użytkownika, oraz tworzy kolejkę epoll i rejestruje odpowiednie obiekty.
    """
    # Czytamy ze standardowego wejścia IP i port, z którym chcemy się połączyć.
    ip, port = self.__get_connection_data()
    while ip == port == None:
      ip, port = self.__get_connection_data()

    self._output_queue = deque()

    # Inicjalizujemy gniazdko sieciowe.
    try:
      self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self._sock.connect((ip,int(port)))

      self._poll = select.epoll(1)
    except socket.error as sockerr:
      print 'Błąd gniazdka: %s. Klient zostaje zamknięty.' % sockerr
      sys.exit(0)

    # Rejestrujemy do monitorowania gniazdko serwera.
    self._poll.register(self._sock.fileno(), select.EPOLLIN | select.EPOLLOUT | 
        select.EPOLLHUP | select.EPOLLERR | select.EPOLLRDHUP | 
        select.EPOLLPRI)

    # Rejestrujemy do monitorowania standardowe wejście.
    self._poll.register(sys.stdin.fileno(), select.EPOLLIN | 
        select.EPOLLHUP | select.EPOLLERR | select.EPOLLPRI)

    self._player = None

  def loop(self):
    """
    Pętla obsługująca zdarzenia w kliencie.

    Funkcja korzysta z mechanizmu epoll, aby wydajnie odbierać zdarzenia ze
    standardowego wejścia, oraz z gniazdka sieciowego.
    """
    while True:
      for fno, event in self._poll.poll(0):
        if fno == sys.stdin.fileno():
          line = sys.stdin.readline().strip()
          self._process_command(line)
        else:
          if event & select.EPOLLHUP or event & select.EPOLLRDHUP:
            self._sock.close()
            print "Połączenie z serwerem zostało niespodziewanie zakończone."
            sys.exit(0)
          elif event & select.EPOLLIN:
            self._handle(fno)
          elif event & select.EPOLLERR:
            print 'Błąd epolla. Coś nie tak?'
          elif event & select.EPOLLPRI:
            print 'EPOLLPRI zaszedł. O cóż może chodzić?'
          elif event & select.EPOLLOUT:
            if len(self._output_queue) > 0:
              data = self._output_queue.popleft()
              self._sock.sendall(data)


  def _handle(self, fno):
    """
    Odbiera dane z serwera i wykonuje odpowiednie akcje.

    Metoda nic nie zwraca.
    """
    pkg = self.__get_pack(self._sock)
    read = PacketReader(pkg)

    if read.header == 0xA3: # Którym graczem jesteś.
      player = read.get_uint()
      self._player = player-1
      print 'Jestem graczem nr %d' % self._player
    elif read.header == 0xA2: # Status
      list_len = read.get_uint()
      tiles = {}
      for _ in xrange(list_len):
        tx, ty, td = read.get_uint(), read.get_uint(), read.get_uint()
        tiles[(tx,ty)] = td
      print '   ABCDEFGHI'
      for y in xrange(9):
        sys.stdout.write('%d: ' % (y+1))
        for x in xrange(9):
          td = tiles.get((x,y), None)
          if td == None:
            sys.stdout.write('-')
          elif td == 1:
            sys.stdout.write('X')
          elif td == 0:
            sys.stdout.write('#')
        sys.stdout.write("\n")
    elif read.header == 0xA1: # Strzelono.
      player = read.get_uint()
      ret = read.get_uint()

      if ret == 0:
        print 'Gracz %d strzelił, ale spudłował.' % player
      elif ret == 1:
        print 'Gracz %d strzelił i trafił w przeciwnika!' % player
      elif ret == 2:
        print 'Gracz %d strzelił i trafił w swój statek.\n\
          Przysługuje mu drugi ruch...' % player
      elif ret == 3:
        print 'Gracz %d strzelił i trafił w przeciwnika, ZATAPIAJĄC STATEK!' % player

    elif read.header == 0xA4: # Koniec gry
      loser = read.get_uint()
      if self._player == loser:
        print 'PRZEGRAŁEŚ! Następnym razem bardziej się postaraj...'
      else:
        print 'ZWYCIĘSTWO! Jesteś prawdziwym wilkiem morskim!'

      self._sock.close()
      sys.exit(0)
    elif read.header == 0xA5: # Start gry
      print 'Gra zaczyna się.'
      if self._player == 0:
        print 'Ty zaczynasz!'
      else:
        print 'Zaczyna przeciwnik!'

    ### BŁĘDY:
    elif read.header == 0xE1:
      print 'Nie można wykonać tej akcji teraz.\
 To chyba nie Twoja tura, albo gra się jeszcze nie zaczęła?'
    elif read.header == 0xE2:
      print 'Złe koordynaty przy strzelaniu. Muszą być w zakresie\
 (A-I) (1-9) i postaci XN'

  def __get_connection_data(self):
    try:
      ip_string = raw_input('Podaj IP i port serwera w formacie ip:port: ')
      ip, port = ip_string.split(':')
    except ValueError:
      print 'Nieprawidłowy format. Musi być IP:Port.'
      return None, None
    
    return ip, port

  def _process_command(self, line):
    """
    Metoda pobiera dane ze standardowego wejścia wykonuje odpowiednią akcję.

    Aktualnie metoda pobiera STATUS oraz żądanie SHOOT i 
    wysyła odpowiednie pakiety do serwera.
    """
    if line == "STATUS":
      self.push(0xC2)
    elif line.startswith('SHOOT'):
      try:
        x, y = int(ord(line[6:7])-ord('A')), int(line[7:8])-1

        self.push(0xC1, (x,y))
      except:
        print 'Zły format strzału. Format: SHOOT XN (X: A-I, Y: 1-9)'

  def __get_pack(self, sock):
    """
    Pobiera pojedyńczy pakiet od klienta, zakładając że ten istnieje.

    Zwraca ciąg danych binarnych, który jest pakietem 
    i może zostać przeczytany.
    """
    packet_id, packet_size = sock.recv(2), sock.recv(4)
    if len(packet_size) < 4:
      print 'Pobrano złe dane z serwera... Coś jest bardzo nie w porządku!'

    data_size = struct.unpack('!I', packet_size)[0]
    packet_data = ''
    # Recv(0) będzie czekać w nieskończoność na dane, których nigdy nie przeczyta.
    if data_size > 0:
      packet_data = sock.recv(data_size)
    
    return packet_id + packet_size + packet_data

  def push(self, head, data = None):
    """
    Wysyła pakiet do serwera korzystając z ustalonego protokołu.

    Metoda nic nie zwraca.
    """

    # Klient wysyła dwa pakiety:
    # * 0xC1 - strzel w pozycję (x,y)
    # * 0xC2 - pobierz status gry z serwera.
    if head == 0xC1:
      x, y = data
      wri = PacketWriter(0xC1)
      wri.push_uint(self._player)
      wri.push_uint(x)
      wri.push_uint(y)

      self._output_queue.append(wri.serialize())
    elif head == 0xC2:
      wri = PacketWriter(0xC2)
      wri.push_uint(self._player)

      self._output_queue.append(wri.serialize())


# Tworzymy instancję klasy Client i wdrażamy ją w pętlę.
c = Client()
c.loop()
