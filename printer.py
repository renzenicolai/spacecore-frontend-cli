import serial
from PIL import Image, ImageOps
import six

class ReceiptPrinter:
	ALIGN_LEFT = 0
	ALIGN_CENTER = 1
	ALIGN_RIGHT = 2

	PRINTMODE_FONT_A = 0x00
	PRINTMODE_FONT_B = 0x01
	PRINTMODE_EMPHASIZED = 0x08
	PRINTMODE_DOUBLE_HEIGHT = 0x10
	PRINTMODE_DOUBLE_WIDTH = 0x20
	PRINTMODE_UNDERLINE = 0x80

	CMD_ESC = b'\x1B'
	CMD_GS = b'\x1D'
	CMD_FS = b'\x1C'
	
	CODE_TABLES = {
		'cp437': b'\x00',
		'cp850': b'\x02',
		'cp858': b'\x13',
	}
	
	def _to_column_format(self, im, line_height):
		"""
		Extract slices of an image as equal-sized blobs of column-format data.
		:param im: Image to extract from
		:param line_height: Printed line height in dots
		"""
		width_pixels, height_pixels = im.size
		top = 0
		left = 0
		blobs = []
		while left < width_pixels:
			remaining_pixels = width_pixels - left
			box = (left, top, left + line_height, top + height_pixels)
			slice = im.transform((line_height, height_pixels), Image.EXTENT, box)
			bytes = slice.tobytes()
			blobs.append(bytes)
			left += line_height
		return blobs

	def _int_low_high(self, inp_number, out_bytes):
		""" Generate multiple bytes for a number: In lower and higher parts, or more parts as needed.
		
		:param inp_number: Input number
		:param out_bytes: The number of bytes to output (1 - 4).
		"""
		max_input = (256 << (out_bytes * 8) - 1);
		if not 1 <= out_bytes <= 4:
			raise ValueError("Can only output 1-4 byes")
		if not 0 <= inp_number <= max_input:
			raise ValueError("Number too large. Can only output up to {0} in {1} byes".format(max_input, out_bytes))
		outp = b'';
		for _ in range(0, out_bytes):
			outp += six.int2byte(inp_number % 256)
			inp_number = inp_number // 256
		return outp

	def __init__(self, kodak=False, device="/dev/ttyUSB0"):
		self.serial = serial.Serial(
			port=device,
			baudrate=19200,
			parity=serial.PARITY_NONE,
			bytesize=serial.EIGHTBITS)
		self.encoding = 'ascii'
		self.kodak = kodak
		self.init()

	def output(self, *data):
		# print(repr(data))
		for block in data:
			self.serial.write(block)

	def init(self):
		if self.kodak:
			self.output(0x11)
		self.output(self.CMD_ESC, b'@')

	def set_code_table(self, name):
		if name in self.CODE_TABLES:
			self.encoding = name
			self.output(self.CMD_ESC, b't', self.CODE_TABLES[name])

	def set_print_mode(self, modes):
		self.output(self.CMD_ESC, b'!', bytes([modes]))

	def set_align(self, align):
		self.output(self.CMD_ESC, b'a', bytes([align]))

	def print_image(self, filename):
		high_density_horizontal = True
		high_density_vertical = True
		im = Image.open(filename)
		im = im.convert("L")  # Invert: Only works on 'L' images
		im = ImageOps.invert(im) # Bits are sent with 0 = white, 1 = black in ESC/POS
		im = im.convert("1") # Pure black and white
		im = im.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
		line_height = 3 if high_density_vertical else 1
		blobs = self._to_column_format (im, line_height * 8);
		height_pixels, width_pixels = im.size
		density_byte = (1 if high_density_horizontal else 0) + (32 if high_density_vertical else 0);
		header = self.CMD_ESC + b"*" + six.int2byte(density_byte) + self._int_low_high( width_pixels, 2 );
		
		self.set_align(self.ALIGN_CENTER)
		self.output(self.CMD_ESC, b'3', six.int2byte(16))
		for blob in blobs:
			self.output(header, blob, b'\n')
		self.output(self.CMD_ESC, bytes([ord('2')]))
		
	def writeline(self, data=None):
		if data:
			self.output(data.encode(self.encoding))
		self.output(b'\n')
		
	def testEncoding(self):
		for i in range(128,255):
			self.output(bytes([i]))
		self.output(bytes([ord('\n')]))

	def write_product_line(self, text, price, amount=None):
		if self.kodak:
			number_text = ' EUR {:.2f}'.format(price)
		else:
			number_text = ' €{:.2f}'.format(price)
		if amount != None:
			text = '{:>4}'.format(amount)+'x '+text
		text_len = 54 - len(number_text)
		self.writeline('{text:<{text_len}}{number}'.format(text=text, number=number_text, text_len=text_len))

	def cut(self, cut_mode=0):
		if self.kodak:
			self.output(self.CMD_ESC, b'i')
		else:
			self.output(self.CMD_GS, b'V', bytes([cut_mode]))
		

	def open_drawer(self):
		# send pulse to pin 0, 0x3c * 2ms on, 0x78 * 2ms off
		self.output(self.CMD_ESC, b'p\x00\x3C\x78')

	def feed(self, line_count=0):
		self.output(self.CMD_ESC, b'd', bytes([line_count]))
