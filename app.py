import readline, cmd, sys, time, datetime, pprint, term

from protocol import RpcClient, ApiError

from datetime import datetime

try:
  from printer import ReceiptPrinter
except:
  msgWarning("No printer support available!")

class Shell(cmd.Cmd):
	def do_register(self, arg):
		arg = arg.split(" ")
		if ((len(arg) == 1) and (len(arg[0])>0)):
			try:
				result = client.addPerson(arg[0])
				msgConfirm("Registered!")
			except ApiError as e:
				msgError(e)
		else:
			msgWarning("Usage: register <nickname>")
	
	def do_deposit(self, arg):
		arg = arg.split(" ")
		try:
			if len(arg) != 2:
				raise Exception("Argument count")
			amount = int(float(convertCommas(arg[0]))*100)
			name = arg[1]
		except:
			msgWarning("Usage: deposit <amount in €> <nickname>")
			return
			
		person = findPerson(client, name, False, False)
		
		if not person:
			msgError("Error: could not find your account, have you spelled your nickname correctly?")
			return
		
		global lastPerson
		
		try:
			transaction = client.invoiceExecute(
				person['id'],
				[],
				[{"description":"Deposit", "price":-amount, "amount":1}]
			)
			
			shell.do_clear("")
			
			printTransaction(transaction, True, True, person)
			
			msgConfirm("Deposit completed!")
			
			global cart
			if len(cart) > 0:
				print("Warning: there are still products in the cart. Either enter your name to buy the products or enter \"abort\" to cancel the pending transaction.")
			
		except ApiError as e:
			msgError(e)
			
	
	def do_amount(self, arg):
		arg = arg.split(" ")
		
		global cart, lastProduct
		
		if not lastProduct:
			msgError("Add a product to the cart first!")
			return
		
		if len(arg) == 1 and arg[0] == "":
			if lastProduct["package"] != None:
				amount = prompt(client, "Amount of "+lastProduct["name"]+" [unit: "+lastProduct["package"]["name"]+"] >")
			else:
				amount = prompt(client, "Amount of "+lastProduct["name"]+" >")
		elif not len(arg) == 1:
			print("Usage: amount <amount>")
			return
		else:
			amount = arg[0]
		
		try:
			amount = int(amount)
		except:
			msgError("Not a number!")
			return
		
		for cartRow in cart:
			if (cart[cartRow]["product"]["id"] == lastProduct["id"]):
				if (amount == 0):
					cart.pop(cartRow)
					shell.do_clear("")
					msgWarning("Removed "+lastProduct["name"]+" from the cart")
				else:
					cart[cartRow]["amount"] = amount
					shell.do_clear("")
					unit = ""
					if lastProduct["package"] != None:
						unit = " "+lastProduct["package"]["name"]
					print("(Changed amount of "+lastProduct["name"]+" to "+str(amount)+unit+")")
				return
		
		if (amount != 0):
			productsToCart(client, [lastProduct])
			msgConfirm("Added "+lastProduct["name"]+" to the cart")
			for cartRow in cart:
				if (cart[cartRow]["product"]["id"] == lastProduct["id"]):
					cart[cartRow]["amount"] = amount
					shell.do_clear("")
					return

	def do_remove(self, arg):
		if not arg == "":
			print("Usage: remove")
			return
		self.do_amount("0")
		
	def do_clear(self, arg):
		if not arg == "":
			print("Usage: clear")
			return
		term.clear()
		self.emptyline()
		
	def do_abort(self, arg):
		global cart
		cart = {}
		self.emptyline()
		shell.do_clear("")
		msgError("Transaction canceled!")
		
	def do_cyber(self, arg):
		print("")
		print("\u001b[103m\u001b[30m               \u001b[49m\u001b[39m")
		print("\u001b[103m\u001b[30m     CYBER     \u001b[49m\u001b[39m")
		print("\u001b[103m\u001b[30m               \u001b[49m\u001b[39m")
		
	def do_print(self, arg):
		if not arg == "":
			print("Usage: print")
			return
		printReceipt()
	
	def do_help(self, arg):
		print("")
		print("\u001b[103m\u001b[30m  ~~~  Welcome to the Tkkrlab barsystem  ~~~  \u001b[49m\u001b[39m")
		print("")
		print(" - register   Create an account")
		print(" - deposit    Add money to your account")
		print(" - amount     Set the amount for the product last added to the cart")
		print(" - remove     Remove the product last added to the cart")
		print(" - clear      Clear screen")
		print(" - abort      Abort transaction")
		print(" - print      Print receipt")
		print(" - cyber      Everyone needs a bit of cyber")
		print(" - help       You've found this one! :D")
		print("")
	
	def default(self, line):
		if line == "EOF":
			sys.exit()

		try:
			waitForConnection()

			if (len(line)>0):
				if not findPerson(client, line):
					if not product(client, line):
						print("\u001b[31mError: unknown command, user or product.\u001b[39m")
						showHeader = False
					else:
						showHeader = False
				else:
					showHeader = False
		except ApiError as e:
			print("\u001b[31mServer error:",e,"\u001b[39m")
		
		setPrompt()
	
	def completedefault(self, *args):
		self.completenames(*args)
	
	def completenames(self, text, line, begidx, endidx):
		#print("Complete",text,line,begidx,endidx)
		query = readline.get_line_buffer().lstrip().lower()
		results = []
		#print("Complete",text, query)
		for product in clProducts:
			if product.startswith(text):
				results.append(product)
		for persons in clPersons:
			if persons.startswith(text):
				results.append(persons)
		#print(results)
		if len(results)>0:
			return results
		return []
	
	def emptyline(self):
		waitForConnection()
		#term.clear()
		print("")
		if (len(cart) == 0):
			term.clear()
			headerConfirm("")
			headerConfirm("  The cart is empty. Scan a product to add it to the cart!")
			headerConfirm("")
			print("")
		else:
			term.clear()
			headerWarning("")
			headerWarning("  The cart contains products. Enter your name to confirm the transaction!")
			headerWarning("")
			print("")
		usage()

