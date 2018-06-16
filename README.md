### standup-bot
A slack bot for performing daily standups. Requires a server.

### Setup (Linux)
* Install the SlackClient library using pip with `pip install slackclient`
* Create a new [Slack app](api.slack.com) with any name and workspace
* Install the app on your workspace under settings -> Install App. This will generate an OAuth Access Token
* Create a new system variable 'SLACK_BOT_TOKEN' with the Bot User OAuth token, using `export SLACK_BOT_TOKEN='<token>'`
* Run the bot with with command `python standupbot.py <hour of standup> <standup minute> <Channel id>`

**Note:**  
The channel id can be found in the url of the slack channel, e.g. `example.slack.com/messages/CB9NYSS5D/`
