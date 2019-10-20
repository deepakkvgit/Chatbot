from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_core.actions.action import Action
from rasa_core.events import SlotSet
import zomatopy
import json

zomato_config={ "user_key":"6ce88a5ec1419e335afa1c7f92f4b739"}
result_of_last_query = ""

class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_restaurant'

	def filterRestaurantBasedOnBudget(self, userbudget, allRestaurants):
		rangeMin = 0
		rangeMax = 100000

		if userbudget.isdigit():
			price = int(userbudget)

			if price == 1:
				rangeMax = 299
			elif price == 2:
				rangeMin = 300
				rangeMax = 699
			elif price == 3:
				rangeMin = 700
			elif price < 300:
				rangeMax = 299
			elif price < 700 and price >= 300:
				rangeMin = 300
				rangeMax = 699
			else:
				rangeMin = 700
		else:
			# default budget 
			rangeMin = 300
			rangeMax = 699

		index = 0
		count = 0
		response = ""
		global result_of_last_query
		result_of_last_query = ""

		for restaurant in allRestaurants:
			++count
			res =  restaurant['restaurant']['name'] + " in " + restaurant['restaurant']['location']['address'] + " has been rated [" + restaurant['restaurant']['user_rating']['aggregate_rating'] + "/5] "

			avg_c_2 = restaurant['restaurant']['average_cost_for_two']

			if avg_c_2 <= rangeMax and avg_c_2 >= rangeMin:
				
				res = restaurant['restaurant']['currency'] + str(restaurant['restaurant']['average_cost_for_two']) + " " + res + "\n"
				if(index < 5):
					response = response + res

				if(index < 10):
					result_of_last_query = result_of_last_query + res
				index = index + 1

		# modifying the search results
		# if the no. of result fall short, appending the results of other price range
		[SlotSet('search_result','found')]
		if index == 0:
			[SlotSet('search_result','zero')]
			response = "Oops! no restaurant found for this query. " + " search results = " + str(count)
		elif index < 5:
			# we can add restaurants from the higher range but for now i am appending an extra message 
			response = response + "\n \nFor more results please search in higher budget range...\n \n"
		elif index < 10:
			result_of_last_query = result_of_last_query + "\n \nFor more results please search in higher budget range...\n \n"

		return response

	def run(self, dispatcher, tracker, domain):
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		budget = tracker.get_slot('budget')
		
		zomato = zomatopy.initialize_app(zomato_config)
		location_detail=zomato.get_location(loc, 1)

		d1 = json.loads(location_detail)
		lat=d1["location_suggestions"][0]["latitude"]
		lon=d1["location_suggestions"][0]["longitude"]
		
		cuisines_dict={
		'american':1,
		'mexican':73,
		'italian':55,
		'chinese':25,
		'north indian':50,
		'south indian':85
		}

		results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)), 50)

		d = json.loads(results)
		response=""

		if (d.get('results_found', 0) == 0):
			response= "Sorry, we didn't find any results for this query."
			[SlotSet('search_result','zero')]
		else:
			response = self.filterRestaurantBasedOnBudget(budget, d['restaurants'])
			[SlotSet('search_result','found')]

		dispatcher.utter_message(str(response))
		return [SlotSet('location',loc)]


t1_t2_cities = ["Bangalore","Chennai","Delhi","Hyderabad","Kolkata","Mumbai","Ahmedabad","Pune","Agra","Ajmer","Aligarh","Amravati","Amritsar",
"Asansol","Aurangabad","Bareilly","Belgaum","Bhavnagar","Bhiwandi","Bhopal","Bhubaneswar","Bikaner","Bilaspur","BokaroSteelCity","Chandigarh",
"CoimbatoreNagpur","Cuttack","Dehradun","Dhanbad","Bhilai","Durgapur","Erode","Faridabad","Firozabad","Ghaziabad","Gorakhpur","Gulbarga","Guntur",
"Gwalior","Gurgaon","Guwahati","Hubli–Dharwad","Indore","Jabalpur","Jaipur","Jalandhar","Jammu","Jamnagar","Jamshedpur","Jhansi","Jodhpur","Kakinada",
"Kannur","Kanpur","Kochi","Kottayam","Kolhapur","Kollam","Kota","Kozhikode","Kurnool","Ludhiana","Lucknow","Madurai","Malappuram","Mathura","Goa","Mangalore",
"Meerut","Moradabad","Mysore","Nanded","Nashik","Nellore","Noida","Palakkad","Patna","Pondicherry","PuruliaAllahabad","Raipur","Rajkot","Rajahmundry","Ranchi",
"Rourkela","Salem","Sangli","Siliguri","Solapur","Srinagar","Thiruvananthapuram","Thrissur","Tiruchirappalli","Tirupati","Tirunelveli","Tiruppur","Tiruvannamalai",
"Ujjain","Bijapur","Vadodara","Varanasi","Vasai-VirarCity","Vijayawada","Vellore","Warangal","Surat","Visakhapatnam"]

t1_t2_cities_list = [x.lower() for x in t1_t2_cities]

# Check if the location exists. using zomato api.if found then save it, else utter not found.
class ActionValidateLocation(Action):
	def name(self):
		return 'action_check_location'

	def run(self, dispatcher, tracker, domain):
		loc = tracker.get_slot('location')
		city = str(loc)

		if city.lower() in t1_t2_cities_list:
			return [SlotSet('location_match',"one")]
		else:
			zomato = zomatopy.initialize_app(zomato_config)

			try:
				results = zomato.get_city_ID(city)
				return [SlotSet('location_match',"tier3")]
			except:
				return [SlotSet('location_match',"zero")]


# Send email the list of 10 restaurants
class ActionSendEmail(Action):
	def name(self):
		return 'action_send_email'

	def run(self, dispatcher, tracker, domain):

		email = tracker.get_slot('email')
		
		# for slack handling
		if len(email.split("|")) == 2:
			email = email.split("|")[1]

		import smtplib 
		s = smtplib.SMTP('smtp.gmail.com', 587) 
		s.starttls() 
		s.login("deepakupgrad@gmail.com", "Upgrad2019#")
		message = "Details of all the restaurants you inquried \n \n"
		global result_of_last_query
		message = message + result_of_last_query

		from email.message import EmailMessage
		msg = EmailMessage()
		msg['Subject'] = "FoodieBot - Restaurant search results"
		msg['From'] = "FoodieBot"
		msg['To'] =  str(email)
		msg.set_content(message)
		
		try:
			s.send_message(msg)
			s.quit()
		except:
			print("error in sending email")
			dispatcher.utter_message(email)

		result_of_last_query = ""
		return [AllSlotsReset()]


from rasa_core.events import AllSlotsReset
from rasa_core.events import Restarted

class ActionRestarted(Action): 	
	def name(self):
		return 'action_do_restart'
	def run(self, dispatcher, tracker, domain):
		return[Restarted()] 

class ActionSlotReset(Action): 
	def name(self): 
		return 'action_slot_reset' 
	def run(self, dispatcher, tracker, domain): 
		return[AllSlotsReset()]
