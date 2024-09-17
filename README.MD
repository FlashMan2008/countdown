This is a countdown program developed by [Flash_Man](https://flashman.top). It can countdown set seconds before set time.

For direct use, download file in `dist` folder and run `a.exe`.

Settings can be configured in `settings.ini` file, the format is as follows:

```ini
[Settings]
audio_file_path = a.mp3 # the countdown audio file path
alarm_times = 8:40:00, 12:15:00, 17:40:00 # the set time for each alarm
countdown_seconds = 5 # the countdown seconds before each alarm
# remember comments are not allowed in settins.ini file, so delete them
```