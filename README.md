# SchmeckleBot
[Reddit](http://www.reddit.com) Bot for converting Rick &amp; Morty Schmeckles to USD

# Invoking SchmeckleBot

When SchmeckleBot is running, it listens to a comment stream on the [/r/rickandmorty](https://www.reddit.com/r/rickandmorty/) subreddit.

A comment is a candidate if it has a number followed by schmeckle (or schmeckles or any other set of letters beyond) like `<number> schmeckle`, and the message contains one of the following strings as well to signify a question or exclamation: `how`, `what`, `?`, `!`.

Regex used:

    p = re.compile('(-?[\d|,]*\.{0,1}\d+ schmeckle[\w]*)', re.IGNORECASE)

---

See comment history for [/u/SchmeckleBot](https://www.reddit.com/user/SchmeckleBot/)
