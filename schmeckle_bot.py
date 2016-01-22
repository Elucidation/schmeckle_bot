#!/usr/bin/python
# -*- coding: utf-8 -*-
# Find comments with schmeckles in it and comment with value converted to USD
import praw
import re
import locale
import collections
import os
import time
from datetime import datetime
from praw.helpers import comment_stream
import requests
import socket
from math import isinf

import auth_config

#########################################################
# Setup

# For converting from string numbers with english-based commas to floats
#locale.setlocale(locale.LC_ALL, 'eng_USA') # Windows
locale.setlocale(locale.LC_ALL, 'en_GB.utf8') # Linux (Raspberry Pi 2)

# Set up praw
schmeckle_bot_name = "SchmeckleBot"
user_agent = schmeckle_bot_name + " converts Schmeckles to USD in rickandmorty subreddit. See https://github.com/Elucidation/schmeckle_bot"

# Login
r = praw.Reddit(user_agent=user_agent)

# Login old-style due to Reddit politics
r.login(auth_config.USERNAME, auth_config.PASSWORD, disable_warning=True)

# Get accessor to comments
subreddit = r.get_subreddit('rickandmorty')
#comments = subreddit.get_comments(limit=None) # Using comment_stream instead for continuous yield

# Look for '<number> schmeckle' ignore case (schmeckles accepted implicitly)
# Works for positive negative floats, but fails softly on EXP
p = re.compile('(-?[\d|,]*\.{0,1}\d+ schmeckle[\w]*)', re.IGNORECASE)

# Ignore quotes
quote_remove = re.compile("^> .*\n", re.MULTILINE)

# How long a quote in either direction can be before truncating
max_sentence_buffer = 100

# How many characters a number can have max
max_number_length = 100

# How many comments to read initially in stream
comment_stream_limit = 100

# How many submissions to read from now initially
submission_read_limit = 100


#########################################################
# Helper Functions

def getQuote(body):
  """Generate Quote for comment"""
  lines = []
  body = quote_remove.sub('', body) # Remove quoted lines

  if len(body) > max_sentence_buffer*2:
    for match in p.finditer(body):
      short_line = ""

      # Handle case of match being larger than sentence buffer
      safe_start = match.start()
      if (match.end() - match.start() > max_number_length):
        safe_start = match.end() - max_number_length

      a = max(0,safe_start-max_sentence_buffer)
      b = min(len(body),match.end()+max_sentence_buffer)
      print(a,b)

      short_line = body[a:b]

      # Append quote initializer to each double newline (markdown newline)
      short_line = '\n\n> '.join(short_line.split('\n\n'))

      if a == 0:
        s_a = ''
      else:
        s_a = '... '
      if b == len(body):
        s_b = ''
      else:
        s_b = ' ...'

      lines.append(s_a+short_line+s_b)
  else:
    lines = [body]
  
  quote = ["> " + p.sub(r'**\1**', line) + "\n" for line in lines]
  return quote

def schmeckle2usd(schmeckle):
  """1 Schmeckle = $148 USD
  https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79"""
  return schmeckle * 148.0

def getConversion(body):
  """Calculate schmeckle to USD responses"""
  values = []
  msg_template_f = u"* {:,.2f} Schmeckles → **${:,.2f} USD**\n" # with decimals
  msg_template_i = u"* {:,.0f} Schmeckles → **${:,.0f} USD**\n" # without decimals
  msg_inf = u"* There's a lot of numbers there, I think you could probably go to Wall Street.\n\n*You ever hear about Wall Street, Morty? Y-Y-Y'know what those guys do i-in-in their fancy boardrooms? They take their balls and they dip 'em in cocaine and wipe 'em all over each other—y'know.*\n"
  pairs = p.findall(body)
  if len(pairs) > 0:
    for match in pairs:
      # '<number> schmeckle' -> match, float(<number>)
      value_str = match.split()[0]

      # Handle numbers with over 9000 characters. Yes, it's over 9000.
      if (len(value_str)) > 9000:
        values.append(locale.atof('inf'))
      else:
        values.append(locale.atof(value_str))
  
  response = []
  for schmeckle in values:
    if isinf(schmeckle):
      response.append(msg_inf)
    else:
      usd = schmeckle2usd(schmeckle)
      if schmeckle.is_integer():
        response.append(msg_template_i.format(schmeckle, usd))
      else:
        response.append(msg_template_f.format(schmeckle, usd))
  
  return [response, values]


