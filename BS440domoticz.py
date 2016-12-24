'''
BS440domoticz.py
Update weight value to Domoticz home automation system
'''

import urllib
import base64
import logging
import traceback

def UpdateDomoticz(config, weightdata, bodydata, persondata):
    log = logging.getLogger(__name__)
    domoticzurl = config.get('Domoticz', 'domoticz_url')
    hardware_id =  config.get('Domoticz', 'hardware_id')
    domoticzuser = ""
    domoticzpwd = ""

    # read user's name
    personsection = 'Person' + str(weightdata[0]['person'])
    if config.has_section(personsection):
        user = config.get(personsection, 'username')
    else:
        log.error('Unable to update Domoticz: No details found in ini file '
                  'for person %d' % (weightdata[0]['person']))
        return

    # read domoticz ids from domoticz section
    personsection = 'Domoticz.' + personsection
    if config.has_section(personsection):
        fatid = config.get(personsection, 'fat_id')
        kcalid = config.get(personsection, 'kcal_id')
        muscleid = config.get(personsection, 'muscle_id')
        boneid = config.get(personsection, 'bone_id')
        waterid = config.get(personsection, 'water_id')
        bmiid = config.get(personsection, 'bmi_id')
        lbsid = config.get(personsection, 'lbs_id')
    else:
        log.error('Unable to update Domoticz: No details found in domoticz section of the ini file '
                  'for person %d' % (weightdata[0]['person']))
        return
    try:
        
        def callurl(url):
            log.debug('calling url: %s' % (url))
            try:
                response = urllib.urlopen(url)
            except Exception, e:
                log.error('Failed to send data to Domoticz (%s)' % (url))

        url_mass = 'http://%s/json.htm?type=command&param=udevice&hid=%s&' \
              'did=%s&dunit=%s&dtype=93&dsubtype=1&nvalue=0&svalue=%s'
        url_per = 'http://%s/json.htm?type=command&param=udevice&idx=%s&nvalue=0&svalue=%s'
        
        id = 79
        unit = 1

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
        lbs_mass = weight - (weight * (fat_per / 100.0))
        lbs_per = (lbs_mass / weight) * 100
        kcal = bodydata[0]['kcal']
        bmi = 0
        for user in persondata:
            if user['person'] == bodydata[0]['person']:
                size = user['size'] / 100.0
                bmi = weight / (size * size)

        log_update = 'Updating Domoticz for user %s at index %s with '
       
        # Mass
        log.info(log_update+'weight %s' % (user, id, weight))
        callurl(url_mass % (domoticzurl, hardwareid, id, unit, weight))

        log.info(log_update+'fat mass %s' % (user, id+1, fat_mass))
        callurl(url_mass % (domoticzurl, hardwareid, id+1, unit, fat_mass))

        log.info(log_update+'water mass %s' % (user, id+2, water_mass))
        callurl(url_mass % (domoticzurl, hardwareid, id+2, unit, water_mass))

        log.info(log_update+'muscle mass %s' % (user, id+3, muscle_mass))
        callurl(url_mass % (domoticzurl, hardwareid, id+3, unit, muscle_mass))

        log.info(log_update+'bone mass %s' % (user, id+4, bone_mass))
        callurl(url_mass % (domoticzurl, hardwareid, id+4, unit, bone_mass))

        log.info(log_update+'lean body mass %s' % (user, id+5, lbs_mass))
        callurl(url_mass % (domoticzurl, hardwareid, id+5, unit, lbs_mass))

        # Percentage

        log.info(log_update+'fat percentage %s' % (user, fatid, fat_per))
        callurl(url_per % (domoticzurl, fatid, fat_per))

        log.info(log_update+'water percentage (TBW) %s' % (user, waterid, water_per))
        callurl(url_per % (domoticzurl, waterid, water_per))
               
        log.info(log_update+'muscle percentage %s' % (user, muscleid, muscle_per))
        callurl(url_per % (domoticzurl, muscleid, muscle_per))

        log.info(log_update+'bone percentage %s' % (user, boneid, bone_per))
        callurl(url_per % (domoticzurl, boneid, bone_per))

        log.info(log_update+'lean body mass percentage %s' % (user, lbsid, lbs_per))
        callurl(url_per % (domoticzurl, lbsid, lbs_per))
        
        # Other
        
        log.info(log_update+'calories %s' % (user, kcalid, kcal))
        callurl(url_per  % (domoticzurl, kcalid, kcal))
            
        log.info(log_update+'body mass index %s' % (user, bmiid, bmi))
        callurl(url_per  % (domoticzurl, bmiid, bmi))
        
        log.info('Domoticz succesfully updated')
    except Exception, e:
        print str(traceback.format_exc())
        print str(e)
        log.error('Unable to update Domoticz: Error sending data.')