def waitForConnection():
	while not client.ping():
		print("Server unavailable. Reconnecting in 2 seconds...")
		time.sleep(2)

def convertCommas(i):
	return i.replace(',','.')

def halt(message, error=None):
	headerError("Fatal error")
	print(message)
	if error:
		headerError("")
		print(error)
	time.sleep(5)
	sys.exit(1)

def msgError(message):
	term.color(40,91,5)
	print(message)
	term.color(0)
	term.color()

def msgWarning(message):
	term.color(40,93,5)
	print(message)
	term.color(0)
	term.color()

def msgConfirm(message):
	term.color(40,92,5)
	print(message)
	term.color(0)
	term.color()

def headerError(message="TkkrLab barsystem"):
	term.header(message, 41, 97, 1, False)
	term.color(0)
	term.color()

def headerWarning(message="TkkrLab barsystem"):
	term.header(message, 30, 103, 1, False)
	term.color(0)
	term.color()

def headerConfirm(message="TkkrLab barsystem"):
	term.header(message, 42, 97, 1, False)
	term.color(0)
	term.color()
	
def headerInfo(message="TkkrLab barsystem"):
	term.header(message, 44, 97, 1, False)
	term.color(0)
	term.color()

def usage():
	global cart
	if len(cart) > 0:
		print("")
		#headerInfo("HELP")
		print("Enter your name to buy the products in the cart.")
		print("Scan or enter the name of a product to add it to the cart.")
		print("Enter 'abort' to clear the cart.")
		print("Enter 'help' for a list of commands.")
		print("")
	else:
		print("")
		#headerInfo("HELP")
		print("Enter your name to display information about your account.")
		print("Scan or enter the name of a product to add it to the cart.")
		print("Enter 'help' for a list of commands.")
		print("")
	
	printCart()

def setPrompt():
	if len(cart) < 1:
		shell.prompt = "\nCommand, user (query info) or product (add to cart)? > "
	else:
		shell.prompt = "\nCommand, user (buy products) or product (add to cart)? > "

