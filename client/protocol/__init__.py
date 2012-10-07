"""
Ten moduł zawiera klasy "połączeniowe" serwera. W szczególności zawiera w sobie
klasę protokołu oraz writer i reader pakietów zgodnych z naszym binarnym 
protokołem.
"""

class PacketError(Exception):
  pass
