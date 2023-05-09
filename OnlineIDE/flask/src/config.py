import os
import secrets

class Config:
    SECRET_KEY  = secrets.token_hex(16)
    REDIS_URL   = os.environ['REDIS_URL']

class ProductionConfig(Config):
    DEBUG       = False

class DevelopmentConfig(Config):
    DEBUG       = True

config  = {
    "development"   : DevelopmentConfig,
    "production"    : ProductionConfig
}