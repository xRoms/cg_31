from __future__ import print_function
import sys
import numpy as np
from enum import Enum
from sortedcontainers import SortedList
import heapq
from numpy.linalg import det
from utils import bound
from cg import Point, turn
from cg.utils import gcd

from utils import eps, handlers

pixels = {}

pixelspassed = {}

def average(ceps, point):
	zeps = int(gethomo(ceps))
	m = gcd(point.z, zeps)
	new_eps = int(zeps * ceps * (point.z // m))
	new_point = Point(int(point.x * (zeps // m)), int(point.y * (zeps // m)), int(point.z * (zeps // m)), homogeneous=True)
	return (new_eps, new_point)

def point_inside(pixel, segment):
	tmp = []
	cnt = 0
	for q in segment.intersections(pixel):
		if (q is not None):
			tmp.append(q)
			cnt += 1
	if cnt == 0:
		return None
	if cnt >= 2:
		temp = tmp[0] + tmp[1]	
		return Point(int(temp.x), int(temp.y), int(temp.z * 2), homogeneous=True)
	return tmp[0]

def add_pixel_to_seg(pixel, segment):
	if (segment in pixelspassed):
		pixelspassed[segment].append((point_inside(pixel, segment), pixel.center))
	else:
		pixelspassed[segment] = [(point_inside(pixel, segment), pixel.center)]

def get_pixel(a):
	na = rounded(a)
	if (na not in pixels):
		pixels[na] = Pixel(na)
	return pixels[na]

def smart_gcd(a, b):
	if a == 0:
		return b
	if b == 0:
		return a
	return gcd(a, b)

def normalize(smth):
	m = smart_gcd(smth.x, smart_gcd(smth.y, smth.z))
	q = 1
	if (smth.z <= 0):
		q = 1
	return Point(int(q * (smth.x // m)), int(q * (smth.y // m)), int(q * (smth.z // m)), homogeneous=True)

#def eprint(*args, **kwargs):
#    print(*args, file=sys.stderr, **kwargs)

def vol(point, *hyperplane):
	return det(np.array([pt.coord for pt in hyperplane] + [point.coord]))

def gethomo(a):
	if (isinstance(a, int)):
		return 1
	c = 1
	while (((c * a)%1 != 0)):
		c *= 10
	return c

def mkpoint(a, b):
	c = max(gethomo(a), gethomo(b))
	return Point(np.array([int(a * c), int(b * c), int(c)]), homogeneous=True)

class Segment:
	"""
	Класс отрезка
	"""

	def __init__(self, a, b):
		"""
		Конструктор отрезка

		:param a, b: концы отрезка, экземпляры Point
		"""
		self.start = normalize(min(a, b))
		self.end = normalize(max(a, b))

	def __eq__(self, other):
		"""
		проверяет два отрезка на равенство

		:param other: экземпляр Segment
		:return: bool
		"""
		return self.start == other.start and self.end == other.end		

	def __hash__(self):
		return hash((self.start.x, self.start.y, self.start.z, self.end.x, self.end.y, self.end.z))

	def atX(self, x):
		sx = self.start.x / self.start.z
		ex = self.end.x / self.end.z - sx
		dx = x - sx
		sy = self.start.y / self.start.z
		ey = self.end.y / self.end.z - sy
		if (dx > ex):
			return sy
		return dx/ex * ey + sy

	def intersects(self, other):
		"""
		пересечение отрезка с другим отрезком или с границами пикселя

		:param other: экземпляр Segment
		:return: Point точка пересечения или None, если пересечения нет
		"""
		a, b = normalize(self.start), normalize(self.end)
		c, d = normalize(other.start), normalize(other.end)
		acd, bcd = turn(a, c, d), turn(b, c, d)
		cab, dab = turn(c, a, b), turn(d, a, b)

		do_intersect = False
		if acd == bcd == cab == dab == 0:
			do_intersect = (a <= c <= b or a <= d <= b or c <= a <= d or c <= b <= d)
		else:
			do_intersect = acd != bcd and cab != dab
		
		if do_intersect:
			cross = lambda a, b: np.cross([a.coord], [b.coord])
			prod = np.cross(cross(a, b), cross(c, d))[0]
			if (prod[0] == 0 and prod[1] == 0 and prod[2] == 0):
				return max(b,d)
			return normalize(Point(prod, homogeneous = True))
		return None

	def intersections(self, pixel):
		return  [self.intersects(pixel.right()), self.intersects(pixel.bottom()), self.intersects(pixel.top()), self.intersects(pixel.left())]

	def __str__(self):
		return '({}, {})'.format(self.start, self.end)

def rounded(point):
	"""
	округляет точку до центра ближайшего пикселя

	:param x: экземпляр Point
	:return: Point, являющийся центром пикселя, которому принадлежит x
	"""

	res = average(eps, point)
	new_eps = res[0]
	new_point = res[1]
	return normalize(Point(int(halfround(new_point.x, new_eps)), int(halfround(new_point.y, new_eps)), int(new_point.z), homogeneous= True))


def halfround(a, new_eps):
	if (a % new_eps <= new_eps / 2): 
		return a - a % new_eps
	else:
		return a + new_eps - a % new_eps 


class Pixel:
	"""
	Класс пикселя
	"""

	def __init__(self, point):
		"""
		Конструктор пикселя

		:param point: экземпляр Point, точка внутри пикселя
		"""
		self.center = rounded(point)

	def __eq__(self, other):
		"""
		проверяет два пикселя на равенство

		:param other: экземпляр Pixel
		:return: bool
		"""
		return self.center == other.center

	def __lt__(self, other):
		return self.center < other.center

	

	def top(self):
		"""
		возвращает отрезок, соответствующий верхней грани пикселя

		:return: Segment
		"""
		return Segment(self.nw, self.ne)
	
	def bottom(self):
		"""
		возвращает отрезок, соответствующий нижней грани пикселя

		:return: Segment
		"""
		return Segment(self.sw, self.se)

	def left(self):
		"""
		возвращает отрезок, соответствующий левой грани пикселя

		:return: Segment
		"""
		return Segment(self.nw, self.sw)

	def right(self):
		"""
		возвращает отрезок, соответствующий правой грани пикселя

		:return: Segment
		"""
		return Segment(self.ne, self.se)

	def is_on_top(self, point):
		"""
		проверяет, лежит ли точка на верхней грани пикселя

		:param point: экземпляр Point
		:return: bool
		"""
		new_self, new_point = self.center.same_level(point)
		yself = new_self[1]
		ypoint = new_point[1]
		cureps = eps / 2 * new_self[2]

		return ypoint == yself + cureps

	def is_on_bottom(self, point):
		"""
		проверяет, лежит ли точка на нижней грани пикселя

		:param point: экземпляр Point
		:return: bool
		"""
		new_self, new_point = self.center.same_level(point)
		yself = new_self[1]
		ypoint = new_point[1]
		cureps = eps / 2 * new_self[2]

		return ypoint == yself - cureps


	def is_on_left(self, point):
		"""
		проверяет, лежит ли точка на левой грани пикселя

		:param point: экземпляр Point
		:return: bool
		"""
		new_self, new_point = self.center.same_level(point)
		xself = new_self[0]
		xpoint = new_point[0]
		cureps = eps / 2 * new_self[2]

		return xpoint == xself - cureps

	def is_on_right(self, point):
		"""
		проверяет, лежит ли точка на правой грани пикселя

		:param point: экземпляр Point
		:return: bool
		"""
		new_self, new_point = self.center.same_level(point)
		xself = new_self[0]
		xpoint = new_point[0]
		cureps = eps / 2 * new_self[2]

		return xpoint == xself + cureps

	def get_top_neighbour(self, point):
		res = average(eps, self.center)
		new_eps = res[0]
		new_self = res[1]
		return get_pixel(Point(int(new_self.x), int(new_self.y + new_eps), int(new_self.z), homogeneous = True))

	def get_bottom_neighbour(self, point):
		res = average(eps, self.center)
		new_eps = res[0]
		new_self = res[1]
		return get_pixel(Point(int(new_self.x), int(new_self.y - new_eps), int(new_self.z), homogeneous = True))

	def get_left_neighbour(self, point):
		res = average(eps, self.center)
		new_eps = res[0]
		new_self = res[1]
		return get_pixel(Point(int(new_self.x - new_eps), int(new_self.y), int(new_self.z), homogeneous = True))

	def get_right_neighbour(self, point):
		res = average(eps, self.center)
		new_eps = res[0]
		new_self = res[1]
		return get_pixel(Point(int(new_self.x + new_eps), int(new_self.y), int(new_self.z), homogeneous = True))

	def get_neighbour(self, point):
		"""
		возвращает пиксель, смежный по той грани, которой принадлежит точка

		:param point: экземпляр Point
		:return: Pixel смежный пиксель
		"""	
		res = average(eps, self.center)
		new_eps = res[0]
		new_self = res[1]

		if self.is_on_top(point):
			return get_pixel(Point(int(new_self.x), int(new_self.y + new_eps), int(new_self.z), homogeneous = True))
		if self.is_on_bottom(point):
			return get_pixel(Point(int(new_self.x), int(new_self.y - new_eps), int(new_self.z), homogeneous = True))
		else:
			return None

	@property
	def x(self):
		return self.center.x

	@property
	def y(self):
		return self.center.y

	@property
	def z(self):
		return self.center.z

	@property
	def nw(self):
		res = average(eps / 2, self.center)
		new_eps = res[0]
		new_self = res[1]
		return Point(int(new_self.x - new_eps), int(new_self.y + new_eps), int(new_self.z), homogeneous = True)

	@property
	def ne(self):
		res = average(eps / 2, self.center)
		new_eps = res[0]
		new_self = res[1]
		return Point(int(new_self.x + new_eps), int(new_self.y + new_eps), int(new_self.z), homogeneous = True)

	@property
	def sw(self):
		res = average(eps / 2, self.center)
		new_eps = res[0]
		new_self = res[1]
		return Point(int(new_self.x - new_eps), int(new_self.y - new_eps), int(new_self.z), homogeneous = True)

	@property
	def se(self):
		res = average(eps / 2, self.center)
		new_eps = res[0]
		new_self = res[1]
		return Point(int(new_self.x + new_eps), int(new_self.y - new_eps), int(new_self.z), homogeneous = True)


class SweepLine:
	"""
	Класс заметающей прямой
	"""
	class Event:
		"""
		Класс события, обрабатываемого заметающей прямой
		"""
		class Type(Enum):
			"""
			Тип события
			"""
			SEG_END      = 0 # конец отрезка
			SEG_START    = 6 # начало отрезка
			SEG_SEG      = 2 # пересечение двух отрезков
			SEG_PIX      = 3 # пересечение отрезка с границей пикселя
			PIX_END      = 4 # конец пикселя
			SEG_REINSERT = 5 # повторное вхождение отрезка после выхода из пикселя


		def __init__(self, etype, point, segment=None, pixel=None):
			"""
			Конструктор события

			:param etype: SweepLine.Event.Type тип события
			:param point: Point точка, в которой происходит событие
			:param segment: Segment для событий типа SEG_START, SEG_END, SEG_PIX, SEG_REINSERT \
			                -- отрезок, участвующий в них
			:param pixel: Pixel для событий типа SEG_PIX, PIX_END -- пиксель, участвующий в них
			"""
			self.etype = etype
			self.point = normalize(point)
			self.segment = segment
			self.pixel = pixel

		def __eq__(self, other):
			"""
			проверяет два события на равенство

			:param other: экземпляр SweepLine.Event 
			:return: bool
			"""
			return self.point == other.point and self.etype == other.etype \
			and self.segment == other.segment and self.pixel == other.pixel

		def __lt__(self, other):
			"""
			лексикографическое "меньше" для событий

			:param other: экземпляр SweepLine.Event
			:return: bool
			"""
			new_self, new_other = self.point.same_level(other.point)
			if self.point.x/self.point.z == other.point.x / other.point.z:
				if self.etype.value == other.etype.value:
					return self.point.y/self.point.z < other.point.y / other.point.z
				else:
					return self.etype.value < other.etype.value	
			return self.point.x/self.point.z < other.point.x / other.point.z

		def __str__(self):
			s = 'type: {}\npoint: {}'.format(self.etype.name, self.point)
			if self.segment is not None:
				s += '\nsegment: {}'.format(self.segment)
			if self.pixel is not None:
				s += '\npixel: {}'.format(self.pixel)
			return s

		def handle(self):
			"""
			вызывает функцию-обработчик для события данного типа
			"""
			handler = handlers[self.etype]
			if self.segment is not None and self.pixel is not None:
				handler(self.point, segment=self.segment, pixel=self.pixel)
			elif self.segment is not None:
				handler(self.point, segment=self.segment)
			elif self.pixel is not None:
				handler(self.point, pixel=self.pixel)
			else:
				handler(self.point)

		@property
		def x(self):
			return self.point.x

		@property
		def y(self):
			return self.point.y
		@property
		def z(self):
			return self.point.z


	def __init__(self, segments):
		"""
		Конструктор заметающей прямой

		:param segments: список отрезков Segment, для работы с которыми строится заметающая прямая
		"""
		self.xpos = 0
		self.status = [] # SortedList(key=lambda seg: seg.atX(self.xpos))
		self.events = []

		# инициализируем список событий началами и концами отрезков
		for s in segments:
			self.push(SweepLine.Event(SweepLine.Event.Type.SEG_START, s.start, segment=s))
			self.push(SweepLine.Event(SweepLine.Event.Type.SEG_END, s.end, segment=s))

	def insert(self, segment):
		"""
		добавляет отрезок в статус, а также вычисляет новые пересечения и добавляет их в очередь events

		:param segment: экземпляр Segment
		:param point: экземпляр Point
		"""
		self.status.append(segment)
		self.status.sort(key=lambda seg: seg.atX(self.xpos))
		"""print("hey")
		for q in self.status:
			print(q)
		print("__events__")
		for q in self.events:
			print("! ", q.etype, " ", q.point)
		print("__________")"""
		i = self.status.index(segment)
		j = i
		while (j > 0):
			if (self.status[i].atX(self.xpos) == self.status[j - 1].atX(self.xpos)):
				j -= 1
				continue
			p = segment.intersects(self.status[j - 1])
			if p is not None and (p.x / p.z >= self.xpos):
				self.push(SweepLine.Event(SweepLine.Event.Type.SEG_SEG, p))
				j -= 1
			else:
				break
		j = i
		while (j < len(self.status) - 1):
			if (self.status[i].atX(self.xpos) == self.status[j + 1].atX(self.xpos)):
				j += 1
				continue
			p = segment.intersects(self.status[j + 1])
			if p is not None and (p.x / p.z >= self.xpos):
				self.push(SweepLine.Event(SweepLine.Event.Type.SEG_SEG, p))
				j += 1
			else:
				break

	def remove(self, segment):
		"""
		удаляет отрезок из статуса

		:param segment: экземпляр Segment
		"""
		if segment in self.status:
			self.status.remove(Segment(segment.start, segment.end))

	def push(self, event):
		"""
		добавляет событие в очередь events

		:param event: экземпляр SweepLine.Event
		"""
		heapq.heappush(self.events, event)

	def peek(self):
		"""
		возвращает самое раннее событие из events, не удаляя его из очереди

		:return: SweepLine.Event
		"""
		return self.events[0]

	def pop(self):
		"""
		возвращает самое раннее событие из events, удаляя его из очереди

		:return: SweepLine.Event
		"""
		return heapq.heappop(self.events)
