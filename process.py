import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

class PlotData:
    DATE = 0
    DISTANCE = 1

    def __init__(self, from_date, till_date):
        self.from_date = from_date
        self.till_date = till_date


    def dilute_dates(self, dates):
        if len(dates) > 20:
            step = int(len(dates) / 20)  # 20 or less
            return [date for index, date in enumerate(dates) if index % step == 0]
        return dates


    def plot_distance(self):
        distance_sequence = list()
        dates = list()
        with open('fitbit_stats.csv', 'r') as data:
            print(next(data))
            for row in data:
                print(row)
                '''if row:
                    row = row.split(',')
                    if self.till_date > datetime.strptime(row[self.DATE], '%d.%m.%Y') and self.from_date < datetime.strptime(row[self.DATE], '%d.%m.%Y'):
                        dates.append(datetime.strptime(row[self.DATE], '%d.%m.%Y'))
                        distance_sequence.append(float(row[7]))
                else:
                    print('End of file.')
                    exit()

        dates = self.dilute_dates(dates)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.plot(dates, distance_sequence)
        plt.gcf().autofmt_xdate()
        plt.show()'''

plot = PlotData(datetime(2021, 2, 23), datetime(2021, 5, 1))

#print(plot.dilute_dates([i for i in range(15)]))

plot.plot_distance()