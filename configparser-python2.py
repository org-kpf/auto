import ConfigParser
import time
config = ConfigParser.ConfigParser()
config.add_section('global')
config.set('Testing', 'name', 'Yohannes')
config.set('Testing', 'age', '10')
file_name = str(int(time.time()))
with open(file_name, 'wt') as configfile:
    # config.write(configfile, space_around_delimiters=False)
    config.write(configfile)