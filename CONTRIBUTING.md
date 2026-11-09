# Quick start for contributors

## Dependencies for development

Install dependencies for raveberry (if not already installed for running raveberry before)
```
sudo apt install -y python3-pip ffmpeg gstreamer1.0-plugins-bad inetutils-ping mopidy postgresql redis-server
```

Install [yarn](https://classic.yarnpkg.com/lang/en/docs/install/).

## Setup Github

Configure git (if not already done for another github project)
https://kbroman.org/github_tutorial/pages/first_time.html

Fork repository on github from https://github.com/raveberry/raveberry/

Clone your own forked repository
```
git clone https://github.com/stappjno/raveberry.git
```

Add remote upstream source (original repo!)
```
cd raveberry/
git remote add upstream https://github.com/raveberry/raveberry.git
```

## Create a branch
Make sure your local and forked repo are in sync with the original repo
```
git pull upstream master && git push origin master
```

Create branch, use "bugfix" or "feature" as type and replace "readme-update" with whatever you are working on
```
git checkout -b feature/readme-update
```

## Start virtual enviroment for development


Create new virtual enviroment for python development
```
python3 -m venv .venv
```

Use new virtual Enviroment (required each time you start a bash session)
```
. .venv/bin/activate
```

Install dev dependencies
```
cd raveberry/
pip3 install -r backend/requirements/dev.txt
```

Start development server
```
bin/raveberry run
```

Fix the issue / add the feature described in your branch

## Build frontend

```
cd frontend
yarn install
yarn build
```

You can also use the `yarn js` and `yarn css` commands to only build the javascript or css files. Use `yarn watch-js` and `yarn watch-css` to automatically rebuild on file changes.

## Build docker containers

Make sure docker in installed. From the root Raveberry directory, run:
```
docker/build.sh
```


## Push & PR

Push your branch to your forked repo
```
git push -u origin feature/readme-update
```

Navigate with your browser to your fork on github and "compare & pull request"
Give your PR a good title and description that we can see what you've added / fixed
Check if the diff of your changes is what you expected
Push the "Create pull request" button!

## Code Quality

Format code
```
black backend bin/raveberry
```
Check types
```
# mypy does not work if backend/__init__.py is present
# alternatively, the config could be adapted to allow running mypy from the backend/ folder,
# but then IDEs would not be able to use mypy
rm backend/__init__.py
mypy
git checkout backend/__init__.py
```
Lint code
```
pylint backend/core backend/main
pylint --disable=missing-module-docstring,missing-class-docstring,missing-function-docstring backend/tests
## the .pylintrc only works with files in backend/, change directory to lint the binary
cd bin
pylint raveberry
```
Run Tests
```
# run raveberry once with postgres to initialize the database
bin/raveberry run --postgres --seed-only
# allow raveberry user to create databases
sudo -u postgres psql -c "ALTER ROLE raveberry CREATEDB;"
# run tests
mopidy
# in a different shell
python3 backend/manage.py test
```
