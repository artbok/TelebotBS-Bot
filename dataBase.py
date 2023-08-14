from peewee import *

conn = SqliteDatabase('values.db')

class BaseModel(Model):
    class Meta:
        database = conn