# Privileges

Complementing Raveberry's [base functionality](functionality.md), additional features are available to logged in users. By visiting the `/login` page, multiple privilege levels can be obtained. Since logins tend to happen quite rarely, this page is not linked from the main page. You can log in with one of the following users and the respective passwords you assigned to them. The default passwords for the `mod` user is `mod`. If you want to change it (you should), set it in the `.env` file.

## Mod
The `mod` user is able to change the playback. They can change the volume (if supported by the player), seek the current song or skip it. They are also allowed to remove songs from the queue regardless of their score.

With mod privileges, playlists can be requested. A new icon appears next to the dice that enables playlist mode. Subsequent searches will then lead to each song of the found playlist being added after one another. Additionally, a robot icon will appear that can be used to add recommendations for the currently playing song.

## Admin
The `admin` user has full access to the page. This user is also the superuser for the webframework. By visiting `/admin` they can edit the database and change user passwords. In addition to all previously mentioned permissions, this user can access `/settings`. On this page, the behavior of Raveberry can be customized extensively.