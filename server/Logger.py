# Encoding: utf-8
import datetime

class Logger(object):  
  """
  Klasa ta zawiera narzędzie do logowania zdarzeń po stronie serwera.
  """

  @staticmethod
  def log(msg):
    """
     Wysyła sformatowaną wiadomość wraz z timestampem na standardowe wyjście.

     Funkcja nic nie zwraca.
    """
    now = datetime.datetime.now()
    print "[%0.4d.%0.2d.%0.2d %0.2d:%0.2d:%0.2d] %s" % (now.year, now.month, 
        now.day, now.hour, now.minute, now.second, msg)

