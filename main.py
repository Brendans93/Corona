import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import pyinputplus as pyip
import warnings
warnings.filterwarnings("ignore")
from countryinfo import CountryInfo

def main():
    download_files()
    data, validCountries = clean_data()
    while True:
        choice = pyip.inputMenu(["Confirmed", "Deaths", "Recovered", "Confirmed per capita", "Deaths per capita", "Recovered per capita", "See countries", "Quit"], numbered=True)
        if choice == "Quit":
            break
        elif choice == "See countries":
            for country in validCountries:
                print(country)
            continue
        response = pyip.inputStr("Enter countries of interest (separate by commas): ")
        countries = response.split(", ")
        for country in countries:
            if country not in validCountries:       #check if countries are valid (in dataframe)
                countries.remove(country)
                print(f"{country} is not a valid entry")

        choiceDict = {"Confirmed": 0, "Deaths": 1, "Recovered": 2, "Confirmed per capita": 3, "Deaths per capita": 4, "Recovered per capita": 5}

        fig, ax = plt.subplots()

        for country in countries:
            data[choiceDict[choice]].T[country].plot(ax=ax)
        ax.legend(countries)
        plt.xlabel("Date")
        label = choice
        if label != "Deaths":
            label += " cases"
        plt.ylabel(f"Number of {label.lower()}")
        plt.title(f"Number of {label.title()}")
        plt.show()

def download_files():
    """
    Download data to current directory /data using the Kaggle API
    :return:
    """
    #delete old files
    dataPath = Path(Path(os.getcwd()) / "data")
    for filename in dataPath.glob("*"):
        os.unlink(filename)

    #download new files
    print("Downloading files...")
    try:
        os.system("kaggle datasets download sudalairajkumar/novel-corona-virus-2019-dataset -f time_series_covid_19_confirmed.csv -p data -q")
        os.system("kaggle datasets download sudalairajkumar/novel-corona-virus-2019-dataset -f time_series_covid_19_deaths.csv -p data -q")
        os.system("kaggle datasets download sudalairajkumar/novel-corona-virus-2019-dataset -f time_series_covid_19_recovered.csv -p data -q")
        print("Downloading files finished")
    except:
        print("Error downloading files")

def clean_data():
    """
    Finds three csv files (confirmed, deaths, recovered) and converts them in to dataframes
    Cleans up unneeded data (Province, longitude, latitude)
    :return dataFrames the dataFrames representing confirmed, deaths, recovered, confirmed per capita, deaths per capita, recovered per capita
    :return countryList a list of valid countries
    """
    datapath = Path(os.getcwd()) / "data"
    files = [str(file) for file in datapath.glob("*.csv")]
    for file in files:
        if file.endswith("confirmed.csv"):
            Confirmed = pd.read_csv(file)
        elif file.endswith("deaths.csv"):
            Deaths = pd.read_csv(file)
        elif file.endswith("recovered.csv"):
            Recovered = pd.read_csv(file)

    dataFrames = [Confirmed, Deaths, Recovered]
    countryList = list(dataFrames[0]["Country/Region"])                #list of valid countries
    countryList = list(dict.fromkeys(countryList))

    #create country population dictionary and align values with those in countryList
    countriesPop = {}
    countriesPop["US"] = CountryInfo("USA").population()
    countriesPop["Czechia"] = CountryInfo("Czech Republic").population()
    countriesPop["Taiwan*"] = CountryInfo("Taiwan").population()
    countriesPop["Korea, South"] = CountryInfo("South Korea").population()
    countriesPop["Eswatini"] = CountryInfo("Swaziland").population()
    countriesPop["Cote d'Ivoire"] = CountryInfo("Ivory Coast").population()

    for country in countryList:
        try:
            countriesPop[country] = CountryInfo(country).population()
        except KeyError:
            pass

    #remove unnecessary information from dataframes
    for count in range(len(dataFrames)):
        dataFrames[count] = dataFrames[count].drop("Province/State",axis=1)
        dataFrames[count] = dataFrames[count].drop("Lat",axis=1)
        dataFrames[count] = dataFrames[count].drop("Long",axis=1)
        dataFrames[count] = dataFrames[count].rename(columns={"Country/Region": "Country"})
        dataFrames[count]["Country"] = dataFrames[count]["Country"].replace({"Korea, South": "South Korea"})
        dataFrames[count] = dataFrames[count].groupby("Country").sum()

    # create per 100k capita values by dividing country data by population
    ConfirmedPC = dataFrames[0].copy()
    DeathsPC = dataFrames[1].copy()
    RecoveredPC = dataFrames[2].copy()
    countryList.append("South Korea")

    for country in countryList:
        try:
            ConfirmedPC.loc[country] = ConfirmedPC.loc[country].divide(countriesPop[country]).multiply(100000)      #confirmed cases per 100k inhabitants
            DeathsPC.loc[country] = DeathsPC.loc[country].divide(countriesPop[country]).multiply(100000)      #deaths  per 100k inhabitants
            RecoveredPC.loc[country] = RecoveredPC.loc[country].divide(countriesPop[country]).multiply(100000)      #recovered cases per 100k inhabitants
        except KeyError:
            pass

    dataFrames.extend([ConfirmedPC, DeathsPC, RecoveredPC])

    return dataFrames, countryList

main()