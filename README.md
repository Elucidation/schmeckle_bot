# SchmeckleBot
[/u/SchmeckleBot](https://www.reddit.com/user/SchmeckleBot/) is a [Reddit](http://www.reddit.com) Bot whose sole purpose is to listen on [/r/rickandmorty](https://www.reddit.com/r/rickandmorty/) subreddit and provide currency conversions from Schmeckles to USD.

According to the creators, [1 Schmeckle is worth about $148 USD](https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79).

## Feedback/Comments

Several options from low priority to high:
* Send a PM to SchmeckleBot with comments.
* If there's an issue with a particular comment by SchmeckleBot, please either reply to that comment with the issue and downvote as needed, I'll be adding auto-deletion if a comment goes negative.
* For software issues/suggestions/feature requests, create a new issue on this Github.


## Invoking SchmeckleBot

SchmeckleBot is usually running on a Raspberry Pi.  It listens to the [/r/rickandmorty](https://www.reddit.com/r/rickandmorty/) subreddit comment stream.

If a comment has both a `<number> schmeckle(s)` and one of the following: `how`, `what`, `?`, `!`, then the bot will generate a reply message that looks like something like [this](https://www.reddit.com/r/rickandmorty/comments/40udy4/brace_yourselves/cyxpgnh?context=10000):

===

> I would pay **2,000 schmeckles** to not see any screenshots. I play the game. I don't need to see screenshots. 

* 2,000.00 Schmeckles → **$296,000.00 USD**

---

<sup>[1 Schmeckle = $148 USD](https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79) | price not guaranteed | [`what is my purpose`](https://github.com/Elucidation/schmeckle_bot 'convert Schmeckles to USD')</sub>

===


If you make a comment that satisfies those two requirements, and the bot is running, it will probably see and reply with the conversion within a couple minutes (10 minutes at worst).

Regex used: `p = re.compile('(-?[\d|,]*\.{0,1}\d+ schmeckle[\w]*)', re.IGNORECASE)`

This allows for variants on `schmeckle` like schmeckles, Schmeckles!!!, schmecklearoos, etc.