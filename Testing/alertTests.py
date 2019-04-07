from notify_run import Notify


def run():
	notify = Notify()

	userMessage = input('Input a message to send\n')

	notify.send(userMessage)

