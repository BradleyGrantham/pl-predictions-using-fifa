# Premier League predictions using fifa ratings

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![Twitter Follow](https://img.shields.io/twitter/follow/espadrine.svg?style=social&label=Follow)](https://twitter.com/BradleyGrantham)

This is the code base I created to both collect football data, and then
use this data to train a neural network to predict the outcomes of football
matches based on the fifa ratings of a team's starting 11.

See the [blog post](https://medium.com/@bradleygrantham/predicting-premier-league-odds-from-ea-player-bfdb52597392)
for more information on the methodology.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

You'll need:
  * [Python 3.6](https://www.python.org/downloads/release/python-360/)
  * [pip](https://pypi.org/project/pip/)

To install the dependencies,
```
pip install -r requirements.txt`
```

#### Crawlers

The crawlers are all written using Scrapy. For proper usage it would be
beneficial to first know how to use Scrapy.

For a *quick start*, just go to `./fifa_ratings_predictor/crawler` and
use

```
scrapy crawl <spider name> -o <output file>
```
It goes without saying that if you do use these crawlers, please don't
bombard the sites with a stupid amount of requests - *scrape responsibly.*

I have deliberately left all of the data off of the repo because a) it's
not really my data and b) it's not good practice to have data on a repo.

### Installing

To install everything except the crawler you can run

```
pip install .
```

from the top level directory.

You can then import the methods, for example the
simulator,

```
from fifa_ratings_predictor.simulation import SeasonSimulator
```


## Built With

* [Python 3.6](https://www.python.org/downloads/release/python-360/) - The programming language
* [Scrapy](https://github.com/scrapy/scrapy) - Scraping framework
* [TensorFlow](https://github.com/tensorflow/tensorflow) - Neural network framework

## Issues

Get in contact on [Twitter](https://twitter.com/BradleyGrantham) if you have any issues.

## Authors

[**Bradley Grantham**](https://twitter.com/BradleyGrantham)

## License

This project is licensed under the MPL-2.0 License - see the [LICENSE](LICENSE) file for details
