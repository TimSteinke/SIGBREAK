#!/usr/bin/env python3

import datetime
from time import sleep
import sys
import curses

class SigBreak:
    RATIO = 0.16

    # states
    WORKING = 0
    ON_BREAK = 1
    SHOULD_WORK = 2

    state = WORKING

    def __init__(self):
        # time at which current work/break period started
        self.t_last_change = datetime.datetime.now()

        # total work/break time (except current period)
        self.work_time = datetime.timedelta(0)
        self.break_budget = datetime.timedelta(0)

        # init curses
        curses.wrapper(self.main)


    def main(self, stdscr):
        # hide cursor
        curses.curs_set(0)

        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)

        stdscr.clear()

        # make getkey() non-blocking
        stdscr.nodelay(True)

        while True:
            self.draw_screen_menu(stdscr)
            self.step(stdscr)
            try:
                key = stdscr.getkey()
                self.handle_input(key)
            except curses.error:
                # curses throws an error if no key was pressed
                pass
            sleep(0.02)


    def step(self, stdscr):
        """ Update timers on screen and handle automatic state changes.
        """
        dt_current_episode = datetime.datetime.now() - self.t_last_change
        if self.state == self.WORKING:
            work_timer_str = str(self.work_time + dt_current_episode)
            break_timer_str = str(self.break_budget + self.RATIO * dt_current_episode)
            stdscr.addstr(3, 0, work_timer_str[:-7])
            stdscr.addstr(3, 15, break_timer_str[:-7])
        elif self.state == self.ON_BREAK:
            if dt_current_episode > self.break_budget:
                self.should_work()
            else:
                work_timer_str = str(self.work_time)
                break_timer_str = str(self.break_budget - dt_current_episode)
                stdscr.addstr(3, 0, work_timer_str[:-7])
                stdscr.addstr(3, 15, break_timer_str[:-7])
        elif self.state == self.SHOULD_WORK:
            # hack to enable blinking in rxvt-unicode (TODO: fix terminal setup/switch?)
            if dt_current_episode.seconds % 2 == 0:
                stdscr.addstr(0, 0, "          #### Time to work! ####          ", curses.A_REVERSE)
            else:
                stdscr.addstr(0, 0, "          #### Time to work! ####          ")
            stdscr.addstr(0, 43, "                                           ")
            work_timer_str = str(self.work_time)
            break_timer_str = str(self.break_budget)
            stdscr.addstr(3, 0, work_timer_str[:-7])
            stdscr.addstr(3, 15, break_timer_str[:-7])
        stdscr.refresh()

    def draw_screen_menu(self, stdscr):
        stdscr.addstr(0, 0, f"Welcome to SIGBREAK. Break/Work ratio is {self.RATIO}.")
        stdscr.addstr(5, 0, "[q]uit         [space] toggle work/break")

        if self.state == self.SHOULD_WORK:
            stdscr.addstr(2, 0, "[w]ork")
            stdscr.addstr(2, 15, "[b]reak")

        if self.state == self.WORKING:
            stdscr.addstr(2, 0, "[w]ork", curses.A_BOLD)
            stdscr.addstr(2, 15, "[b]reak")

        if self.state == self.ON_BREAK:
            stdscr.addstr(2, 0, "[w]ork")
            stdscr.addstr(2, 15, "[b]reak", curses.A_BOLD)
        stdscr.refresh()


    def should_work(self):
        assert self.state == self.ON_BREAK
        self.state = self.SHOULD_WORK
        self.break_budget = datetime.timedelta(0)
        self.t_last_change = datetime.datetime.now()


    def work(self):
        assert (self.state in [self.ON_BREAK, self.SHOULD_WORK])
        if self.state == self.ON_BREAK:
            # update break budget if previously on break
            dt_current_episode = datetime.datetime.now() - self.t_last_change
            self.break_budget -= dt_current_episode
        self.t_last_change = datetime.datetime.now()
        self.state = self.WORKING

    def take_break(self):
        assert self.state == self.WORKING
        # update work timer
        dt_current_episode = datetime.datetime.now() - self.t_last_change
        self.work_time += dt_current_episode
        self.break_budget += dt_current_episode * self.RATIO
        self.t_last_change = datetime.datetime.now()
        self.state = self.ON_BREAK

    def handle_input(self, key):
        if key == "w" and (self.state in [self.ON_BREAK, self.SHOULD_WORK]):
            self.work()
        elif key == " " and (self.state in [self.ON_BREAK, self.SHOULD_WORK]):
            self.work()
        elif key == "b" and self.state == self.WORKING:
            self.take_break()
        elif key == " " and self.state == self.WORKING:
            self.take_break()
        elif key == "q":
            sys.exit(0)

SigBreak()