def main():
	global client, shell
	
	term.clear()
	msgWarning("Loading configuration...")
	
	# Load the configuration from files (to-do: replace with proper configuration file)
	
	try:
		hostFile = open('spacecore-cli.uri', 'r')
		uri = hostFile.read().strip()
		hostFile.close()
	except:
		halt("Configuration error", "Could read uri file.")

	try:
		pwFile = open('spacecore-cli.pw', 'r')
		password = pwFile.read().strip()
		pwFile.close()
	except:
		halt("Configuration error", "Could read password file.")

	msgWarning("Connecting to server ({})...".format(uri))

	client = RpcClient(uri)
	
	waitForConnection()
	
	if not client.createSession():
		halt("Communication error", "Could not start the session!")

	if not client.login("barsystem", password):
		halt("Communication error", "Could not authenticate!")
	
	msgWarning("Connecting to printer...")
	
	global printer
	try:
		printer = ReceiptPrinter("/dev/ttyUSB0")
	except:
		printer = None
		msgWarning("Printer not available!")
	
	msgWarning("Welcome!")
	
	initCompletion()	
	shell = Shell()
	setPrompt()
	shell.do_clear("")
	shell.cmdloop()

pp = pprint.PrettyPrinter(indent=4)

cart = {}
lastCmd = ''
lastPerson = None
lastProduct = None
cmd_params = []
development = False
lastTransaction = []
lastTransactionTotal = []

def initCompletion():
	global clProducts, clPersons
	clProducts = []
	clPersons = []
	print("Please wait, querying list of products...")
	products = client.productList({})
	for product in products:
		clProducts.append(product["name"].lower())
	print("Please wait, querying list of persons...")
	persons = client.personList({})
	for person in persons:
		clPersons.append(person["nick_name"].lower())

def product(client, name):
	global cart, lastProduct
	results = client.productFindByIdentifier(name) + client.productFindByName(name)
	if len(results) > 0:
		if len(results) > 1:
			#sys.stdout.write("\r\n\u001b[31mError: multiple results for query!\u001b[39m\r\n\r\n")
			#return True

			sys.stdout.write("\r\n\u001b[33m=== MULTIPLE RESULTS ===\u001b[39m\r\n\r\n")
			for i in range(0,len(results)):
				product = results[i]
				#mbr_pr = str(round(float(product['member_price']),2))
				#std_pr = str(round(float(product['standard_price']),2))
				print(str(i+1)+". "+'{0: <25}'.format(product['name']))#+'{0: <6}'.format("€ "+mbr_pr)+" / "+'{0: <6}'.format("€ "+std_pr))
			try:
				choice = int(prompt(client, "\r\nPick one (or abort):"))-1
				if (choice >= 0) and (choice < len(results)):
					result = results[choice]
				else:
					print("\u001b[31mCanceled\u001b[39m")
					return True
			except:
				print("\u001b[31mCanceled\u001b[39m")
				return True

		else:
			result = results[0]

		lastProduct = result
		
		productsToCart(client, [result])

		shell.do_clear("")

		if result['package'] != None:
			if result['package']['ask']:
				shell.do_amount("")

		return True

	return False

def executeTransaction(client, person):
	global cart
		
	product_rows = []
	
	for cartRow in cart:
		data = {"id": cart[cartRow]["product"]["id"], "amount": cart[cartRow]["amount"]}
		product_rows.append(data)
	
	transaction = client.invoiceExecute(
		person["id"],
		product_rows,
		[]
	)

	cart = {}

	shell.do_clear("")

	msgConfirm("Transaction completed!")

	printTransaction(transaction)


