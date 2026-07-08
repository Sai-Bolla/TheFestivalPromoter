import streamlit as st

import requests           # the key API Python library
from pprint import pprint # Pretty Print
import time               # measuring the length of time between different items being run




print('hello')
# creating the webpage
st.title('The Festival promoter')


st.header('Welcome to our project')

'''
 country code: GB
    
    ID 	Market
    202 	London (UK)
    203 	South (UK)
    204 	Midlands and Central (UK)
    205 	Wales and North West (UK)
    206 	North and North East (UK)
    207 	Scotland
    208 	Ireland
    209 	Northern Ireland

    dmaId 	Market

    601 	All of United Kingdom
    602 	London
    603 	South
    604 	Midlands and Central
    605 	Wales and North West
    606 	North and North East
    607 	Scotland
    608 	All of Ireland
    609 	Northern Ireland

previous URLs:

https://app.ticketmaster.com/discovery/v2/events.json?classificationName=music&dmaId=324&apikey=BoAGsXs6gY0DExT82C1VQopCVBBDT7uj


'''


full_url = 'https://app.ticketmaster.com/discovery/v2/events.json?classificationName=music&dmaId=602&apikey=BoAGsXs6gY0DExT82C1VQopCVBBDT7uj'
# Send the GET request
response = requests.get(full_url)

print(f"Status Code: {response.status_code}") # 200 means OK, 404 means Not Found
print(f"URL Used: {response.url}")

data = response.json()
st.write(data)

print(data)
