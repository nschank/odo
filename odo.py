import argparse
import os

from odo_op import add, getdata, print_command, rewrite, rm, mark, unmark, hide, batch, edit, push, pull, determine, indetermine, dim, undim
from pickle import dump

def create_add(parser):
  subparser = parser.add_parser('add', help='Adds an item to the todo list.')
  subparser.add_argument('item', nargs='+', help='The item to add.')
  subparser.add_argument('-d', dest='dimmed', action='store_true', default=False, help='Marks the action as dimmed, i.e. less visible.')
  subparser.add_argument('-i', dest='indeterminate', action='store_true', default=False, help='Marks the added argument as indeterminate. The command odo pull selects a random indeterminate item and unhides it; odo push hides a random indeterminate item. Intended for use with activities that can be done at any time.')
  subparser.add_argument('-m', dest='marked', action='store_true', default=False, help='Marks the added argument.')
  subparser.add_argument('-p', dest='hide', action='store_true', default=False, help='Hides this item after adding it.')
  subparser.add_argument('-s', dest='start', nargs='+', help='Adds a start date to the added action. Does not print (except if verbose) until that date.')
  subparser.add_argument('-t', dest='time', nargs='+', help='Adds a due date to the added action.')
  subparser.set_defaults(func=add)
  
def create_batch(parser, command, helpval, action):
  subparser = parser.add_parser(command, help=helpval)
  subparser.add_argument('indices', nargs='+', type=int, help='The item indices to alter.')
  subparser.add_argument('-f', dest='force', action='store_true', default=False, help='Allows operation on hidden values.')
  subparser.set_defaults(func=batch)
  subparser.set_defaults(innerfunc=action)
  
def create_edit(parser):
  subparser = parser.add_parser('edit', help='Edits an item on the todo list.')
  subparser.add_argument('index', type=int, help='The index of the item to edit.')
  subparser.add_argument('-c', dest='category', nargs='*', help='Adds or edits the category of the specified action. If no argument is given, removes the category.')
  subparser.add_argument('-f', dest='force', action='store_true', default=False, help='Allows operation on hidden values.')
  subparser.add_argument('-p', dest='hide', action='store_true', default=False, help='Hides this item after adding it.')
  edit_imp = subparser.add_mutually_exclusive_group()
  edit_imp.add_argument('-i', dest='indeterminate', action='store_true', default=False, help='Marks the argument as indeterminate.')
  edit_imp.add_argument('-I', dest='determinate', action='store_true', default=False, help='Marks the added argument as not indeterminate.')
  edit_mrk = subparser.add_mutually_exclusive_group()
  edit_mrk.add_argument('-d', dest='dim', action='store_true', default=False, help='Marks the index as less visible.')
  edit_mrk.add_argument('-m', dest='mark', action='store_true', default=False, help='Marks the index as more visible.')
  edit_mrk.add_argument('-n', dest='normal', action='store_true', default=False, help='Marks the index as normal visibility.')
  subparser.add_argument('-s', dest='start', nargs='*', help='Adds or edits a start date to the specified action. If no argument is given, removes the start date.')
  subparser.add_argument('-t', dest='time', nargs='*', help='Adds or edits a due date to the specified action. If no argument is given, removes the due date.')
  subparser.add_argument('-v', dest='item', nargs='+', help='Sets the title of the specified action.')
  subparser.set_defaults(func=edit)
  
def create_init(parser):
  subparser = parser.add_parser('init', help='Creates an empty todo list.')
  subparser.set_defaults(func=init)
  
def create_print(parser):
  subparser = parser.add_parser('print', help='Prints the todo list.')
  subparser.add_argument('categories', metavar='C', nargs='*', help='Categories within the todo list to get from specifically. None is an option.')
  subparser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Prints entire list rather than just relevant items.')
  print_ind = subparser.add_mutually_exclusive_group()
  print_ind.add_argument('-i', dest='indeterminate', action='store_true', default=False, help='Displays only indeterminates')
  print_ind.add_argument('-d', dest='determinate', action='store_true', default=False, help='Suppresses inactive indeterminates.')
  subparser.set_defaults(func=print_command)
  
def create_pull(parser):
  subparser = parser.add_parser('pull', help='Unhides hidden, indeterminate items at random.')
  subparser.add_argument('quantity', type=int, nargs='?', default=1, help='The number of items to pull. Default: 1.')
  subparser.add_argument('-c', dest='categories', default=[], nargs='+', help='Categories within the todo list to get from specifically. None is an option.')
  subparser.set_defaults(func=pull)
  
def create_push(parser):
  subparser = parser.add_parser('push', help='Hides a visible, indeterminate item at random.')
  subparser.add_argument('quantity', type=int, nargs='?', default=1, help='The number of items to push. Default: 1.')
  subparser.set_defaults(func=push)
  
def init(settings):
  filename = settings.filename
  try:
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(fd, 'wb') as f:
      dump([], f, protocol=0)
  except OSError:
    print "File '{}' already exists.".format(filename)

def parse():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Allows for basic usage of a to-do list.')
  parser.add_argument('filename', metavar='F', help='A file to be used as a to-do list.')
  subparsers = parser.add_subparsers(help='sub-command help')
  
  create_add(subparsers)
  create_init(subparsers)
  create_print(subparsers)
  create_batch(subparsers,"rm","Removes elements from the todo list.",rm)
  create_batch(subparsers,"hide","Hides elements from the todo list for three days, or up to until 2 days before the item is due, whichever is earlier.",hide)
  create_batch(subparsers,"mark","Marks elements on the todo list to call attention.",mark)
  create_batch(subparsers,"unmark","Unmarks elements from the todo list which have been marked.",unmark)
  create_batch(subparsers,"fix","Sets indeterminate items from the todo list as not indeterminate. See odo pull/push.",determine)
  create_batch(subparsers,"indet","Sets elements from the todo list as indeterminate. See odo pull/push",indetermine)
  create_batch(subparsers,"dim","Dims an element so that it is less visible in the list.",dim)
  create_batch(subparsers,"undim","Undims an element so that it is at regular visibility in the list",undim)
  create_push(subparsers)
  create_pull(subparsers)
  create_edit(subparsers)
  
  return parser.parse_args()
    
def main():
  settings = parse()
  settings.func(settings)
    
main()
