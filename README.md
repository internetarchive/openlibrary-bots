# openlibrary-bots
[Open Library](https://openlibrary.org) is an open, editable library catalog, building towards a web page for every book ever published. This repository contains cleanup bots implementing the `openlibrary-client` which allow developers to add/edit/remove different works/editions on Open Library.

## Table of Contents
   - [Overview](#overview)
   - [Installation](#installation)
   - [Developer's Guide](#developers-guide)
   - [Contributing](#contributing)
   - [FAQs](https://openlibrary.org/help/faq)
   - [License](#license)
   - [Bots Wiki](https://github.com/internetarchive/openlibrary-bots/wiki)

## Overview

Open Library is an effort started in 2006 to create "one web page for every book ever published". It provides access to many public domain and out-of-print books, which can be read online.

- [Learn more about the Open Library project](https://openlibrary.org/about)
- [The Vision (Dream) of OpenLibrary](https://openlibrary.org/about/vision)
- [Visit the Blog](http://blog.openlibrary.org)

## Installation

First, fork the [OpenLibrary repo](https://github.com/internetarchive/openlibrary-bots) to your own [Github](https://www.github.com) account and clone your forked repo to your local machine:

```
git clone git@github.com:YOURACCOUNT/openlibrary-bots.git
```

Enter the project directory using the following commands:
```
cd openlibrary-bots/
```

## Developer's Guide

For instructions on administrating your Open Library instance and build instructions for developers, refer the Developer's [Getting Started with Bots](https://github.com/internetarchive/openlibrary/wiki/Writing-Bots) Guide.

You can also find more information regarding Developer Documentation for Open Library in the Open Library [Wiki](https://github.com/internetarchive/openlibrary/wiki/)

Typically every folder signifies a different bot. The folder must contain code with respect to the bot, a `README.md` file which tells the user how to run the bot and any dependecies or `requirements.txt` file which can make it easier for a user to run the bot.

## Contributing

[Check out our contributor's guide](CONTRIBUTING.md) to learn how you can contribute!

## License

All source code published here is available under the terms of the GNU Affero General Public License, version 3. Please see http://gplv3.fsf.org/ for more information.

## Current Active Bots
- IA-Wishlist Bot - (Maintained by [Salman Shah](https://github.com/salman-bhai)).
- ONIX Bot - (Maintained by [Salman Shah](https://github.com/salman-bhai))
- NY Times Bestseller Bot

## Inactive Bots
- [Cathar Bot](https://github.com/hornc/catharbot) - (Maintained by [Charles](https://github.com/hornc))