import requests
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import re
import traceback
import sys
import json

class Parser:
  """
  A class used to parse the html content

  Attributes:
    cvr(str): the CVR number 

  Methods:
    get_hmtl(cvr): Returns the html content of the page of the specified CVR\n
    get_active(): Returns active content of the page\n
    get_inactive(): Returns inactive content of the page\n
    get_all_posts(): Returns concatenated active and inactive content\n
    get_capital_increase(parsed_text): Returns data related to capital increase\n
    get_capital_decrease(parsed_text, currency): Returns data related to capital decrease\n
    get_creation(parsed_text, currency): Returns data related to company creation\n
    append_data(amount, change_date, investment_type, price, date, change_type, currency): Appends relevant data to a list of dictionaries\n
    get_currency(parsed_text): Returns the type of currency\n
    get_history(): Returns a list of dictionaries with company data\n
  """
  def __init__(self,cvr):
    self.cvr=cvr
    self.htlm_text=self.get_html()
    self.page_soup = BeautifulSoup(self.htlm_text, "html.parser")
    self.capital_changes_obj=[]

  def get_html(self):
      """
      Returns the html content of the page of the specified CVR.

      Parameters:
        cvr(str): The CVR number of a company

      Returns:
        html_text(str): The html content of the page  
      """
      chrome_options = webdriver.ChromeOptions()
      chrome_options.add_argument('--headless')
      chrome_options.add_argument('--no-sandbox')
      chrome_options.add_argument('--disable-dev-shm-usage')
      wd = webdriver.Chrome('chromedriver', options=chrome_options)

      url='https://datacvr.virk.dk/data/visenhed?enhedstype=virksomhed&id={0}&soeg={0}&language=da'.format(self.cvr)
      wd.get(url)
      time.sleep(2) # wait for the page to load
      html_text=wd.page_source
      wd.close()
      return html_text

  def get_active(self):
    """
    Returns html contect of active class

    Parameters:

    Returns:
      elements(str): The active html content of the page  
    """
    active =self.page_soup.find("div", {"class": "aktive-registreringstidende"})
    if active:
      elements = active.find_all("div", {"class": "row dataraekker"})
      return elements
    elif "Du er nu i kø til Virk Data" in self.page_soup.text:
      return []
    
  def get_inactive(self):
    """
    Returns html contect of inactive class

    Parameters:

    Returns:
      elements(str): The inactive html content of the page  
    """
    try:
      inactive = self.page_soup.find("div", {"id": "resterende-registreringstidende"})
      if inactive:
        elements=inactive.find_all('div',{"class": "row dataraekker"})
      # result=list(map(lambda x : x.text,elements))
        return elements
      elif "Du er nu i kø til Virk Data" in self.page_soup.text:
        return []
    except AttributeError as e:
      return []
    except Exception as e:
      raise e
    
  def get_all_posts(self):
    """
    Returns concatenated page content

    Parameters:

    Returns:
      all(str): The active and inactive html content of the page  
    """
    active=self.get_active()
    inactive=self.get_inactive()
    if inactive is not None:
      all=active+inactive
    else:
      all=active
    return all

  def get_capital_increase(self, parsed_text):
    """
    Returns data related to capital increase.

    Parameters:
      parsed_text(str): The string for extracting capital increase data.

    Returns:
      amount(str): Amount of money invested\n
      investment_type(str): Type of investment\n
      price(str): Price\n
    """
    
    amount = parsed_text.strip().split(' ')[0][:-1]

    x = parsed_text.split('kurs')
    investment_type = re.sub(r"[0123456789\.\,]",'', x[0]).strip()
    price = re.sub(r"[^0123456789\.\,]",'', x[1])[:-1]

    return amount, investment_type, price

  def get_capital_decrease(self, parsed_text, currency):
    """
    Returns data related to capital decrease.

    Parameters:
      parsed_text(str): The string for extracting capital decrease data

    Returns:
      change_date(str): Date of the change\n
      amount(str): Amount of money invested\n 
      investment_type(str): Type of investment\n
      price(str): Price.
    """
    change_date, amount, investment_type, price = "", "", "", ""
    x = parsed_text.split('\n')[0].split(currency)
    if len(x) > 1:
      y = re.sub(r"[^0123456789\.\,]",':', x[1][:-1].strip()).split(':')
      z = x[0]
      dates = re.findall(r'\d{2}.\d{2}.\d{4}', z)
      if dates:
        change_date = dates[0]
        split_date = dates[-1]
        investment_type = z.split(split_date)[-1].strip()
    
      amount = y[0]
      price = y[-1]

    return change_date, amount, investment_type, price


  def get_creation(self, parsed_text, currency):
    """
    Returns data related to company creation

    Parameters:
      parsed_text(str): The string for extracting company data

    Returns:
      amount(str): Amount of money invested\n 
      investment_type(str): Type of investment\n
      price(str): Price\n
    """
    x = parsed_text.split('\n')[0].split(currency)
    investment_type = x[0][2:].strip()

    z = re.sub(r"[^0123456789\.\,]",':', x[1][:-1].strip()).split(':')
    str_list = list(filter(None, z))
    amount = str_list[0]
    price = str_list[-1][:-1]
    return amount, investment_type, price

  def append_data(self, amount, change_date, investment_type, price, date, change_type, currency):
    """
    Appends relevant data to a list of dictionaries

    Parameters:
      amount(str): The capital amount\n
      change_date(str): The date of status change\n
      investment_type(str): Investment text\n
      price(str): The price of investment\n
      date(str): The date of the post\n
      change_type(str): They type of event (either capital increase, decrease or company creation)\n
      currency(str): The currency type\n

    Returns:
      capital_changes_obj(str): List of dictionaries with company data.
    """
    amount_data = {"amount":amount,
                    "date":change_date,
                    "investment_type":investment_type,
                    "price":price}

    self.capital_changes_obj.append({"date":date,
                                "change_type":change_type,
                                "status_changed_date":change_date,
                                "amount_data":amount_data,
                                "cvr": self.cvr,
                                "currency": currency})

  def get_currency(self,  parsed_text):
    """
    Returns the type of currency

    Parameters:
      parsed_text(str): The string for extracting the currency.

    Returns:
      currency(str): Type of currency (only considering euro and kr. at the moment)
    """
    currency = None
    if "euro" in parsed_text:
      currency = "euro"
    elif "kr." in parsed_text:
      currency = "kr."
    return currency

  

  def get_history(self):
    """
    Returns the list of dictionaries with company information

    Parameters:

    Returns:
      capital_changes_obj(list): A list of dictionaries with the company data
    """
    i = self.get_all_posts() # read data with Beautiful Soup
    # only include posts related to capital or new company
    filtered_list = [items for items in i if ("kapital" in items.find('b').text.lower()) or ("nye selskaber" in items.find('b').text.lower())]
    for items in filtered_list:
        if int(items.find('b').text[6:10]) > 2015: # only consider posts with date is after 2015
            try:
                date = items.find('b').text[:10]

                if ('Kapitalforhøjelse' in items.text) and ('Kapitalnedsættelse' not in items.text): # for posts with capital increase only
                    currency = self.get_currency(items.text.split('Kapitalforhøjelse')[1]) # check currency
                    change_date = items.text.split('Vedtægter ændret:')[1][:11].strip() 
                    parsed_text = items.text.split('Kapitalforhøjelse')[1].replace('\n','').replace(':', '').split(currency)
                    for index in range(1, len(parsed_text)-1): # iterate in case there are more than one events
                        amount, investment_type, price = self.get_capital_increase(parsed_text[index])
                        self.append_data(amount, change_date, investment_type, price, date, 'Kapitalforhøjelse', currency)
                    
                elif ('Kapitalforhøjelse' in items.text) and ('Kapitalnedsættelse' in items.text): # for posts with both capital increase and decrease
                    currency = self.get_currency(items.text.split('Kapitalforhøjelse')[1]) # check currency
                    # Only extract capital increase here
                    parsed_text = items.text.split('Kapitalforhøjelse')[1].replace('\n','').replace(':', '').split(currency)[1].split('Kapitalnedsættelse')
                    change_date = items.text.split('Vedtægter ændret:')[1][:11].strip()

                    amount, investment_type, price = self.get_capital_increase(parsed_text[0])

                    self.append_data(amount, change_date, investment_type, price, date, 'Kapitalforhøjelse', currency)

                if 'Kapitalnedsættelse' in items.text: # For posts with capital decrease
                    decrease_split = items.text.split('Kapitalnedsættelse')
                    for index in range(1, len(decrease_split)): # iterate in case there are more than one events
                      parsed_text = decrease_split[index]
                      currency = self.get_currency(parsed_text)

                      change_date, amount, investment_type, price = self.get_capital_decrease(parsed_text, currency)
                      if change_date:
                        self.append_data(amount, change_date, investment_type, price, date, 'Kapitalnedsættelse', currency)

                if "Indbetalingsmåde" in items.text: # For posts with new company
                    parsed_text = items.text.split('Indbetalingsmåde')[1]
                    change_date = items.text.split('Stiftelsesdato')[1].split('\n')[0][2:-1]
                    currency = self.get_currency(parsed_text)

                    amount, investment_type, price = self.get_creation(parsed_text, currency)
                    self.append_data(amount, change_date, investment_type, price, date, 'Indbetalingsmåde', currency)

            except Exception:
                print(traceback.format_exc())
    return self.capital_changes_obj



def main(args):
  """
  main is an example of the usage of the Parser class
  """
  # Check input arguments
  if len(args) != 2:
      sys.stderr.write("usage: %s <text file>\n" % args[0])
      sys.exit(1)

  companies = read_file(args[1])
  capital_changes=[]

  for company in companies:
      print("Processing CVR: ", company)
      parser = Parser(company) # get company data from virk
      
      capital_changes.extend(parser.get_history()) 
      
  print(capital_changes)

  f = open("tests/demo_data.txt", "w")
  f.write(str(capital_changes))
  f.close()

def read_file(filename):
    """
    Reads from file and returns a list of CVR numbers

    Parameters:
      filename(str): The file containing the CVR numbers

    Returns:
      companies(list): List of CVR numbers
    """
    companies = []
    with open(filename, 'r') as reader:
      line = reader.readline()
      while line != '':  
        companies.append(line.strip())
        line = reader.readline()
    return companies
if __name__ == '__main__':
    sys.exit(main(sys.argv))

