#!/usr/bin/python
"""Let's have us some base64 for simple integer keys."""

from math import log, floor

# Completely bikeshedded base64 character set, aimed at maximal
# typability.
charset = '.abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-'

def encode64(number):
    if number == 0:
        return charset[0]
    text = ''
    width = int(floor(log(number, 64)))
    for power in xrange(width, -1, -1):
        place_value = number / 64**power
        text += charset[place_value]
        number -= place_value * 64**power
    return text

def decode64(text):
    number = 0
    for power in xrange(len(text) - 1, -1, -1):
        place_value = charset.index(text[len(text) - power - 1])
        number += place_value * 64**power
    return number

if __name__ == '__main__':
    for i in xrange(0,5000):
        encd = encode64(i)
        decd = decode64(encd)
        print 'VAL:', i, encd, decd
