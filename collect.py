from python_fitbit_master import fitbit
import python_fitbit_master.gather_keys_oauth2 as Oauth2
import datetime
import time
import csv
from pprint import pprint
from collections import namedtuple

class InvokeClient:
    def __init__(self):
        KEYS = open('keys.txt', 'r').readlines()
        self.CLIENT_ID = KEYS[0].strip('\n')
        self.CLIENT_SECRET = KEYS[1].strip('\n')

    def invoke_client(self):
        # Using the ID and Secret, we can obtain the access and refresh tokens that authorize us to get our data.
        server = Oauth2.OAuth2Server(self.CLIENT_ID, self.CLIENT_SECRET)
        server.browser_authorize()
        ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
        REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
        auth2_client = fitbit.Fitbit(self.CLIENT_ID, self.CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN) #TODO token dict
        auth2_client.API_VERSION = 1.2
        return auth2_client


class TimeRange:
    def __init__(self, days_to_past):
        self._days        = days_to_past
        self._sleep_dates = None

    @property
    def intraday_dates(self):
        '''Produce strings of dates sequence.'''
        return (str((datetime.datetime.now() - datetime.timedelta(days=day)).strftime("%Y-%m-%d")) for day in range(self._days))

    @property
    def sleep_and_activity_dates(self):
        '''Produce sequence of date objects.'''
        return (datetime.datetime.now().date() - datetime.timedelta(days=day) for day in range(self._days))


