'''
BS440domoticz.py
Update weight value to Domoticz home automation system
'''

import urllib
import base64
import logging
import traceback
import json
from ConfigParser import *

write_config = False

data = '{}'
query = True

configDomoticz = SafeConfigParser()
configDomoticz.read('BS440domoticz.ini')

def UpdateDomoticz(config, weightdata, bodydata, persondata):
    log = logging.getLogger(__name__)
    domoticzurl = config.get('Domoticz', 'domoticz_url')
    domoticzuser = ""
    domoticzpwd = ""
  
    # read user's name
    personsection = 'Person1'
    """
    personsection = 'Person' + str(weightdata[0]['person'])
    
    if config.has_section(personsection):
        user = config.get(personsection, 'username')
    else:
        log.error('Unable to update Domoticz: No details found in ini file '
                  'for person %d' % (weightdata[0]['person']))
        return
    """
    user = 'Tristan'
    
    url_mass = 'http://%s/json.htm?type=command&param=udevice&hid=%s&' \
              'did=%s&dunit=%s&dtype=93&dsubtype=1&nvalue=0&svalue=%s'
    url_per = 'http://%s/json.htm?type=command&param=udevice&idx=%s&nvalue=0&svalue=%s'
    url_hardware_add = 'http://%s/json.htm?type=command&param=addhardware&htype=15&port=1&name=%s&enabled=true'
    url_hardware = 'http://%s/json.htm?type=hardware'
    url_sensor = 'http://%s/json.htm?type=devices&filter=utility&used=true&order=Name'
    url_sensor_add = 'http://%s/json.htm?type=createvirtualsensor&idx=%s&sensorname=%s&sensortype=%s'

    def open_url(url):
        log.debug('Opening url: %s' % (url))
        try:
            response = urllib.urlopen(url)
        except Exception, e:
            log.error('Failed to send data to Domoticz (%s)' % (url))
            return '{}'
        return response

    def exists_hardware(name):
        response = open_url(url_hardware % (domoticzurl))
        data = json.loads(response.read())
        if 'result' in data:
            for i in range(0,len(data['result'])):
                if name == data['result'][i]['Name']:
                    return data['result'][i]['idx']
        return 'None'

    # Check if hardware exists and add if not..
    harwarename = 'Medisana'

    hardwareid = exists_hardware(harwarename)
    if 'None' == hardwareid:
        response = open_url(url_hardware_add % (domoticzurl, harwarename.replace(' ', '%20')))
        hardwareid = exists_hardware(harwarename)
        if 'None' == hardwareid:
                log.error('Unable to access Domoticz hardware')
                return


    def exists_sensor(name):
        global query
        global data
        if query:
            response = open_url(url_sensor % (domoticzurl))
            data = json.loads(response.read())
            query = False
        if 'result' in data:
            for i in range(0,len(data['result'])):
                if name == data['result'][i]['Name'] and int(hardwareid) == data['result'][i]['HardwareID']:
                    return data['result'][i]['idx']
        return 'None'

    def exists_id(sensorid):
        global query
        global data
        if query:
            response = open_url(url_sensor % (domoticzurl))
            data = json.loads(response.read())
            query = False
        if 'result' in data:
            for i in range(0,len(data['result'])):
                if sensorid == data['result'][i]['idx'] and int(hardwareid) == data['result'][i]['HardwareID']:
                    return True
        return False

    def use_virtual_sensor(name,type,options=''):
        global query
        sensorid = exists_sensor(name)
        if 'None' != sensorid:
            return sensorid
        if 'None' == sensorid:
            url = url_sensor_add % (domoticzurl, hardwareid, name.replace(' ', '%20'),str(type))
            if options != '':
                url = url + '&sensoroptions=' + options
            response = open_url(url)
            query = True
            return exists_sensor(name)

    SensorPercentage = 2
    SensorCustom     = 1004
   
    write_config = False

    # create or discover sensors
    def get_id(iniid,text,type,options=""):
        try:
            write_config = True
            rid = configDomoticz.get(personsection, iniid)
            if not exists_id(id):
                raise Exception
        except:
            rid = use_virtual_sensor(user + ' ' + text,type,options)
            configDomoticz.set(personsection, iniid, rid)
            write_config = True
        return rid
        

    try:
        try:
            configDomoticz.add_section(personsection)
        except DuplicateSectionError:
            pass
        fatid = get_id('fat_id','Fat Percentage',SensorPercentage)
        print "f"
        print fatid
        bmrid = get_id('bmr_id','BMR',SensorCustom,'1;Calories')
        muscleid = get_id('muscle_id','Muscle Percentage',SensorPercentage)
        boneid = get_id('bone_id','Bone Percentage',SensorPercentage)
        waterid = get_id('water_id','Water Percentage',SensorPercentage)
        lbmid = get_id('lbm_id','Water Percentage',SensorPercentage)
        bmiid = get_id('bmi_id','BMI',SensorCustom,'1;')
    except Exception, e:
        print str(e)
        log.error('Unable to access Domoticz sensors')
        return

    write_config = True

    if write_config:
        with open('BS440domoticz.ini', 'wb') as configfile:
            configDomoticz.write(configfile)
            configfile.close()

    return
    try:
        
        # calculate and populate variables
        weight = weightdata[0]['weight']
        fat_per = bodydata[0]['fat']
        fat_mass = weight * (fat_per / 100.0)
        water_per = bodydata[0]['tbw']
        water_mass = weight * (water_per / 100.0)
        muscle_per = bodydata[0]['muscle']
        muscle_mass = (muscle_per / 100) * weight
        bone_mass = bodydata[0]['bone']
        bone_per = (bone_mass / weight) * 100
        lbm = weight - (weight * (fat_per / 100.0))
        lbm_per = (lbm / weight) * 100
        kcal = bodydata[0]['kcal']
        bmi = 0
        for user in persondata:
            if user['person'] == bodydata[0]['person']:
                size = user['size'] / 100.0
                bmi = weight / (size * size)

        log_update = 'Updating Domoticz for user %s at index %s with '
       
        # Mass
        id = 79
        unit = 1

        log.info((log_update+'weight %s') % (user, id, weight))
        open_url(url_mass % (domoticzurl, hardwareid, id, unit, weight))

        log.info((log_update+'fat mass %s') % (user, id+1, fat_mass))
        open_url(url_mass % (domoticzurl, hardwareid, id+1, unit, fat_mass))

        log.info((log_update+'water mass %s') % (user, id+2, water_mass))
        open_url(url_mass % (domoticzurl, hardwareid, id+2, unit, water_mass))

        log.info((log_update+'muscle mass %s') % (user, id+3, muscle_mass))
        open_url(url_mass % (domoticzurl, hardwareid, id+3, unit, muscle_mass))

        log.info((log_update+'bone mass %s') % (user, id+4, bone_mass))
        open_url(url_mass % (domoticzurl, hardwareid, id+4, unit, bone_mass))

        log.info((log_update+'lean body mass %s') % (user, id+5, lbm))
        open_url(url_mass % (domoticzurl, hardwareid, id+5, unit, lbm))

        # Percentage

        log.info((log_update+'fat percentage %s') % (user, fatid, fat_per))
        open_url(url_per % (domoticzurl, fatid, fat_per))

        log.info((log_update+'water percentage %s') % (user, waterid, water_per))
        open_url(url_per % (domoticzurl, waterid, water_per))
               
        log.info((log_update+'muscle percentage %s') % (user, muscleid, muscle_per))
        open_url(url_per % (domoticzurl, muscleid, muscle_per))

        log.info((log_update+'bone percentage %s') % (user, boneid, bone_per))
        open_url(url_per % (domoticzurl, boneid, bone_per))

        log.info((log_update+'lean body mass percentage %s') % (user, lbmid, lbm_per))
        open_url(url_per % (domoticzurl, lbmid, lbm_per))
        
        # Other
        
        log.info((log_update+'calories %s') % (user, kcalid, kcal))
        open_url(url_per  % (domoticzurl, kcalid, kcal))
            
        log.info((log_update+'body mass index %s') % (user, bmiid, bmi))
        open_url(url_per  % (domoticzurl, bmiid, bmi))
        
        log.info('Domoticz succesfully updated')
    except Exception, e:
        print str(traceback.format_exc())
        print str(e)
        log.error('Unable to update Domoticz: Error sending data.')
