from datetime import date, timedelta

BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7

def color_code(color, foreground=True, bold=False):
  ret = "\033["
  if foreground:
    ret = ret + "3" + str(color)
  elif bold:
    ret = ret + "10" + str(color)
  else:
    ret = ret + "4" + str(color)
  if bold and foreground:
    ret = ret + ";1"
  elif foreground:
    ret = ret + ";22"
  return ret + "m"

class TodoItem:
  def __dir__(self):
    return ['text','marked','dimmed','indeterminate','category','startdate','duedate','timeestimate']

  def __init__(self, text):
    self.text = text
    
  def __getattr__(self,name):
    if name in ["marked", "indeterminate", "dimmed"]:
      return False
    elif name in self.__dir__():
      return None
    else:
      raise AttributeError
      
  def __lt__(self,other):
    if self.category == other.category:
      return self.text < other.text
    elif self.category is None:
      return False
    elif other.category is None:
      return True
    else:
      return self.category < other.category

  def anyTrue(self, predicates):
    return reduce(lambda a,b: a or b, map(lambda f: f(self), predicates), False)
      
  def color(self):
    codes = []
    if self.dimmed:
      codes.append(color_code(BLACK, bold=True))
      
    not_marked = not self.marked 
    if self.startdate is None:
      pass
    elif self.startdate == date.today() and not self.dimmed:
      codes.append(color_code(GREEN, foreground=not_marked))
    elif self.startdate > date.today():
      codes.append(color_code(BLUE, foreground=not_marked, bold=True))
     
    if self.category is None and not codes: 
      codes.append(color_code(MAGENTA, foreground=not_marked))
    
    if self.duedate is None:
      if not codes:
        codes.append(color_code(CYAN, foreground=not_marked, bold=True))
    elif self.duedate < date.today():
      codes.append(color_code(RED, foreground=not_marked))
    elif self.duedate == date.today():
      codes.append(color_code(RED, foreground=not_marked, bold=True))
    elif self.duedate - timedelta(days=2) <= date.today():
      codes.append(color_code(YELLOW, foreground=not_marked))
    elif self.duedate - timedelta(days=6) > date.today() and not codes:
      codes.append(color_code(BLACK, bold=True))
      if self.marked:
        codes.append(color_code(WHITE, foreground=False))
      
    if self.marked:
      if not codes:
        codes.append(color_code(WHITE, foreground=False, bold=True))
      codes.append(color_code(BLACK))
    return ''.join(codes)

  def category_str(self):
    if self.category is not None:
      return "{!s:>6}".format(self.category) + ":"
    return "       "