import os
import sys
import time
import datetime
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
REPORT_HOUR = int(sys.argv[1])
REPORT_MINUTE = int(sys.argv[2])
REPORT_GREETING = "It's time for your weather report!"
REPORT_QUESTIONS = ("What's the weather looking like?",
                    "How are your tasks going?",
                    "Do you need help with your tasks?")
NUM_QUESTIONS = len(REPORT_QUESTIONS)
RESULTS_CHANNEL = sys.argv[3]
FINISH_MESSAGE = "That's all for today!"


class User:
    """
    User class to hold status and responses of each user
    """
    def __init__(self, user_id, user_dm_id, user_name, user_img, user_status="WAITING"):
        """
        Constructor for the user
        :param user_id: slack id of the user
        :param user_status: current status of the user
        """
        self.id = user_id
        self.dm_id = user_dm_id
        self.status = user_status
        self.response = []
        self.name = user_name
        self.img = user_img


def formulate_user_responses(user):
    """
    Function to create the user response for the thread, returns None if the user's status is not 'DONE'
    :param user: user object to gather the responses for
    :return: A response to add to the thread of responses, None if the user's status is not 'DONE'
    """
    result = ""
    for i in range(len(user.response)):
        result += "*{}*\n".format(REPORT_QUESTIONS[i])
        result += "{}\n".format(user.response[i])

    return result


def send_start_messages(user):
    """
    Sends the initial greeting and question to the specified user
    :param user: user object to send greeting to
    :return: None
    """
    slack_client.api_call(
        "chat.postMessage",
        channel=user.dm_id,
        text=REPORT_GREETING
    )
    send_next_question(user)


def update_results_thread(users, thread):
    """
    Updates the results thread in the results channel
    :param users: a dict holding all the users
    :param thread:
    :return:
    """
    for user in users:
        if users[user].status == "DONE":
            slack_client.api_call(
                "chat.postMessage",
                channel=users[user].dm_id,
                text=FINISH_MESSAGE
            )
            if thread is None:  # creates a new message to the channel
                thread = slack_client.api_call(
                    "chat.postMessage",
                    channel=RESULTS_CHANNEL,
                    text="Here are the results of today's weather report"
                )["ts"]

            user_response = formulate_user_responses(users[user])
            slack_client.api_call(
                "chat.postMessage",
                channel=RESULTS_CHANNEL,
                thread_ts=thread,
                username=users[user].name,
                icon_url=users[user].img,
                text=user_response
            )
    return thread


def update_user_responses(users):
    """
    Updates the user responses for all the users, and changes their status to WAITING if they have responded
    :param users: a dictionary of users mapped by their user ids
    :return: None
    """
    for event in slack_client.rtm_read():
        if event["type"] == "message" and "subtype" not in event:
            for user in users:
                if (event["channel"] == users[user].dm_id) and (users[user].status == "RESPONDING"):
                    users[user].response.append(event["text"])
                    users[user].status = "WAITING"


def send_next_question(user):
    """
    Sends the user the next question if their status is WAITING
    :param user: a user object
    :return: None
    """
    if user.status == "WAITING":
        question_index = len(user.response)
        if question_index == NUM_QUESTIONS:
            user.status = "DONE"
        else:
            slack_client.api_call(
                "chat.postMessage",
                channel=user.dm_id,
                text=REPORT_QUESTIONS[question_index]
            )
            user.status = "RESPONDING"


def start_weather_report():
    """
    Starts the weather report for the users
    :return: None
    """
    users = dict()
    thread = None
    finished = False

    # Collates all the user ids into a dictionary with a list of users
    for user in slack_client.api_call("users.list")["members"]:
        if not user["is_bot"] and user["id"] != "USLACKBOT":
            users[user["id"]] = User(user["id"],
                                     slack_client.api_call("im.open", user=user["id"])["channel"]["id"],
                                     user["profile"]["display_name"],
                                     user["profile"]["image_512"])

    for user in users.keys():
        send_start_messages(users[user])
        users[user].status = "RESPONDING"

    while not finished:
        update_user_responses(users)
        finished = True  # assumes it is done until it checks all the users
        for user in users:
            send_next_question(users[user])
            if users[user].status != "DONE":  # if any of the users are not done, the finished flag is set to False
                finished = False
        thread = update_results_thread(users, thread)
        time.sleep(RTM_READ_DELAY)  # polls once every second


# Main
if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling the Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            curr_time = datetime.datetime.now().time()
            if curr_time.hour == REPORT_HOUR and curr_time.minute == REPORT_MINUTE and curr_time.second == 0:
                start_weather_report()
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
