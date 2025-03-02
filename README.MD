This is a countdown program developed by [Flash_Man](https://flashman.top). It can countdown set seconds before set time, and then countdown set seconds before shutting down the computer, if set.

For direct use, download file in `dist` folder and run `a.exe`.

Settings can be configured in `settings.ini` file, the format is as follows:

```ini
[Settings]
audio_file_path = a.mp3 # the countdown audio file path
countdown_seconds = 5 # the countdown seconds before each alarm
shutdown_countdown_seconds = 20 # the countdown seconds before shutting down the computer
alarm_times = 8:40:00, 12:15:00, 17:40:00 # the set time for each alarm
shutdown_after_alarm = 1, 0, 1 # whether to shut down the computer after each alarm, 1 for yes, 0 for no
# remember comments are not allowed in settins.ini file, so delete them
```

Settings can also be configured through the right-click menu of the program.

# Bugs

1. ~~An error occurs when the program exits after a countdown trigger, which also prevents the program from restarting after saving settings.~~
2. When running the packaged EXE file, the program freezes for a long time after clicking the "Save Settings" button.

# Updates

## 2024/09/30

1. The GUI for settings has been added, but it's very simple.
2. The log file from the previous run will not be overwritten each time it is run.

## 2025/3/2

1. The GUI is now more user-friendly.
2. After saving settings, the program will not restart, but instead restart all the threads.
3. Add a function to decide whether to shut down the computer after each alarm.