from datetime import date, timedelta
from dateutil import parser as dparse
from odo_item import TodoItem
from pickle import load, dump
from string import punctuation
from sys import exit
from random import shuffle, randint
from shutil import copyfile
from os import remove

past_startdate = lambda item: item.startdate is not None and item.startdate > date.today()
is_det = lambda item: past_startdate(item) and item.indeterminate
is_indet = lambda item: not item.indeterminate

strict = [past_startdate]

def to_date(rawdate, default=None):
  if rawdate is None:
    return default
  if "today" in rawdate:
    return date.today()
  if "tomorrow" in rawdate:
    return date.today() + timedelta(days=1)
  try:
    return dparse.parse(' '.join(rawdate)).date()
  except Exception:
    print "Warning: date string `{}' could not be parsed. Used default value `{}' instead.".format(' '.join(rawdate), default)
    return default

def indet_hide(item):
  if item.duedate is None:
    pushval = randint(1,30)
    item.startdate = date.today() + timedelta(days=pushval)
    print "Item `{}' pushed {} days.".format(item.text, pushval)
  elif item.duedate <= date.today() + timedelta(days=2):
    print "Warning: item `{}' was selected, but cannot be hidden since it is due soon.".format(item.text)
  else:
    diff = (item.duedate - date.today()).days
    val = randint(1,min(diff-2,30))
    print "Item `{}' pushed {} days.".format(item.text, val)
    item.startdate = date.today() + timedelta(days=val)

def add(settings):
  broken = ' '.join(settings.item).split(':',1)
  item = TodoItem(broken[-1].strip())
  if len(broken) == 2:
    item.category = broken[0].upper()
    if len(item.category) > 6:
      item.category = item.category[:6]
  data = getdata(settings.filename)
  
  if settings.indeterminate:
    item.indeterminate = True
  if settings.marked:
    item.marked = True
  if settings.dimmed:
    item.dimmed = True
  
  item.duedate = to_date(settings.time)
  item.startdate = to_date(settings.start, date.today())
  if item.duedate is not None and item.startdate is not None and item.duedate < item.startdate:
    item.duedate = item.startdate
    print "Warning: item due date was before start date. Due date pushed forward to {}.".format(item.duedate.strftime("%a %d %b"))
  
  if settings.hide:
    indet_hide(item)
    
  data.append(item)
  data.sort()
  
  if item.anyTrue(strict):
    print "Item added at index {} but hidden. Use odo print -v to see item.".format(data.index(item))
  else: print "Item added at index {}.".format(data.index(item))
  
  print_list(data, print_item_sparse, strict)
  rewrite(settings.filename, data)
  
def batch(settings):
  data = getdata(settings.filename)
  
  settings.indices.sort()
  settings.indices.reverse()
  for element in settings.indices:
    if element < 0 or element >= len(data):
      print "Element {} does not exist.".format(element)
    elif settings.force or not data[element].anyTrue(strict):
      settings.innerfunc(settings, data, element)
    else:
      print "Element {} is hidden. Use -f to edit hidden values.".format(element)
  
  data.sort()
  print_list(data, print_item_sparse, strict)
  rewrite(settings.filename, data)
  
def edit(settings):
  data = getdata(settings.filename)
  if settings.index < 0 or settings.index >= len(data):
    print "Element {} does not exist.".format(settings.index)
    exit(1)
  
  item = data[settings.index]
  
  if not settings.force and item.anyTrue(strict):
    print "Element {} is hidden. Use -f to edit hidden values.".format(settings.index)
    exit(1)
  
  if settings.indeterminate:
    item.indeterminate = True
  if settings.mark:
    item.marked = True
  if settings.determinate:
    item.indeterminate = False
  if settings.normal:
    item.marked = False
    item.dimmed = False
  if settings.dim:
    item.dimmed = True
  
  if settings.start is not None:
    if len(settings.start) == 0:
      item.startdate = None
    else:
      item.startdate = to_date(settings.start, item.startdate)
  if settings.time is not None:
    if len(settings.time) == 0:
      item.duedate = None
    else:
      item.duedate = to_date(settings.time, item.duedate)
  if settings.item is not None:
    data[settings.index].text = ' '.join(settings.item)
  if settings.category is not None:
    if len(settings.category) == 0:
      item.category = None
    else:
      item.category = settings.category[0].upper()
      
  if item.duedate is not None and item.startdate is not None and item.duedate < item.startdate:
    item.duedate = item.startdate
    print "Warning: item due date was before start date. Due date pushed forward to {}.".format(item.duedate.strftime("%a %d %b"))
    
  
  if settings.hide:
    indet_hide(item)
    
  data[settings.index] = item
  data.sort()
  
  if item.anyTrue(strict):
    print "Item now at index {} but hidden. Use odo print -v to see item.".format(data.index(item))
  else: print "Item now at index {}.".format(data.index(item))
  
  print_list(data, print_item_sparse, strict)
  rewrite(settings.filename, data)

