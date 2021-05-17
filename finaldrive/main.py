import requests
import json
import csv
import time
from constants import fieldnames, headers
import os


class FinalDrives_Scraper:
    def __init__(self, proxies: list, proxy_username: str, proxy_password: str, headers: dict, output_filepath: str) -> None:
        self.__proxies = proxies
        self.__proxy_username = proxy_username
        self.__proxy_password = proxy_password
        self.__headers = headers
        self.__output_filepath = output_filepath
        self.__proxy_index = 0

    def run(self):
        finished_labels = self.__get_finished_labels()
        output_file, csv_writer = self.__get_csv_handler()
        machine_makes = self.__get_machine_makes()
        # json.dump(machine_makes, open('machine_makes.json', 'w'), indent=4)
        for machine_make in machine_makes['Items']:
            if 'FinalDrive' in machine_make['ModelComponentTypes']:
                make = machine_make['Make']
                machine_make_id = machine_make['Id']
                print(f'make: {make}, id: {machine_make_id}')
                machine_models = self.__get_machine_models(machine_make_id)
                # json.dump(machine_models, open('machine_models_per_machine_make.json', 'w'), indent=4)
                for machine_model in machine_models['Items']:
                    model = machine_model['Model']
                    machine_model_id = machine_model['Id']
                    print(f'\tmodel: {model}, id: {machine_model_id}')
                    label = make + ',' + model
                    if label not in finished_labels:
                        machines = self.__get_machines(machine_model_id)
                        # json.dump(machines, open('machines_per_model.json', 'w'), indent=4)
                        for machine in machines['Items']:
                            print('\t\tid: ' + machine['Id'])
                            machine['Make'] = make
                            machine['Model'] = model
                            del machine['$type']
                            csv_writer.writerow(machine)
                            output_file.flush()
                    else:
                        print('\t\tskip.')

    def __get_finished_labels(self):
        finished_labels = []
        try:
            input_file = open(self.__output_filepath)
            reader = csv.DictReader(input_file)
            finished_labels = []
            for row in reader:
                label = row['Make'] + ',' + row['Model']
                if label not in finished_labels:
                    finished_labels.append(label)
            input_file.close()
        except:
            pass
        return finished_labels

    def __get_csv_handler(self):  
        if os.path.exists(self.__output_filepath):
            output_file = open('output.csv', 'a', newline='')
            csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            return output_file, csv_writer
        else:
            output_file = open('output.csv', 'w', newline='')
            csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            csv_writer.writeheader()
            output_file.flush()
            return output_file, csv_writer

    def __get_machine_makes(self) -> dict:
        url = 'http://quotesv2.finaldrives.com/api/data/machineMakes'
        return requests.get(url, headers=self.__headers).json()

    def __get_machine_models(self, machine_make_id: int):
        url = f'http://quotesv2.finaldrives.com/api/data/machineModels/{machine_make_id}?componentType=FinalDrive'
        return requests.get(url, headers=headers).json()

    def __get_machines(self, machine_model_id: int):
        url = f'http://quotesv2.finaldrives.com/api/data/getMachines/{machine_model_id}?componentType=FinalDrive&language=en_US&recaptchaResponse=NA&source=FinalDrivesEU-Website'
        return self.__get_request(url)

    def __get_remaining_searches(self, proxy: dict) -> int:
        response = requests.get('http://quotesv2.finaldrives.com/api/data/lookupsRemaining?componentType=FinalDrive', proxies=proxy, timeout=60).json()
        return int(response['Item'])

    def __get_proxy(self, proxy_index: int) -> dict:
        proxy = self.__proxies[proxy_index]
        return {
            'http': f'http://{self.__proxy_username}:{self.__proxy_password}@{proxy}',
            'https': f'http://{self.__proxy_username}:{self.__proxy_password}@{proxy}'
        }

    def __get_request(self, url: str) -> dict:
        response = {}
        for _ in range(len(self.__proxies)):
            proxy = self.__get_proxy(self.__proxy_index)
            print('\t\tusing proxy:', proxy['http'])
            try:
                remaining_searches = self.__get_remaining_searches(proxy)
                print('remaining searches: ', remaining_searches)
                if remaining_searches > 0:
                    response = requests.get(url, headers=headers, proxies=proxy, timeout=60).json()
                    break
            except:
                pass
            self.__proxy_index = (self.__proxy_index + 1)%len(self.__proxies)
            print('next proxy index: ', self.__proxy_index)
        return response

    def __get_request_scraperapi(self, url: str, api_key: str):
        response = None
        for i in range(5):
            try:
                response = requests.get(f'http://api.scraperapi.com?api_key={api_key}&url={url}', headers=self.__headers, timeout=60)
                return response.json()
            except Exception as e:
                print(e)
                print('request failed, retrying in 10 sec.')
                time.sleep(10)
        print(response)


if __name__ == '__main__':
    credentials_filepath = os.path.join(os.path.dirname(__file__), 'credentials.json')
    credentials = json.load(open(credentials_filepath))
    output_filepath = os.path.join(os.path.dirname(__file__), 'output.csv')
    proxies = open('proxies.txt').read().split('\n')[:-1]
    scraper = FinalDrives_Scraper(proxies, credentials['proxy_username'], credentials['proxy_password'], headers, output_filepath)
    scraper.run()