question_indicators = ["how","what","value","?", "!"]
def getResponse(body, skipPartial=True):
  """Get response packet to use for replying to message"""
  # If there is a schmeckle value in body
  if p.search(body):
    if skipPartial and not any([q in body.lower() for q in question_indicators]):
      print("\n------\nPartial Match Skipped:\n%s\n------\n"%body)
      return None
    quote = getQuote(body)
    conversion, values = getConversion(body)

    # Combine into message
    msg = "\n\n".join(quote)
    msg += "\n" + "\n".join(conversion)
    msg += "\n---\n"
    msg += "\n[^(1 Schmeckle = $148 USD)](https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79)^( | price not guaranteed |) [^(`what is my purpose`)](https://github.com/Elucidation/schmeckle_bot 'convert Schmeckles to USD')"
    return [quote, conversion, values, msg]

  return None

# Filename containing list of comment ids that have already been processed, updated at end of program
processed_filename = "comments_already_processed.txt"
replies_filename = "comments_reply_list.txt"
def loadProcessed():
  if not os.path.isfile(processed_filename):
    print("%s - Starting new processed file" % datetime.now())
    return set()
  else:
    print("Loading existing processed file...")
    with open(processed_filename,'r') as f:
      return set([x.strip() for x in f.readlines()])

def saveProcessed(already_processed):
  with open(processed_filename,'w') as f:
    for comment_id in already_processed:
      f.write("%s\n" % comment_id)
  print("%s - Saved processed ids to file" % datetime.now())

def updateProcessed(comment_or_submission, response):
  """Update Comments or Submission in text file containing all comments/submissions made"""
  quote, conversions, values, msg = response
  name = "Comment"
  if type(comment_or_submission) == praw.objects.Submission:
      name = "Submission"
  with open(replies_filename,'a') as f:
    # ignore unicode arrow, remove footer and strip extra newlines
    f.write("# {} ID `{}` - {}\n{}\n---\n".format(name, comment_or_submission.id, datetime.now(), msg.split('---')[0].encode('ascii','ignore').strip()))

def checkSubmissions(limit=submission_read_limit):
  """Check new submissions in subreddit and add comments if they warrant a response"""
  submissions = subreddit.get_new(limit=limit)
  internal_count = 0

  print("\n---\n%s - Checking latest submissions..." % (datetime.now()))
  for submission in submissions:
    if submission.id in already_processed:
      print("%s - Skipping previously processed: %s" % (datetime.now(), submission.id))
      continue
    
    response = getResponse(submission.title, skipPartial=False)
    #print("\t Read(%s): %s" % (submission.id, submission))
    
    # If valid submission
    if response:
      internal_count += 1
      msg = response[3] # response = [quote_text, conversion_text, value, full_response_text]
      while True:
        try:
          print("\n%s - Commenting on %s..." % (datetime.now(), submission.id))
          print("\n\t%s\n\n" % (submission))
          submission.add_comment(msg)
          already_processed.add(submission.id) # Remove from already_processed as we didn't get it
          print("> %s - Successful added comment to %s" % (datetime.now(), submission.id))
          updateProcessed(submission, response)
          break
        except praw.errors.AlreadySubmitted as e:
          print("> %s - Already submitted skipping..." % datetime.now())
          break
        except praw.errors.RateLimitExceeded as e:
          print("> %s - Rate Limit Error for replying to {}, sleeping for {} before retrying...".format(datetime.now(), submission.id, e.sleep_time))
          sleep_time = e.sleep_time
          while sleep_time > 60:
            time.sleep(60) # sleep in increments of 1 minute
            sleep_time -= 60
            print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
          time.sleep(sleep_time)

  # Number of comments sent
  return internal_count

