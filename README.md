
# create-ebay-deals

This script creates deals to submit to the ebay seller marketplace:
https://sellerportal.ebay.com/s

It needs an active listing download that can be downloaded here:
https://www.ebay.com/sh/reports/downloads

It makes deals based on listing statistics (ebay will not allow more than 200 deals):
```
1) 40 with the highest number of watchers
2) 40 with the highest quantity available to sell
3) 40 with the most recent list date
4) 40 with the highest sold quantity
5) it pulls as many as possible from listings containing the word "laptop"
6) then if it needs to it pulls the rest from the highest available quantity
```
# Requirements:
```
pip install pandas
```

# Usage
Before running, edit the file to contain the right path to the folder containing your active listing reports.

Just run this from the command line: ```python createDeals.py```

It will prompt for the name of the file.




