from selenium import webdriver
import os
import time
import json

#supply the script with the url of the first episode and the index of the first url to download.
first_episode_url = 'https://wcostream.cc/watch/jujutsu-kaisen-tv-dub-kPLY-episode-1/'
start_episode_index = 8

driver = webdriver.Chrome(os.path.join(os.path.dirname(__file__), 'chromedriver'))
driver.get(first_episode_url)
episodes = driver.find_elements_by_xpath('//a[contains(@id, "episode")]')
episodes_urls = []
time.sleep(5)
for episode in episodes:
    episodes_urls.append(episode.get_attribute('href'))
counter = 1
for episode_url in episodes_urls:
    if counter < start_episode_index:
        counter += 1
        continue
    driver.get(episode_url)
    time.sleep(5)
    while driver.find_element_by_xpath('//script[@type="application/ld+json"]').get_attribute("innerHTML") == '':
        time.sleep(1)
    video_id = json.loads(driver.find_element_by_xpath('//script[@type="application/ld+json"]').get_attribute("innerHTML"))['@graph'][0]['video']['embedUrl'].split('/e/')[-1].split('?domain')[0]
    print(video_id)
    download_url = f'https://vidstream.pro/download/{video_id}'
    driver.get(download_url)
    driver.execute_script('arguments[0].click()', driver.find_element_by_xpath('//button'))
    time.sleep(60)
    counter += 1
