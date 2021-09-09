Project: HCC Home Control Centre

An IoT demonstration project to control and monitor electric devices via a flask full stack web app. 

Open 'samples' folder to view page and hardware samples.

Backend Language: Python (Flask)
Database tool: SQLite
Structure/ Style Tools: HTML5, CSS3
Frontend Language: JavaScript, jQuery, Jinja Template language
Arduino - MCU board
ESP8266 01 - WiFi module

RGB LED, 12V DC Fan, Bulb or basically any AC/DC device can be connected via relays.

Features and functions:

1. Register and Login user with hashed passwords.(Passwords are saved and        matched using hash functions from the werkzeug.security module.)

2. Or direct login with Google OAuth API.

3. Arduino controls the devices and communicates with ESP01 WiFi module via AT commands.

4. ESP01 module operates in access point (AP) mode and connects to any local network.

5. Web App sends ESP01 module HTTP requests to communicate device states in JSON.

6. Database also stores power consumptions of devices which are showed on devicesdata.html page.