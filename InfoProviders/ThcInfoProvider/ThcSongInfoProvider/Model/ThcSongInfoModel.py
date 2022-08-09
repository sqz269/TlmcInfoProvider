from operator import truediv
from peewee import *

ThccDb = SqliteDatabase('./InfoProviders/ThcInfoProvider/ThcSongInfoProvider/Data/thc_song_data.db')


class BaseModel(Model):
    class Meta:
        database = ThccDb

class ProcessStatus:
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class Album(BaseModel):
    album_id = TextField(primary_key=True, unique=True)
    title_jp = TextField(null=True)
    title_jp_romanji = TextField(null=True)
    title_en = TextField(null=True)
    title_zh = TextField(null=True)

    release_date = TextField(null=True)
    convention = TextField(null=True)
    catalogno = TextField(null=True)

    number_of_disc = IntegerField(null=True)

    website = TextField(null=True)
    digital = TextField(null=True)

    arrangements = TextField(null=True)
    lyrics = TextField(null=True)
    vocals = TextField(null=True)
    album_artist = TextField(null=True)
    illustration = TextField(null=True)
    track_count = IntegerField(null=True)
    cover_image = TextField(null=True)
    cover_char = TextField(null=True)
    genre = TextField(null=True)

    data_source = TextField(null=True)

    seller = TextField(null=True)

    process_status = TextField(null=True)


class Track(BaseModel):
    track_id = TextField(primary_key=True, unique=True)
    album = ForeignKeyField(Album, backref='tracks')
    disc_no = IntegerField(null=True)
    index = IntegerField(null=True)
    title_jp = TextField(null=True)
    title_romanji = TextField(null=True)
    title_en = TextField(null=True)
    title_zh = TextField(null=True)
    duration = TextField(null=True)
    arrangement = TextField(null=True)
    composer = TextField(null=True)
    circle = TextField(null=True)
    lyrics = TextField(null=True)
    lyrics_author = TextField(null=True)
    vocal = TextField(null=True)

    original = TextField(null=True)
    original_title = TextField(null=True)
    original_release_album = TextField(null=True)
    original_release_title = TextField(null=True)
    
    src_album_not_th = TextField(null=True)
    src_track_not_th = TextField(null=True)

    source = TextField(null=True)

    process_status = TextField(null=True)

class SaleSource(BaseModel):
    sell_id = TextField(primary_key=True, unique=True)
    album = ForeignKeyField(Album, backref='sales')
    type = TextField(null=True)
    path = TextField(null=True)
    title = TextField(null=True)


ThccDb.connect()
ThccDb.create_tables([Track, Album, SaleSource])
