# Top 10 Publications App
The project is written in Python and has been tested from a 3.7.3 version. It uses trending news API “executium” to scrape data with published articles and price changes among several currency pairs.

#### Purpose of this project
* Help traders and trading journalists in their discovering of correlations between publications.
* Try to give them insightful information about the price impact of the news.

#### Desired result
The program should present a scatter chart and a list with ten ranked publications and counted percentage of price impact. Also, the application should allow the user to set a date and currency pair. 

#### Installation guide
* Make sure you have Python, ver. 3.7.3 installed.
* Open a command-line interface then use the package manager pip to install pycurl, certifi, pandas, plotly and dash.
```
pip install pycurl certifi pandas plotly dash
```
* Then use git to clone executium repository to your working directory.
```
git clone https://github.com/executium/trending-historical-cryptocurrency-news.git executium
```
* Run the app with `python app.py` and visit http://127.0.0.1:8050/ in your web browser.

#### External link to already built application
https://top-tenpub-app.herokuapp.com/
