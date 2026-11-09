# Spotify

Raveberry uses the Spotify API to play songs on any of your devices (e.g. your phone).
Your Raveberry instance can be anywhere, as long as it's connected to the internet.

Setup:
* Enable your account for https://developer.spotify.com/
* Create a new App in your [dashboard](https://developer.spotify.com/dashboard)
* In Redirect URIs, add `http://127.0.0.1:8888/callback`
* Copy the client id and client secret
* Open the `/settings` of your Raveberry instance
* Go to the Spotify section for device playback
* Provide the client id, client secret and redirect uri from the app in your Spotify dashboard
* Click the link that appears
* Authenticate with your Spotify Account
* Copy the link that you are redirected to from the address bar of your browser
* Provide this link to "Auth Url"
* Click "Set Credentials"
* Enable Spotify (checkbox at the top of the settings section)
* Make sure your desired output device is active (e.g. by playing any song on your phone)
* In the "Sound Output" section, click the dropdown for Output
* Choose your Spotify device

Now Raveberry should be able to see and control your devices.
Test it by queuing any Spotify song from the main page. You might need to restart Raveberry.

The requested permissions and their uses are:
* `user-read-playback-state`: list devices, currently playing
* `user-modify-playback-state`: play songs, pause, seek, volume
* `playlist-read-private, playlist-read-collaborative, user-library-read`: suggest private playlists and songs in search