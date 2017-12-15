import os
import sys
import time
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
import pandas as pd
from collections import Counter
from sqlalchemy import create_engine
from apscheduler.schedulers.blocking import BlockingScheduler
import shutil

cwd = os.getcwd()
des_dir = os.environ['COPY_TO_DIR']

src_file = os.path.join(cwd, "geckodriver.exe")
des_file = os.path.join(des_dir, "geckodriver.exe")

shutil.copyfile(src_file, des_file)  


sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():

    print('This job is run every 1 minutes.')


    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("working directory path:",dir_path,".")


    # Set the MOZ_HEADLESS environment variable which casues Firefox to start in headless mode.
    os.environ['MOZ_HEADLESS'] = '1'
    exeFirefox = os.environ['FIREFOX_EXE']

    # Select your Firefox binary.
    binary = FirefoxBinary(exeFirefox, log_file=sys.stdout)

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", dir_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/xml,text/plain,text/xml,image/jpeg,text/csv")

    # Start selenium with the configured binary.
    driver = webdriver.Firefox(firefox_binary=binary, firefox_profile=profile)
#     driver = webdriver.Firefox(firefox_profile=profile)

    # Visit this webpage.
    driver.get("https://thatoneprivacysite.net/vpn-comparison-chart/")

    # Click the csv link to download csv file.
    driver.find_element_by_link_text("csv").click()

    # Wait to make sure file is downloaded
    time.sleep(10)

    # Quit the webdriver
    driver.quit()


    print("downloaded the file.")
    print("uploading csv data to the database.")

    engine = create_engine('mysql://p8j4q9u7itbc9epz:zlyrdub556dhg5hz@ffn96u87j5ogvehy.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/ml0vnaijudbhqrn0')
    conn = engine.connect()
    
    vpnCompDataDF = pd.read_csv("That One Privacy Guy's VPN Comparison Chart - VPN Comparison.csv")
    vpnCompDataDF1 = vpnCompDataDF[3:-3]
    vpnCompDataDF2 = vpnCompDataDF1.fillna('Unknown')
    vpnCompDataDF2.columns = vpnCompDataDF2.iloc[0]
    vpnCompDataDF2.reindex(vpnCompDataDF2.index.drop(3))
    vpnCompDataDF3 = vpnCompDataDF2[1:]
    vpnCompDataDF3.reindex
    columns = vpnCompDataDF3.columns 
    columnsList = columns.tolist()
    counts = Counter(columns)
    for s,num in counts.items():
        if num > 1: # ignore strings that only appear once
            for suffix in range(1, num + 1): # suffix starts at 1 and increases by 1 each time
                columnsList[columnsList.index(s)] = s + str(suffix) # replace each appearance of s
    columns = pd.Index(columnsList)
    columns = [i.replace(' ', '_') for i in columns]
    vpnCompDataDF4 = vpnCompDataDF3
    vpnCompDataDF4.columns = columns

    vpnCompDataDF4.to_sql('vpn_master', engine, if_exists='replace', chunksize=10000)
    conn.execute("ALTER TABLE vpn_master DROP COLUMN `index`;")
    conn.execute("ALTER TABLE vpn_master ADD id INT PRIMARY KEY AUTO_INCREMENT;")


sched.start()
