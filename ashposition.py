#!/usr/bin/env python3

#################################  ashcomm.py  #################################
#
#	Copyright 2019 by John Ackermann, N8UR jra@febo.com https://febo.com
#	Version number can be found in the ashglobal.py file
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	Software to communicate with Ashtech GPS receivers via serial port.
################################################################################

import sys
import time
import serial
import io
import struct
import math

class Position:
#    keylist = ['lat_float','lat_deg','lat_minute_float',
#        'lat_minute','lat_second_float','lon_float','lon_deg',
#        'lon_minute_float','lon_minute','lon_second_float','height']

	def __init__(self,x,y,z):
		# x,y,z are ECEF coordinates
		self.x = x
		self.y = y
		self.z = z
		return

	def xyz_float_list(self):
		return self.x,self.y,self.z

	def xyz_string_list(self,x_places=3,y_places=3,z_places=3):
		lat = '{1:.{0}f}'.format(x_places,self.x)
		lon = '{1:.{0}f}'.format(y_places,self.y)
		height = '{1:.{0}f}'.format(z_places,self.z)
		return lat,lon,height

	def ddxxx_float_list(self):
		(lat,lon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		lat
		return lat,lon,height

	def ddxxx_string_list(self,x_places=6,y_places=6,z_places=3,quad=True):
		(lat,lon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		lat = '{1:.{0}f}'.format(x_places,lat)
		lon = '{1:.{0}f}'.format(y_places,lon)
		height = '{1:.{0}f}'.format(z_places,height)

		if quad:
			if float(lat) > 0:
				lat = lat + 'N'
			else:
				lat = lat + 'S'
			if float(lon) > 0:
				lon = lon + 'E'
			else:
				lon = lon + 'W'
		return lat,lon,height

	def ddmmxxx_float_list(self):
		(lat,lon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		(latdeg,latmin) = self.decdeg_to_dm(lat)
		(londeg,lonmin) = self.decdeg_to_dm(lon)
		return int(latdeg),latmin,int(londeg),lonmin,height

	def ddmmxxx_string_list(self,x_places=4,y_places=4,z_places=3,quad=True):
		(rawlat,rawlon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		(latdeg,latmin) = self.decdeg_to_dm(rawlat)
		(londeg,lonmin) = self.decdeg_to_dm(rawlon)

		lat = str(int(latdeg)) + ":" + '{1:.{0}f}'.format(x_places,latmin)
		lon = str(int(londeg)) + ":" + '{1:.{0}f}'.format(y_places,lonmin)
		height = '{1:.{0}f}'.format(z_places,height)

		if quad:
			if float(rawlat) > 0:
				lat = lat + 'N'
			else:
				lat = lat + 'S'
			if float(rawlon) > 0:
				lon = lon + 'E'
			else:
				lon = lon + 'W'
		return lat,lon,height

	def ddmmxxx_string(self):
		(lat,lon,height) = self.ddmmxxx_string_list()
		return lat + " " +lon + " " + height + "M"

	def ddmmssxxx_float_list(self):
		(lat,lon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		(latdeg,latmin,latsec) = self.decdeg_to_dms(lat)
		(londeg,lonmin,lonsec) = self.decdeg_to_dms(lon)
		return int(latdeg),int(latmin),latsec, \
			int(londeg),int(lonmin),lonsec,height

	def ddmmssxxx_string_list(self,x_places=3,y_places=3,z_places=3,quad=True):
		(rawlat,rawlon,height) = self.ecef_to_wgs84(self.x,self.y,self.z)
		(latdeg,latmin,latsec) = self.decdeg_to_dms(rawlat)
		(londeg,lonmin,lonsec) = self.decdeg_to_dms(rawlon)

		lat = str(int(latdeg)) + ":" + str(int(latmin)) + \
			":" +'{1:.{0}f}'.format(x_places,latsec)
		lon = str(int(londeg)) + ":" + str(int(lonmin)) + \
			":" +'{1:.{0}f}'.format(y_places,lonsec)
		height = '{1:.{0}f}'.format(z_places,height)

		if quad:
			if float(rawlat) > 0:
				lat = lat + 'N'
			else:
				lat = lat + 'S'
			if float(rawlon) > 0:
				lon = lon + 'E'
			else:
				lon = lon + 'W'
		return lat,lon,height


###############################################################################
# This script provides coordinate transformations from Geodetic -> ECEF,
# ECEF -> ENU, and Geodetic -> ENU (the composition of the two previous 
# functions). Running the script by itself runs tests.
# based on https://gist.github.com/govert/1b373696c9a27ff4c72a.
# From https://gist.github.com/sbarratt/a72bede917b482826192bf34f9ff5d0b
###############################################################################

	def geodetic_to_ecef(self,lat, lon, h):
	    # (lat, lon) in WSG-84 degrees
   		# h in meters
		a = 6378137
		b = 6356752.3142
		f = (a - b) / a
		e_sq = f * (2-f)

		lamb = math.radians(lat)
		phi = math.radians(lon)
		s = math.sin(lamb)
		N = a / math.sqrt(1 - e_sq * s * s)

		sin_lambda = math.sin(lamb)
		cos_lambda = math.cos(lamb)
		sin_phi = math.sin(phi)
		cos_phi = math.cos(phi)

		x = (h + N) * cos_lambda * cos_phi
		y = (h + N) * cos_lambda * sin_phi
		z = (h + (1 - e_sq) * N) * sin_lambda

		return x, y, z

	def ecef_to_enu(self,x, y, z, lat0=0, lon0=0, h0=0):
		a = 6378137
		b = 6356752.3142
		f = (a - b) / a
		e_sq = f * (2-f)
	
		lamb = math.radians(lat0)
		phi = math.radians(lon0)
		s = math.sin(lamb)
		N = a / math.sqrt(1 - e_sq * s * s)

		sin_lambda = math.sin(lamb)
		cos_lambda = math.cos(lamb)
		sin_phi = math.sin(phi)
		cos_phi = math.cos(phi)

		x0 = (h0 + N) * cos_lambda * cos_phi
		y0 = (h0 + N) * cos_lambda * sin_phi
		z0 = (h0 + (1 - e_sq) * N) * sin_lambda

		xd = x - x0
		yd = y - y0
		zd = z - z0

		xEast = -sin_phi * xd + cos_phi * yd
		yNorth = -cos_phi * sin_lambda * xd - sin_lambda * sin_phi * yd + cos_lambda * zd
		zUp = cos_lambda * cos_phi * xd + cos_lambda * sin_phi * yd + sin_lambda * zd

		return xEast, yNorth, zUp

	def geodetic_to_enu(self,lat, lon, h, lat_ref, lon_ref, h_ref):
		x, y, z = geodetic_to_ecef(lat, lon, h)
		return ecef_to_enu(x, y, z, lat_ref, lon_ref, h_ref)


###############################################################################
# The above doesn't include an ECEF to normal lat/lon/height conversion,
# but this one does the job, converting x,y,z to every format you might want:
# DD.xxx, DD:MM.xxx, DD:MM:SS.xxx in WGS-84 datum
# Ported from C++ at # https://gist.github.com/govert/1b373696c9a27ff4c72a
###############################################################################
	def ecef_to_wgs84(self,x,y,z):

		PI = 3.141592653589793
		# WGS-84 geodetic constants
		a = 6378137.0				# WGS-84 Earth semimajor axis (m)
		b = 6356752.314245			# Derived Earth semiminor axis (m)
		f = (a - b) / a				# Ellipsoid Flatness
		f_inv = 1.0 / f				# Inverse flattening

		# f_inv = 298.257223563; // WGS-84 Flattening Factor of the Earth 
		# b = a - a / f_inv;
		# f = 1.0 / f_inv;

		a_sq = a * a
		b_sq = b * b
		e_sq = f * (2 - f)			# Square of Eccentricity

		eps = e_sq / (1.0 - e_sq)
		p = math.sqrt(x * x + y * y)
		q = math.atan2((z * a), (p * b))
		sin_q = math.sin(q)
		cos_q = math.cos(q)
		sin_q_3 = sin_q * sin_q * sin_q
		cos_q_3 = cos_q * cos_q * cos_q
		phi = math.atan2((z + eps * b * sin_q_3), (p - e_sq * a * cos_q_3))
		lmbda = math.atan2(y, x)
		v = a / math.sqrt(1.0 - e_sq * math.sin(phi) * math.sin(phi))

		lat_float = math.degrees(phi)
		lon_float = math.degrees(lmbda)
		height_float = (p / math.cos(phi)) - v
	
		return lat_float,lon_float,height_float

###############################################################################
# decdeg_to_dms -- convert decimal degrees to degree, minute, second
###############################################################################
	def decdeg_to_dms(self,dd):
		negative = dd < 0
		dd = abs(dd)
		minutes,seconds = divmod(dd*3600,60)
		degrees,minutes = divmod(minutes,60)
		if negative:
			if degrees > 0:
				degrees = -degrees
			elif minutes > 0:
				minutes = -minutes
			else:
				seconds = -seconds
		return (degrees,minutes,seconds)

###############################################################################
# decdeg_to_dm -- convert decimal degrees to degree and decimal minute
###############################################################################
	def decdeg_to_dm(self,dd):
		negative = dd < 0
		dd = abs(dd)
		minutes,seconds = divmod(dd*3600,60)
		degrees,minutes = divmod(minutes,60)
		minutes = minutes + (seconds / 60)
		if negative:
			if degrees > 0:
				degrees = -degrees
			elif minutes > 0:
				minutes = -minutes
			else:
				seconds = -seconds
		return (degrees,minutes)

# end of ashutils.py
