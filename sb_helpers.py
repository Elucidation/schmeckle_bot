# -*- coding: utf-8 -*-
import re
import time
import locale
from datetime import datetime
from math import isinf

# For converting from string numbers with english-based commas to floats
#locale.setlocale(locale.LC_ALL, 'eng_USA') # Windows
locale.setlocale(locale.LC_ALL, 'en_GB.utf8') # Linux (Raspberry Pi 2)

def getResponseFooter():
  return "\n\n---\n\n[^(1 Schmeckle = $148 USD)](https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79)^( | price not guaranteed |) [^(`what is my purpose`)](https://github.com/Elucidation/schmeckle_bot 'convert Schmeckles to USD')"

def schmeckle2usd(schmeckle):
  """1 Schmeckle = $148 USD
  https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79"""
  return schmeckle * 148.0

def getValue(value_str):
  # Strings with more than 9000 characters are considered too big to handle so
  # we don't run into char limits when generating a reply
  if (len(value_str)) > 9000:
    value = locale.atof('inf')
  else:
    value = locale.atof(value_str)
  return value

def getCommentDepth(comment):
  depth = 0
  while not comment.is_root:
    comment = comment.parent()
    depth += 1
  return depth

def generateResponseMessage(search_result):
  match = search_result.groups()[1] # Middle group
  value_str = match.split()[0]
  
  if len(match) > 1000 or len(value_str) > 300:
    # message or value was too big, generate a different message
    msg = u"# **Nope.**\n"
  else:
    value = getValue(value_str) # pass found value string
    usd = schmeckle2usd(value)
    quote = u"> ... {}{}{} ...".format(search_result.groups()[0], match, search_result.groups()[2])
    if value > 1e15:
      msg = u"{}\n\n* {:,g} Schmeckles → **${:,g} USD**\n".format(
        quote, value, usd)
    elif value.is_integer():
      msg = u"{}\n\n* {:,d} Schmeckles → **${:,d} USD**\n".format(
        quote, int(value), int(usd))
    else:
      msg = u"{}\n\n* {:,.8g} Schmeckles → **${:,.2f} USD**\n".format(
      quote, value, usd)

  return u"{}{}".format(msg, getResponseFooter())


# Look for '<number> schmeckle' ignore case (schmeckles accepted implicitly)
# Also handles common mispellings of schmeckle
# Works for positive negative floats, but fails softly on EXP
# Also catches neighboring region around it
# p = re.compile('(-?[\d|,]*\.{0,1}\d+ sc?hmeck?(?:le|el)[\w]{0,80})', re.IGNORECASE)
# Ignore numbers > 300 chars on either side of decimal
# Also require a question-mark in statement
p = re.compile('([^\n\.\,\r\d-]{0,30})(-?[\d|,]{0,300}\.{0,1}\d{1,300} schmeckle[\w]{0,80})([^\n\.\,\r\d-]{0,30})', re.IGNORECASE)
def searchForSchmeckles(body_text):
  if any([x in body_text.lower() for x in ['?', 'how much', 'what is']]):
    return p.search(body_text)
  return None


# Check if comment has a comment by this bot already, or is a comment by bot
def previouslyRepliedTo(comment, me):
  # Check if comment author is self, skip if so
  if comment.author == me:
    return True
  # Check if author of parent of comment is self
  if comment.parent().author == me:
    # Check if comment contains github self-link, skip if so as it's probably
    # a quote
    if 'github.com/Elucidation/schmeckle_bot' in comment.body:
      return True
  comment.refresh() # So we can see replies
  for reply in comment.replies.list():
    if reply.author == me:
      return True
  return False


def waitWithComments(sleep_time, segment=60):
  """Sleep for sleep_time seconds, printing to stdout every segment of time"""
  print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
  while sleep_time > segment:
    time.sleep(segment) # sleep in increments of 1 minute
    sleep_time -= segment
    print("\t%s - %s seconds to go..." % (datetime.now(), sleep_time))
  time.sleep(sleep_time)

def logMessage(comment, status=""):
  print("{} | {} {}: {}".format(datetime.now(), comment.id, status, comment.body[:80].replace('\n','\\n').encode('utf-8')))
