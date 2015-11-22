#!/usr/bin/python
import time
import astral

a = Astral()
d = time.strftime("%x")

location = a['Los Angeles']
print('Information for %s' % location.name)

timezone = location.timezone
print('Timezone: %s' % timezone)

print('Latitude: %.02f; Longitude: %.02f' % (location.latitude,location.longitude))

sun = location.sun(local=True, date=d) # won't run because the date format needs to be xxxx,xx,xx not xx/xx/xxxx

print('Dawn:    %s' % str(sun['dawn'])) # won't run bc of ^^^