class CollectData:
    requests_counter = 0
    cycle_counter = 0
    header = ('date', 
            'distance', 
            'floors', 
            'elevation', 
            'steps',
            'resting_heart_rate', 
            'basal_metabolic_rate',
            'total_caloric_exp',
            'sedentary_activity_dist',
            'sedentary_activity_min',
            'lightly_activity_dist', 
            'lightly_activity_min',
            'moderately_activity_dist',
            'moderately_activity_min',
            'very_activity_dist', 
            'very_activity_min',
            'out_of_range_cals',
            'out_of_range_min',
            'fat_burn_cals',
            'fat_burn_min',
            'cardio_cals',
            'cardio_min',
            'peak_cals',
            'peak_min')
        
    sleep_header = ('date',
                    'record_type',
                    'duration', 
                    'efficiency', 
                    'start_time', 
                    'end_time', 
                    'sleep_level_sequence_string',
                    'deep_count',
                    'deep_min',
                    'light_count',
                    'light_min',
                    'rem_count',
                    'rem_min',
                    'wake_count',
                    'wake_min',
                    'minutes_after_wakeup',
                    'minutes_asleep',
                    'minutes_awake',
                    'minutes_to_fall_asleep')



    def __init__(self, days):
        self.auth2_client = InvokeClient().invoke_client()
        self.time         = TimeRange(days) # rather from datetime
        

    @classmethod
    def counter_of_requests(cls, request):
        cls.requests_counter += request
        print('Request number: ', cls.requests_counter)
        if cls.requests_counter > 73:
            print('Waiting...')
            cls.cycle_counter += 1
            print('Number of cycles: ', cls.cycle_counter)
            time.sleep(3600) # avoiding "too many requests error" - 150 requests per hour
            cls.requests_counter = 0
            print('Requests continue...')

    
    def collect_distance(self, stats):
        try:
            return stats['summary']['distance']
        except KeyError:
            return 'N/A'
    
    
    def collect_floors(self, stats):
        try:
            return stats['summary']['floors']
        except KeyError:
            return 'N/A'


    def collect_elevation(self, stats):
        try:
            return stats['summary']['elevation']
        except KeyError:
            return 'N/A'


    def collect_steps(self, stats):
        try:
            return stats['summary']['steps']
        except KeyError:
            return 'N/A'

    
    def resting_heart_rate(self, hr_stats):
        try:
            return hr_stats['activities-heart'][0]['value']['restingHeartRate']
        except KeyError:
            return 'N/A'


    def collect_calories(self, stats):
        try:
            return stats['summary']['calories']['bmr'], stats['summary']['calories']['total']
        except KeyError:
            return 'N/A', 'N/A'

    def flatten(self, sequence):
        return [element for subseq in sequence for element in subseq]

    ##### activity stats #####
    def collect_all_levels_of_activity(self, activity):
        activity_levels = ('sedentary', 'lightly', 'moderately', 'very')
        activity_levels_values = list()
        for activity_level in activity_levels:
            try:
                activity_levels_values.append(activity[activity_level])
            except KeyError:
                activity_levels_values.append(['N/A', 'N/A'])

        activity_levels_values = self.flatten(activity_levels_values)
        return activity_levels_values


    def collect_activity_levels(self, stats):
        try:
            activity = {stats['summary']['activityLevels'][i]['name']:
                [stats['summary']['activityLevels'][i]['distance'], 
                stats['summary']['activityLevels'][i]['minutes']] 
                for i in range(len(stats['summary']['activityLevels']))}
        except KeyError:
            return ('N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A')

        return self.collect_all_levels_of_activity(activity)
                    

    ##### HR zones #####
    def yield_hr_zones(self, hr_zones):
        zones = ('Out of Range', 'Fat Burn', 'Cardio', 'Peak')
        zones_values = list()
        for zone in zones:
            try:
                zones_values.append(hr_zones[zone])
            except KeyError:
                zones_values.append(['N/A', 'N/A'])

        zones_values = self.flatten(zones_values)
        return zones_values
        

    def collect_heart_rate_zones(self, stats):
        try:
            hr_zones = {stats['summary']['heartRateZones'][i]['name']: 
                [stats['summary']['heartRateZones'][i]['caloriesOut'], 
                stats['summary']['heartRateZones'][i]['minutes']] 
                for i in range(len(stats['summary']['heartRateZones']))}
            return self.yield_hr_zones(hr_zones)
        except KeyError:
            return ('N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A')
    ####################


    def activity_stats(self):
        ActivityData = namedtuple('ActivityData', self.header)
        for sleep_activity_date, intraday_date in zip(self.time.sleep_and_activity_dates, 
                                                        self.time.intraday_dates):

            stats = self.auth2_client.activities(sleep_activity_date)
            hr_stats = self.auth2_client.intraday_time_series('activities/heart', 
                                                                    base_date=intraday_date, 
                                                                    detail_level='1sec')

            date = sleep_activity_date.strftime('%d.%m.%Y')
            distance = self.collect_distance(stats)
            floors = self.collect_floors(stats)
            elevation = self.collect_elevation(stats)
            steps = self.collect_steps(stats)
            resting_heart_rate = self.resting_heart_rate(hr_stats)
            basal_metabolic_rate, \
            total_caloric_exp = self.collect_calories(stats)
            sedentary_activity_dist, \
            sedentary_activity_min, \
            lightly_activity_dist, \
            lightly_activity_min, \
            moderately_activity_dist, \
            moderately_activity_min, \
            very_activity_dist, \
            very_activity_min = self.collect_activity_levels(stats)
            out_of_range_cals, \
            out_of_range_min, \
            fat_burn_cals, \
            fat_burn_min, \
            cardio_cals, \
            cardio_min, \
            peak_cals, \
            peak_min = self.collect_heart_rate_zones(stats)

            self.counter_of_requests(1)
            yield ActivityData(date, 
                    distance, 
                    floors, 
                    elevation, 
                    steps,
                    resting_heart_rate,
                    basal_metabolic_rate, 
                    total_caloric_exp, 
                    sedentary_activity_dist,
                    sedentary_activity_min,
                    lightly_activity_dist,
                    lightly_activity_min,
                    moderately_activity_dist,
                    moderately_activity_min,
                    very_activity_dist,
                    very_activity_min, 
                    out_of_range_cals,
                    out_of_range_min,
                    fat_burn_cals,
                    fat_burn_min,
                    cardio_cals,
                    cardio_min,
                    peak_cals,
                    peak_min)


    def sleep_duration(self, stats):
        try:
            return stats['sleep'][0]['duration']
        except KeyError:
            return 'N/A'


    def sleep_efficiency(self, stats):
        try:
            return stats['sleep'][0]['efficiency']
        except KeyError:
            return 'N/A'


    def stard_end_time_of_sleep(self, stats):
        try:
            return stats['sleep'][0]['startTime'], stats['sleep'][0]['endTime']
        except KeyError:
            return 'N/A', 'N/A'


    def parse_sleep_pattern(self, stats):
        full_record = ''
        for record in stats['sleep'][0]['levels']['data']:
            full_record = full_record + '*' + str(record['dateTime']) + '_' + str(record['level']) + '_' + str(record['seconds'])
        return full_record


    def obtain_sleep_level_count(self, stats, sleep_level):
        try:
            return stats['sleep'][0]['levels']['summary'][sleep_level]['count']
        except KeyError:
            return 'N/A'

    
    def obtain_sleep_level_minutes(self, stats, sleep_level):
        try:
            return stats['sleep'][0]['levels']['summary'][sleep_level]['minutes']
        except KeyError:
            return 'N/A'


    def summary_sleep(self, stats):
        sleep_levels = ('deep', 'light', 'rem', 'wake')
        summary_sleep_levels = tuple()
        for sleep_level in sleep_levels:
            summary_sleep_levels = summary_sleep_levels + (self.obtain_sleep_level_count(stats, sleep_level),
                                                            self.obtain_sleep_level_minutes(stats, sleep_level))
        return summary_sleep_levels


    def collect_minutes_after_wakeup_sleep(self, stats):
        try:
            return stats['sleep'][0]['minutesAfterWakeup']
        except KeyError:
            return 'N/A'


    def collect_minutes_asleep_sleep(self, stats):
        try:
            return stats['sleep'][0]['minutesAsleep']
        except KeyError:
            return 'N/A'


    def collect_minutes_awake_sleep(self, stats):
        try:
            return stats['sleep'][0]['minutesAwake']
        except KeyError:
            return 'N/A'


    def collect_minutes_to_fall_asleep_sleep(self, stats):
        try:
            return stats['sleep'][0]['minutesToFallAsleep']
        except KeyError:
            return 'N/A'
    

    def sleep_stats(self):
        SleepData = namedtuple('SleepData', self.sleep_header)
        for day in self.time.sleep_and_activity_dates:
            stats = self.auth2_client.sleep(date=day)
            if stats['sleep'][0]['isMainSleep'] and stats['sleep'][0]['type'] == 'stages': # full record
                date = day
                record_type = 'full'
                duration = self.sleep_duration(stats)
                efficiency = self.sleep_efficiency(stats)
                start_time, end_time = self.stard_end_time_of_sleep(stats)
                sleep_level_sequence_string = self.parse_sleep_pattern(stats)
                deep_count, \
                deep_min, \
                light_count, \
                light_min, \
                rem_count, \
                rem_min, \
                wake_count, \
                wake_min = self.summary_sleep(stats)
                minutes_after_wakeup = self.collect_minutes_after_wakeup_sleep(stats)
                minutes_asleep = self.collect_minutes_asleep_sleep(stats)
                minutes_awake = self.collect_minutes_awake_sleep(stats)
                minutes_to_fall_asleep = self.collect_minutes_to_fall_asleep_sleep(stats)
            elif stats['sleep'][0]['isMainSleep'] and stats['sleep'][0]['type'] == 'classic': # partial record
                date = day
                record_type = 'partial'
                duration = self.sleep_duration(stats)
                efficiency = self.sleep_efficiency(stats)
                start_time, end_time = self.stard_end_time_of_sleep(stats)
                sleep_level_sequence_string = self.parse_sleep_pattern(stats)
                deep_count = 'N/A'
                deep_min = 'N/A'
                light_count = 'N/A'
                light_min = 'N/A'
                rem_count = 'N/A'
                rem_min = 'N/A'
                wake_count = 'N/A'
                wake_min = 'N/A'
                minutes_after_wakeup = self.collect_minutes_after_wakeup_sleep(stats)
                minutes_asleep = self.collect_minutes_asleep_sleep(stats)
                minutes_awake = self.collect_minutes_awake_sleep(stats)
                minutes_to_fall_asleep = self.collect_minutes_to_fall_asleep_sleep(stats)

            self.counter_of_requests(1)
            yield SleepData(date,
                    record_type,
                    duration, 
                    efficiency, 
                    start_time, 
                    end_time, 
                    sleep_level_sequence_string,
                    deep_count,
                    deep_min,
                    light_count,
                    light_min,
                    rem_count,
                    rem_min,
                    wake_count,
                    wake_min,
                    minutes_after_wakeup,
                    minutes_asleep,
                    minutes_awake,
                    minutes_to_fall_asleep)


    def write_data_to_csv(self):
        with open('fitbit_stats.csv', 'w', newline='') as csvfile:
            write = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            write.writerow(self.header + self.sleep_header)
            for activity_data, sleep_data in zip(self.activity_stats(), self.sleep_stats()):
                print(activity_data, sleep_data)
                write.writerow(tuple(activity_data) + tuple(sleep_data)) # convert to normal tuple


    def wholetime_stats(self):
        pprint(self.auth2_client.frequent_activities())
        pprint(self.auth2_client.favorite_activities())


    
if __name__ == '__main__':
    collect = CollectData(1)

    #collect.wholetime_stats()

    '''
    activity = collect.activity_stats()
    for i in activity:
        print(i)'''


    collect.write_data_to_csv()
    