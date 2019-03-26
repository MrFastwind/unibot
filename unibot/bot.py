import logging
from os import environ
from datetime import datetime, date, time, timedelta
import time as os_time

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

import unibot.messages as messages
import unibot.users
import unibot.courses as courses
import unibot.class_schedule as class_schedule
import unibot.conversations.setup
import unibot.conversations.remindme

class Bot:
    def __init__(self):
        self.users = unibot.users.UserRepo
        self.user_settings = unibot.users.UserSettingsRepo
        self.updater = Updater(token=environ['BOT_TOKEN'], use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.handlers = [
            CommandHandler('start', self.cmd_start),
            CommandHandler('help', self.cmd_command_list),
            CommandHandler('orario', self.cmd_schedule_today),
            CommandHandler('oggi', self.cmd_schedule_today),
            CommandHandler('domani', self.cmd_schedule_tomorrow),
            CommandHandler('nonricordarmi', self.cmd_remindme_off),
            unibot.conversations.setup.get_handler(),
            unibot.conversations.remindme.get_handler()
        ]
        self.daily_schedule_repeat_every = timedelta(minutes=5)
        self.daily_schedule_last_run = datetime.now()

    def run(self):
        self.register_handlers()
        self.dispatcher.job_queue.run_repeating(self.daily_schedule, self.daily_schedule_repeat_every)
        # self.dispatcher.job_queue.run_once(self.daily_schedule, 3)
        self.dispatcher.job_queue.start()
        self.updater.start_polling(poll_interval=1.0)
        self.updater.idle()

    def register_handlers(self):
        for h in self.handlers:
            self.dispatcher.add_handler(h)

    def cmd_start(self, update, context):
        if (environ['TESTING'] == '1'):
            self.send(update, context, ("Io non sono il vero UniBot ma solo un'istanza di test.\n"
                                        "Usa @unibo_orari_bot"))
            return
        self.send(update, context, messages.CMD_START)

    def cmd_command_list(self, update, context):
        self.send(update, context, messages.COMMAND_LIST.format(environ['BOT_VERSION']))

    def cmd_schedule_today(self, update, context):
        settings = self.user_settings().get(update.effective_user.id, update.effective_chat.id)
        if settings is None:
            self.send(update, context, messages.NEED_SETUP)
            return
        logging.info("REQUEST schedule_today course_id={} year={} curricula={}".format(
            settings.course_id, settings.year, settings.curricula))
        schedule = class_schedule.get_schedule(settings.course_id, settings.year, settings.curricula).today()
        if not schedule.has_events():
            self.send(update, context, messages.NO_LESSONS_TODAY)
            return
        self.send(update, context, schedule.tostring(with_date=True))

    def cmd_schedule_tomorrow(self, update, context):
        settings = self.user_settings().get(update.effective_user.id, update.effective_chat.id)
        if settings is None:
            self.send(update, context, messages.NEED_SETUP)
            return
        logging.info("REQUEST schedule_tomorrow course_id={} year={} curricula={}".format(
            settings.course_id, settings.year, settings.curricula))
        schedule = class_schedule.get_schedule(settings.course_id, settings.year, settings.curricula).tomorrow()
        if not schedule.has_events():
            self.send(update, context, messages.NO_LESSONS_TOMORROW)
            return
        self.send(update, context, schedule.tostring(with_date=True))

    def cmd_remindme_off(self, update, context):
        settings = self.user_settings()
        setting = settings.get(update.effective_user.id, update.effective_chat.id)
        if setting is None:
            self.send(update, context, messages.NEED_SETUP)
            return
        setting.do_remind = False
        settings.update(setting)
        self.send(update, context, messages.REMINDME_OFF)

    def daily_schedule(self, context):
        settings_repo = self.user_settings()
        now = datetime.now()
        users = settings_repo.get_to_remind()
        users = [u for u in users if u.remind_time is not None]
        users = [u for u in users if self.daily_schedule_last_run.time() < u.remind_time <= now.time()]
        logging.info('Sending todays schedule to {} users'.format(len(users)))
        for user in users:
            schedule = class_schedule.get_schedule(user.course_id, user.year, user.curricula)
            if not schedule.week_has_lessons():
                continue
            try:
                context.bot.send_message(chat_id=user.chat_id, parse_mode=ParseMode.HTML, text=schedule.today().tostring(with_date=True))
            except Exception as e:
                logging.warning(e)
                settings_repo.delete(user)
            os_time.sleep(0.1)
        self.daily_schedule_last_run = now
        logging.info("Done sending daily schedule")

    def send(self, update, context, text):
        context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.HTML, text=text)
