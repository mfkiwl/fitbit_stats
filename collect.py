from python_fitbit_master import fitbit
import python_fitbit_master.gather_keys_oauth2 as Oauth2
import datetime
import time
import csv
from pprint import pprint

class InvokeClient:
    def __init__(self):
        self.CLIENT_ID = '22BZVM'
        self.CLIENT_SECRET = '8e1df82f0355605210b22be6a3a37433'

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
    counter = 0
    header = ('date', 
            'distance', 
            'floors', 
            'elevation', 
            'steps',
            'restingHeartRate', #### !
            'basal_metabolic_rate',
            'total_caloric_exp',
            'sedentary_activity_dist',
            'sedentary_activity_minutes',
            'lightly_activity_dist', 
            'lightly_activity_minutes',
            'moderately_activity_dist',
            'moderately_activity_minutes',
            'very_activity_dist', 
            'very_activity_minutes',
            'HR_out_of_range_calories',
            'HR_out_of_range_minutes',
            'HR_fat_burn_calories',
            'HR_fat_burn_minutes',
            'HR_cardio_calories',
            'HR_cardio_minutes',
            'HR_peak_calories',
            'HR_peak_minutes',)



    def __init__(self, days):
        self.auth2_client = InvokeClient().invoke_client()
        self.time         = TimeRange(days) # rather from datetime
        

    @classmethod
    def counter_of_requests(cls, request):
        cls.counter += request
        if cls.counter == 149:
            time.sleep(3600) # avoiding "too many requests error" - 150 requests per hour
            cls.counter = 0
            print('Requests continue...')

    
    def collect_distance(self):
        try:
            return self.stats['summary']['distance']
        except Exception:
            return 'N/A'
    
    
    def collect_floors(self):
        try:
            return self.stats['summary']['floors']
        except Exception:
            return 'N/A'


    def collect_elevation(self):
        try:
            return self.stats['summary']['elevation']
        except Exception:
            return 'N/A'


    def collect_steps(self):
        try:
            return self.stats['summary']['steps']
        except Exception:
            return 'N/A'

    
    def resting_heart_rate(self):
        try:
            return self.HR_stats['activities-heart'][0]['value']['restingHeartRate']
        except Exception:
            return 'N/A'


    def collect_calories(self):
        try:
            return self.stats['summary']['calories']['bmr'], self.stats['summary']['calories']['total']
        except Exception:
            return 'N/A', 'N/A'


    def sedentary_activity(self, activity):
        try:
            return activity['sedentary']
        except Exception:
            return 'N/A', 'N/A'
 

    def lightly_activity(self, activity):
        try:
            return activity['lightly']
        except Exception:
            return 'N/A', 'N/A'


    def moderately_activity(self, activity):
        try:
            return activity['moderately']
        except Exception:
            return 'N/A', 'N/A'


    def very_activity(self, activity):
        try:
            return activity['very']
        except Exception:
            return 'N/A', 'N/A'


    def collect_activity_levels(self):
        try:
            activity = {self.stats['summary']['activityLevels'][i]['name']:
                [self.stats['summary']['activityLevels'][i]['distance'], 
                self.stats['summary']['activityLevels'][i]['minutes']] for i in range(len(self.stats['summary']['activityLevels']))}
            sedentary_activity_dist, sedentary_activity_minutes = self.sedentary_activity(activity)
            lightly_activity_dist, lightly_activity_minutes = self.lightly_activity(activity)
            moderately_activity_dist, moderately_activity_minutes = self.moderately_activity(activity)
            very_activity_dist, very_activity_minutes = self.very_activity(activity)
            return (sedentary_activity_dist, 
                    sedentary_activity_minutes, 
                    lightly_activity_dist, 
                    lightly_activity_minutes,
                    moderately_activity_dist,
                    moderately_activity_minutes,
                    very_activity_dist,
                    very_activity_minutes)
                    
        except Exception:
            return ('N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A')



    
    def gather_stats(self):
        for sleep_activity_date, intraday_date in zip(self.time.sleep_and_activity_dates, 
                                        self.time.intraday_dates):
            try:
                # summary: activityLevels (distance, minutes, name), distance, elevation, floors, calories, heart zones, steps
                self.stats = self.auth2_client.activities(sleep_activity_date)
                self.HR_stats = self.auth2_client.intraday_time_series('activities/heart', 
                                                                        base_date=intraday_date, 
                                                                        detail_level='1sec')

                distance = self.collect_distance()
                floors = self.collect_floors()
                elevation = self.collect_elevation()
                steps = self.collect_steps()
                resting = self.resting_heart_rate()
                basal_metabolic_rate, \
                total_caloric_exp = self.collect_calories()
                sedentary_activity_dist, \
                sedentary_activity_minutes, \
                lightly_activity_dist, \
                lightly_activity_minutes, \
                moderately_activity_dist, \
                moderately_activity_minutes, \
                very_activity_dist, \
                very_activity_minutes = self.collect_activity_levels()

                
                # clean up
                heartRateZones = {self.stats['summary']['heartRateZones'][i]['name']: 
                                [self.stats['summary']['heartRateZones'][i]['caloriesOut'], 
                                self.stats['summary']['heartRateZones'][i]['minutes']] for i in range(len(self.stats['summary']['heartRateZones']))}


                self.counter_of_requests(1)
                yield (sleep_activity_date.strftime('%d.%m.%Y'), 
                        distance, 
                        floors, 
                        elevation, 
                        steps,
                        resting,
                        basal_metabolic_rate, 
                        total_caloric_exp, 
                        sedentary_activity_dist,
                        sedentary_activity_minutes,
                        lightly_activity_dist,
                        lightly_activity_minutes,
                        moderately_activity_dist,
                        moderately_activity_minutes,
                        very_activity_dist,
                        very_activity_minutes, heartRateZones)
            except KeyError: # key error may (not sure) refer on absence of data for particular day
                print('error')
                continue

    def sleep_stats(self):
        for day in self.time.sleep_and_activity_dates:
            try:
                stats = self.auth2_client.sleep(date=day)
                self.counter_of_requests(1)
                yield stats
            except KeyError: # key error may (not sure) refer on absence of data for particular day
                continue



    def wholetime_stats(self):
        pprint(self.auth2_client.frequent_activities())
        pprint(self.auth2_client.favorite_activities())


    

collect = CollectData(10)


slp = collect.sleep_stats()
activity = collect.gather_stats()

#collect.wholetime_stats()



for i in activity:
    print(i)

'''
for j in slp:
    pprint(j)'''



class WriteData:
    pass