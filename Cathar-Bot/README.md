# catharbot
Open Library clean-up bot making use of the [openlibrary-client](https://github.com/internetarchive/openlibrary-client)

This is an experimental extension of the openlibrary-client, and hopefully some of its features will be moved back into the parent client as the prove successful.

Usage:

```
from catharbot import catharbot
bot = catharbot.CatharBot()
```

gives you a bot that is a sub-class of the `olclient` `OpenLibrary` which can do everything the parent can do, and more!

`edition = bot.load_doc("OL12345M")`

Loads JSON representation of an OpenLibrary document (Author, Work, or Edition) by ID.

The fields can then be read and manipulated.

`edition['title'] = "Changed Title"`

To save the edition back to Open Library:

`bot.save_one(edition, "Some comment describing the changes")`

Multiple documents can be saved in one commit by passing a list to

`bot.save_many([e1, e2, w1, a1, a2, ... etc], "Comment for all the changes")`

This bot has some functions that perform changes in one step, **use with caution!**

## Merge Editions
**use with caution!**
Performs a simplistic merge, assuming all data on duplicates has already been transferred to the target master :

`bot.merge_editions(["OL...1M, "OL...2M", "OL...3M"], "OL<master>M")`

This takes a list of edition OLIDs and converts them into redirects pointing the master edition.

## Merge Works
**use with caution!**
Performs a simplistic merge, assuming all data on duplicates has already been transferred to the target master:

`bot.merge_works(["OL...1W, "OL...2W", "OL...3W"], "OL<master>W")`

This collects all editions of the duplicate works, and changes their work key to point to the master work, then converts the duplicate works to redirects to the master.

## Bulk Deletes
**use with caution!**
This does not check for external references and could leave things broken -- only use when absolutely sure the records should go. Redirects are always preferred when relevant. 

`bot.delete_list(["OL...1M, "OL...2M", "OL...3M"], "Comment explaining reason for deletion")`
