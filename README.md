# Installation

- Install `Docker` on your machine
- Checkout this repo and enter the main directory
- Edit the search queries at the bottom of `scrape.py`
- Run `docker build -t scraper .` to build the container
- Run `docker run -v $(pwd):/opt/scrape scraper` to run the container
- The results will be appended to the `watch.txt` file each time you run the container
