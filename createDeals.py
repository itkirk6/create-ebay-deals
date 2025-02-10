import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math

def choose_file(prompt):
    root = tk.Tk()
    root.withdraw() #hide the root window

    file_path = filedialog.askopenfilename(
        title=prompt,
        filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")]
    )

    if not file_path:
        raise ValueError("No file selected")
    
    return file_path


DBC_FOLDER = os.path.join(os.getcwd(), "listing reports")
fileName = choose_file("Choose Active Listing Report: ")

while 1:
    switchAdjustmentAmount = input("Enter amount to adjust switch prices up from listing price (recommended 5): ")
    try:
        switchAdjustmentAmount = int(switchAdjustmentAmount)
        break
    except:
        if switchAdjustmentAmount == "":
            switchAdjustmentAmount = 0
            break    
    print("Please enter a valid intetger adjustment amount or hit enter to default to 0")
    #please don't judge me for this masterpiece

df = pd.read_csv(fileName)
print(f"Read in csv with {len(df)} entries")

#build a table with just unique items
df["Item number"] = pd.to_numeric(df["Item number"])
df_unique_items = df.drop_duplicates(subset=['Item number'])
print(f"Dropped {len(df)-len(df_unique_items)} duplicate listings")
#df_unique_items.to_csv("df_unique_items"+".csv", index=False)

#build a table with just duplicate items
duplicate_rows = df[df.duplicated(subset=['Item number'], keep=False)]
#duplicate_rows.to_csv("duplicate_rows"+".csv", index=False)

# Function to get the price of an item
def get_item_price(item):
    if math.isnan(item['Current price']):
        return item['Start price']
    else:
        return item['Current price']

# Check for duplicates in Item header with different start prices
duplicates_to_remove = []
for item_number, group in duplicate_rows.groupby('Item number'):
    groupPrices = []

    #get prices for each item
    for index, row in group.iterrows():
        groupPrices.append(get_item_price(row))

    #check if they are all the same
    are_all_same = all(element == groupPrices[0] for element in groupPrices)
    if not are_all_same:
        print(f"Had to remove listing ID {row["Item number"]} because prices were different: {groupPrices}")
        duplicates_to_remove.append(row["Item number"])

print(f"Removed: {duplicates_to_remove}\n{len(duplicates_to_remove)} items")
df_filtered = df_unique_items[~df_unique_items['Item number'].isin(duplicates_to_remove)]
#df_filtered.to_csv("df_filtered_1"+".csv", index=False)

# Filter out rows where "available Quantity" is not equal to 0
print(f"Removed with 0 quantity: {df_filtered[df_filtered['Available quantity'] == 0].shape[0]}")
df_filtered = df_filtered[df_filtered['Available quantity'] != 0]
#df_filtered.to_csv("df_filtered_noquantity"+".csv", index=False)

#this is now our sheet to pull from.
"""
1) pull the 40 most recent listings
2) pull the 40 listings with the most quantity
3) pull the 40 listings with most watchers
4) pull the 40 listings with this most sold quantity
5) pull the rest from listings that have "laptop" in the title (most quantity first)
6) if any left over, pull from listings with highest available quantity
(max 200 listings)
"""

date_format = "%b-%d-%y %H:%M:%S"
df_filtered["Start date"] = pd.to_datetime(df_filtered["Start date"].str[:-4], format=date_format)
df_filtered["Available quantity"] = pd.to_numeric(df_filtered["Available quantity"])
df_filtered["Watchers"] = pd.to_numeric(df_filtered["Watchers"])
df_filtered["Sold quantity"] = pd.to_numeric(df_filtered["Sold quantity"])

pullSheet = [
    ("Start date", 40),
    ("Available quantity", 40),
    ("Watchers", 40),
    ("Sold quantity", 40)
]
df_new = pd.DataFrame()

for header, num in pullSheet:
    print(num, header)
    top_rows = df_filtered.nlargest(num, header)
    df_new = df_new._append(top_rows)
    df_filtered.drop(top_rows.index, inplace=True)
    df_filtered.reset_index(drop=True, inplace=True)


#5) pull the rest with the title "laptop"
df_laptop = df_filtered[df_filtered['Title'].str.contains('laptop', case=False)]
top_rows = df_laptop.nlargest(40, "Available quantity")
print(f"attempt at 40 laptop highest quantity: pulled {top_rows.shape[0]}")
df_new = df_new._append(df_laptop)
df_filtered = df_filtered.drop(top_rows.index)


#check to see if we're at 200:
num_rows, num_columns = df_new.shape
if num_rows > 200:
    print("ERROR: Over 200 rows")
elif num_rows < 200:
    print("Adding in the rest with highest quantity")
    top_rows = df_filtered.nlargest(200 - num_rows, "Available quantity")
    df_new = df_new._append(top_rows)
    df_filtered = df_filtered.drop(top_rows.index)


#now we have our df, just need to get it in the right format
df_final = pd.DataFrame()

# 1) rename header
df_final["ebay Item Id"] = df_new["Item number"].copy()

# 2) set deal price
def deal_price(row):
    price = get_item_price(row)
    # Find the next multiple of 5 greater than the given number
    new_price = math.ceil((price + 0.1) / 5.0) * 5.0 - 0.01

    #add in the switch adjustment
    if "switch" in str(row['Title']).lower():
        new_price += switchAdjustmentAmount
        new_price = float(str(new_price).split(".")[0] + ".99")
        #this is to get rid of floating-point errors, i know it's janky

    return str(new_price)

df_final["Deal Price"] = df_new.apply(lambda row: deal_price(row), axis=1)

# 3) set list price
def list_price(row):
    description = row["Title"].lower()
    price = get_item_price(row)
    msrp = 0

    if "switch" in description:
        if "oled" in description:
            msrp = 349.99
        elif "v2" in description:
            msrp = 299.99
        elif "lite" in description:
            msrp = 199.99
    
    if msrp <= price:
        msrp = math.ceil(price * 1.2 / 5.0) * 5 - 0.01

    return str(msrp)

df_final["List Price"] = df_new.apply(lambda row: list_price(row), axis=1)

#4) set quantity
def set_quantity(row):
    quantity = row["Available quantity"]
    if quantity < 20:
        return str(math.ceil(quantity / 5) * 5)
    else:
        return str(math.ceil(quantity / 10) * 10)
        
df_final["Quantity"] = df_new.apply(lambda row: set_quantity(row), axis=1)

# 5) set Maximum Purchases
df_final["Maximum Purchases"] = 100

# 6) set the other junk columns
for col in ["Sellers Deal Price MSKU Lower", "Sellers Deal Price MSKU Upper", "List Price MSKU Lower", "List Price MSKU Upper"]:
    df_final[col] = None

df_final["Quantity"] = pd.to_numeric(df_final["Quantity"])
df_final = df_final.sort_values(by="Quantity", ascending=False)

#save the dataframe
df_final.to_csv(fileName.split("/")[-1].split(".")[0]+"_submission.csv", index=False)
print(fileName)

input("Press enter to close")

