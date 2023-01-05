from peewee import *
import os

print(os.getcwd())

BasicInfoDb = SqliteDatabase(r'./InfoProviders/BasicInfoProvider/data/new_song_data.db')

class BaseModel(Model):
    class Meta:
        database = BasicInfoDb

class BasicCircle(BaseModel):
    id = TextField(primary_key=True, unique=True)
    name = TextField(null=True)
    alias = TextField(null=True)

class BasicCircleUnparsedMap(BaseModel):
    id = TextField(primary_key=True, unique=True)
    unparsed_name = TextField()
    circle_id = ForeignKeyField(BasicCircle, backref='circle')

class BasicAlbum(BaseModel):
    album_id = TextField(primary_key=True, unique=True)
    album_name = TextField()
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

class BasicAlbumPerformer(BaseModel):
    album_id = ForeignKeyField(BasicAlbum, backref='albums')
    performer_id = ForeignKeyField(BasicCircle, backref='circles')

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
BasicInfoDb.create_tables([BasicAlbum, BasicTrack, BasicCircle, BasicCircleUnparsedMap, BasicAlbumPerformer])
