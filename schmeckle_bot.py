#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SchmeckleBot daemon
# Listens on rickandmorty subreddit for comments that
# have schmeckle conversion requests in them and respond with conversion
# Run with --dry to dry run without actual submissions
from __future__ import print_function
import praw
import requests
import socket
import time
from datetime import datetime
import argparse

from sb_helpers import *

REPLY_WAIT_TIME = 300
FAIL_WAIT_TIME = 30


def startStream(args):
  reddit = praw.Reddit('SB') # client credentials set up in local praw.ini file
  sb = reddit.user.me() # SchmeckleBot object
  subreddit = reddit.subreddit('rickandmorty')

  # Start live stream on all submissions in the subreddit
  for comment in subreddit.stream.comments():
    # Check if comment already has a reply
    if not previouslyRepliedTo(comment, sb):
      # check if comment has schmeckles in it
      if len(comment.body) > 9000:
        # Ignore really long comments, worst case 9000 nines takes ~27 seconds
        # to search through
        search_result = None
      else:
        search_result = searchForSchmeckles(comment.body)
      if search_result:
        # Generate response
        response = generateResponseMessage(search_result)

        # Reply to submission with response
        if not args.dry:
          logMessage(comment,"[REPLIED]")
          comment.reply(response)
        else:
          logMessage(comment,"[DRY-RUN-REPLIED]")

        # Wait after submitting to not overload
        waitWithComments(REPLY_WAIT_TIME)
      
      else:
        # Not a schmeckle message
        logMessage(comment)
        time.sleep(1) # Wait a second between normal submissions

    else:
      logMessage(submission,"[SKIP]") # Skip since replied to already
    

def main(args):
  running = True
  while running:
    try:
      startStream(args)
    except (socket.error, requests.exceptions.ReadTimeout,
            requests.packages.urllib3.exceptions.ReadTimeoutError,
            requests.exceptions.ConnectionError) as e:
      print(
        "> %s - Connection error, retrying in %d seconds: %s" % (
        FAIL_WAIT_TIME, datetime.now(), e))
      time.sleep(FAIL_WAIT_TIME)
      continue
    except Exception as e:
      print("Unknown Error, attempting restart in %d seconds:" % FAIL_WAIT_TIME
        ,e)
      time.sleep(FAIL_WAIT_TIME)
      continue
    except KeyboardInterrupt:
      print("Keyboard Interrupt: Exiting...")
      running = False
  print('Finished')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--dry', help='dry run (don\'t actually submit replies)',
                      action="store_true", default=False)
  args = parser.parse_args()
  main(args)