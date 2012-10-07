# Encoding: utf-8

from config.AbstractConfig import *
import json

class ConfigError(Exception):
  pass

class JSONConfig(AbstractConfig):
  """
  Klasa realizująca czytanie pliku konfiguracyjnego zapisanego w technologii JSON.

  Realizuje założenia klasy abstrakcyjnej AbstractConfig.
  """
  def __init__(self, source):
    """
    Konstruktor klasy.

    Czyta JSONa z uchwytu pliku lub czystych danych tekstowych.
    """
    try:
      self.__data = json.load(source) if hasattr(source, 'read') else json.loads(source)
    except ValueError:
      raise ConfigError('Failed to load configuration variables!')
    except IOError:
      raise ConfigError('Failed to load configuration variables!')

    self.__caching = {}
  
  def lookup(self, config_string):
    """
    Metoda realizująca klasę abstrakcyjną AbstractConfig.

    Mając zadany configstring, zwraca nam odpowiednią daną z pliku konfiguracyjnego.
    """
    parts = config_string.split('.')

    if config_string in self.__caching:
      return self.__caching[config_string]
    
    node = self.__data
    try:
      for part in parts:
        node = node[part]
    except KeyError:
      return None
   
    self.__caching[config_string] = node 
    return node
    

    
      
