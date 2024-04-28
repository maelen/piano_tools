#!/usr/bin/env python3

# How to use
#   convert_songbook.py <input> -sf <split file>
# Split file format (One song per line)
#   <page number in pdf> <title of song>

import logging
import argparse
import os
import sys
import subprocess
import hashlib
from lxml import etree

def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="musicxml or musescore input file")
    parser.add_argument("output", nargs='?', help="optional output folder")
    parser.add_argument("-sf", "--split", help="File used to split input pdf document")
    args = parser.parse_args()
    return args


def main():
  args = process_args()
  #logging.basicConfig(level=logging._nameToLevel[args.debug])
  if not os.path.isfile(args.input):
    print("File does not exist: {}".format(args.input))
    sys.exit(-1)
  # Open split file
  previous_line = None
  i=100
  with open(args.split) as split_file:
    for line in split_file:
      line = line.rstrip()
      if previous_line is None:
         previous_line = line
         continue
      first_page, title = previous_line.split(" ", 1)
      last_page = int(line.split(" ", 1)[0]) - 1
      print (f"pdftk '{args.input}' cat {first_page}-{last_page} output '{i}-{title}.pdf'")
      try:
        subprocess.run(["pdftk", f"{args.input}", "cat", f"{first_page}-{last_page}", "output", f"{i}-{title}.pdf"])
      except:
        print("Probleme running pdftk")
        sys.exit(1)
      previous_line = line
      i+=1

if __name__ == "__main__":
    main()
