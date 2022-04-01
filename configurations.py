class BaseConfig(object):
    '''
    Base config class
    '''
    DEBUG = True
    TESTING = False

class ProductionConfig(BaseConfig):
    '''
    Production config class
    '''
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    '''
    Develoment config class
    '''
    DEBUG = True
    TESTING = True