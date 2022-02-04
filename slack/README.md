# Slack message analyzer and archiver

## how to use
1. Get export data from Slack

   You can download the export data in json format from administration page (e.g. https://YOURSLACK.slack.com/services/export )

2. unzip the downloaded data. The folder should contain json files covering user information, channel information. Each channel has their folder, where messages are saved per days.
The top directory will be rootDir to run the code.

   The exported data is as follows:

   ```
   rootDir
   |-- channel1
   |     |-- 2022.01.01.json
   |     |-- 2022.01.02.json
   |     ...
   |-- channel2
   |     |-- 2022.01.01.json
   |     |-- 2022.01.03.json
   |     ...
   ...
   ```


3. run the code. You'll get html files archiving the messages.

   For example, to make html files for all channels,
   ```
   analyzeSlack.py -o out rootDir
   ```

   If you'd like to make html file for dedicated one,  
   ```
   analyzeSlack.py -o out -c channel1 rootDir
   ```

   To get the usage:

   ```
   analyzeSlack.py -h
   usage: analyzeSlack.py [-h] [--outputDir OUTPUTDIR] [--channels CHANNELS [CHANNELS ...]] [--project PROJECT] rootDir
   
   positional arguments:
     rootDir               Directory containing directories with json
   
   optional arguments:
     -h, --help            show this help message and exit
     --outputDir OUTPUTDIR, -o OUTPUTDIR
                           Directory to write files; default <rootDir>
     --channels CHANNELS [CHANNELS ...], -c CHANNELS [CHANNELS ...]
                           Only process these channels
     --project PROJECT, -p PROJECT
                           Name of project; default PFS
   ```

