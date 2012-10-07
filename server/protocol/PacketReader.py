# Encoding: UTF-8
import struct

class PacketReader:
  """
  Klasa realizująca czytanie pakietów naszego binarnego protokołu. Po więcej informacji dotyczących protokołu, należy przeczytać plik PACKETS dołączony z kodem źródłowym.

  Zawiera w sobie metody, który odczytują odpowiednie typy.
  Technicznie jest to enkapsulacja klasy struct z biblioteki standardowej Pythona.
  """
  def __init__(self, packet_data):
    """
    Konstruktor klasy.

    Ustawia odpowiednie pola, żadna magia tutaj się nie dzieje.
    """
    self.header, self.length = struct.unpack_from('!hI', packet_data)
    self.__offset = struct.calcsize('!hI')
    self.__data = packet_data
    self.__read = 0

  def __get_by_fmt(self, fmt):
    """
    Metoda prywatna, która realizuje nam odczyt wszystkich typów zadanych w argumencie.

    Metoda ta rzuca wyjątkiem PacketError w momencie, kiedy przekroczyliśmy zdefiniowany w konstruktorze 'koniec pakietu', próbując odczytać jakiś typ.

    Gdy powiedzie się, modyfikuje wewnętrzny wskaźnik i zwraca nam wartość zadanego typu.
    """
    data_size = struct.calcsize('!' + fmt)
    if (self.__read + data_size) > self.length:
      raise PacketError('offset is greater than length after operation')
    
    data = struct.unpack_from('!' + fmt, self.__data, self.__offset)
    self.__offset += data_size
    self.__read += data_size
    return data[0]

  def get_uint(self):
    """
    Pobiera z pakietu daną liczbę całkowitą bez znaku.
    """
    return self.__get_by_fmt('I')

  def get_int(self): 
    """
    Pobiera z pakietu daną liczbę całkowitą ze znakiem.
    """
    return self.__get_by_fmt('i')

  def get_string(self):
    """
    Pobiera z pakietu ciąg znaków.
    """
    length = self.__get_by_fmt('B')
    print length
    return self.__get_by_fmt(str(length) + 's')

  def get_float(self):
    """
    Pobiera z pakietu liczbę zmiennoprzecinkową.
    """
    return self.__get_by_fmt('f')

    
  
    