def printTransaction(transaction, neg=False, noAmount=False, person=None):
	global lastPerson, lastTransaction, lastTransactionTotal
	
	lastTransaction = []
	
	if neg:
		neg = -1
	else:
		neg = 1
		
	if not person:
		person = lastPerson
	
	headerConfirm("TRANSACTION RECEIPT")
	print("")
	for row in transaction["rows"]:
		if noAmount:
			print('{0: <32}'.format(row["description"])+'{0: <6}'.format("€ "+str(neg*round(row["price"]*row["amount"]/100.0,2))))
		else:
			print(str(row["amount"])+"x "+'{0: <29}'.format(row["description"])+'{0: <6}'.format("€ "+str(neg*round(row["price"]*row["amount"]/100.0,2))))
		lastTransaction.append((row["description"], row["amount"], neg*round(row["price"]*row["amount"]/100.0,2)))

	if not neg:
		print("\r\nTransaction total:\t\t€ "+'{0: <6}'.format("{:.2f}".format(transaction['invoice']['total']/100.0)))
	else:
		print("")
	print("Balance before transaction:\t€ "+'{0: <6}'.format("{:.2f}".format(person['balance']/100.0)))
	print("Balance after transaction:\t€ "+'{0: <6}'.format("{:.2f}".format(transaction['person']['balance']/100.0)))
	lastTransactionTotal = [
		("Total",transaction['invoice']['total']/100.0),
		("Balance before transaction",person['balance']/100.0),
		("Balance after transaction",transaction['person']['balance']/100.0)
		]
	
	global printer
	if printer != None:
		print("\n")
		print("Use 'print' to print this receipt.")
	print("")

	
def findPerson(client, name, doTransaction=True, showInfo=True):
	global cart, lastPerson
	person = client.personFind(name)
	if (person != None):
		if (len(cart)<1) and showInfo:
			print("")
			name = person['nick_name']
			if (person['first_name'] != ""):
				name = person['first_name']
			if (person['last_name'] != ""):
				name += " "+person['last_name']
			print("Hello "+name+"! Your balance is "+'{0: <6}'.format("€ "+"{:.2f}".format(person['balance']/100.0)))
			print("")
			printLastTransactionsOfPerson(person['id'], 5)

		if (len(cart)>0) and doTransaction:
			lastPerson = person
			executeTransaction(client, person)
		return person
	return None

def printLastTransactionsOfPerson(person, amount):
	global client
	lastTransactions = client.lastInvoicesOfPerson(person, amount)
	for transaction in lastTransactions:
		when = datetime.fromtimestamp(transaction['timestamp']).strftime('%Y-%m-%d %H:%M:%S')+" (€ {0: <8})".format("{:.2f}".format(transaction['total']/100.0))
		for row in transaction['rows']:
			product = '{0: >4}'.format(str(row['amount']))+"x "+'{0: <25}'.format(row['description'])
			print('{0: <32}'.format(when)+product)
			when = ""
	

def productsToCart(client, products):
	global cart
	for i in products:
		product_id = i["id"]
		if not product_id in cart:
			cart[product_id] = {"product": i, "amount": 1}
		else:
			item = cart[product_id]
			item["amount"]+=1
			cart[product_id] = item

def printCart():
	global cart, client
	if len(cart) > 0:
		print("")
		headerInfo("CART")
		for i in cart:
			product = cart[i]["product"]
			amount = cart[i]["amount"]
			unit = ""
			if product['package'] != None:
				unit = product['package']['name']
			line = '{0: >4}'.format(str(amount))+" "+'{0: <16}'.format(unit)+'{0: <25}'.format(product['name'])
			line += "\t"
			groups = client.getGroups()
			for i in range(len(groups)):
				group = groups[i]
				last = i < (len(groups) - 1)
				if last:
					last = " / "
				else:
					last = ""
				price = False
				for entry in product['prices']:
					if entry['person_group_id'] == group['id']:
						price = entry['amount']
				if price:
					price = "€ "+'{0: <6}'.format("{:.2f}".format(price*amount/100.0))
					line += '{0: <6}'.format(price)
			print(line)
		print("")

# Shell helper functions

def queryLocation(client):
	locations = client.getLocations()
	for i in range(len(locations)):
		sub = ""
		if locations[i]["sub"]:
			sub = "(Position "+str(locations[i]["sub"])+")"
		print(str(i)+". "+locations[i]['name']+" "+sub)
	
	location = prompt(client, "Where? > ",False,False)
	try:
		location = int(location)
		location = locations[location]["id"]
		return location
	except:
		print("Invalid input.")
		return -1

