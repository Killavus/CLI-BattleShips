# Encoding: utf-8
import struct
import array

import cStringIO

class PacketWriter:
  """
  PacketWriter realizuje funkcje tworzenia zadanych pakietów binarnych zgodnych z naszym protokołem.

  Aby uzyskać więcej informacji na jego temat, należy skonsultować się z plikiem server/PACKETS.
  """
  def __init__(self, head):
    """
    Konstruktor klasy.
    """
    self.__header = head
    self.__packet_data = []

  def push_uint(self, data):
    """
    Wrzuca do pakietu unsigned inta.

    Zwraca referencję do samego siebie, co umożliwia 'chainowanie' wywołań.
    """
    self.__packet_data.append(('I', int(data)))

    return self

  def push_int(self, data):
    """
    Wrzuca do pakietu signed inta.

    Zwraca referencję do samego siebie, co umożliwia 'chainowanie' wywołań.
    """
    self.__packet_data.append(('i', int(data)))

    return self

  def push_string(self, string):
    """
    Wrzuca do pakietu stringa.

    Zwraca referencję do samego siebie, co umożliwia 'chainowanie' metod.
    """
    length = len(string)
    self.__packet_data.append((str(length+1) + 'p', string))

    return self

  def push_float(self, data):
    """
    Wrzuca do pakietu floata.
    
    Zwraca referencję do samego siebie, co umożliwia 'chainowanie' metod.
    """
    self.__packet_data.append(('f', float(data)))

    return self

  def __str__(self):
    """
    Definiuje reprezentację "stringową" instancji PacketReader jako pakiet, który ta instancja tworzy.

    Za kulisami korzysta z metody serialize().
    """
    return self.serialize()

  def serialize(self):
    """
    Serializuje tworzony pakiet do ciągu znaków.

    Zwraca string będący reprezentacją binarną pakietu stworzonego przez instancję klasy.
    """
    fmt = ''.join([ch[0] for ch in self.__packet_data])
    data = map(lambda x: x[1], self.__packet_data)

    return apply(struct.pack, ['!hI' + fmt] + 
        [self.__header, struct.calcsize(fmt)] + data)

 