def dim(settings, data, index):
  print "Element `{}' dimmed.".format(data[index].text)
  data[index].dimmed = True
  data[index].marked = False
  
def rm(settings, data, index):
  print "Element `{}' removed.".format(data.pop(index).text)
  
def mark(settings, data, index):
  print "Element `{}' marked.".format(data[index].text)
  data[index].marked = True
  data[index].dimmed = False
  
def hide(settings, data, index):
  if data[index].anyTrue(strict):
    print "Warning: element {} already hidden. Item skipped.".format(index)
    return
  if data[index].indeterminate:
    indet_hide(data[index])
  elif data[index].duedate is None: 
    data[index].startdate = date.today() + timedelta(days=3)
    print "Element `{}' will be shown again in 3 days.".format(data[index].text)
  else: 
    data[index].startdate = min(date.today() + timedelta(days=3), data[index].duedate - timedelta(days=2))
    print "Element `{}' will be shown again in {} days.".format(data[index].text, (date.today()-data[index].startdate).days)
  
def undim(settings, data, index):
  print "Element `{}' undimmed.".format(data[index].text)
  data[index].dimmed = False
  
def unmark(settings, data, index):
  print "Element `{}' unmarked.".format(data[index].text)
  data[index].marked = False
  
def determine(settings, data, index):
  if not data[index].indeterminate:
    print "Warning: Element {} was not indeterminate.".format(index)
  data[index].indeterminate = False
  print "Element `{}' fixed.".format(data[index].text)
  
def indetermine(settings, data, index):
  if data[index].indeterminate:
    print "Warning: Element {} was already indeterminate.".format(index)
  data[index].indeterminate = True
  print "Element `{}' is now indeterminate.".format(data[index].text)
  
def pull(settings):
  data = getdata(settings.filename)
  
  categoryRestrict = [str.upper() for str in settings.categories]
  catlam = lambda item: not (item.category in categoryRestrict or (item.category is None and "NONE" in categoryRestrict))
  
  #All indeterminate hidden items, restricted to categories if necessary
  indet = [item for item in data if item.indeterminate and (len(categoryRestrict) == 0 or not catlam(item)) and item.anyTrue(strict)]
  
  quant = settings.quantity
  if quant < 1:
    quant = 1
    print "Warning: Quantity must be positive. Defaulted to pulling 1."
  
  shuffle(indet)
  for item in indet[:min(quant,len(indet))]:
    print "Pulling element {}.".format(data.index(item))
    item.startdate = date.today()
    
  print_list(data, print_item_sparse, strict)
  rewrite(settings.filename, data)
  
def push(settings):
  data = getdata(settings.filename)
  
  #All indeterminate hidden items, restricted to categories if necessary
  indet = [item for item in data if item.indeterminate and not item.anyTrue(strict)]
  
  if len(indet) == 0:
    print "Warning: No indeterminate items to hide."
    print_list(data, print_item_sparse, strict)
    return
  
  quant = settings.quantity
  if quant < 1:
    quant = 1
    print "Warning: Quantity must be positive. Defaulted to pushing 1."
  
  shuffle(indet)
  for item in indet[:min(quant,len(indet))]:
    indet_hide(item)
    
  print_list(data, print_item_sparse, strict)
  rewrite(settings.filename, data)
  
