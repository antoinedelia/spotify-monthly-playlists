import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dataclasses import dataclass
from datetime import datetime
import argparse
from itertools import groupby


@dataclass
class Track:
    """Class to get basic information about a Spotify track"""
    id: str
    name: str
    added_at: datetime


parser = argparse.ArgumentParser()
parser.add_argument('--public', required=False, action='store_true',
                    help='Will make the newly created playlists public',
                    dest='public')
args = parser.parse_args()

IS_PUBLIC = args.public
privacy = 'public' if IS_PUBLIC else 'private'
print(f"The playlists will be created in {privacy} mode.")

# Authenticate to Spotify
scope = f'user-library-read playlist-modify-{privacy} playlist-read-private playlist-read-public'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
print("Successfully authenticated!")


# We get all the user's playlists
PLAYLISTS = []
results = sp.current_user_playlists(limit=50)
while results['next']:
    for item in results['items']:
        PLAYLISTS.append(item['name'])
    results = sp.next(results)
# We do an extra for loop to get the last tracks
for item in results['items']:
    PLAYLISTS.append(item['name'])


# Getting all the user's tracks
ALL_USER_TRACKS = []


def add_track(item):
    ALL_USER_TRACKS.append(Track(
            id=item['track']['id'],
            name=item['track']['name'],
            added_at=datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%SZ'),
        ))


results = sp.current_user_saved_tracks()
while results['next']:
    for item in results['items']:
        add_track(item)
    results = sp.next(results)

# We do an extra for loop to get the last tracks
for item in results['items']:
    add_track(item)

# Reverse tracks so that the oldest ones are at the top
ALL_USER_TRACKS[::-1]

start = ALL_USER_TRACKS[0].added_at
end = ALL_USER_TRACKS[-1].added_at

print(f"First song was added at: {start}")
print(f"Last song was added at: {end}")

dates = [track.added_at for track in ALL_USER_TRACKS[::-1]]
year_months = map(lambda x: (x.year, x.month), dates)

init = 0
CREATED_PLAYLISTS_IDS = []
# Iterate over all the grouped months/years
for v, g in groupby(year_months):
    year, month = v[0], "%02d" % int(v[1])
    playlist_name = f"{year}/{month}"
    number_of_songs = sum(1 for _ in g)
    print(f"Found {number_of_songs} songs for {playlist_name}")

    songs_id = [track.id for track in ALL_USER_TRACKS[init:number_of_songs+init]]
    init = init + number_of_songs

    # Check if playlist already exists and skip if it does
    if playlist_name in PLAYLISTS:
        print(f"Playlist {playlist_name} already exists, skipping.")
        continue

    # Create playlist
    current_user_id = sp.current_user()['id']
    new_playlist_id = sp.user_playlist_create(user=current_user_id, name=playlist_name, public=IS_PUBLIC)['id']
    CREATED_PLAYLISTS_IDS.append(new_playlist_id)

    # Can't add more than 100 songs at a time
    for i in range(0, len(songs_id), 100):
        sp.user_playlist_add_tracks(user=current_user_id, playlist_id=new_playlist_id, tracks=songs_id[i:i+100])

print(f"Created {len(CREATED_PLAYLISTS_IDS)} playlists.")
