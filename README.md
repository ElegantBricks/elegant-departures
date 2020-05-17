# elegant-departures
A dynamic API based train departure board display system

This is a Python script designed for the Raspberry Pi.

It controls an OLED display board to show either live train departure data from National Rail Enquiries or simulated train data.

Usage:

Python3 elegant-departures.py -d ssd1322 -i spi --width 256 --height 64

This assumes a display using the SSD1322 chipset, an SPI interface, and a display with 256x64 resolution.