def getdata(filename):
  with open(filename, 'rb') as f:
    try:
      return load(f)
    except Exception:
      print "File '{}' could not be loaded correctly. Run `odo init' to create a new todo file.".format(filename)
      exit(1)
      
def print_command(settings):
  data = getdata(settings.filename)
  categoryRestrict = [str.upper() for str in settings.categories]
  skipPred = [lambda item: not (item.category in categoryRestrict or (item.category is None and "NONE" in categoryRestrict))]
  if len(categoryRestrict) == 0:
    skipPred = []
    
  if settings.determinate:
    skipPred = skipPred + [is_det]
  elif settings.indeterminate:
    skipPred = skipPred + [is_indet]
    
  if settings.verbose:
    print_list(data, print_item_verbose, skipPred)
  else:
    print_list(data, print_item_sparse, strict + skipPred)
      
def print_item_sparse(index, item):
  if index < 0:
    print '|  ID |    CAT  ITEM DESCRIPTION                                  |   DUE      |'
    return
  duestr = item.duedate.strftime("%a %d %b") if item.duedate is not None else ""
  wrapped = wrap(item.text, 47, 45)
  imp = " "
  if item.indeterminate and item.dimmed:
    imp = "d"
  elif item.indeterminate:
    imp = "?"
  elif item.dimmed:
    imp = "D"
  print '| {:3d} | {}{} {!s:<47s} {}\033[0m | {:10s} |'.format(index,item.color(),item.category_str(),wrapped[0], imp, duestr)
  for extraline in wrapped[1:]:
    print ('|     | {}          {!s:<45s}  \033[0m | {:10s} |'.format(item.color(),extraline," "))
    
def print_item_verbose(index, item):
  if index < 0:
    print '|  ID |    CAT  ITEM DESCRIPTION                     |   START         DUE     |'
    return
  duestr = item.duedate.strftime("%a %d %b") if item.duedate is not None else ""  
  stdstr = item.startdate.strftime("%a %d %b") if item.startdate is not None else ""
  dash = "-" if item.startdate is not None and item.duedate is not None else " "
  wrapped = wrap(item.text, 34, 32)
  imp = " "
  if item.indeterminate and item.dimmed:
    imp = "d"
  elif item.indeterminate:
    imp = "?"
  elif item.dimmed:
    imp = "D"
  print '| {:3d} | {}{} {!s:<34s} {}\033[0m | {:10s} {} {:10s} |'.format(index,item.color(),item.category_str(),wrapped[0], imp, stdstr, dash, duestr)
  for extraline in wrapped[1:]:
    print ('|     | {}          {!s:<32s}  \033[0m | {:23s} |'.format(item.color(),extraline," "))
      
def print_list(data, method=print_item_sparse, skip_preds=[]):
  print '+'+'='*78+'+'
  method(-1,None)
  print '+'+'='*78+'+'
  for num,item in enumerate(data):
    if not item.anyTrue(skip_preds):
      method(num,item)
  print '+'+'='*78+'+'
      
def rewrite(filename, data):
  data.sort()
  midwayfile = filename+".dump"+str(randint(1,1000))
  try:
    with open(midwayfile, 'wb') as f:
      dump(data, f, protocol=0)
  except Exception:
    print "Fatal Error: File failed to rewrite! Changes safely aborted."
    exit(1)
  copyfile(midwayfile, filename)
  remove(midwayfile)
    
def wrap(str, wrapLen, shortenLen):
  if str is None or len(str) == 0:
    return []
  if wrapLen > len(str):
    return [str]
  splitInd, include, curInd = -1,0,0
  while curInd < wrapLen:
    if str[curInd] == ' ':
      include = 0
      splitInd = curInd
    elif str[curInd] in punctuation:
      include = 1
      splitInd = curInd
    curInd = curInd + 1
  if splitInd == -1: return [str[:wrapLen]]+wrap(str[wrapLen:], shortenLen, shortenLen)
  return [str[:splitInd+include]]+wrap(str[splitInd+1:], shortenLen, shortenLen)