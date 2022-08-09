import datetime
import os
import re
import mwparserfromhell as mw
from urllib.parse import unquote, urlparse

try:
    from InfoProviders.CacheInfoProvider.Model.CacheModel import SourceCacheTable
except:
    from Model.CacheModel import SourceCacheTable

def NormalizePath(path, subchar="_"):
    return re.sub(r'\<|\>|\:|\"|\/|\\|\||\?|\*', subchar, path)

def get_url_path(url):
    parsed = urlparse(url)
    return parsed.path

def cached(cache_id, cache_dir, debug=False):
    if (not os.path.isdir(cache_dir)):
        os.makedirs(cache_dir, exist_ok=True)

    def actual_decorator(func):
    
        def wrapper(url):
            path_id = cache_id + "__" + NormalizePath(unquote(get_url_path(url)))
            if (SourceCacheTable.select().where(SourceCacheTable.path == path_id).exists()):
                cached = SourceCacheTable.get(SourceCacheTable.path == path_id).cached_source_path
                if (cached != "" and os.path.exists(cached)):
                    if (debug):
                        print("Cache Hit for " + url)
                    with open(cached, "r", encoding="utf-8") as f:
                        return mw.parse(f.read())
            if (debug):
                print("Cache Miss for " + url)
            src = func(url)
            with open(caced_src_path := os.path.join(cache_dir, path_id), 'w', encoding="utf-8") as f:
                if (debug):
                    print("Caching " + url)
                f.write(str(src))
                if (SourceCacheTable.select().where(SourceCacheTable.path == path_id).exists()):
                    SourceCacheTable.replace(path=path_id, cached_source_path=caced_src_path, time_cached=datetime.datetime.now())
                else:
                    SourceCacheTable.create(path=path_id, cached_source_path=caced_src_path, time_cached=datetime.datetime.now())
            return src

        return wrapper
    
    return actual_decorator
