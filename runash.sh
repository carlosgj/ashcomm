#!/bin/bash

./ashcomm.py \
--serport=/dev/ttyS4 \
--baud=115200 \
--msg_rate=30 \
--site=N8UR \
--operator='John Ackermann' \
--marker=DECK \
--marker_number=21A34 \
--observer=jra \
--agency="Three Letter Acronym" \
--rx_num=143A221 \
--antenna_number="1" \
--antenna_type="TRM41249.00" \
--antenna_height=1.5 \
--antenna_east=0 \
--antenna_north=0 \
--verbose=False
