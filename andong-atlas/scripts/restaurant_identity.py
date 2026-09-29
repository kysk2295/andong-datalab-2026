"""Conservative business identity joins; shared address alone is insufficient."""
import re
import unicodedata

def normalize(value):
    return re.sub(r'\s|[()·]', '', unicodedata.normalize('NFC', value or ''))

def address(value):
    value = unicodedata.normalize('NFC', value or '')
    value = re.sub(r'\([^)]*\)', '', value).replace('경상북도', '').replace('경북', '')
    return normalize(value)

# Explicit source/catalog aliases; still require an identical road address.
ALIASES = {'신세계찜닭':'안동신세계찜닭', '원조안동찜닭':'원조안동찜닭본점'}

def same_business(place, source):
    name=normalize(place['name'])
    return (ALIASES.get(name,name)==normalize(source['title']) and
            bool(address(place.get('address'))) and address(place.get('address'))==address(source['addr1']))
