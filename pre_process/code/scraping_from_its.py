from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import sys
import json


def scraping_from_its(in_json_name, out_json_name, repo_name):
    driver = webdriver.Chrome()
    json_open = open(in_json_name, 'r')
    json_load = json.load(json_open)
    issueID_list = []
    for commit in json_load:
        for issue_id in commit['issue_id']:
            if issue_id not in issueID_list:
                issueID_list.append(issue_id)
        
    if repo_name == 'qt':
        url = 'https://bugreports.qt.io/projects/QTBUG/issues/'
        id = 'quickSearchInput'
        id2 = 'summary-val'
        id3 = 'priority-val'
        id4 = 'description-val'
        driver.get(url)
        issueID_inf_list = []
        for issue_id in issueID_list:
            print(issue_id)     
            issue_dict = {}
            issue_dict['issue_id'] = issue_id
            try:
                search_box = driver.find_element(By.ID, id)
                search_box.send_keys(issue_id)
                search_box.send_keys(Keys.RETURN)
            except NoSuchElementException:
                driver.back()
                continue
            try:
                element = driver.find_element(By.ID, id2)
                issue_dict['title'] = element.text
            except NoSuchElementException:
                pass
            try:
                element = driver.find_element(By.ID, id3)
                issue_dict['priority_level'] = element.text
            except NoSuchElementException:
                pass
            try:
                element = driver.find_element(By.ID, id4)
                issue_dict['description'] = element.text
            except NoSuchElementException:
                pass
            if 'priority_level' not in issue_dict.keys() and 'discription' not in issue_dict.keys():
                continue                
            issueID_inf_list.append(issue_dict)
        
    elif repo_name == 'openstack':
        url = 'https://bugs.launchpad.net/openstack'   
        driver.get(url)
        id = 'field\.searchtext'
        selector = '#edit-title > span'
        selector2 = '#affected-software > tbody'
        selector3  = '#edit-description > div.yui3-editable_text-text'
        issueID_inf_list = []

        for issue_id in issueID_list:
            print(issue_id)     
            issue_dict = {}
            issue_dict['issue_id'] = issue_id
            try:
                search_box = driver.find_element(By.ID, id)
                search_box.clear()
                search_box.send_keys(issue_id)
                search_box.send_keys(Keys.RETURN)
            except NoSuchElementException:
                driver.back()
                continue
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                issue_dict['title'] = element.text
            except NoSuchElementException:
                pass
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector2)
                trlist = element.find_elements(By.TAG_NAME, 'tr')
                issue_dict['priority_level'] = []
                for i in range(0, len(trlist)):
                    tds = trlist[i].find_elements(By.TAG_NAME, 'td')
                    if len(tds) == 6:
                        tmp = tds[1].text+'-'+tds[3].text
                        issue_dict['priority_level'].append(tmp)
            except NoSuchElementException:
                pass
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector3)
                issue_dict['description'] = element.text
            except NoSuchElementException:
                pass
            if 'priority_level' not in issue_dict.keys() and 'discription' not in issue_dict.keys():
                driver.back()
                continue               
            issueID_inf_list.append(issue_dict)
            driver.back()
        
    driver.quit()
    with open(out_json_name, 'w', encoding='utf-8') as f:
        json.dump(issueID_inf_list, f, indent=2)


if __name__ == '__main__':
    in_json_name = sys.argv[1]
    out_json_name = sys.argv[2]
    repo_name = sys.argv[3]
    scraping_from_its(in_json_name, out_json_name, repo_name)