# Piker Bot

Stock trading bot for executing planned trades for me while I work

## Features
- TO DO

## Configuration
- TO DO

## Running the Bot

`docker build -f Dockerfile -t piker-bot .`

`docker run --name piker_bot -d -v [PATH_TO_YOUR_DATA_FOLDER]:/var/lib/piker-bot -v [PATH_TO_YOUR_CODE_FOLDER]:/app piker-bot:latest`
`docker run --name piker_bot -d -v d:/development/docker-data:/var/lib/piker-bot -v d:/development/piker-bot:/app piker-bot:latest`

