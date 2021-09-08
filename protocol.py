import requests, time

try:
	import ujson as json
	print("(Using ujson)")
except:
	print("(Please install ujson! Falling back on the slow built in json library)")
	time.sleep(2)
	import json

class ApiError(Exception):
	def __init__(self, error):
		if 'message' in error:
			message = error['message']
		else:
			message = error
		if 'code' in error:
			code = error['code']
		else:
			code = -1
		super().__init__(message)

class RpcClient:
	def __init__(self, uri="http://127.0.0.1:8000"):
		self._uri = uri
		self._session = None
		self.user = None
		
		self._username = ""
		self._password = ""

	def _request(self, method, params=None, retry=True):
		id = round(time.time())
		data = {"jsonrpc":"2.0", "id": id, "method": method, "params": params}
		if self._session != None:
			data["token"] = self._session
		request = requests.post(self._uri, json=data)
		data = json.loads(request.text)
		if (not 'id' in data) or (data['id']!=id):
			print("DEBUG",data)
			raise ApiError("API returned incorrect id!")
		if (data['jsonrpc']!="2.0"):
			raise ApiError("Invalid response")
		if 'error' in data:
			#print("ERROR", data['error'])
			if retry and data['error']['code'] == -32001: #Access denied
				print("\u001b[33mSession interrupted. Connecting...\u001b[39m")
				self.createSession()
				self.login(self._username, self._password)
				return self._request(method, params, False)
			raise ApiError(data['error'])
		if 'result' in data:
			return data['result']
		return None

	# PING MODULE

	def ping(self):
		try:
			if self._request("ping", None) == "pong":
				return True
		except:
			pass
		return False

	# SESSIONS MODULE

	def createSession(self):
		try:
			self._session = self._request("session/create")
			return True
		except ApiError as e:
			print("Could not create session:",e)
			return False

	def login(self, username, password):
		self._username = username
		self._password = password
		try:
			self.user = self._request("user/authenticate", {"user_name": username, "password": password})
			return True
		except ApiError as e:
			print(e)
			return False
		
	def getGroups(self, query={}):
		return self._request("person/group/list", query)

	# PERSONS MODULE

	def addPerson(self, name):
		return self._request("person/create", name)

	def personList(self, search):
		return self._request("person/listForVendingNoAvatar", search)

	def personFind(self, search):
		return self._request("person/findForVending", search)

	# PRODUCTS MODULE

	def productList(self, query):
		return self._request("product/list/noimg", query)

	def productFindByName(self, name):
		return self._request("product/find", name)
	
	def productFindByIdentifier(self, identifier):
		return self._request("product/findByIdentifier", identifier)
		
	def productSetPrice(self, product, group, price):
		return self._request("product/price/set", {"product_id":product, "group_id":group, "amount":price})
		
	def addStock(self, product, location, amount):
		return self._request("product/addStock", {"product_id": product, "location_id": location, "amount": amount})
	
	def removeStock(self, stock_id, amount):
		return self._request("product/removeStock", {"id": stock_id, "amount": amount})
	
	def getLocations(self, query=None):
		return self._request("product/location/list", query)
	
	# INVOICE MODULE
	
	def invoices(self, person=None, after=None, before=None):
		query = {}
		if person != None:
			query['person_id'] = person
		if after != None and before != None:
			query['timestamp'] = {">=": after, "<=": before}
		elif after != None:
			query['timestamp'] = {">=": after}
		elif before != None:
			query['timestamp'] = {"<=": before}
		return self._request("invoice/list", query)
	
	def lastInvoice(self, amount):
		return self._request("invoice/list/last", amount)

	def lastInvoicesOfPerson(self, person, amount):
		return self._request("invoice/list/last", {"query": {'person_id': person}, "amount": amount})
	
	def invoiceExecuteProducts(self, person, products=[]):
		transaction = {"person_id": person, "products": products}
		print(transaction)
		return self._request("invoice/create", transaction)
	
	def invoiceExecuteCustom(self, person, other=[]):
		# Expects other to have the following format:
		# {"description:"...", "price":123, "amount":123}
		# where price is the unit price and amount is the amount of units
		transaction = {"person_id": person, "other": other}
		return self._request("invoice/create", transaction)
	
	def invoiceExecute(self, person, products=[], other=[]):
		transaction = {"person_id": person, "products": products, "other": other}
		return self._request("invoice/create", transaction)
