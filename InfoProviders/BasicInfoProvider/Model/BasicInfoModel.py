from peewee import *
import os

print(os.getcwd())

BasicInfoDb = SqliteDatabase(r'./InfoProviders/BasicInfoProvider/data/song_data.db')

class BaseModel(Model):
    class Meta:
        database = BasicInfoDb

class BasicAlbum(BaseModel):
    album_id = TextField(primary_key=True, unique=True)
    album_name = TextField()
    cue_path = TextField()
    performer = TextField(null=True)
    error_status = TextField(null=True)

class BasicTrack(BaseModel):
    track_id = TextField(primary_key=True, unique=True)
    album = ForeignKeyField(BasicAlbum, backref='tracks')
    index = IntegerField(null=True)
    title = TextField(null=True)
    offset = TextField(null=True)
    flac = TextField(null=True)
    error_status = TextField(null=True)

BasicInfoDb.connect()
BasicInfoDb.create_tables([BasicAlbum, BasicTrack])
