# Encoding: utf-8

class AbstractConfig:
  """
  Klasa abstrakcyjna definiująca nam interfejs do zaimplementowania, oraz metodę przeciążającą operator [].
  """
  def __init__(self):
    """
    Konstruktor klasy.

    Zawsze zwraca wyjątek. Ten konstruktor powinien być przeciążony przez klasy potomne.
    """
    raise ConfigError("You can not initialize AbstractConfig class.")


  # Stringi konfiguracyjne w formacie:
  # (<category>.)*<item>
  def lookup(self, config_string):
    """
    Metoda zwracająca nam odpowiednie wartości z pomocą formatstringa.

    Formatstring jest w postaci [<kategoria konfigu>].<klucz konfigu>.

    Każda klasa potomna musi przeciążyć tą metodę.
    """
    raise ConfigError('Not implemented')


  def __getitem__(self, i):
    """
    Metoda przeciążająca operator [].
    """
    return self.lookup(i)
    
  
