# Encoding: utf-8
"""
Ten moduł zawiera klasy "połączeniowe" serwera. W szczególności zawiera w sobie
klasy writer i reader pakietów zgodnych z naszym binarnym protokołem.
"""

class PacketError(Exception):
  pass
