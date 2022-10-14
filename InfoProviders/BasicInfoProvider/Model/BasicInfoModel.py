from peewee import *
import os

print(os.getcwd())

BasicInfoDb = SqliteDatabase(r'./InfoProviders/BasicInfoProvider/data/new_song_data.db')

class BaseModel(Model):
    class Meta:
        database = BasicInfoDb

class BasicAlbum(BaseModel):
    album_id = TextField(primary_key=True, unique=True)
    album_name = TextField()
    performer = TextField(null=True)
    release_date = TextField(null=True)
    disc_id = TextField(null=True)
    release_convention = TextField(null=True)
    catalog_number = TextField(null=True)
    album_img = TextField(null=True)
    other_img = TextField(null=True)
    other_files = TextField(null=True)
    error_status = TextField(null=True)
    
    need_cue_split = BooleanField(default=False)
    target_cue_path = TextField(null=True)
    target_audio = TextField(null=True)

class BasicTrack(BaseModel):
    track_id = TextField(primary_key=True, unique=True)
    album = ForeignKeyField(BasicAlbum, backref='tracks')
    index = IntegerField(null=True)
    title = TextField(null=True)
    offset = TextField(null=True)
    performer = TextField(null=True)
    flac = TextField(null=True)
    error_status = TextField(null=True)

BasicInfoDb.connect()
BasicInfoDb.create_tables([BasicAlbum, BasicTrack])