#########################################################
# Main Script
# Track commend ids that have already been processed successfully

# Load list of already processed comment ids
already_processed = loadProcessed()
print("%s - Starting with already processed: %s\n==========\n\n" % (datetime.now(), already_processed))

last = time.time()
count = 0
count_actual = 0
running = True
while running:
  try:    
    # Read in comments from accessor and process them
    print ("\n\t---\n\t%s - Generating fresh comment stream\n\t---\n\n" % datetime.now())
    comments = comment_stream(r, subreddit, limit=comment_stream_limit)
    for comment in comments:
      if ((time.time() - last) > 120):
        print("\n\t---\n\t%s - %d processed comments, %d read\n" % (datetime.now(), count_actual, count))
        # Read in submissions and process
        # Check submissions
        print ("\n\t---\n\t%s - Processing hot submissions \n\t---\n\n" % datetime.now())
        count_actual += checkSubmissions()
        print ("\n\t---\n")

        last = time.time()
      
      if (count > comment_stream_limit):
        print("#%d Read(%s): %s" % (count, comment.id, comment))

      count += 1
      # Ignore self comments or comments that have been processed already
      if comment.author.name == schmeckle_bot_name:
        print("%s - Skipping self comment: %s" % (datetime.now(), comment.id))
        continue
      elif comment.id in already_processed:
        print("%s - Skipping previously processed: %s" % (datetime.now(), comment.id))
        continue
      
      # If there is a schmeckle value in body
      response = getResponse(comment.body)
      if not response:
        # Not a schmeckle convertable comment, continue
        continue
      
      count_actual += 1
      # response = [quote_text, conversion_text, value, full_response_text]
      msg = response[3]
      while True:
        try:
          print("\n%s - Replying to %s..." % (datetime.now(), comment.id))
          comment.reply(msg)
          already_processed.add(comment.id) # Remove from already_processed as we didn't get it
          print("> %s - Successful reply to %s" % (datetime.now(), comment.id))
          updateProcessed(comment, response)
          break
        except praw.errors.AlreadySubmitted as e:
          print("> %s - Already submitted skipping..." % datetime.now())
          break
        except praw.errors.RateLimitExceeded as e:
          print("> %s - Rate Limit Error for replying to {}, sleeping for {} before retrying...".format(datetime.now(), comment.id, e.sleep_time))
          sleep_time = e.sleep_time
          while sleep_time > 60:
            time.sleep(60) # sleep in increments of 1 minute
            sleep_time -= 60
            print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
          time.sleep(sleep_time)
      
      # Save after each comment
      saveProcessed(already_processed)
      # 5 minutes per comment max speed, add on time it takes to check submissions
      sleep_time = 300
      print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
      while sleep_time > 60:
        time.sleep(60) # sleep in increments of 1 minute
        sleep_time -= 60
        print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
      time.sleep(sleep_time)

  except (socket.error, requests.exceptions.ReadTimeout, requests.packages.urllib3.exceptions.ReadTimeoutError, requests.exceptions.ConnectionError) as e:
    print("> %s - Connection error, resetting accessor, waiting 30 and trying again: %s" % (datetime.now(), e))
    saveProcessed(already_processed)
    time.sleep(30)
    continue
  except Exception as e:
    print("Unknown Error:",e)
  except KeyboardInterrupt:
    print("Exiting...")
    running = False
  finally:
    saveProcessed(already_processed)
    print("%s - Processed so far:\n%s" % (datetime.now(),already_processed))

print("%s - Program Ended. Total Processed Comments (%d replied / %d read):\n%s" % (datetime.now(), count_actual, count, already_processed))

# TODO: handle print() unicode error at some point
# TODO: track comments that have been replied to in a deque cache to avoid repeats
# TODO: Consider markdown tables