def queryGroup(client):
	groups = client.getGroups()
	for group in groups:
		print(str(group["id"])+". "+group["name"])
	group_id = prompt(client, "Group? > ",False,False)
	try:
		group_id = int(group_id)
		for group in groups:
			if (group_id == group["id"]):
				return group_id
	except:
		print("Invalid input.")
	return None
		
def setprice(client):
	global lastProduct, cmd_params, cart
	if lastProduct:
		print("Set price of of "+lastProduct['name']+".")
		group = queryGroup(client)
		if (group == None):
			print("Invalid input.")
			return
		price = queryPrice(client, "Price")
		if (price == None):
			print("Invalid input.")
			return
		print("Setting price of "+str(lastProduct["id"])+" to "+str(price)+" for group "+str(group))
		client.productSetPrice(lastProduct["id"], group, price)
		cart = {}
	else:
		print("No product.")
		
def listgroups(client):
	groups = client.getGroups()
	for group in groups:
		print(str(group["id"])+". "+group["name"])
		
def lasttransactions():
	global client
	lastTransactions = client.lastTransactions(5)
	for transaction in lastTransactions:
		print("------")
		pp.pprint(transaction)
	print("------")
	

def queryPrice(client, text="Amount"):
	amount = prompt(client, text+" > €",False,False)
	if len(amount) < 1:
		return
	try:
		amount = int(float(amount)*100)
	except:
		print("Not a number.")
		return None
	return amount
	
def clear():
	sys.stdout.write("\033c")

def prompt(client, prompt=">",header=False, headerCart=False, history=False):
	if (header):
		#clear()
		sys.stdout.write("\r\n\u001b[33mTkkrlab\u001b[39m barsystem\r\n")

	if (headerCart):
		if len(cart) > 0:
			printCart()
		print("")

	sys.stdout.write("\u001b[36m"+prompt+"\u001b[39m ")
	sys.stdout.flush()
	buffer = ""
	last = ""
	buffer = sys.stdin.readline()
	i = buffer.replace("\r","").replace("\n","")
	print("")
	sys.stdout.flush()
	return i

def printReceipt():
	global printer, lastPerson, lastTransaction, lastTransactionTotal
	
	if printer == None:
		msgError("No printer available.")
		return
	
	if len(lastTransaction) < 1:
		msgError("No transaction available.")
		return
		
	customer_name = lastPerson['nick_name']
	if (len(lastPerson['first_name'])+len(lastPerson['last_name'])) > 0:
		customer_name = lastPerson['first_name']+" "+lastPerson['last_name']
	
	printer.init()
	printer.set_code_table('cp858')
	printer.print_image('tkkrlab.bmp')
	printer.feed(1)
	printer.set_align(printer.ALIGN_CENTER)
	printer.set_print_mode(printer.PRINTMODE_FONT_A)
	printer.writeline('*** TkkrLab Barsystem ***')
	printer.feed(1)
	printer.set_align(printer.ALIGN_LEFT)
	printer.writeline('Customer {}'.format(customer_name))
	printer.writeline('Date     {}'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
	printer.feed(2)

	printer.set_align(printer.ALIGN_LEFT)
	printer.set_print_mode(printer.PRINTMODE_FONT_B)

	# products
	for name, amount, cost in lastTransaction:
		printer.write_product_line(name, cost, amount)

	printer.set_print_mode(printer.PRINTMODE_FONT_A)
	printer.writeline('-' * 42)
	printer.set_print_mode(printer.PRINTMODE_FONT_B | printer.PRINTMODE_EMPHASIZED | printer.PRINTMODE_DOUBLE_HEIGHT)
	first = True
	for name, cost in lastTransactionTotal:
		printer.write_product_line(name, cost)
		if first:
			first = False
			printer.set_print_mode(printer.PRINTMODE_FONT_B | printer.PRINTMODE_EMPHASIZED)
			printer.feed(1)
	printer.set_print_mode(printer.PRINTMODE_FONT_A)

	printer.feed(6)
	printer.cut(0)
	
	msgConfirm("Receipt sent to the printer!")

if __name__ == '__main__':
	main()
