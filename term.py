import sys, datetime, time, os

try:
    import msvcrt
    getch = msvcrt.getch
except:
    import sys, tty, termios
    def _unix_getch():
        """Get a single character from stdin, Unix version"""

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())          # Raw read
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

getch = _unix_getch

def goto(x,y):
	print(u"\u001b["+str(y)+";"+str(x)+"H",end="")

def home():
	goto(1,1)

def clear():
	print(u"\u001b[2J",end="")
	home()
	
def color(*args):
	if len(args)==0:
		args = (37,40,1)
	#print("COLOR", args)
	code = "\u001b["
	for i in range(len(args)):
		code += str(args[i])
		if i < len(args)-1:
			code += ";"
	code += "m"
	print(code, end="")
	
def getSize():
	r,c = os.popen('stty size', 'r').read().split()
	return (int(r),int(c))
	
def header(text = "", colorFg=37, colorBg=41, colorStyle=1, goHome=True):
	rows, columns = getSize()
	left = text
	empty = columns - len(left)
	if goHome:
		home()
	color(colorFg, colorBg, colorStyle)
	print(left,end="")
	if empty > 0:
		for i in range(empty):
			print(" ",end="")
	#print(right)
	color()
	
def draw_menu(title, items, selected=0):
	header(False, title)
	for i in range(0, len(items)):
		if (selected == i):
			color(30, 47, 0)
		else:
			color()
		print(items[i])
	color()
		
def menu(title, items, selected = 0):
	clear()
	while True:
		draw_menu(title, items, selected)
		key = getch()
		if (ord(key)==0x1b):
			key = getch()
			if (key=="["):
				key = getch()
				if (key=="A"):
					if (selected>0):
						selected -= 1
				if (key=="B"):
					if (selected<len(items)-1):
						selected += 1
		if (ord(key)==0xa):
			return selected

def cmdline(prompt, buff = ""):
	running = True
	while running:
		rows, columns = getSize()
		goto(0, rows-1)
		print(prompt+" ", end="")
		color(30, 47, 0)
		print(buff, end="")
		if len(buff) < 64:
			print(" "*(columns-len(buff)-len(prompt)-1),end="")
		color()
		last = getch()
		if last == '\n' or last == '\r':
			return buff
		if ord(last) >= 32 and ord(last) < 127:
			buff += last
		if ord(last) == 127:
			buff = buff[:-1]

def prompt(prompt, x, y, buff = ""):
	running = True
	while running:
		goto(x, y)
		print(prompt+": ", end="")
		color(30, 47, 0)
		print(buff, end="")
		if len(buff) < 64:
			print(" "*(64-len(buff)),end="")
		color()
		last = getch()
		if last == '\n' or last == '\r':
			return buff
		if ord(last) >= 32 and ord(last) < 127:
			buff += last
		if ord(last) == 127:
			buff = buff[:-1]

def empty_lines(count = 10):
	for i in range(0,count):
		print("")
